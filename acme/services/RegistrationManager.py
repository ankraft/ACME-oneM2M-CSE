#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resources and AE, CSE registrations
#
"""	Implementation of the RegistrationManager, which is responsible for handling registrations and de-registrations of 
	AE, CSE and other resources. """

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

from ..etc.Types import ResourceTypes, JSON, CSEType, OriginatorType
from ..etc.ResponseStatusCodes import APP_RULE_VALIDATION_FAILED, ORIGINATOR_HAS_ALREADY_REGISTERED, INVALID_CHILD_RESOURCE_TYPE
from ..etc.ResponseStatusCodes import BAD_REQUEST, OPERATION_NOT_ALLOWED, CONFLICT, NOT_IMPLEMENTED, ResponseException
from ..etc.IDUtils import uniqueAEI, getIdFromOriginator, originatorToID
from ..etc.DateUtils import getResourceDate
from ..etc.Constants import RuntimeConstants as RC
from ..runtime.Configuration import Configuration
from ..runtime.EventManager import EventManager, EventHandler, onEvent, EventData
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers.Singleton import Singleton
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import *
from ..runtime.EventManager import *


if TYPE_CHECKING:
	from ..resources.Resource import Resource
	from ..services.Dispatcher import Dispatcher
	from ..services.SecurityManager import SecurityManager
	from ..runtime.Storage import Storage
	from ..runtime.Importer import Importer
	from ..services.Validator import Validator
	from acme.plugins.services.RemoteCSEManager import RemoteCSEManager


