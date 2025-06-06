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

from ..etc.Types import CSEStatus, ResourceTypes, CSEType, ResponseStatusCode, JSON, CSERequest, Operation
from ..etc.Types import ContentSerializationType, BindingType, CSERegistrar
from ..etc.ResponseStatusCodes import exceptionFromRSC, ResponseException, NOT_FOUND, BAD_REQUEST, INTERNAL_SERVER_ERROR, CONFLICT, TARGET_NOT_REACHABLE
from ..etc.ACMEUtils import pureResource
from ..etc.IDUtils import csiFromRelativeAbsoluteUnstructured, isAbsolute, getSPFromID, originatorToID	# cannot import at the top because of circel import
from ..etc.Utils import isHttpUrl, isWSUrl, buildBasicAuthUrl
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..helpers.TextTools import findXPath, setXPath
from ..resources.CSR import CSR
from ..resources.CSEBase import CSEBase, getCSE
from ..resources.Resource import Resource
from ..resources.Factory import resourceFromDict
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..runtime.Logging import Logging as L


class RemoteCSEManager(object):
	"""	This class defines functionalities to handle remote CSE/CSR registrations.

		Attributes:
			connectionMonitor: A `BackgroundWorker` that periodically checks the registrations.
			descendantCSR: A dictionary of descendant CSEs mappings: csi -> (CSR, registeredATcsi)
			registrarConfig: The local registrar configuration entry.
			spRegistrarConfigs: A dictionary of all SP registrar configurations except the own one.
	"""

	__slots__ = (
		'connectionMonitor',
		'descendantCSR',
		'registrarConfig',
		'spRegistrarConfigs',

		'_eventRegisteredToRegistrarCSE',
		'_eventDeregisteredFromRegistrarCSE',
	)


	def __init__(self) -> None:
		"""	Class constructor.
		"""

		# Some manager attributes
		self.connectionMonitor:BackgroundWorker = None				# BackgroundWorker
		self.descendantCSR:Dict[str, Tuple[Resource, str]]	= {}	# dict of descendantCSR's - "csi : (CSR, registeredATcsi)". CSR is None for CSEs further down 
		self.registrarConfig:CSERegistrar = None 					# Locally store the own registrar's config entry for simplicity

		# Get the configuration settings
		self._assignConfig()

		#	The following lines register event handlers for registration and de-registration events.
		#	The following events are registered when registerueng and de-registerung from the registrar CSE
		CSE.event.addHandler(CSE.event.registeredToRegistrarCSE, self.handleRegistrarRegistrationEvent)				# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRegistrarCSE, self.handleRegistrarDeregistrationEvent)		# type: ignore

		#	The following events are usually thrown by the Registration Manager.
		CSE.event.addHandler(CSE.event.registreeCSEHasRegistered, self.handleRegistreeCSERegistrationEvent)			# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEHasDeregistered, self.handleRegistreeCSEDeregistrationEvent)		# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEUpdate, self.handleRegistreeCSEUpdateEvent)							# type: ignore

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		# Add a handler when the CSE is started
		CSE.event.addHandler(CSE.event.cseStartup, self.start)	# type: ignore
		L.isInfo and L.log('RemoteCSEManager initialized')

		# Optimize event handling
		self._eventRegisteredToRegistrarCSE = CSE.event.registeredToRegistrarCSE			# type: ignore [attr-defined]
		self._eventDeregisteredFromRegistrarCSE = CSE.event.deregisteredFromRegistrarCSE	# type: ignore [attr-defined]



	def shutdown(self) -> bool:
		"""	Shutdown the RemoteCSEManager.
		
			Return:
				Always return True.
		"""
		self.stop()
		L.isInfo and L.log('RemoteCSEManager shut down')
		return True


	def restart(self) -> None:
		"""	Restart the remote service monitor.
		"""
		if self.connectionMonitor:
			self.connectionMonitor.workNow()
		L.isDebug and L.logDebug('RemoteManager restarted')


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		# Locally store the own registrar's config entry for simplicity
		self.registrarConfig = Configuration.cse_registrars.get(RC.cseSpid)
		self.spRegistrarConfigs = {spid:config for spid, config in Configuration.cse_registrars.items() if spid != RC.cseSpid}	# all SP registrar configs except the own one


	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.enableRemoteCSE' ] or not key.startswith(('cse.registrar', 'cse.sp.registrar.')):
			return

		# assign new values
		self._assignConfig()


	#########################################################################
	#
	#	Connection Monitor
	#

	def start(self, name:str) -> None:
		"""	Start the remote monitor as a background worker. 

			Args:
				name: Event name.
		"""
		if not Configuration.cse_enableRemoteCSE:
			return

		# Internal optimization: collect all descendant CSEs in a dictionary
		L.isDebug and L.logDebug('Rebuild internal descendants list')
		self.descendantCSR.clear()
		for eachCsr in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.CSR):

			if self.registrarConfig and self.registrarConfig.spID == RC.cseSpid and (csi := eachCsr.csi) != self.registrarConfig.cseID:			# Skipping the own registrar csr
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


	def stop(self) -> None:
		"""	Stop the connection monitor. Also delete the CSR resources on both sides, if possible.
		"""
		if not Configuration.cse_enableRemoteCSE:
			return
		L.isInfo and L.log('Stopping remote CSE connection monitor')

		# Stop the worker
		if self.connectionMonitor:
			self.connectionMonitor.stop()
			self.connectionMonitor = None

		# Remove <csr> resources
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

	def handleRegistrarRegistrationEvent(self, name:str,  
									  	   registrarConfig:CSERegistrar,
										   registrarCSE:Resource, 
										   ownRegistrarCSR:Resource) -> None:
		""" Event handler for adding a registrar CSE/CSR CSI to the list of registered csi.

			Args:
				name:Event name.
				registrarConfig: The registrar configuration that is registered.
			 	registrarCSE: The CSR that just registered (the CSR from the registrar CSE).
				ownRegistrarCSR: The own CSR on the the registrar CSE
		"""
		registrarConfig._registrarCSEBaseResource = registrarCSE


	def handleRegistrarDeregistrationEvent(self, 
										   name:str, 
										   registrarConfig:CSERegistrar,
										   registrarCSE:Optional[Resource]=None) -> None:
		"""	Event handler for removing the registrar CSE/CSR CSI from the list of registered csi.

			Args:
				name:Event name.
				registrarConfig: The registrar configuration that is de-registered.
				registrarCSE: The registrar CSE that is de-registered.
		"""
		registrarConfig._registrarCSEBaseResource = None


	def handleRegistreeCSERegistrationEvent(self, name:str, registreeCSR:Resource) -> None:
		"""	Event handler for adding a registree's CSE's <CSR> to the list of registered descendant CSE. 

			Only the local registrar configuration is involved here.

			Args:
				name:Event name.
				registreeCSR: The CSR that just registered.
		"""
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
		CSE.event.registeredToRemoteCSE(registreeCSR)	# type: ignore


	def handleRegistreeCSEDeregistrationEvent(self, name:str, registreeCSR:Resource) -> None:
		"""	Event handler for removals of registree's CSE/CSR CSI from the list of registered descendant CSE. 

			Only the local registrar configuration is involved here.
		
			Args:
				name:Event name.
				registreeCSR: the CSR that just de-registered.
		"""
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


	def handleRegistreeCSEUpdateEvent(self, name:str, registreeCSR:Resource, updateDict:JSON) -> None:
		"""	Event handler for an updates of a registree CSE.

			Only the local registrar configuration is involved here.

			Args:
				name:Event name.
				registreeCSR: The updated registree CSE.
				updateDict: The resource dictionary with the updated attributes.
		"""
		L.isDebug and L.logDebug(f'Handle registree CSE update: {registreeCSR}\nupdate: {updateDict}')

		# handle update of dcse in remoteCSR
		registreeCsi = registreeCSR.csi

		L.isDebug and L.logDebug(f'Update of descendantCSRs: {self.descendantCSR}')
		# remove all descendant tuples that are from this CSR
		for eachDcse in list(self.descendantCSR.keys()):	# !!! make a copy of the keys bc the list changes in this loop
			if eachDcse in self.descendantCSR:	# Entry could have been deleted, so we need to check
				(_, registeredAtCsi) = self.descendantCSR[eachDcse]
				if registeredAtCsi == registreeCsi :	# remove all descedants EXCEPT the ones hosted on THIS CSE
					L.isDebug and L.logDebug(f'Removing from internal dcse list: {eachDcse}')
					if eachDcse in self.descendantCSR:
						del self.descendantCSR[eachDcse]

		# add new/updated values from remoteCSR
		if dcse := findXPath(updateDict, 'm2m:csr/dcse'):
			for eachDcse in dcse:
				if eachDcse in self.descendantCSR:	# don't overwrite existing ones. Can this actually happen?
					continue
				self.descendantCSR[eachDcse] = (None, registreeCsi)	# don't have the CSR for further descendants available

		if RC.cseType in [ CSEType.ASN, CSEType.MN ]:	# update own registrar CSR
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
						self._createLocalCSR(registrarConfig)		# ignore result
						self._eventRegisteredToRegistrarCSE(registrarConfig, registrarConfig._registrarCSEBaseResource, csr)
						L.isInfo and L.log(f'Registered to registrar CSE: {registrarConfig.cseID}')
					except:
						pass
				except:
					L.isInfo and L.log('Disconnected from registrar CSE')
					self._eventDeregisteredFromRegistrarCSE(registrarConfig, csr)
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
					self._createLocalCSR(registrarConfig) 	# create local CSR including ACPs to local CSR and local CSE. Ignore result
					self._eventRegisteredToRegistrarCSE(registrarConfig, registrarConfig._registrarCSEBaseResource, csr)
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
		for eachCsr in self._retrieveLocalCSRResources(registrarConfig, withRegistreeCSR=True):
			L.isDebug and L.logDebug(f'Checking connection to registree CSE: {eachCsr.csi}')
			if (to := self.getRemoteCSEBaseAddress(eachCsr.csi)) is None:
				self._deleteRegistreeCSR(eachCsr)
				continue
			try:
				sp = getSPFromID(eachCsr.csi)	# !!! In CSR the csi attribute contains the absolute csi, other then in the CSEBase
				match sp:
					case None | RC.cseSpid:	# no SP or own SP
						originator = RC.cseCsi
					case _:
						originator = f'//{RC.cseSpid}{RC.cseCsi}'	# SP-relative originator

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

	def _retrieveLocalCSRResources(self, registrarConfig:CSERegistrar,
										 includeRegistrarCSR:Optional[bool]=False, 
										 withRegistreeCSR:Optional[bool]=False) -> List[Resource]:
		"""	Retrieve the local <CSR> resources.
		
			Args:
				registrarConfig: The registrar configuration to use for the search.
				includeRegistrarCSR: If *True* then include the CSR to the registrar CSE in the result.
				withRegistreeCSR: if *True* then include the CSR(s) to the registree CSE(s) in the result.

			Return:
				A list of found CSR resources.
		"""
		registreeCsrList = []
		for eachCSR in CSE.dispatcher.retrieveDirectChildResources(pi=RC.cseRi, ty=ResourceTypes.CSR):


		# TODO in this search, instead of a fixed cseid use a list and accept all cseIDs that are in the list
			L.isDebug and L.logDebug(f'Checking local CSR: {eachCSR.csi} - registrarConfig: {registrarConfig}')
			
			if registrarConfig and eachCSR.csi == registrarConfig._registrarAbsoluteCSI:		# type: ignore[name-defined]
				if includeRegistrarCSR: 	
					registreeCsrList.append(eachCSR)
			else:
				if withRegistreeCSR: 	
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
		csrResource.initialize(localCSE.ri, RC.cseOriginator)	# remoteCSE.csi as name!

		# add local CSR and ACP's
		try:
			CSE.dispatcher.createLocalResource(csrResource, localCSE, originator=remoteCSE.csi)
			CSE.registration.handleCSRRegistration(csrResource, csrResource.csi)
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
		if not CSE.registration.handleRegistreeCSRDeRegistration(registreeCSR):
			raise BAD_REQUEST('cannot de-register registree CSR')

		# Delete local CSR
		CSE.dispatcher.deleteLocalResource(registreeCSR)


	#
	#	Remote Registrar CSR request methods
	#

	def _retrieveOwnCSRfromRegistrarCSE(self, registrarConfig:CSERegistrar) -> Resource:
		"""	Retrieve the own <CSR> resource from the registrar CSE.
		
			Return:
				Resource object
		"""
		L.isDebug and L.logDebug(f'Retrieve own CSR from registrar CSE: {registrarConfig._registrarAbsoluteCSI} ID: {registrarConfig._csrOnRegistrarSRN}')
		
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.RETRIEVE,
													   to=registrarConfig._csrOnRegistrarSRN,
													   _directURL=registrarConfig._csrOnRegistrarSRN,	# Fallback, because there might be no registration yet
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
		return resourceFromDict(cast(JSON, res.data), pi='')


	def _createCSRonRegistrarCSE(self, registrarConfig:CSERegistrar) -> Resource:
		L.isDebug and L.logDebug(f'creating CSR at registrar CSE: {registrarConfig.cseID} uri: {registrarConfig._registrarCSESRN}')	
		
		# get local CSEBase and copy relevant attributes
		localCSE = getCSE()
		csrResource = CSR()
		csrResource.setResourceName(registrarConfig._registrarCSRRN)
		csrResource.setAttribute('rr', True)
		self._copyCSE2CSR(registrarConfig, 
						  csrResource, 
						  localCSE, 
						  targetCsi=registrarConfig.cseID,
						  forOwnCSR=True)	# type: ignore[name-defined]
		
		# Create the <csr> on the registrar CSE
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.CREATE,
													   to=registrarConfig._registrarCSESRN,
													   _directURL=registrarConfig._registrarCSEURL,	# We may not have the resource yet, so we need to use the configured URL
													#    originator=RC.cseCsi, # own CSE.csi is the originator
													   originator=registrarConfig.originator,
													   ty=ResourceTypes.CSR, 
													   pc=csrResource.asDict(),
													   ct=cast(ContentSerializationType, registrarConfig.serialization),
													   credentials=registrarConfig.security.credentials)
										   )[0].result	# there should be at least one result

		if res.rsc not in [ ResponseStatusCode.CREATED, ResponseStatusCode.OK, ResponseStatusCode.CONFLICT ]:
			_exc = exceptionFromRSC(res.rsc)
			if _exc:
				raise _exc(dbg = L.logDebug(f'error creating CSR on registrar CSE: {int(res.rsc)} dbg: {res.resource}')) # type:ignore[call-arg]
			raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')
		
		# If the resource already exists then perhaps it is a leftover from a previous session. It should have been deleted,
		# but who knows? Just re-use that one for now.
		if res.rsc == ResponseStatusCode.CONFLICT:
			raise CONFLICT(L.logDebug(f'error creating CSR on registrar CSE: {res.rsc.name} dbg: {res.data}'))
		else:
			L.isDebug and L.logDebug(f'created CSR on registrar CSE: {registrarConfig.cseID}')
		return resourceFromDict(cast(JSON, res.data), pi = '')


	def _updateOwnCSRonRegistrarCSE(self, registrarConfig:CSERegistrar, hostingCSE:Optional[Resource]=None) -> Resource:
		"""	Update the own <CSR> resource on the registrar CSE.

			Args:
				registrarConfig: The registrar configuration to use for the update.
				hostingCSE: Optional CSE resource to use for the update. If None, the hosting <CSEBase> resource will be used.

			Return:
				Resource
		"""
		L.isDebug and L.logDebug(f'updating own <CSR> on registrarCSE: {registrarConfig.cseID} URI: {registrarConfig._csrOnRegistrarSRN}')
		if not hostingCSE:
			hostingCSE = getCSE()
		
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
													   to=registrarConfig._csrOnRegistrarSRN, 
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
		return resourceFromDict(cast(JSON, res.data), pi='')


	def _deleteOwnCSRonRegistrarCSE(self, registrarConfig:CSERegistrar) -> None:
		"""	Delete the own <CSR> resource from the registrar CSE.

			Args:
				registrarConfig: The registrar configuration to use for the deletion.
		"""
		if registrarConfig:
			L.isDebug and L.logDebug(f'Deleting own CSR on registrar CSE: {registrarConfig.cseID} URI: {registrarConfig._csrOnRegistrarSRN}')
			res = CSE.request.handleSendRequest(CSERequest(op=Operation.DELETE,
														   to=registrarConfig._csrOnRegistrarSRN,
														   _directURL=registrarConfig._registrarCSEURL,	# Fallback, because there might be no registration yet
													  	   originator=registrarConfig.originator,
														   ct=cast(ContentSerializationType, registrarConfig.serialization),
														   credentials=registrarConfig.security.credentials)
											)[0].result	# there should be at least one result

			# NOT_FOUND might be raised above
			if res.rsc not in [ ResponseStatusCode.DELETED, ResponseStatusCode.OK ]:
				_exc = exceptionFromRSC(res.rsc)
				if _exc:
					raise _exc(dbg=L.logDebug(f'cannot delete remote CSR: {int(res.rsc)} dbg: {res.dbg}')) # type:ignore[call-arg]
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
		L.isDebug and L.logDebug(f'Retrieving registrar CSEBase from: {registrarConfig._registrarAbsoluteCSI}')	
		
		res = CSE.request.handleSendRequest(CSERequest(op=Operation.RETRIEVE,
													   to=registrarConfig._registrarCSESRN,
													   _directURL=registrarConfig._registrarCSEURL,	# Fallback, because there might be no registration yet
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


	def getAllLocalCSRs(self) -> List[Resource]:
		"""	Return all local <CSR> resources. This includes the <CSR> of the registrar CSE.
			This function builds the list from a temporary internal list, but not from the database.

			Return:
				List of <CSR> resources.
		"""
		return [ csr for (csr, _) in self.descendantCSR.values() if csr ]


	#########################################################################


	def retrieveRemoteResource(self, id:str, originator:Optional[str]=None) -> Resource:
		"""	Retrieve a remote resource from one of the interconnected CSEs.

			Args:
				id: The resource ID. It must be at least in SP-relative format.
				originator: Optional request originator. If *None* is given then the CSE's CSE-ID is used.
			
			Return:
				Result object with the status and, if successful, the resource object in the *resource* attribute.
		"""

		# We cannot regularly retrieve a remote resource if we are not fully registered (yet).
		resourceList = self._retrieveLocalCSRResources(None, includeRegistrarCSR=True, withRegistreeCSR=True)

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
		return resourceFromDict(cast(JSON, res.data))


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
		
		ri, ids = csiFromRelativeAbsoluteUnstructured(id)

		# Normally, ri is the csi stem, but with absolute IDs we need to
		# construct the ri a bit differently. Hack.
		if isAbsolute(id):
			ri = f'{ids[2]}_{ids[3]}'

		# Search for a <CSR> that either has the csi attribute set, or that has the looked-for
		# registree CSE as a descendant CSE.

		try:
			registreeCSR = CSE.dispatcher.retrieveLocalResource(ri=ri)
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


	#########################################################################


	def _copyCSE2CSR(self, registrarConfig:CSERegistrar,
				  		   target:Resource, 
						   source:Resource, 
						   isUpdate:Optional[bool]=False, 
						   targetCsi:str=None,
						   forOwnCSR:Optional[bool]=False) -> None:
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
		for attr in [ 'cst', 'csz', 'lbl', 'nl', 'rr', 'srv', 'st' ]:
			if attr in source and attr not in registrarConfig.excludeCSRAttributes:
				target[attr] = source[attr]

		if 'csi' not in registrarConfig.excludeCSRAttributes:
			if registrarConfig.spID == RC.cseSpid:
				target['csi'] = source['csi']
			else:
				target['csi'] = f'//{RC.cseSpid}{source.csi}' if forOwnCSR else f'//{registrarConfig.spID}{source.csi}'	# prepend the SP-ID if it is not the same as the CSE's SP-ID

		if 'cb' not in registrarConfig.excludeCSRAttributes:
			if registrarConfig.spID == RC.cseSpid:
				target['cb'] = f'{source.csi}/{source.rn}'
			else:
				target['cb'] = f'//{RC.cseSpid}{source.csi}/{source.rn}' if forOwnCSR else f'//{registrarConfig.spID}{source.csi}/{source.rn}'	# prepend the SP-ID if it is not the same as the CSE's SP-ID

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

