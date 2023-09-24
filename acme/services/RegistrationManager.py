#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resources and AE, CSE registrations
#

from __future__ import annotations
from typing import List, cast, Any, Optional

from copy import deepcopy

from ..etc.Types import Permission, ResourceTypes, JSON, CSEType
from ..etc.ResponseStatusCodes import APP_RULE_VALIDATION_FAILED, ORIGINATOR_HAS_ALREADY_REGISTERED, INVALID_CHILD_RESOURCE_TYPE
from ..etc.ResponseStatusCodes import BAD_REQUEST, OPERATION_NOT_ALLOWED, CONFLICT, ResponseException
from ..etc.Utils import uniqueAEI, getIdFromOriginator, uniqueRN
from ..etc.DateUtils import getResourceDate, utcTimeObject
from ..etc.Constants import Constants
from ..services.Configuration import Configuration
from ..services import CSE
from ..resources.Resource import Resource
from ..resources.ACP import ACP
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..services.Logging import Logging as L


class RegistrationManager(object):

	__slots__ = (
		'expWorker',

		'allowedCSROriginators',
		'allowedAEOriginators',
		'checkExpirationsInterval',
		'enableResourceExpiration',
		'acpPvsAcop',

		'_eventRegistreeCSEHasRegistered',
		'_eventRegistreeCSEHasDeregistered',
		'_eventAEHasRegistered',
		'_eventAEHasDeregistered',
		'_eventRegistreeCSEUpdate',
		'_eventExpireResource',
	)

	def __init__(self) -> None:

		# Get the configuration settings
		self._assignConfig()

		# Start expiration Monitor
		self.expWorker:BackgroundWorker	= None
		self.startExpirationMonitor()
		
		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)			# type: ignore

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		# Optimized event handling
		self._eventRegistreeCSEHasRegistered = CSE.event.registreeCSEHasRegistered			# type: ignore
		self._eventRegistreeCSEHasDeregistered = CSE.event.registreeCSEHasDeregistered		# type: ignore
		self._eventAEHasRegistered = CSE.event.aeHasRegistered								# type: ignore
		self._eventAEHasDeregistered = CSE.event.aeHasDeregistered							# type: ignore
		self._eventRegistreeCSEUpdate = CSE.event.registreeCSEUpdate						# type: ignore
		self._eventExpireResource = CSE.event.expireResource								# type: ignore

		L.isInfo and L.log('RegistrationManager initialized')


	def shutdown(self) -> bool:
		self.stopExpirationMonitor()
		L.isInfo and L.log('RegistrationManager shut down')
		return True


	def _assignConfig(self) -> None:
		self.allowedCSROriginators 		= Configuration.get('cse.registration.allowedCSROriginators')
		self.allowedAEOriginators		= Configuration.get('cse.registration.allowedAEOriginators')
		self.checkExpirationsInterval	= Configuration.get('cse.checkExpirationsInterval')
		self.enableResourceExpiration 	= Configuration.get('cse.enableResourceExpiration')
		self.acpPvsAcop					= Configuration.get('resource.acp.selfPermission')

	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Any = None) -> None:
		"""	Handle configuration updates.
		"""
		if key not in [ 'cse.checkExpirationsInterval', 
						'cse.registration.allowedCSROriginators',
						'cse.registration.allowedAEOriginators',
						'cse.enableResourceExpiration',
						'resource.acp.selfPermission']:
			return
		self._assignConfig()
		self.restartExpirationMonitor()


	def restart(self, name:str) -> None:
		"""	Restart the registration services.
		"""
		self._assignConfig()
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
		ty = resource.ty

		if ty == ResourceTypes.AE:
			originator = self.handleAERegistration(resource, originator, parentResource)

		elif ty == ResourceTypes.REQ:
			if not self.handleREQRegistration(resource, originator):
				raise BAD_REQUEST('cannot register REQ')

		elif ty == ResourceTypes.CSR:
			if CSE.cseType == CSEType.ASN:
				raise OPERATION_NOT_ALLOWED('cannot register to ASN CSE')
			try:
				self.handleCSRRegistration(resource, originator)
			except ResponseException as e:
				e.dbg = f'cannot register CSR: {e.dbg}'
				raise e

		elif ty == ResourceTypes.CSEBaseAnnc:
			try:
				self.handleCSEBaseAnncRegistration(resource, originator)
			except ResponseException as e:
				e.dbg = f'cannot register CSEBaseAnnc: {e.dbg}'
				raise e
		# fall-through

		# Test and set creator attribute.
		self.handleCreator(resource, originator)

		# return (possibly new) originator
		return originator	


	def postResourceCreation(self, resource:Resource) -> None:
		"""	Handle some post-create aspects, for example send events for some resources.

			Args:
				resource: Resource that was created.
		"""
		ty = resource.ty
		if ty == ResourceTypes.AE:
			# Send event
			self._eventAEHasRegistered(resource)
		elif ty == ResourceTypes.CSR:
			# send event
			self._eventRegistreeCSEHasRegistered(resource)


	def handleCreator(self, resource:Resource, originator:str) -> None:
		"""	Check for set creator attribute as well as assign it to allowed resources.
		"""
		if resource.hasAttribute('cr'):	# not get, might be empty
			if not resource.hasAttributeDefined('cr'):
				raise BAD_REQUEST(f'"creator" attribute is not allowed for resource type: {resource.ty}')
			if resource.cr is not None:		# Check whether cr is set to a value in the request. This is wrong
				raise BAD_REQUEST(L.logWarn('setting the "creator" attribute is not allowed.'))
			resource.setAttribute('cr', originator)
		# fall-through


	def checkResourceUpdate(self, resource:Resource, updateDict:JSON) -> None:
		if resource.ty == ResourceTypes.CSR:
			if not self.handleCSRUpdate(resource, updateDict):
				raise BAD_REQUEST('cannot update CSR')
		# fall-through


	def checkResourceDeletion(self, resource:Resource) -> None:
		ty = resource.ty
		if ty == ResourceTypes.AE:
			if not self.handleAEDeRegistration(resource):
				raise BAD_REQUEST('cannot deregister AE')

		elif ty == ResourceTypes.REQ:
			if not self.handleREQDeRegistration(resource):
				raise BAD_REQUEST('cannot deregister REQ')

		elif ty == ResourceTypes.CSR:
			if not self.handleRegistreeCSRDeRegistration(resource):
				raise BAD_REQUEST('cannot deregister CSR')
		# fall-through


	def postResourceDeletion(self, resource:Resource) -> None:
		"""	Handle some post-delete aspects, for example send events for some resources.

			Args:
				resource: Resource that was created.
		"""
		ty = resource.ty
		if ty == ResourceTypes.AE:
			# Send event
			self._eventAEHasDeregistered(resource)
		elif ty == ResourceTypes.CSR:
			# send event
			self._eventRegistreeCSEHasDeregistered(resource)


	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae:Resource, originator:str, parentResource:Resource) -> str:
		""" This method creates a new originator for the AE registration, depending on the method choosen."""

		L.isDebug and L.logDebug(f'handle AE registration for: {ae.ri} with originator: {originator}')

		# check for empty originator and assign something
		if not originator:
			originator = 'C'

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not CSE.security.isAllowedOriginator(originator, self.allowedAEOriginators):
			raise APP_RULE_VALIDATION_FAILED(L.logDebug('Originator not allowed'))

		# Assign originator for the AE
		if originator == 'C':
			originator = uniqueAEI('C')
		elif originator == 'S':
			originator = uniqueAEI('S')
		elif originator is not None:	# Allow empty originators
			originator = getIdFromOriginator(originator)
		# elif originator is None or len(originator) == 0:
		# 	originator = uniqueAEI('S')

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

		return originator


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, ae:Resource) -> bool:
		# More De-registration functions happen in the AE's deactivate() method
		L.isDebug and L.logDebug(f'DeRegistering AE. aei: {ae.aei}')

		# Send event
		self._eventAEHasDeregistered(ae)

		return True


	def hasRegisteredAE(self, originator:str) -> bool:
		"""	Check wether an AE with *originator* is registered at the CSE.

			Args:
				originator: ID of the originator / AE.
			Return
				True if the originator is registered with the CSE.
		"""
		return len(CSE.storage.searchByFragment({'aei' : originator})) > 0

	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr:Resource, originator:str) -> None:
		L.isDebug and L.logDebug(f'Registering CSR. csi: {csr.csi}')

		# Check whether an AE with the same originator has already registered

		if originator != CSE.cseOriginator and self.hasRegisteredAE(originator):
			raise OPERATION_NOT_ALLOWED(L.logWarn(f'Originator has already registered an AE: {originator}'))
		
		# Always replace csi with the originator (according to TS-0004, 7.4.4.2.1)
		if not CSE.importer.isImporting:	# ... except when the resource was just been imported
			csr['csi'] = originator
			csr['ri']  = getIdFromOriginator(originator)

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
		self._eventRegistreeCSEHasDeregistered(registreeCSR)
		return True


	#
	#	Handle CSR Update
	#

	def handleCSRUpdate(self, csr:Resource, updateDict:JSON) -> bool:
		L.isDebug and L.logDebug(f'Updating CSR. csi: {csr.csi}')
		# send event
		self._eventRegistreeCSEUpdate(csr, updateDict)
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
		cbA.setResourceName(uniqueRN(f'{cbA.tpe}_{getIdFromOriginator(originator)}'))


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
	##
	##	Resource Expiration
	##

	def startExpirationMonitor(self) -> None:
		# Start background monitor to handle expired resources
		if not self.enableResourceExpiration:
			L.isDebug and L.logDebug('Expiration disabled. NOT starting expiration monitor')
			return

		L.isDebug and L.logDebug('Starting expiration monitor')
		if self.checkExpirationsInterval > 0:
			self.expWorker = BackgroundWorkerPool.newWorker(self.checkExpirationsInterval, self.expirationDBMonitor, 'expirationMonitor', runOnTime=False).start()


	def stopExpirationMonitor(self) -> None:
		# Stop the expiration monitor
		L.isDebug and L.logDebug('Stopping expiration monitor')
		if self.expWorker:
			self.expWorker.stop()


	def restartExpirationMonitor(self) -> None:
		# Stop the expiration monitor
		L.isDebug and L.logDebug('Restart expiration monitor')
		if self.expWorker:
			self.expWorker.restart(self.checkExpirationsInterval)


	def expirationDBMonitor(self) -> bool:
		# L.isDebug and L.logDebug('Looking for expired resources')

		if CSE.storage.isMongoDB():
			now = utcTimeObject()
			resources = CSE.storage.retrieveResourcesByLessDate(Constants.attrExpireTime, now)
		else:
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

	# TODO remove after 0.13.0 . Check whether the acp.functions are still needed !!!
	

	# def _createACP(self, parentResource:Optional[Resource] = None, 
	# 					 rn:Optional[str] = None, 
	# 					 createdByResource:Optional[str] = None, 
	# 					 originators:Optional[List[str]] = None, 
	# 					 permission:Optional[Permission] = None, 
	# 					 selfOriginators:Optional[List[str]] = None, 
	# 					 selfPermission:Optional[Permission] = None) -> Resource:
	# 	""" Create an ACP with some given defaults. """
	# 	if not parentResource or not rn or not originators or permission is None:	# permission is an int
	# 		raise BAD_REQUEST('missing attribute(s)')

	# 	# Remove existing ACP with that name first
	# 	try:
	# 		acpSrn = f'{CSE.cseRn}/{rn}'
	# 		acpResourse = CSE.dispatcher.retrieveResource(id = acpSrn)	# May throw an exception if no resource exists
	# 		CSE.dispatcher.deleteLocalResource(acpResourse)	# ignore errors
	# 	except:
	# 		pass

	# 	# Create the ACP
	# 	selfPermission = selfPermission if selfPermission is not None else Permission(self.acpPvsAcop)

	# 	origs = deepcopy(originators)
	# 	origs.append(CSE.cseOriginator)	# always append cse originator

	# 	selfOrigs = [ CSE.cseOriginator ]
	# 	if selfOriginators:
	# 		selfOrigs.extend(selfOriginators)

	# 	acpResourse = ACP({}, pi = parentResource.ri, rn = rn)
	# 	acpResourse.setCreatedInternally(createdByResource)
	# 	acpResourse.addPermission(origs, permission)
	# 	acpResourse.addSelfPermission(selfOrigs, selfPermission)

	# 	self.checkResourceCreation(acpResourse, CSE.cseOriginator, parentResource)
	# 	return CSE.dispatcher.createLocalResource(acpResourse, parentResource, originator = CSE.cseOriginator)


	# def _removeACP(self, srn:str, resource:Resource) -> None:
	# 	""" Remove an ACP created during registration before. """

	# 	try:
	# 		acpResourse = CSE.dispatcher.retrieveResource(id = srn)
	# 	except ResponseException as e:
	# 		L.isWarn and L.logWarn(f'Could not find ACP: {srn}: {e.dbg}')	# ACP not found, either not created or already deleted
	# 		return
	# 	# only delete the ACP when it was created in the course of AE registration internally
	# 	if  (createdWithRi := acpResourse.createdInternally()) and resource.ri == createdWithRi:
	# 		CSE.dispatcher.deleteLocalResource(acpResourse)