@EventHandler
@requires(remoteCSEManager='acme.plugins.services.RemoteCSEManager', required=False)
@requires(dispatcher='acme.services.Dispatcher')
@requires(storage='acme.runtime.Storage')
@requires(securityManager='acme.services.SecurityManager')
@requires(importer='acme.runtime.Importer')
@requires(validator='acme.services.Validator')
class RegistrationManager(metaclass=Singleton):
	"""	RegistrationManager to handle registrations and de-registrations resources. """

	dispatcher: Dispatcher = None	# type: ignore
	""" Injected Dispatcher instance. """

	storage:Storage = None	# type: ignore
	""" Injected Storage instance. """

	securityManager: SecurityManager = None	# type: ignore
	""" Injected SecurityManager instance. """

	remoteCSEManager: Optional[RemoteCSEManager] = None	# type: ignore
	""" Injected RemoteCSEManager plugin, if available. """

	importer: Importer = None	# type: ignore
	""" Injected Importer instance. """

	validator: Validator = None	# type: ignore
	""" Validator instance. """

	__slots__ = (
		'expWorker',
	)
	""" Slots for the RegistrationManager. """

	def initialize(self) -> None:
		""" Initialize the RegistrationManager.
		"""
		# Start expiration Monitor
		self.expWorker:BackgroundWorker	= None
		"""	Background worker for checking expired resources. 
		"""
		
		self.startExpirationMonitor()		
		L.isInfo and L.log('RegistrationManager initialized')


	def shutdown(self) -> bool:
		""" Shutdown the RegistrationManager. 

			Return:
				Always *True*.
		"""
		self.stopExpirationMonitor()
		L.isInfo and L.log('RegistrationManager shut down')
		return True


	@onEvent(eventManager.configUpdate)
	def configUpdate(self, eventData: EventData) -> None:
		"""	Handle configuration updates.
			
			Args:
				eventData: The event data, containing the name of the updated configuration setting and its new value.
		"""
		key:Optional[str] = eventData[0]
		value:Any = eventData[1]

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
		"""	Check the creation of a resource, for example handle registrations for AE, CSR and CSEBase resources.
		
			Args:
				resource: The resource to be created.
				originator: The originator of the request that triggered the creation of the resource.
				parentResource: The parent resource of the resource to be created, if available. 
			Return:
				The (possibly new) originator to be used for the resource creation. 
					This is relevant for AE registrations, where a new originator is created for the registered AE.	
			Raises:
				OPERATION_NOT_ALLOWED: If the operation is not allowed.
				BAD_REQUEST: If the request is malformed or invalid.
		"""
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
				eventManager.aeHasRegistered(EventData(payload=resource))	# type: ignore [attr-defined]
			case ResourceTypes.CSR:
				# send event
				eventManager.registreeCSEHasRegistered(EventData(payload=resource))


	def handleCreator(self, resource:Resource, originator:str) -> None:
		"""	Check for set creator attribute as well as assign it to allowed resources.

			Args:
				resource: The resource for which to check and set the creator attribute.
				originator: The originator to set as creator, if allowed.

			Raises:
				BAD_REQUEST: If the creator attribute is not allowed for the resource type, or if the originator is not allowed to be set as creator.

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
		"""	Check the update of a resource, for example handle updates for CSR resources.
		
			Args:
				resource: The resource to be updated.
				updateDict: The update dict with the new values for the resource attributes.

			Raises:
				BAD_REQUEST: If the update is not allowed for the resource type.
		"""
		match resource.ty:
			case ResourceTypes.CSR:
				if not self.handleCSRUpdate(resource, updateDict):
					raise BAD_REQUEST('cannot update CSR')
		# fall-through


	def checkResourceDeletion(self, resource:Resource) -> None:
		"""	Check the deletion of a resource, for example handle de-registrations for AE, CSR and REQ resources.

			Args:
				resource: The resource to be deleted.

			Raises:
				BAD_REQUEST: If the deletion is not allowed for the resource type.
		"""
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
				eventManager.aeHasDeregistered(EventData(payload=resource))
			case ResourceTypes.CSR:
				# send event
				eventManager.registreeCSEHasDeregistered(EventData(payload=resource))


	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae:Resource, originator:str, parentResource:Resource) -> str:
		""" This method creates a new originator for the AE registration, depending on the method choosen.
		
			Args:
				ae: The AE resource to be registered.
				originator: The originator of the request that triggered the registration of the AE. 
					This can be empty, in which case a new originator is created for the AE.
				parentResource: The parent resource of the AE to be registered. This should be the CSEBase resource.
			
			Return:
				The originator to be used for the AE registration. 

			Raises:
				APP_RULE_VALIDATION_FAILED: If the originator is not allowed.
				INVALID_CHILD_RESOURCE_TYPE: If the parent resource is not the CSEBase.
		"""

		L.isDebug and L.logDebug(f'handle AE registration for: {ae.ri} with originator: {originator}')

		# check for empty originator and assign something
		if not originator:
			originator = 'C'	# TODO make this configurable

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not self.securityManager.isAllowedOriginator(originator, Configuration.cse_registration_allowedAEOriginators):
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
		self.storage.addOriginator(originator, OriginatorType.CAEID)

		return originator


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, ae:Resource) -> bool:
		""" Handle the de-registration of an AE resource. This includes the deletion of the originator and sending events.
		
			Args:
				ae: The <AE> resource to be de-registered.
			
			Return:
				Always *True*.
		"""
		# More De-registration functions happen in the AE's deactivate() method
		L.isDebug and L.logDebug(f'DeRegistering AE. aei: {ae.aei}')

		# Special handling for "S" registrations
		if ae.aei.startswith('S'):
			self.deregisterSOriginator(ae)

		# delete the originator from the database
		self.storage.removeOriginator(ae.aei)	

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
		return self.storage.getOriginator(originator) is not None	

	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr:Resource, originator:str) -> None:
		""" Handle the registration of a <CSR> resource. 
			
			Args:
				csr: The <CSR> resource to be registered.
				originator: The originator of the request that triggered the registration of the <CSR>.

			Raises:
				OPERATION_NOT_ALLOWED: If the registration is not allowed.
				NOT_IMPLEMENTED: If the RemoteCSEManager is disabled.
		"""
		L.isDebug and L.logDebug(f'Registering CSR. csi: {csr.csi}')

		if not self.remoteCSEManager:
			raise NOT_IMPLEMENTED(L.logWarn('RemoteCSEManager is disabled, cannot register CSR'))
		# Check whether this is an ASN-CSE
		if RC.cseType == CSEType.ASN and originator != self.remoteCSEManager.registrarConfig.cseID:
			raise OPERATION_NOT_ALLOWED(L.logWarn('Registration to ASN CSE is not allowed'))
	
		# Check that the originator is not an AE
		if self.securityManager.isAEOriginator(originator):
			if originator != RC.cseOriginator:
				raise OPERATION_NOT_ALLOWED(L.logWarn('AE originator not allowed for CSR registration'))
			L.isWarn and L.logWarn('Warning: CSR registration with Admin originator')

		# Check whether a CSE with the same originator has already registered

		if originator != RC.cseOriginator and self.hasRegisteredAE(originator):
			raise OPERATION_NOT_ALLOWED(L.logWarn(f'Originator has already registered an AE: {originator}'))
		
		# Always replace csi with the originator (according to TS-0004, 7.4.4.2.1)
		if not self.importer.isImporting:	# ... except when the resource was just been imported
			csr['csi'] = originator if originator.startswith('/') else f'/{originator}'	# A bit of a HACK to allow Admin AE to register CSR with csi = /CSE-ID
			csr['ri']  = originatorToID(originator)

		# Validate csi in csr
		self.validator.validateCSICB(csr.csi, 'csi')

		# Validate cb in csr
		self.validator.validateCSICB(csr.cb, 'cb')


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
		"""	Handle the update of a <CSR> resource.
		
			Args:
				csr: The <CSR> resource to be updated.
				updateDict: The update dict with the new values for the resource attributes.
			
			Return:
				Always *True*.
		"""
		L.isDebug and L.logDebug(f'Updating CSR. csi: {csr.csi}')
		# send event
		eventManager.csrUpdated(EventData(payload=(csr, updateDict)))
		return True


	#########################################################################

	#
	#	Handle CSEBaseAnnc registration
	#

	def handleCSEBaseAnncRegistration(self, cbA:Resource, originator:str) -> None:
		""" Handle the registration of a <CSEBaseAnnc> resource. 
			
			Args:
				cbA: The <CSEBaseAnnc> resource to be registered.
				originator: The originator of the request that triggered the registration of the <CSEBaseAnnc>.

			Raises:
				CONFLICT: If a <CSEBaseAnnc> with the same lnk already exists.
		"""
		L.isDebug and L.logDebug(f'Registering CSEBaseAnnc. csi: {cbA.csi}')

		# Check whether the same CSEBase has already registered (-> only once)
		if (lnk := cbA.lnk):
			if len(self.storage.searchByFragment({'lnk': lnk})) > 0:
				raise CONFLICT(L.logDebug(f'CSEBaseAnnc with lnk: {lnk} already exists'))

		# Assign a rn
		# TODO get infos from CBAnnc: spID and csi
		# cbA.setResourceName(uniqueRN(f'{cbA.typeShortname}_{getIdFromOriginator(originator)}'))


	#########################################################################

	#
	#	Handle REQ registration
	#

	def handleREQRegistration(self, req:Resource, originator:str) -> bool:
		"""	Handle the registration of a <REQ> resource. 
		
			Args:
				req: The <REQ> resource to be registered.
				originator: The originator of the request that triggered the registration of the <REQ>.
				
			Return:
				Always *True*.
		"""
		L.isDebug and L.logDebug(f'Registering REQ: {req.ri}')
		# Add originator as creator to allow access
		req.setOriginator(originator)
		return True


	#
	#	Handle REQ deregistration
	#

	def handleREQDeRegistration(self, resource:Resource) -> bool:
		"""	Handle the de-registration of a <REQ> resource.
		
			Args:
				resource: The <REQ> resource to be de-registered.
			
			Return:
				Always *True*.
		"""
		L.isDebug and L.logDebug(f'DeRegisterung REQ. ri: {resource.ri}')
		return True


	#########################################################################

	#
	#	Handle CSEBaseregistration
	#

	def handleCSEBaseRegistration(self, cb:Resource, originator:str) -> None:
		""" Handle the registration of a <CSEBase> resource. 
		
			Args:
				cb: The <CSEBase> resource to be registered.
				originator: The originator for the CSEBase registration. This should be the Admin originator.

			Raises:
				CONFLICT: If a <CSEBase> with the same csi already exists, which means that a CSEBase can only be registered once.
		"""
		csi = cb.csi
		L.isDebug and L.logDebug(f'Registering CSEBase. csi: {cb.csi}')
		if self.storage.getOriginator(csi):
			raise CONFLICT(L.logDebug(f'CSEBase with csi: {csi} already exists'))
		
		# For now only store the csi as originator
		self.storage.addOriginator(csi, OriginatorType.CSEID)


	#########################################################################
	##
	##	Resource Expiration
	##

	def startExpirationMonitor(self) -> None:
		""" Start the expiration monitor, which periodically checks for expired resources and deletes them.
		"""
		# Start background monitor to handle expired resources
		if not Configuration.cse_enableResourceExpiration:
			L.isDebug and L.logDebug('Expiration disabled. NOT starting expiration monitor')
			return

		L.isDebug and L.logDebug('Starting expiration monitor')
		if Configuration.cse_checkExpirationsInterval > 0:
			self.expWorker = BackgroundWorkerPool.newWorker(Configuration.cse_checkExpirationsInterval, self.expirationDBMonitor, 'expirationMonitor', runOnTime=False).start()


	def stopExpirationMonitor(self) -> None:
		""" Stop the expiration monitor.
		"""
		# Stop the expiration monitor
		L.isDebug and L.logDebug('Stopping expiration monitor')
		if self.expWorker:
			self.expWorker.stop()


	def restartExpirationMonitor(self) -> None:
		""" Restart the expiration monitor, for example after a CSE restart.
		"""
		# Stop the expiration monitor
		L.isDebug and L.logDebug('Restart expiration monitor')
		if self.expWorker:
			self.expWorker.restart(Configuration.cse_checkExpirationsInterval)


	def expirationDBMonitor(self) -> bool:
		""" Check the database for expired resources and delete them. This is called periodically by the expiration monitor.
		
			Return:
				Always *True*.
		"""
		# L.isDebug and L.logDebug('Looking for expired resources')
		now = getResourceDate()
		resources = self.storage.searchByFilter(lambda r: (et := r.get('et'))  and et < now)
		for resource in resources:
			# try to retrieve the resource first bc it might have been deleted as a child resource
			# of an expired resource
			if not self.storage.hasResource(ri=resource.ri):
				continue
			L.isDebug and L.logDebug(f'Expiring resource (and child resouces): {resource.ri}')
			self.dispatcher.deleteLocalResource(resource, withDeregistration=True)	# ignore result
			eventManager.expireResource(EventData(payload=resource))
				
		return True


	#########################################################################

	#########################################################################

	def registerSOriginator(self, ae: Resource, originator: str) -> str:
		"""	Register the S-Originator for an AE resource.

			Args:
				ae: The <AE> resource.
				originator: The original originator.
			Return:
				The assigned S-Originator.
		"""
		return uniqueAEI('S')


	def deregisterSOriginator(self, ae: Resource) -> None:
		"""	Deregister the S-Originator for an <AE> resource.

			Args:
				ae: The <AE> resource.
		"""
		# In case an \<AE> resource hosted on a MN-CSE or ASN-CSE with AE-ID-Stem starting with "S" is
		# requested to be deleted, the \<AEAnnc> resource that was created on the IN-CSE during the 
		# initial registration of the associated Application Entity shall be updated with the value 
		# "INACTIVE" for the link attribute and the value INACTIVE for the *registrationStatus* attribute,
		# that the associated Application Entity is currently not registered. After this update of the 
		# \<AEAnnc> resource is completed, the procedure for AE Deregistration 
		# shall follow the procedure described in this clause.
		pass