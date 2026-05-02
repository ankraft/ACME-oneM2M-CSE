#
#	RemoteCSEManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles the registration to remote CSEs as well as the management
#	of remotly registered CSEs in this CSE. It also handles the forwarding of
#	transit requests to remote CSEs.
#

"""	This module implements remote CSR registration service and helper functions. """

from __future__ import annotations
from typing import List, Tuple, Dict, cast, Optional, Any

from ...etc.Types import CSEStatus, ResourceTypes, CSEType, ResponseStatusCode, JSON, CSERequest, Operation
from ...etc.Types import ContentSerializationType, BindingType, CSERegistrar
from ...etc.ResponseStatusCodes import exceptionFromRSC, ResponseException, NOT_FOUND, BAD_REQUEST, INTERNAL_SERVER_ERROR, CONFLICT, TARGET_NOT_REACHABLE
from ...etc.ACMEUtils import pureResource
from ...etc.IDUtils import csiFromRelativeAbsoluteUnstructured, isValidSPID, isValidCSI, isAbsolute, getSPFromID, toSPRelative	# cannot import at the top because of circel import
from ...etc.Utils import isHttpUrl, isWSUrl, buildBasicAuthUrl, normalizeURL
from ...etc.Constants import Constants, RuntimeConstants as RC
from ...helpers.TextTools import findXPath, setXPath
from ...helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ...resources.CSR import CSR
from ...resources.CSEBase import CSEBase, getCSE
from ...resources.Resource import Resource
from ...runtime.Factory import Factory
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime import CSE
from ...runtime.EventManager import EventManager, EventHandler, onEvent, EventData
from ...runtime.Logging import Logging as L
from ...runtime.PluginSupport import plugin, start, stop, restart, configure, validate
from ...services.RegistrationManager import RegistrationManager
from ...services.Dispatcher import Dispatcher

eventManager = EventManager()	# type: ignore
"""	Event manager singleton instance. """

registration: RegistrationManager = RegistrationManager()	# type: ignore
"""	Registration manager singleton instance. """

dispatcher: Dispatcher = Dispatcher()	# type: ignore
"""	Dispatcher singleton instance. """

factory: Factory = Factory()	# type: ignore
""" Factory singleton instance. """

