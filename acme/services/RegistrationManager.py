#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resources and AE, CSE registrations
#

from __future__ import annotations
from typing import Any, Optional

from ..etc.Types import ResourceTypes, JSON, CSEType, OriginatorType
from ..etc.ResponseStatusCodes import APP_RULE_VALIDATION_FAILED, ORIGINATOR_HAS_ALREADY_REGISTERED, INVALID_CHILD_RESOURCE_TYPE
from ..etc.ResponseStatusCodes import BAD_REQUEST, OPERATION_NOT_ALLOWED, CONFLICT, NOT_IMPLEMENTED, ResponseException
from ..etc.IDUtils import uniqueAEI, getIdFromOriginator, uniqueRN, originatorToID
from ..etc.DateUtils import getResourceDate
from ..etc.Constants import RuntimeConstants as RC
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..runtime.EventManager import EventManager, EventHandler, onEvent, EventData
from ..resources.Resource import Resource
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires


eventManager = EventManager()
""" Event manager singleton instance. """

@EventHandler
@requires(remoteCSEManager='acme.plugins.services.RemoteCSEManager', required=False)
class RegistrationManager(object):

	remoteCSEManager: Optional[Any] = None	# type: ignore

	__slots__ = (
		'expWorker',

		'_eventAEHasRegistered',
		'_eventAEHasDeregistered',
		'_eventExpireResource',
	)

	def __init__(self) -> None:

		# Start expiration Monitor
		self.expWorker:BackgroundWorker	= None
		self.startExpirationMonitor()
		
		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)			# type: ignore

		# Optimized event handling
		self._eventAEHasRegistered = CSE.event.aeHasRegistered								# type: ignore
		self._eventAEHasDeregistered = CSE.event.aeHasDeregistered							# type: ignore
		self._eventExpireResource = CSE.event.expireResource								# type: ignore

		L.isInfo and L.log('RegistrationManager initialized')


	def shutdown(self) -> bool:
		self.stopExpirationMonitor()
		L.isInfo and L.log('RegistrationManager shut down')
		return True


	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Any = None) -> None:
		"""	Handle configuration updates.
		"""
		if key not in ( 'cse.checkExpirationsInterval', 
						'cse.enableResourceExpiration'
						):
			return
		self.restartExpirationMonitor()


	@onEvent(eventManager.cseReset)
	def restart(self, eventData: EventData) -> None:
		"""	Restart the registration services.
		"""
		self.restartExpirationMonitor()
		L.isDebug and L.logDebug('RegistrationManager restarted')


	#########################################################################

	#
	#	Handle new resources in general
	#

	def checkResourceCreation(self, resource:Resource, 
									originator:str, 
									parentResource:Optional[Resource] = None) -> str:
		# Some Resources are not allowed to be created in a request, return immediately

		match resource.ty:
			case ResourceTypes.AE:
				originator = self.handleAERegistration(resource, originator, parentResource)
			case ResourceTypes.CSR:
				if RC.cseType == CSEType.ASN:
						raise OPERATION_NOT_ALLOWED('cannot register to ASN CSE')
				try:
					self.handleCSRRegistration(resource, originator)
				except ResponseException as e:
					e.dbg = f'cannot register CSR: {e.dbg}'
					raise e
			case ResourceTypes.REQ:
				if not self.handleREQRegistration(resource, originator):
					raise BAD_REQUEST('cannot register REQ')
			case ResourceTypes.CSEBaseAnnc:
				try:
					self.handleCSEBaseAnncRegistration(resource, originator)
				except ResponseException as e:
					e.dbg = f'cannot register CSEBaseAnnc: {e.dbg}'
					raise e
			case ResourceTypes.CSEBase:
				self.handleCSEBaseRegistration(resource, originator)

		# Test and set creator attribute.
		self.handleCreator(resource, originator)

		# return (possibly new) originator
		return originator	


	def postResourceCreation(self, resource:Resource) -> None:
		"""	Handle some post-create aspects, for example send events for some resources.

			Args:
				resource: Resource that was created.
		"""
		match resource.ty:
			case ResourceTypes.AE:
				# Send event
				self._eventAEHasRegistered(resource)
			case ResourceTypes.CSR:
				# send event
				eventManager.registreeCSEHasRegistered(EventData(payload=resource))


	def handleCreator(self, resource:Resource, originator:str) -> None:
		"""	Check for set creator attribute as well as assign it to allowed resources.
		"""
		if resource.hasAttribute('cr'):	# not get, might be empty, which is an indication that it needs to be set
			# Check whether the creator is allowed to be set for this resource 
			# This could be done during validation, but we do it here to have a more specific error message
			# and to return early
			if not resource.hasAttributeDefined('cr'):
				raise BAD_REQUEST(f'"creator" attribute is not allowed for resource type: {resource.ty}')
			
			# Check whether a creator is set in the request
			if resource.cr is not None:		# Check whether cr is set to a value in the request. This is wrong
				raise BAD_REQUEST(L.logWarn('setting the "creator" attribute is not allowed.'))
			resource.setAttribute('cr', originator)
		# fall-through


	def checkResourceUpdated(self, resource:Resource, updateDict:JSON) -> None:
		match resource.ty:
			case ResourceTypes.CSR:
				if not self.handleCSRUpdate(resource, updateDict):
					raise BAD_REQUEST('cannot update CSR')
		# fall-through


	def checkResourceDeletion(self, resource:Resource) -> None:
		match resource.ty:
			case ResourceTypes.AE:
				if not self.handleAEDeRegistration(resource):
					raise BAD_REQUEST('cannot deregister AE')
			case ResourceTypes.REQ:
				if not self.handleREQDeRegistration(resource):
					raise BAD_REQUEST('cannot deregister REQ')
			case ResourceTypes.CSR:
				if not self.handleRegistreeCSRDeRegistration(resource):
					raise BAD_REQUEST('cannot deregister CSR')
			# We do not CSEBase de-registration. This should never happen


	def postResourceDeletion(self, resource:Resource) -> None:
		"""	Handle some post-delete aspects, for example send events for some resources.

			Args:
				resource: Resource that was created.
		"""
		match resource.ty:
			case ResourceTypes.AE:
				# Send event
				self._eventAEHasDeregistered(resource)
			case ResourceTypes.CSR:
				# send event
				eventManager.registreeCSEHasDeregistered(EventData(payload=resource))


	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae:Resource, originator:str, parentResource:Resource) -> str:
		""" This method creates a new originator for the AE registration, depending on the method choosen."""

		L.isDebug and L.logDebug(f'handle AE registration for: {ae.ri} with originator: {originator}')

		# check for empty originator and assign something
		if not originator:
			originator = 'C'	# TODO make this configurable

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not CSE.security.isAllowedOriginator(originator, Configuration.cse_registration_allowedAEOriginators):
			raise APP_RULE_VALIDATION_FAILED(L.logDebug('Originator not allowed'))

		# Assign originator for the AE
		match originator:
			case 'C':
				# Assigning a C originator is trivial, just create a unique AEI in
				# the scope of the local CSE
				originator = uniqueAEI('C')
			case 'S':
				# Assigning an S originator requires interactions with the {remote) IN-CSE.
				originator = self.registerSOriginator(ae, originator)

		# Check whether an originator has already registered with the same AE-ID
		if self.hasRegisteredAE(originator):
			raise ORIGINATOR_HAS_ALREADY_REGISTERED(L.logWarn(f'Originator has already registered: {originator}'))
		
		# Make some adjustments to set the originator in the <AE> resource
		L.isDebug and L.logDebug(f'Registering AE. aei: {originator}')
		ae['aei'] = originator												# set the aei to the originator
		ae['ri'] = getIdFromOriginator(originator, idOnly=True)		# set the ri of the ae to the aei (TS-0001, 10.2.2.2)

		# Verify that parent is the CSEBase, else this is an error
		if not parentResource or parentResource.ty != ResourceTypes.CSEBase:
			raise INVALID_CHILD_RESOURCE_TYPE('Parent must be the CSE')

		# Add the originator to the database
		# TODO distinguid between C and S originators 
		CSE.storage.addOriginator(originator, OriginatorType.CAEID)

		return originator


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, ae:Resource) -> bool:
		# More De-registration functions happen in the AE's deactivate() method
		L.isDebug and L.logDebug(f'DeRegistering AE. aei: {ae.aei}')

		# Special handling for "S" registrations
		if ae.aei.startswith('S'):
			self.deregisterSOriginator(ae)

		# delete the originator from the database
		CSE.storage.removeOriginator(ae.aei)	

		# Send event
		self._eventAEHasDeregistered(ae)

		return True


	def hasRegisteredAE(self, originator:str) -> bool:
		"""	Check wether an AE with *originator* is registered at the CSE.

			Args:
				originator: ID of the originator / AE.
			Return
				True if the originator is registered with the CSE.

			Todo:
				Currently this is done by searching the storage. This should be optimized by using an index for the originator.
		"""
		return CSE.storage.getOriginator(originator) is not None	

	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Registering CSR. csi: {csr.csi}')

		if not self.remoteCSEManager:
			raise NOT_IMPLEMENTED(L.logWarn('RemoteCSEManager is disabled, cannot register CSR'))
		# Check whether this is an ASN-CSE
		if RC.cseType == CSEType.ASN and originator != self.remoteCSEManager.registrarConfig.cseID:
			raise OPERATION_NOT_ALLOWED(L.logWarn('Registration to ASN CSE is not allowed'))
	
		# Check that the originator is not an AE
		if CSE.security.isAEOriginator(originator):
			if originator != RC.cseOriginator:
				raise OPERATION_NOT_ALLOWED(L.logWarn('AE originator not allowed for CSR registration'))
			L.isWarn and L.logWarn('Warning: CSR registration with Admin originator')

		# Check whether a CSE with the same originator has already registered

		if originator != RC.cseOriginator and self.hasRegisteredAE(originator):
			raise OPERATION_NOT_ALLOWED(L.logWarn(f'Originator has already registered an AE: {originator}'))
		
		# Always replace csi with the originator (according to TS-0004, 7.4.4.2.1)
		if not CSE.importer.isImporting:	# ... except when the resource was just been imported
			csr['csi'] = originator if originator.startswith('/') else f'/{originator}'	# A bit of a HACK to allow Admin AE to register CSR with csi = /CSE-ID
			csr['ri']  = originatorToID(originator)

		# Validate csi in csr
		CSE.validator.validateCSICB(csr.csi, 'csi')

		# Validate cb in csr
		CSE.validator.validateCSICB(csr.cb, 'cb')


	#
	#	Handle CSR deregistration
	#

	def handleRegistreeCSRDeRegistration(self, registreeCSR:Resource) ->  bool:
		"""	Handle the de-registration of a registree <CSR> resource.
		
			Args:
				registreeCSR: The <CSR> resource to de-register.
			
			Return:
				Always *True*.
		"""
		L.isDebug and L.logDebug(f'De-registering registree CSR. csi: {registreeCSR.csi}')
		# send event
		eventManager.registreeCSEHasDeregistered(EventData(payload=registreeCSR))
		return True


	#
	#	Handle CSR Update
	#

	def handleCSRUpdate(self, csr:Resource, updateDict:JSON) -> bool:
		L.isDebug and L.logDebug(f'Updating CSR. csi: {csr.csi}')
		# send event
		eventManager.csrUpdated(EventData(payload=(csr, updateDict)))
		return True


	#########################################################################

	#
	#	Handle CSEBaseAnnc registration
	#

	def handleCSEBaseAnncRegistration(self, cbA:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Registering CSEBaseAnnc. csi: {cbA.csi}')

		# Check whether the same CSEBase has already registered (-> only once)
		if (lnk := cbA.lnk):
			if len(CSE.storage.searchByFragment({'lnk': lnk})) > 0:
				raise CONFLICT(L.logDebug(f'CSEBaseAnnc with lnk: {lnk} already exists'))

		# Assign a rn
		# TODO get infos from CBAnnc: spID and csi
		# cbA.setResourceName(uniqueRN(f'{cbA.typeShortname}_{getIdFromOriginator(originator)}'))


	#########################################################################

	#
	#	Handle REQ registration
	#

	def handleREQRegistration(self, req:Resource, originator:str) -> bool:
		L.isDebug and L.logDebug(f'Registering REQ: {req.ri}')
		# Add originator as creator to allow access
		req.setOriginator(originator)
		return True


	#
	#	Handle REQ deregistration
	#

	def handleREQDeRegistration(self, resource:Resource) -> bool:
		L.isDebug and L.logDebug(f'DeRegisterung REQ. ri: {resource.ri}')
		return True


	#########################################################################

	#
	#	Handle CSEBaseregistration
	#

	def handleCSEBaseRegistration(self, cb:Resource, originator:str) -> None:
		csi = cb.csi
		L.isDebug and L.logDebug(f'Registering CSEBase. csi: {cb.csi}')
		if CSE.storage.getOriginator(csi):
			raise CONFLICT(L.logDebug(f'CSEBase with csi: {csi} already exists'))
		
		# For now only store the csi as originator
		CSE.storage.addOriginator(csi, OriginatorType.CSEID)


	#########################################################################
	##
	##	Resource Expiration
	##

	def startExpirationMonitor(self) -> None:
		# Start background monitor to handle expired resources
		if not Configuration.cse_enableResourceExpiration:
			L.isDebug and L.logDebug('Expiration disabled. NOT starting expiration monitor')
			return

		L.isDebug and L.logDebug('Starting expiration monitor')
		if Configuration.cse_checkExpirationsInterval > 0:
			self.expWorker = BackgroundWorkerPool.newWorker(Configuration.cse_checkExpirationsInterval, self.expirationDBMonitor, 'expirationMonitor', runOnTime=False).start()


	def stopExpirationMonitor(self) -> None:
		# Stop the expiration monitor
		L.isDebug and L.logDebug('Stopping expiration monitor')
		if self.expWorker:
			self.expWorker.stop()


	def restartExpirationMonitor(self) -> None:
		# Stop the expiration monitor
		L.isDebug and L.logDebug('Restart expiration monitor')
		if self.expWorker:
			self.expWorker.restart(Configuration.cse_checkExpirationsInterval)


	def expirationDBMonitor(self) -> bool:
		# L.isDebug and L.logDebug('Looking for expired resources')
		now = getResourceDate()
		resources = CSE.storage.searchByFilter(lambda r: (et := r.get('et'))  and et < now)
		for resource in resources:
			# try to retrieve the resource first bc it might have been deleted as a child resource
			# of an expired resource
			if not CSE.storage.hasResource(ri=resource.ri):
				continue
			L.isDebug and L.logDebug(f'Expiring resource (and child resouces): {resource.ri}')
			CSE.dispatcher.deleteLocalResource(resource, withDeregistration = True)	# ignore result
			self._eventExpireResource(resource) 
				
		return True


	#########################################################################

	#########################################################################

	def registerSOriginator(self, ae: Resource, originator: str) -> str:
		"""	Register the S-Originator for an AE resource.

			Args:
				ae: The AE resource.
				originator: The original originator.
			Return:
				The assigned S-Originator.
		"""
		return uniqueAEI('S')


	def deregisterSOriginator(self, ae: Resource) -> None:
		"""	Deregister the S-Originator for an AE resource.

			Args:
				ae: The AE resource.
		"""
		# In case an \<AE> resource hosted on a MN-CSE or ASN-CSE with AE-ID-Stem starting with "S" is
		# requested to be deleted, the \<AEAnnc> resource that was created on the IN-CSE during the 
		# initial registration of the associated Application Entity shall be updated with the value 
		# "INACTIVE" for the link attribute and the value INACTIVE for the *registrationStatus* attribute,
		# that the associated Application Entity is currently not registered. After this update of the 
		# \<AEAnnc> resource is completed, the procedure for AE Deregistration 
		# shall follow the procedure described in this clause.
		pass