@EventHandler
@plugin(property='remoteCSEManager', tags=['acme', 'remote'], priority=20)
class RemoteCSEManager(object):
	"""	This class defines functionalities to handle remote CSE/CSR registrations.

		Attributes:
			connectionMonitor: A `BackgroundWorker` that periodically checks the registrations.
			descendantCSR: A dictionary of descendant CSEs mappings: csi -> (CSR, registeredATcsi)
			registrarConfig: The local registrar configuration entry.
			spRegistrarConfigs: A dictionary of all SP registrar configurations except the own one.
	"""

	remoteCSEManager: Optional[Any] = None

	__slots__ = (
		'connectionMonitor',
		'descendantCSR',
		'registrarConfig',
		'spRegistrarConfigs',
	)


	def __init__(self) -> None:
		"""	Class constructor.
		"""

		# Some manager attributes
		self.connectionMonitor:BackgroundWorker = None				# BackgroundWorker
		self.descendantCSR:Dict[str, Tuple[Resource, str]]	= {}	# dict of descendantCSR's - "csi : (CSR, registeredATcsi)". CSR is None for CSEs further down 
		self.registrarConfig:CSERegistrar = None 					# Locally store the own registrar's config entry for simplicity


	@start
	def start(self) -> None:
		# Get the configuration settings
		self._assignConfig()
		L.isInfo and L.log('RemoteCSEManager initialized')


	@stop
	def stop(self) -> bool:
		"""	Stop the RemoteCSEManager.
		
			Return:
				Always return True.
		"""
		self.stopConnectionMonitor()
		L.isInfo and L.log('RemoteCSEManager shut down')
		return True


	@restart
	def restart(self) -> None:
		"""	Restart the remote service monitor.
		"""
		if self.registrarConfig:
			self.registrarConfig.restart()
		self.descendantCSR.clear()
		self.checkConnectionsNow()	# Force the connection monitor to check the connections now
		L.isDebug and L.logDebug('RemoteManager restarted')


	def checkConnectionsNow(self) -> None:
		"""	Force the connection monitor to check the connections now.

			This is useful for testing purposes or when the CSE is started and the connection monitor
			should be run immediately.
		"""
		if self.connectionMonitor:
			self.connectionMonitor.workNow()


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		# Locally store the own registrar's config entry for simplicity
		self.registrarConfig = Configuration.cse_registrars.get(RC.cseSPid)
		self.spRegistrarConfigs = {spid:config for spid, config in Configuration.cse_registrars.items() if spid != RC.cseSPid}	# all SP registrar configs except the own one


	@onEvent(eventManager.configUpdate)
	def configUpdate(self, eventData: EventData) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				eventData: The event data, containing the name of the updated configuration setting and its new value.
		"""
		key:Optional[str] = eventData[0]
		value:Any = eventData[1]

		if key not in [ 'cse.enableRemoteCSE' ] or not key.startswith(('cse.registrar', 'cse.sp.registrar.')):
			return

		# assign new values
		self._assignConfig()


	#########################################################################
	#
	#	Connection Monitor
	#

	@onEvent(eventManager.cseStartup)
	def startConnectionMonitor(self, eventData: EventData) -> None:
		"""	Start the remote monitor as a background worker. 

			Args:
				name: Event name.
		"""
		if not Configuration.cse_enableRemoteCSE:
			return

		# Internal optimization: collect all descendant CSEs in a dictionary
		L.isDebug and L.logDebug('Rebuild internal descendants list')
		self.descendantCSR.clear()
		for eachCsr in dispatcher.retrieveResourcesByType(ResourceTypes.CSR):

			if self.registrarConfig and self.registrarConfig.spID == RC.cseSPid and (csi := eachCsr.csi) != self.registrarConfig.cseID:			# Skipping the own registrar csr
				L.isDebug and L.logDebug(f'Addind remote CSE: {csi}')
				self.descendantCSR[csi] = (eachCsr, RC.cseCsi)		# Add the direct child CSR
				
				# Add the descendant CSE's to the internal descendant list
				if eachCsr.dcse:
					for eachDcse in eachCsr.dcse:
						L.isDebug and L.logDebug(f'Adding descendant CSE: {csi} -> {eachDcse}')
						self.descendantCSR[eachDcse] = (None, csi)

		L.isInfo and L.log('Starting remote CSE connection monitor')
		self.connectionMonitor = BackgroundWorkerPool.newWorker(Configuration.cse_registration_checkInterval, 
														  		self.connectionMonitorWorker, 
																'csrMonitor').start()


	def stopConnectionMonitor(self) -> None:
		"""	Stop the connection monitor. Also delete the CSR resources on both sides, if possible.
		"""
		if not Configuration.cse_enableRemoteCSE:
			return
		L.isInfo and L.log('Stopping remote CSE connection monitor')

		# Stop the worker
		if self.connectionMonitor:
			self.connectionMonitor.stop()
			self.connectionMonitor = None

		# Remove <csr> resources and thereby de-register from registrar CSEs
		if Configuration.cse_registration_unregisterWhenStopping:
			L.isDebug and L.logDebug('Unregistering from registrar CSEs')
			if RC.cseType in [ CSEType.ASN, CSEType.MN ]:
				try:
					self._deleteOwnCSRonRegistrarCSE(self.registrarConfig)	# delete remote CSR. Ignore result
					L.isInfo and L.log(f'De-registered from registrar CSE: {self.registrarConfig.cseID}')
				except:
					pass
			
			if len(resources := self._retrieveLocalCSRResources(self.registrarConfig, includeRegistrarCSR=True)):	# retrieve local CSR of the registrar
				L.isDebug and L.logDebug('Deleting local registrar CSR ')
				try:
					self._deleteRegistreeCSR(resources[0])		# delete local CSR of the registrar
				except:
					pass
	

	def connectionMonitorWorker(self) -> bool:
		"""	The background worker that checks periodically whether the connection to the registrar and
			registree CSEs is still valid.

			Return:
				Always *True* to keep the worker running.
		"""
		if RC.cseStatus != CSEStatus.RUNNING:
			return True

		try:

			# Check only the intra-SP connections first, filter perhaps by own SP-ID

			match RC.cseType:

				case CSEType.ASN:
					# when checkLiveliness == False then only check when there is no connection to registrar CSEs
					if not Configuration.cse_registration_checkLiveliness:
						if len(self._retrieveLocalCSRResources(self.registrarConfig, includeRegistrarCSR=True)) == 1:
							return True
						# fallthrough: There is no local CSR, so we need to check the connection
			
					# Check the connection to the registrar CSE and establish one if necessary
					self._checkConnectionToRegistrarCSE(self.registrarConfig)

				case CSEType.MN:

					# when checkLiveliness == False then only check when there is no connection to registrar CSEs
					if not Configuration.cse_registration_checkLiveliness:
						if len(self._retrieveLocalCSRResources(self.registrarConfig, includeRegistrarCSR=True)) == 1:
							return True
						# fallthrough
			
					# Check the connection to the registrar CSE and establish one if necessary
					self._checkConnectionToRegistrarCSE(self.registrarConfig)
					
					# Check the liveliness of registree CSR connections
					if Configuration.cse_registration_checkLiveliness:	
						self._checkRegistreeLiveliness(self.registrarConfig)

				case CSEType.IN:

					# Check the liveliness of registree CSR connections
					if Configuration.cse_registration_checkLiveliness:	
						self._checkRegistreeLiveliness(self.registrarConfig)
					
					# Check Inter-SP connections via Mcc'
					for registrarConfig in self.spRegistrarConfigs.values():
		
						# Check the connection to the registrar CSE and establish one if necessary
						self._checkConnectionToRegistrarCSE(registrarConfig)

		except Exception as e:
			L.logErr(f'Exception during connection monitor run: {e}', exc = e)
			return True

		return True


	#########################################################################
	#
	#	Event Handlers
	#

	@onEvent(eventManager.registeredToRegistrarCSE)
	def handleRegistrarRegistrationEvent(self, eventData: EventData) -> None:
		""" Event handler for adding a registrar CSE/CSR CSI to the list of registered csi.

			Args:
				eventData: The event data containing the registrar configuration, the registrar CSE resource, the own CSR on the registrar CSE and the local CSR representing the registrar CSE.
		"""
		# registrarConfig = eventData[0]
		# registrarCSE = eventData[1]
		# ownRegistrarCSR = eventData[2]
		localRegistrarCSR = eventData[3]

		# Update the own CSEBase if necessary with further informatioon from the registrar CSE
		if localRegistrarCSR is not None:
			updatedAttributes = self._updateOwnCSEBaseWithRegistrarCSEInfo(localRegistrarCSR)
			if updatedAttributes:
				# Update direct registree CSRs
				try:
					self.updateRemoteDescendantCSR({ 'm2m:csr' : updatedAttributes })
				except Exception as e:
					L.logErr(f'Cannot update descendant CSRs: {e}')


	@onEvent(eventManager.deregisteredFromRegistrarCSE)
	def handleRegistrarDeregistrationEvent(self, eventData: EventData) -> None:
		"""	Event handler for removing the registrar CSE/CSR CSI from the list of registered csi.

			Args:
				eventData: The event data containing the registrar configuration and the registrar CSE resource that is de-registered.
		"""
		registrarConfig = eventData[0]
		#registrarCSE = eventData[1]
		registrarConfig._registrarCSEBaseResource = None


	@onEvent(eventManager.registreeCSEHasRegistered)
	def handleRegistreeCSERegistrationEvent(self, eventData: EventData) -> None:
		"""	Event handler for adding a registree's CSE's <CSR> to the list of registered descendant CSE. 

			Only the local registrar configuration is involved here.

			Args:
				eventData: The event data containing the registree CSR resource that is registered.
		"""
		registreeCSR: Resource = cast(Resource, eventData.payload)

		if not (registreeCSRcsi := registreeCSR.csi):	# Not a CSR?
			return
		if registreeCSRcsi in self.descendantCSR:	# already registered
			return

		# don't register registrar CSE here
		if self.registrarConfig and (registrarCSE := self.registrarConfig._registrarCSEBaseResource) and registrarCSE.csi and registrarCSE.csi == registreeCSRcsi:
			return

		# Add to the descendant CSE : (remoteCSR, this CSE's csi )
		self.descendantCSR[registreeCSRcsi] = (registreeCSR, RC.cseCsi)

		# Update the own dcse list with the dcse's from the remoteCSR
		if registreeCSR.dcse:	
			L.isDebug and L.logDebug(f'Adding registree CSEs descendants: {registreeCSR.dcse}')

			for eachDcse in registreeCSR.dcse:
				if eachDcse in self.descendantCSR:	# don't overwrite existing ones
					continue
				self.descendantCSR[eachDcse] = (None, registreeCSRcsi)	# add the remoteCSRcsr to self's dcse list

		L.isDebug and L.logDebug(f'Registree CSE registered {registreeCSRcsi}')
		
		# Update the registrar CSE with the new values
		if RC.cseType in [ CSEType.ASN, CSEType.MN ]:
			try:
				self._updateOwnCSRonRegistrarCSE(self.registrarConfig)
			except NOT_FOUND as e:
				L.isDebug and L.logDebug(e.dbg)
				return
		
		# Send another event when the own CSE has fully registered
		eventManager.registeredToRemoteCSE(EventData(payload=(registreeCSR)))	# type: ignore


	@onEvent(eventManager.registreeCSEHasDeregistered)
	def handleRegistreeCSEDeregistrationEvent(self, eventData: EventData) -> None:
		"""	Event handler for removals of registree's CSE/CSR CSI from the list of registered descendant CSE. 

			Only the local registrar configuration is involved here.
		
			Args:
				eventData: The event data containing the registree CSR resource that is de-registered. The CSR resource must contain the csi of the deregistering CSE.
		"""
		registreeCSR:Resource = cast(Resource, eventData.payload)

		L.isDebug and L.logDebug(f'Handling de-registration of registree CSE: {registreeCSR.csi}')

		# Remove the deregistering CSE from the descendant list
		if (registreeCSRcsi := registreeCSR.csi) and registreeCSRcsi in self.descendantCSR:
			del self.descendantCSR[registreeCSRcsi]
			
		# Also remove all descendants that are refer to that remote CSE
		for eachDescendantCsi in list(self.descendantCSR):	# List might change in the loop
			dcse = self.descendantCSR[eachDescendantCsi]	# returns tuple (CSR, csi)
			if dcse[1] == registreeCSRcsi:	# registered to deregistering remote CSE?
				del self.descendantCSR[eachDescendantCsi]
		
		if RC.cseType in [ CSEType.ASN, CSEType.MN ] and registreeCSR.csi != self.registrarConfig.cseID:	# No need to update the own CSR on the registrar when deregistering anyway
			self._updateOwnCSRonRegistrarCSE(self.registrarConfig)


	@onEvent(eventManager.csrUpdated)	# type: ignore
	# def handleCSRUpdateEvent(self, name: str, csr: Resource, updateDict: JSON) -> None:
	def handleCSRUpdateEvent(self, eventData: EventData) -> None:
		"""	Event handler for an updates of a registree or registrar CSR.

			Only the local registrar configuration is involved here.

			Args:
				eventData: The event data containing the updated CSR and the update dictionary.
		"""
		csr:Resource = eventData[0]		# type: ignore
		updateDict:JSON = eventData[1]	# type: ignore

		L.isDebug and L.logDebug(f'Handle registree or registrar CSR update: {csr}\nupdate: {updateDict}')

	
		# If this is the registrar CSR that has been updated, then update own CSEBase, and perhaps descendant CSRs
		csrCsi = csr.csi
		if csrCsi == self.registrarConfig.cseID:
			L.isDebug and L.logDebug('Update of registrar CSR detected')
			# This is the registrar CSR that has been updated
			updatedAttributes = self._updateOwnCSEBaseWithRegistrarCSEInfo(csr)
			if updatedAttributes:
				# Update direct registree CSRs
				try:
					self.updateRemoteDescendantCSR({ 'm2m:csr' : updatedAttributes })
				except Exception as e:
					L.logErr(f'Cannot update descendant CSRs: {e}')

			# Update the stored registrar CSEBase resource in the config.
			# The registrar obviously has changed something.
			self.registrarConfig._registrarCSEBaseResource = self._retrieveRegistrarCB(self.registrarConfig) # retrieve the remote CSEBase


		else:
			# This is any registree CSR that has been updated

			# handle update of dcse in remoteCSR

			L.isDebug and L.logDebug(f'Update of descendantCSRs: {self.descendantCSR}')
			# remove all descendant tuples that are from this CSR
			for eachDcse in list(self.descendantCSR.keys()):	# !!! make a copy of the keys bc the list changes in this loop
				if eachDcse in self.descendantCSR:	# Entry could have been deleted, so we need to check
					(_, registeredAtCsi) = self.descendantCSR[eachDcse]
					if registeredAtCsi == csrCsi :	# remove all descedants EXCEPT the ones hosted on THIS CSE
						L.isDebug and L.logDebug(f'Removing from internal dcse list: {eachDcse}')
						if eachDcse in self.descendantCSR:
							del self.descendantCSR[eachDcse]

			# add new/updated values from remoteCSR
			if dcse := findXPath(updateDict, 'm2m:csr/dcse'):
				for eachDcse in dcse:
					if eachDcse in self.descendantCSR:	# don't overwrite existing ones. Can this actually happen?
						continue
					self.descendantCSR[eachDcse] = (None, csrCsi)	# don't have the CSR for further descendants available

			if RC.cseType in [ CSEType.ASN, CSEType.MN ]:	# update own  CSR on registrar CSE
				self._updateOwnCSRonRegistrarCSE(self.registrarConfig)


	#########################################################################
	#
	#	Connection Checkers
	#

	def _checkConnectionToRegistrarCSE(self, registrarConfig:CSERegistrar) -> None:
		"""	Check the connection for this CSE to the registrar CSE.
		"""
		L.isDebug and L.logDebug('Checking connection to Registrar CSE')
		
		# first check whether there is already a local CSR, which indicates that we are registered to the registrar CSE
		if len(_csrs := self._retrieveLocalCSRResources(registrarConfig, includeRegistrarCSR=True)):
			registrarCSR = _csrs[0] # hopefully, there is only one registrar CSR

			# Define variable here for scoping. An exception might skip its definition otherwise
			csr:Optional[Resource] = None			

			try:
				# retrieve own CSR from the registrar CSE
				csr = self._retrieveOwnCSRfromRegistrarCSE(registrarConfig)

				L.isDebug and L.logDebug('CSR found on registrar CSE')

				# own remote CSR is still on the registrar CSE, so check for changes in remote CSE
				try:
					registrarConfig._registrarCSEBaseResource = self._retrieveRegistrarCB(registrarConfig) # retrieve the remote CSE
					if registrarConfig._registrarCSEBaseResource.isModifiedAfter(registrarCSR):	# remote CSE modified
						# Update the local registrar <CSR> resource
						L.isDebug and L.logDebug(f'Updating local registrar CSR resource: {registrarCSR.rn}')
						self._copyCSE2CSR(registrarConfig, registrarCSR, registrarConfig._registrarCSEBaseResource)
						registrarCSR.dbUpdate(True)		# update in DB only
						L.isDebug and L.logDebug('Local CSR updated')
				except ResponseException as e:
					registrarConfig._registrarCSEBaseResource = None	# Always assign, if there is an error "resource" is None
					
				# Check whether the own CSE has been changed. If yes, then update it on the registrar CSE
				localCSE = getCSE()
				if localCSE.isModifiedAfter(csr):	# local CSE modified
					self._updateOwnCSRonRegistrarCSE(registrarConfig, localCSE)
					L.isDebug and L.logDebug('Remote CSR updated because local <CSEBase> has been modified since last registration')

			except TARGET_NOT_REACHABLE:
				L.isWarn and L.logWarn('Registrar CSE unreachable - assuming it is still there')

			# No CSR on registrar CSE found, try to register
			except Exception as e:
				# L.logErr(str(e), exc = e)
				L.isDebug and L.logDebug('CSR not found on registrar CSE')
				# Potential disconnect
				try:
					# This deletes the CSR of the Registrar
					self._deleteRegistreeCSR(registrarCSR)	# ignore result
				except:
					pass
				# Indicate that we are not registered to the registrar CSE anymore
				registrarConfig._registrarCSEBaseResource = None	
				try:
					try:
						csr = self._createCSRonRegistrarCSE(registrarConfig)
					except CONFLICT:
						L.isWarn and L.logWarn(f'Conflict when creating CSR on registrar CSE. This is expected when the remote CSR is still present')
						csr = self._retrieveOwnCSRfromRegistrarCSE(registrarConfig)	# retrieve the remote CSR again, which should be the same as before
					try:
						registrarConfig._registrarCSEBaseResource = self._retrieveRegistrarCB(registrarConfig)	# We are registered to the registrar CSE again
						localRegistrarCSR = self._createLocalCSR(registrarConfig)		# ignore result

						#Send registration event
						eventManager.registeredToRegistrarCSE(EventData(payload=(registrarConfig, 
																				 registrarConfig._registrarCSEBaseResource, 
																				 csr, 
																				 localRegistrarCSR)))
						L.isInfo and L.log(f'Registered to registrar CSE: {registrarConfig.cseID}')
					except:
						pass
				except:
					L.isInfo and L.log('Disconnected from registrar CSE')
					eventManager.deregisteredFromRegistrarCSE(EventData(payload=(registrarConfig, csr)))
					registrarConfig._registrarCSEBaseResource = None
		
		else:	# No local CSR

			# try to delete an optional remote one and re-create everything. 
			try:
				L.isDebug and L.logDebug('No local CSR found, trying to delete remote CSR first')
				self._deleteOwnCSRonRegistrarCSE(registrarConfig)
				rsc = ResponseStatusCode.DELETED
			except ResponseException as e:
				rsc = e.rsc

			if rsc in [ ResponseStatusCode.DELETED, ResponseStatusCode.NOT_FOUND ]:	# delete potential remote CSR
				try:
					# Should be None after an exception of the following calls
					try:
						csr = self._createCSRonRegistrarCSE(registrarConfig)
					except CONFLICT:
						L.isWarn and L.logWarn(f'Conflict when creating CSR on registrar CSE. This is expected when the remote CSR is still present')
						csr = self._retrieveOwnCSRfromRegistrarCSE(registrarConfig)	# retrieve the remote CSR again, which should be the same as before

					registrarConfig._registrarCSEBaseResource = self._retrieveRegistrarCB(registrarConfig)	# retrieve remote CSE
					localRegistrarCSR = self._createLocalCSR(registrarConfig) 	# create local CSR including ACPs to local CSR and local CSE. Ignore result

					# Send registration event
					eventManager.registeredToRegistrarCSE(EventData(payload=(registrarConfig, 
															  				 registrarConfig._registrarCSEBaseResource, 
																			 csr, 
																			 localRegistrarCSR)))
					L.isInfo and L.log(f'Registered to registrar CSE: {registrarConfig.cseID}')
				except:
					registrarConfig._registrarCSEBaseResource = None


	def _checkRegistreeLiveliness(self, registrarConfig:CSERegistrar) -> None:
		"""	Check the liveliness of all registree CSEss that are connected to this CSE.
			This is done by trying to retrieve the own remote <CSR> from the remote CSE.
			If it cannot be retrieved then the related local CSR is removed.

			Args:
				registrarConfig: The registrar configuration to use for the search.
		"""
		for eachCsr in self._retrieveLocalCSRResources(registrarConfig, includeRegistreeCSR=True):
			L.isDebug and L.logDebug(f'Checking connection to registree CSE: {eachCsr.csi}')
			if (to := self.getRemoteCSEBaseAddress(eachCsr.csi)) is None:
				self._deleteRegistreeCSR(eachCsr)
				continue
			try:
				sp = getSPFromID(eachCsr.csi)	# !!! In CSR the csi attribute contains the absolute csi, other then in the CSEBase
				match sp:
					case None | RC.cseSPIDSlashLess:	# no SP or own SP
						originator = RC.cseCsi
					case _:
						originator = f'{RC.cseSPid}{RC.cseCsi}'	# SP-relative originator

				L.isDebug and L.logDebug(f'Requesting remote CSEBase: {eachCsr.csi} originator: {originator}')
				res = CSE.request.handleSendRequest(CSERequest(op=Operation.RETRIEVE,
															   to=to,
															#    originator=RC.cseCsi)
															   originator=originator)
													)[0].result		# there should be at least one result
				if res.rsc != ResponseStatusCode.OK:
					L.isWarn and L.logWarn(f'Registree CSE unreachable. Removing CSR: {eachCsr.rn if eachCsr else ""}')
					self._deleteRegistreeCSR(eachCsr)
			except TARGET_NOT_REACHABLE:
					L.isWarn and L.logWarn(f'Registree CSE unreachable. Removing CSR: {eachCsr.rn if eachCsr else ""}')
					self._deleteRegistreeCSR(eachCsr)


	#
	#	Local CSR
	#

	def _retrieveLocalCSRResources(self, registrarConfig: CSERegistrar,
										 includeRegistrarCSR: Optional[bool]=False, 
										 includeRegistreeCSR: Optional[bool]=False) -> List[Resource]:
		"""	Retrieve the local <CSR> resources.
		
			Args:
				registrarConfig: The registrar configuration to use for the search.
				includeRegistrarCSR: If *True* then include the CSR to the registrar CSE in the result.
				includeRegistreeCSR: if *True* then include the CSR(s) to the registree CSE(s) in the result.

			Return:
				A list of found CSR resources.
		"""
		registreeCsrList = []
		for eachCSR in dispatcher.retrieveDirectChildResources(pi=RC.cseRi, ty=ResourceTypes.CSR):


		# TODO in this search, instead of a fixed cseid use a list and accept all cseIDs that are in the list
			L.isDebug and L.logDebug(f'Checking local CSR: {eachCSR.csi} - registrarConfig: {registrarConfig}')
			
			if registrarConfig and eachCSR.csi == registrarConfig.registrarAbsoluteCSI:		# type: ignore[name-defined]
				if includeRegistrarCSR: 	
					registreeCsrList.append(eachCSR)
			else:
				if includeRegistreeCSR: 	
					registreeCsrList.append(eachCSR)
		return registreeCsrList


	def _createLocalCSR(self, registrarConfig:CSERegistrar) -> Resource:
		remoteCSE = registrarConfig._registrarCSEBaseResource
		L.isDebug and L.logDebug(f'Creating local CSR for CSE: {remoteCSE.ri}')

		# copy local CSE attributes into a new CSR
		localCSE = getCSE()
		csrResource = CSR()
		csrResource.setAttribute('rr', True)
		self._copyCSE2CSR(registrarConfig, csrResource, remoteCSE)
		csrResource.initialize(localCSE.ri)	# remoteCSE.csi as name!

		# add local CSR and ACP's
		try:
			dispatcher.createLocalResource(csrResource, localCSE, originator=remoteCSE.csi)
			registration.handleCSRRegistration(csrResource, csrResource.csi)
		except ResponseException as e:
			raise BAD_REQUEST(f'cannot register CSR: {e.dbg}')

		return csrResource.dbUpdate(True)


	def _deleteRegistreeCSR(self, registreeCSR:Resource) -> None:
		"""	Delete a local registree <CSR> resource. Unregister it first.

			Args:
				registreeCSR: The <CSR> resource to de-register and delete.
		"""
		L.isDebug and L.logDebug(f'Deleting registree CSR: {registreeCSR.ri}')

		# De-register the registree CSR first
		if not registration.handleRegistreeCSRDeRegistration(registreeCSR):
			raise BAD_REQUEST('cannot de-register registree CSR')

		# Delete local CSR
		dispatcher.deleteLocalResource(registreeCSR)


	#
	#	Remote Registrar CSR request methods
	#

	def _retrieveOwnCSRfromRegistrarCSE(self, registrarConfig:CSERegistrar) -> Resource:
		"""	Retrieve the own <CSR> resource from the registrar CSE.
		
			Return:
				Resource object
		"""
		L.isDebug and L.logDebug(f'Retrieve own CSR from registrar CSE: {registrarConfig.registrarAbsoluteCSI} ID: {registrarConfig.csrOnRegistrarSRN}')
		
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.RETRIEVE,
													   to=registrarConfig.csrOnRegistrarSRN,
													   _directURL=registrarConfig.csrOnRegistrarSRN,	# Fallback, because there might be no registration yet
													   originator=registrarConfig.originator,
													   ct=cast(ContentSerializationType, registrarConfig.serialization),
						  							   credentials=registrarConfig.security.credentials)
										   )[0].result	# there should be at least one result
		if not res.rsc == ResponseStatusCode.OK:
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'cannot retrieve CSR from registrar CSE: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
		# <CSR> found, return it in the result
		return factory.resourceFromDict(cast(JSON, res.data), pi='')


	def _createCSRonRegistrarCSE(self, registrarConfig:CSERegistrar) -> Resource:
		L.isDebug and L.logDebug(f'creating CSR at registrar CSE: {registrarConfig.cseID} uri: {registrarConfig.registrarCSESRN}')	
		
		# get local CSEBase and copy relevant attributes
		localCSE = getCSE()
		csrResource = CSR()
		csrResource.setResourceName(registrarConfig.registrarCSRRN)
		csrResource.setAttribute('rr', True)
		self._copyCSE2CSR(registrarConfig, 
						  csrResource, 
						  localCSE, 
						  targetCsi=registrarConfig.cseID,
						  forOwnCSR=True)	# type: ignore[name-defined]
		
		# Create the <csr> on the registrar CSE
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.CREATE,
													   to=registrarConfig.registrarCSESRN,
													   _directURL=registrarConfig.registrarCSEURL,	# We may not have the resource yet, so we need to use the configured URL
													#    originator=RC.cseCsi, # own CSE.csi is the originator
													   originator=registrarConfig.originator,
													   ty=ResourceTypes.CSR, 
													   pc=csrResource.asDict(),
													   ct=cast(ContentSerializationType, registrarConfig.serialization),
													   credentials=registrarConfig.security.credentials)
										   )[0].result	# there should be at least one result
		# The result contains the transmitted data in .data, even when it is an error.

		if res.rsc not in [ ResponseStatusCode.CREATED, ResponseStatusCode.OK, ResponseStatusCode.CONFLICT ]:
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg=L.logWarn(f'error creating CSR on registrar CSE: {int(res.rsc)} dbg: {res.data}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
		
		# If the resource already exists then perhaps it is a leftover from a previous session. It should have been deleted,
		# but who knows? Just re-use that one for now.
		if res.rsc == ResponseStatusCode.CONFLICT:
			raise CONFLICT(L.logWarn(f'error creating CSR on registrar CSE: {res.rsc.name} dbg: {res.data}'))
		else:
			L.isDebug and L.logDebug(f'created CSR on registrar CSE: {registrarConfig.cseID}')
		return factory.resourceFromDict(cast(JSON, res.data), pi='')


	def _updateOwnCSRonRegistrarCSE(self, registrarConfig:CSERegistrar, hostingCSE:Optional[Resource]=None) -> Resource:
		"""	Update the own <CSR> resource on the registrar CSE.

			Args:
				registrarConfig: The registrar configuration to use for the update.
				hostingCSE: Optional CSE resource to use for the update. If None, the hosting <CSEBase> resource will be used.

			Return:
				Resource
		"""
		L.isDebug and L.logDebug(f'updating own <CSR> on registrarCSE: {registrarConfig.cseID} URI: {registrarConfig.csrOnRegistrarSRN}')
		if not hostingCSE:
			hostingCSE = getCSE()

		# Check whether we are actually registed before updating
		if not self.isRegisteredToRegistrarCSE():
			L.isDebug and L.logDebug('Not registered to registrar CSE, cannot update own remote CSR')
			return None

		# create a new CSR resource and fill it with the current attributes
		csr = CSR()
		self._copyCSE2CSR(registrarConfig, 
						  csr, 
						  hostingCSE, 
						  isUpdate=True, 
						  targetCsi=registrarConfig.cseID, 
						  forOwnCSR=True)	# type: ignore[name-defined]
		del csr['acpi']			# remove ACPI (don't provide ACPI in updates!)
		
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.UPDATE,
													   to=registrarConfig.csrOnRegistrarSRN, 
													   originator=registrarConfig.originator,
													   pc=csr.asDict(), 
													   ct=cast(ContentSerializationType, registrarConfig.serialization),
													   credentials=registrarConfig.security.credentials)
										   )[0].result	# there should be at least one result
		if res.rsc not in [ ResponseStatusCode.UPDATED, ResponseStatusCode.OK ]:
			if res.rsc != ResponseStatusCode.CONFLICT:
				L.isDebug and L.logDebug(f'error updating registrar CSR on CSE: {int(res.rsc)}')
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'cannot update remote CSR: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')

		L.isDebug and L.logDebug(f'registrar CSR updated on CSE: {registrarConfig.cseID}')
		return factory.resourceFromDict(cast(JSON, res.data), pi='')


	def _deleteOwnCSRonRegistrarCSE(self, registrarConfig:CSERegistrar) -> None:
		"""	Delete the own <CSR> resource from the registrar CSE.

			Args:
				registrarConfig: The registrar configuration to use for the deletion.
		"""
		if registrarConfig:
			L.isDebug and L.logDebug(f'Deleting own CSR on registrar CSE: {registrarConfig.cseID} URI: {registrarConfig.csrOnRegistrarSRN}')
			res = CSE.request.handleSendRequest(CSERequest(op=Operation.DELETE,
														   to=registrarConfig.csrOnRegistrarSRN,
														   _directURL=registrarConfig.registrarCSEURL,	# Fallback, because there might be no registration yet
													  	   originator=registrarConfig.originator,
														   ct=cast(ContentSerializationType, registrarConfig.serialization),
														   credentials=registrarConfig.security.credentials)
											)[0].result	# there should be at least one result

			# NOT_FOUND might be raised above
			if res.rsc not in [ ResponseStatusCode.DELETED, ResponseStatusCode.OK ]:
				if res.rsc == ResponseStatusCode.NOT_FOUND:
					L.isDebug and L.logDebug('Remote CSR not found on registrar CSE during deletion - This may happen if this is a new registration or if the remote CSR was already deleted.')
					return
				else:
					_exc = exceptionFromRSC(res.rsc)
					if _exc:
						raise _exc(dbg=L.logDebug(f'cannot delete remote CSR: {int(res.rsc)} dbg: {res.data}')) # type:ignore[call-arg]
				raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
			L.isDebug and L.logDebug(f'Registrar CSR deleted: {registrarConfig.cseID}')


	#
	#	Remote Registrar CSE
	#

	def _retrieveRegistrarCB(self, registrarConfig:CSERegistrar) -> Resource:
		"""	Retrieve the remote registrar CSEBase resource.

			The actual request uses a direct URL as a fallback because the RETRIEVE request happens when the 
			actual registration may not yet have happened, and the registrars <CSR> resource with the actual
			POA is not available at that time.

			Return:
				The registrar's <CSE> resource.
		"""
		L.isDebug and L.logDebug(f'Retrieving registrar CSEBase from: {registrarConfig.registrarAbsoluteCSI}')	
		
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.RETRIEVE,
													   to=registrarConfig.registrarCSESRN,
													   _directURL=registrarConfig.registrarCSEURL,	# Fallback, because there might be no registration yet
													   originator=registrarConfig.originator,
													   ct=cast(ContentSerializationType, registrarConfig.serialization),
													   credentials=registrarConfig.security.credentials)
										   )[0].result	# there should be at least one result

		if (_registrarCSI := findXPath(cast(JSON, res.data), 'm2m:cb/csi')) == None:
			raise BAD_REQUEST(L.logErr('csi not found in remote CSE resource', showStackTrace = False))
		
		# Correcting the registrar CSI
		if not _registrarCSI.startswith('/'):
			L.isWarn and L.logWarn('Remote CSE.csi doesn\'t start with /. Correcting.')	# TODO Decide whether correcting this is actually correct. Also in validator.validateCSICB()
			setXPath(cast(JSON, res.data), 'm2m:cb/csi', f'/{_registrarCSI}')


		return CSEBase(cast(JSON, res.data)) # Don't use the Factory here (less checks)


	def _updateOwnCSEBaseWithRegistrarCSEInfo(self, localRegistrarCSR: Resource) -> JSON:
		"""	Update the local CSEBase resource with information from the registrar CSE's CSR.

			Args:
				localRegistrarCSR: The local <CSR> resource for the registrar CSE. This resource is provided during a registration or update event.

			Return:
				Dictionary with the updated attributes. If no attributes have been updated then an empty dictionary is returned.
		"""
		csebase = getCSE()
		updatedAttributes: JSON = {}

		# Add spi and ici to the CSEBase when this resource is created or modified
	
		if localRegistrarCSR.spi != csebase.spi:
			L.isDebug and L.logDebug(f'Updating CSEBase.spi to {localRegistrarCSR.spi}, was: {csebase.spi}')
			csebase.setAttribute('spi', localRegistrarCSR.spi)
			self.registrarConfig.spID = localRegistrarCSR.spi	# also update the registrarConfig spID
			updatedAttributes['spi'] = localRegistrarCSR.spi
	
		if localRegistrarCSR.ici != csebase.ici:
			L.isDebug and L.logDebug(f'Updating CSEBase.ici to {localRegistrarCSR.ici}, was: {csebase.ici}')
			csebase.setAttribute('ici', localRegistrarCSR.ici)
			self.registrarConfig.INCSEcseID = localRegistrarCSR.ici	# also update the registrarConfig INCSEcseID
			updatedAttributes['ici'] = localRegistrarCSR.ici
	
		if updatedAttributes:
			self.registrarConfig.reInit()	# re-initialize the registrarConfig with the new values
			csebase.dbUpdate()

		return updatedAttributes


	def getAllLocalCSRs(self) -> List[Resource]:
		"""	Return all local <CSR> resources. This includes the <CSR> of the registrar CSE.
			This function builds the list from a temporary internal list, but not from the database.

			Return:
				List of <CSR> resources.
		"""
		return [ csr for (csr, _) in self.descendantCSR.values() if csr ]


	#########################################################################


	def isRegisteredToRegistrarCSE(self) -> bool:
		"""	Check whether this CSE is registered to its registrar CSE.

			Return:
				True if registered, False otherwise.
		"""
		return self.registrarConfig is not None and self.registrarConfig._registrarCSEBaseResource is not None
	

	def retrieveRemoteResource(self, id:str, originator:Optional[str]=None) -> Resource:
		"""	Retrieve a remote resource from one of the interconnected CSEs.

			Args:
				id: The resource ID. It must be at least in SP-relative format.
				originator: Optional request originator. If *None* is given then the CSE's CSE-ID is used.
			
			Return:
				Result object with the status and, if successful, the resource object in the *resource* attribute.
		"""

		# We cannot regularly retrieve a remote resource if we are not fully registered (yet).
		resourceList = self._retrieveLocalCSRResources(None, includeRegistrarCSR=True, includeRegistreeCSR=True)

		_id = f'{id}/'
		for eachCsr in resourceList:
			if _id.startswith(eachCsr.csi):
				break	# found a matching CSR
		else: # Not found, so not registered
			raise NOT_FOUND(L.logDebug(f'Not registered to remote CSE to send request: {id}'))
			
		# Assign fallback originator
		if not originator:
			originator = RC.cseCsi
		
		# Retrieve the remote resource via its SP-relative ID
		L.isDebug and L.logDebug(f'Retrieve remote resource id: {id}')
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.RETRIEVE,
													   to=id, 
													   originator=originator)
											)[0].result		# there should be at least one result
		if res.rsc != ResponseStatusCode.OK:
			raise exceptionFromRSC(res.rsc)
		
		# assign the remote ID to the resource's dictionary
		_, typeShortname, _ = pureResource(cast(JSON, res.data))
		setXPath(cast(JSON, res.data), f'{typeShortname}/{Constants.attrRemoteID}', id)

		# Instantiate
		return factory.resourceFromDict(cast(JSON, res.data))


	def getCSRFromPath(self, id:str) -> Optional[Tuple[Resource, List[str]]]:
		"""	Try to get a CSR even from a longer path (only the first 2 path elements are relevant). 

			If no direct CSR could be found then that CSR is returned where the addressed csi is a descendant.

			Args:
				id: CSE-ID to search for

			Return:
				A tuple (csr resource, list of path elements), or (None, None) in case of an error).
		"""

		# L.logWarn(f'getCSRFromPath id: {id} ')
		def getCSRWithDescendant(csi:str) -> Resource:
			"""	Get the <CSR> which descendant is a <CSE> with the *csi*.
			
				Args:
					csi: CSE ID for the CSE to look for.
				
				Return:
					The <CSR> resource that has the looked-for CSE as a descendant.
			"""
			# L.logWarn(self.descendantCSR)
			t = self.descendantCSR.get(csi)
			
			if t and t[0]:
				return t[0]		# already a CSR resource
			if t and t[1]:
				return getCSRWithDescendant(t[1]) # indirect, need further step
			return None

		if not id:
			return None, None
		
		# Check whether this ID points to a CSE within the own SP. Then convert the ID to SP-relative format.
		if isAbsolute(id) and getSPFromID(id) == RC.cseSPid:
			id = toSPRelative(id)
		
		ri, ids = csiFromRelativeAbsoluteUnstructured(id)

		# Normally, ri is the csi stem, but with absolute IDs we need to
		# construct the ri a bit differently. Hack.
		if isAbsolute(id):
			ri = f'{ids[2]}_{ids[3]}'

		# Search for a <CSR> that either has the csi attribute set, or that has the looked-for
		# registree CSE as a descendant CSE.

		try:
			registreeCSR = dispatcher.retrieveLocalResource(ri=ri)
		except ResponseException as e:
			L.isDebug and L.logDebug(f'getCSRFromPath: {e.dbg}')
			registreeCSR = getCSRWithDescendant(f'/{ri}')
		# L.logWarn(csr)
		return registreeCSR, ids


	def getRemoteCSEBaseAddress(self, csi:str) -> Optional[str]:
		"""	Get the SP-relative */csi/ri* resource ID of a remote CSE from its CSI.
			The searched for remote CSE must be registered either directly, or
			be a descendant CSE.

			Args:
				csi: The CSI of the remote CSE.

			Return:
				The SP-relative */csi/ri* resource ID of the remote CSE, or *None* if not found.
		"""
		if csi == RC.cseCsi:
			return f'{RC.cseCsi}/{RC.cseRi}'
		if (csr := self.getCSRFromPath(csi))[0] is None:
			return None
		return csr[0].cb


	def updateRemoteDescendantCSR(self, data: JSON, target: Optional[list[str] | str]=None) -> None:

		def _updateDescendant(csrID: str) -> None:
			"""	Handler function to update a descendant CSR in the background.

				Args:
					csrID: The CSR ID to update.
			"""
			L.isDebug and L.logDebug(f'Updating descendant CSR: {csrID} with body: {data}')

			# Send the request
			res = CSE.request.handleSendRequest(CSERequest(op=Operation.UPDATE, 
														to=f'{self.descendantCSR[csrID][0].cb}{RC.cseCsi}', 
														originator=RC.cseCsi, 
														pc=data))[0].result		# there should be at least one result
			if res.rsc != ResponseStatusCode.UPDATED:
				L.isWarn and L.logWarn(f'Error updating descendant CSR: {csrID} RSC: {int(res.rsc)} dbg: {res.data}')
			else:
				L.isDebug and L.logDebug(f'Descendant CSR updated: {csrID}')

		if target is None:
			target = list(self.descendantCSR.keys())
		elif isinstance(target, str):
			target = [target]

		for csrID in target:
			# Launch background worker for each update
			BackgroundWorkerPool.newActor(lambda: _updateDescendant(csrID), name=f'{csrID}-updateDescendant').start()


	def _copyCSE2CSR(self, registrarConfig: CSERegistrar,
				  		   target: Resource, 
						   source: Resource, 
						   isUpdate: Optional[bool] = False, 
						   targetCsi: str = None,
						   forOwnCSR: Optional[bool] = False) -> None:
		"""	Copy the relevant attributes from a <CSEBase> to a <CSR> resource.
		
			Args:
				registrarConfig: The registrar configuration to use for the copy operation.
				target: The target <CSEBase> resource.
				source: The source <CSR> resource.
				isUpdate: Indicator that the copy operation is for an UPDATE request.
				targetCsi: Optional target CSE-ID to use for the copy operation.
				forOwnCSR: If *True* then the copy is for the own CSR, otherwise it is for a remote CSR.
		"""


		# Don't just copy but assign a new value
		# TODO check whether this is really necessary. There is no attribute "csb"

		# if 'csb' in source and 'csb' not in registrarConfig.excludeCSRAttributes:
		# 	target['csb'] = registrarConifg._registrarCSEURL
		
		# copy certain attributes
		for attr in [ 'cst', 'csz', 'lbl', 'nl', 'rr', 'srv', 'st', 'spi', 'ici' ]:
			if attr in source and attr not in registrarConfig.excludeCSRAttributes:
				target[attr] = source[attr]

		if 'csi' not in registrarConfig.excludeCSRAttributes:
			if registrarConfig.spID == RC.cseSPid:
				target['csi'] = source['csi']
			else:
				target['csi'] = f'{RC.cseSPid}{source.csi}' if forOwnCSR else f'{registrarConfig.spID}{source.csi}'	# prepend the SP-ID if it is not the same as the CSE's SP-ID

		if 'cb' not in registrarConfig.excludeCSRAttributes:
			if registrarConfig.spID == RC.cseSPid:
				target['cb'] = f'{source.csi}/{source.rn}'
			else:
				target['cb'] = f'{RC.cseSPid}{source.csi}/{source.rn}' if forOwnCSR else f'{registrarConfig.spID}{source.csi}/{source.rn}'	# prepend the SP-ID if it is not the same as the CSE's SP-ID

		if 'dcse' not in registrarConfig.excludeCSRAttributes:
			target['dcse'] = list(self.descendantCSR.keys())		# Always do this bc it might be different, even empty for an update
		
		# Modify POA for http and ws if necessary
		# so far, only basic auth is supported
		target['poa'] = []
		for p in source.poa:
			# Get the credentials that we want the remote CSE to use to connect to us
			if Configuration.http_security_enableBasicAuth or Configuration.websocket_security_enableBasicAuth:

				# Determine the binding type
				bindingType = BindingType.HTTP if isHttpUrl(p) else BindingType.WS if isWSUrl(p) else BindingType.UNKNOWN

				# Get the credentials for the remote CSE
				# targetCsi might be None, but then we want create a URL to be used in the creation of the localCSR
				username, password = CSE.security.getPOACredentialsForCSEID(registrarConfig, targetCsi, binding=bindingType)
				if username and password:
					# Check if we need to add basic auth to the URL (http or ws) and do so
					if (bindingType == BindingType.HTTP and Configuration.http_security_enableBasicAuth) or (bindingType == BindingType.WS and Configuration.websocket_security_enableBasicAuth):
						# Add basic auth to the URL (same for http and ws)
						p = buildBasicAuthUrl(p, username, password)
				else:
					L.isWarn and L.logWarn(f'No credentials found for POA authentiction for CSE: {targetCsi} - using plain URL')
							
			target['poa'].append(p)
		
		# Always remove some attributes
		for attr in [ 'acpi' ]:
			if attr in target:
				target.delAttribute(attr, setNone = False)

		# Remove attributes in updates
		if isUpdate:
			# rm some attributes
			for attr in [ 'ri', 'rn', 'ct', 'lt', 'ty', 'cst', 'cb', 'csi']:
				if attr in target:
					target.delAttribute(attr, setNone = False)


	#########################################################################
	#
	#	Configuration and validation
	#

	@configure
	def configure(self, config: Configuration) -> None:

		parser = config.configParser

		def parseRegistrar(section:str, registrar:CSERegistrar) -> None:
			registrar._configurationSection = section # Set the configuration section for the registrar
			# Parse a registrar configuration section and populate the registrar object
			registrar.spID = parser.get(section, 'spID', fallback=None)
			registrar.address = parser.get(section, 'address', fallback=None)
			registrar.cseID = parser.get(section, 'cseID', fallback=None)
			registrar.excludeCSRAttributes = parser.getlist(section, 'excludeCSRAttributes', fallback=[])		# type: ignore [attr-defined]
			registrar.resourceName = parser.get(section, 'resourceName', fallback='')
			registrar.root = parser.get(section, 'root', fallback='')
			registrar.serialization = parser.get(section, 'serialization', fallback='json')
			registrar.INCSEcseID = parser.get(section, 'INCSEcseID', fallback=None)
			registrar.originator = parser.get(section, 'originator', fallback=None)


		def parseRegistrarSecurity(section:str, registrar:CSERegistrar) -> None:
			# Parse the security section for a registrar and populate the security attributes
			registrar.security.credentials.httpUsername = parser.get(section, 'httpUsername', fallback=None)
			registrar.security.credentials.httpPassword = parser.get(section, 'httpPassword', fallback=None)
			registrar.security.credentials.httpToken = parser.get(section, 'httpBearerToken', fallback=None)
			registrar.security.credentials.wsUsername = parser.get(section, 'wsUsername', fallback=None)
			registrar.security.credentials.wsPassword = parser.get(section, 'wsPassword', fallback=None)
			registrar.security.credentials.wsToken = parser.get(section, 'wsBearerToken', fallback=None)
			registrar.security.selfCredentials.httpUsername = parser.get(section, 'selfHttpUsername', fallback=None)
			registrar.security.selfCredentials.httpPassword = parser.get(section, 'selfHttpPassword', fallback=None)
			registrar.security.selfCredentials.wsUsername = parser.get(section, 'selfWsUsername', fallback=None)
			registrar.security.selfCredentials.wsPassword = parser.get(section, 'selfWsPassword', fallback=None)

		#	Registrar CSE
		registrar = CSERegistrar()
		parseRegistrar('cse.registrar', registrar)


		# Registrar CSE Security
		if parser.has_section('cse.registrar.security'):
			# parseRegistrarSecurity('cse.registrar.security', registrar)
			parseRegistrarSecurity('cse.registrar.security', registrar)

		config.cse_registrars[RC.cseSPid] = registrar

		# Get the SP (Mcc') configurations
		spMapping:dict[str, str] = {}
		for section in parser.sections():
			if section.startswith('cse.sp.registrar.'):
				if not section.endswith('.security'):
					registrar = CSERegistrar()
					spName = section[len('cse.sp.registrar.'):]  # Extract the SP name from the section
					if spName == RC.cseSPIDSlashLess:
						raise ConfigurationError(r'The registrar within the same Service Provider domain must be configured in the \[cse.registrar] section.')
					parseRegistrar(section, registrar)
					spMapping[spName] = registrar.spID 					# Map the SP name to its spID
					config.cse_registrars[registrar.spID] = registrar	# Store the registrar in the configuration under its spID

				else: 
					spName = section[len('cse.sp.registrar.'):-len('.security')]
					if spName not in spMapping:
						raise ConfigurationError(fr'No SP Registrar configuration found for security section: {spName} -> {section}')
					registrar = config.cse_registrars.get(spMapping[spName], None)
					if not registrar:
						raise ConfigurationError(fr'No SP Registrar configuration found for security section: {spName} -> {section}')
					parseRegistrarSecurity(f'cse.sp.registrar.{spName}.security', registrar)
				

	@validate
	def validate(self, config: Configuration) -> None:

		# Validate CSE Type and remove default registrar if not IN
		for spName, registrar in config.cse_registrars.copy().items():

			# First finish the registrar initialization. This can only be done after all the other configurations have been read
			config.cse_registrars[spName].reInit()

			# Set the correct originator
			if registrar.originator is None:
				# If the originator is not set, use the own Service Provider ID as the originator
				registrar.originator = RC.cseCsi
				if registrar.spID is not None and registrar.spID != RC.cseSPid:
					# If the Service Provider ID is set and is not the own Service Provider ID, expand the
					# originator to include the Service Provider ID and CSE ID
					registrar.originator = f'{RC.cseSPid}{RC.cseCsi}'

			# If the registrar has no name, use the own spID as the key
			# This seems to be a bit of a hack, but at the time when the own registrar is added, the RC.cseSpid is not yet set
			if registrar.spID is None:
				registrar.spID = RC.cseSPid	# Use the own Service Provider ID if not set
			if spName is None:
				# Find the first non-None cseID or spID to use as the key
				registrar.spID = registrar.spID or RC.cseSPid	# Use the own Service Provider ID if not set
				config.cse_registrars[RC.cseSPid] = registrar
				config.cse_registrars.pop(spName)
				spName = RC.cseSPid
			
			# Check if the Service Provider ID is valid
			if not isValidSPID(registrar.spID):
				raise ConfigurationError(f'The Service Provider ID {registrar.spID} is not set or invalid.')

			match config.cse_type:
				# IN CSEs can NOT have a registrar other than other SP's one
				case CSEType.IN if spName == RC.cseSPid:
					if registrar.cseID != '/':	# "/" indicates an empty CSE ID
						raise ConfigurationError(r'An IN CSE can not have a registrar (section: \[cse.registrar])')
					config.cse_registrars.pop(RC.cseSPid)
					continue

				# MN and ASN CSEs may have a registrar
				case CSEType.MN | CSEType.ASN if spName == RC.cseSPid:	
					if registrar.cseID == '/':	# "/" indicates an empty CSE ID, so remove it
						config.cse_registrars.pop(RC.cseSPid)

				# MN and ASCN CSE must not have a SP registrar
				case CSEType.MN | CSEType.ASN if spName != RC.cseSPid:	
					raise ConfigurationError(fr'Service Provider Registrar: "{spName}" is not allowed for CSE Type: "{config.cse_type.name if isinstance(config.cse_type, CSEType) else config.cse_type}". Only the registrar with the same SP-ID as the CSE (section: \[cse.registrar]) is allowed for MN and ASN CSEs.')


		# Validate CSE Registrars
		for spName, registrar in config.cse_registrars.items():

			if spName != RC.cseSPid:
				if not registrar.spID:
					raise ConfigurationError(fr'Missing \[{registrar._configurationSection}]:spID for registrar: {spName}')
				if not registrar.cseID:
					raise ConfigurationError(fr'Missing \[{registrar._configurationSection}]:cseID for registrar: {spName}')
				if not registrar.resourceName:
					raise ConfigurationError(fr'Missing \[{registrar._configurationSection}]:resourceName for registrar: {spName}')
				if not registrar.address:
					raise ConfigurationError(fr'Missing \[{registrar._configurationSection}]:address for registrar: {spName}')

			# Normalize addresses
			registrar.address = normalizeURL(registrar.address)
			registrar.root = normalizeURL(registrar.root)

			# Registrar Serialization
			if isinstance(ct := registrar.serialization, str):
				registrar.serialization = ContentSerializationType.getType(ct)
				if registrar.serialization == ContentSerializationType.UNKNOWN:
					raise ConfigurationError(fr'Unsupported \[{registrar._configurationSection}]:serialization: {ct}')

			# Check that the CSE-ID is valid
			# if registrar.address and registrar.cseID and config.cse_type != CSEType.IN:
			if registrar.address and registrar.cseID:
				if not isValidCSI(val := registrar.cseID): 
					raise ConfigurationError(fr'Invalid format for [i]\[{registrar._configurationSection}]:cseID[/i]: {val}')
				if len(registrar.cseID) > 0 and len(registrar.resourceName) == 0:
					raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}]:resourceName[/i]')

			if registrar.INCSEcseID:
				if not isValidCSI(val := registrar.INCSEcseID):
					raise ConfigurationError(fr'Wrong format for [i]\[{registrar._configurationSection}]:INCSEcseID[/i]: {val}')
			#TODO Investigate: The INCSEcseID above might need be set the same as the cseID, if not set.

			if registrar.security.credentials.httpUsername and not registrar.security.credentials.httpPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:httpPassword[/i] (password is required if username is set)')
			if not registrar.security.credentials.httpUsername and registrar.security.credentials.httpPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:httpUsername[/i] (username is required if password is set)')
			if registrar.security.credentials.httpToken and registrar.security.credentials.httpUsername:
				raise ConfigurationError(rf'Only one of [i]\[{registrar._configurationSection}.security]:httpBearerToken[/i] or [i]\[{registrar._configurationSection}.security]:httpUsername[/i] can be set')
			if registrar.security.credentials.wsUsername and not registrar.security.credentials.wsPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:wsPassword[/i] (password is required if username is set)')
			if not registrar.security.credentials.wsUsername and registrar.security.credentials.wsPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:wsUsername[/i] (username is required if password is set)')
			if registrar.security.credentials.wsToken and registrar.security.credentials.wsUsername:
				raise ConfigurationError(rf'Only one of [i]\[{registrar._configurationSection}.security]:wsBearerToken[/i] or [i]\[{registrar._configurationSection}.security]:wsUsername[/i] can be set')

			if registrar.security.selfCredentials.httpUsername and not registrar.security.selfCredentials.httpPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:selfHttpPassword[/i] (password is required if username is set)')
			if not registrar.security.selfCredentials.httpUsername and registrar.security.selfCredentials.httpPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:selfHttpUsername[/i] (username is required if password is set)')
			if registrar.security.selfCredentials.wsUsername and not registrar.security.selfCredentials.wsPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:selfWsPassword[/i] (password is required if username is set)')
			if not registrar.security.selfCredentials.wsUsername and registrar.security.selfCredentials.wsPassword:
				raise ConfigurationError(rf'Missing configuration [i]\[{registrar._configurationSection}.security]:selfWsUsername[/i] (username is required if password is set)')