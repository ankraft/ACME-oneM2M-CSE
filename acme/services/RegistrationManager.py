#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resources and AE, CSE registrations
#

from copy import deepcopy
from typing import List, cast, Any

from ..etc.Types import Permission, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON, CSEType
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..services import CSE as CSE
from ..resources.Resource import Resource
from ..resources.ACP import ACP
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool



class RegistrationManager(object):

	def __init__(self) -> None:
		self._getConfig()

		# Start expiration Monitor
		self.expWorker:BackgroundWorker	= None
		self.startExpirationMonitor()
		
		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)			# type: ignore

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		L.isInfo and L.log('RegistrationManager initialized')


	def shutdown(self) -> bool:
		self.stopExpirationMonitor()
		L.isInfo and L.log('RegistrationManager shut down')
		return True

	def _getConfig(self) -> None:
		self.allowedCSROriginators 		= Configuration.get('cse.registration.allowedCSROriginators')
		self.allowedAEOriginators		= Configuration.get('cse.registration.allowedAEOriginators')
		self.checkExpirationsInterval	= Configuration.get('cse.checkExpirationsInterval')


	def configUpdate(self, key:str = None, value:Any = None) -> None:
		"""	Handle configuration updates.
		"""
		if key not in [ 'cse.checkExpirationsInterval']:
			return
		self.checkExpirationsInterval = value
		self.restartExpirationMonitor()


	def restart(self) -> None:
		"""	Restart the registration services.
		"""
		self._getConfig()
		self.restartExpirationMonitor()
		L.isDebug and L.logDebug('RegistrationManager restarted')



	#########################################################################

	#
	#	Handle new resources in general
	#

	def checkResourceCreation(self, resource:Resource, originator:str, parentResource:Resource = None) -> Result:
		# Some Resources are not allowed to be created in a request, return immediately
		ty = resource.ty

		if ty == T.AE:
			if not (res := self.handleAERegistration(resource, originator, parentResource)).status:
				return res
			originator = cast(str, res.data)	# assigns new originator
		if ty == T.REQ:
			if not self.handleREQRegistration(resource, originator):
				return Result.errorResult(dbg = 'cannot register REQ')
		if ty == T.CSR:
			if CSE.cseType == CSEType.ASN:
				return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'cannot register to ASN CSE')
			if not (res := self.handleCSRRegistration(resource, originator)).status:
				res.dbg = f'cannot register CSR: {res.dbg}'
				return res
		if ty == T.CSEBaseAnnc:
			if not (res := self.handleCSEBaseAnncRegistration(resource, originator)).status:
				res.dbg = f'cannot register CSEBaseAnnc: {res.dbg}'
				return res

		# Test and set creator attribute.
		if not (res := self.handleCreator(resource, originator)).status:
			return res

		return Result(status = True, data = originator) # return (possibly new) originator


	def handleCreator(self, resource:Resource, originator:str) -> Result:
		"""	Check for set creator attribute as well as assign it to allowed resources.
		"""
		if resource.hasAttribute('cr'):	# not get, might be empty
			if not T.isCreatorAllowed(resource.ty):
				return Result.errorResult(dbg = f'"creator" attribute is not allowed for resource type: {resource.ty}')
			if resource.cr:		# Check whether cr is set to a value in the request. This is wrong
				L.isWarn and L.logWarn('Setting "creator" attribute is not allowed.')
				return Result.errorResult(dbg = 'setting "creator" attribute is not allowed')
			else:
				resource['cr'] = originator
				# fall-through
		return Result.successResult() # implicit OK


	def checkResourceUpdate(self, resource:Resource, updateDict:JSON) -> Result:
		if resource.ty == T.CSR:
			if not self.handleCSRUpdate(resource, updateDict):
				return Result.errorResult(dbg = 'cannot update CSR')
		return Result.successResult()


	def checkResourceDeletion(self, resource:Resource) -> Result:
		ty = resource.ty
		if ty == T.AE:
			if not self.handleAEDeRegistration(resource):
				return Result.errorResult(dbg = 'cannot deregister AE')
		if ty == T.REQ:
			if not self.handleREQDeRegistration(resource):
				return Result.errorResult(dbg = 'cannot deregister REQ')
		if ty == T.CSR:
			if not self.handleCSRDeRegistration(resource):
				return Result.errorResult(dbg = 'cannot deregister CSR')
		return Result.successResult()



	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae:Resource, originator:str, parentResource:Resource) -> Result:
		""" This method creates a new originator for the AE registration, depending on the method choosen."""

		# check for empty originator and assign something
		if not originator:
			originator = 'C'

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not CSE.security.isAllowedOriginator(originator, self.allowedAEOriginators):
			L.logDebug(dbg := 'Originator not allowed')
			return Result.errorResult(rsc = RC.appRuleValidationFailed, dbg = dbg)

		# Assign originator for the AE
		if originator == 'C':
			originator = Utils.uniqueAEI('C')
		elif originator == 'S':
			originator = Utils.uniqueAEI('S')
		elif originator is not None:	# Allow empty originators
			originator = Utils.getIdFromOriginator(originator)
		# elif originator is None or len(originator) == 0:
		# 	originator = Utils.uniqueAEI('S')

		# Check whether an originator has already registered with the same AE-ID
		if Utils.hasRegisteredAE(originator):
			L.logWarn(dbg := f'Originator has already registered: {originator}')
			return Result.errorResult(rsc = RC.originatorHasAlreadyRegistered, dbg = dbg)
		
		# Make some adjustments to set the originator in the <AE> resource
		L.isDebug and L.logDebug(f'Registering AE. aei: {originator}')
		ae['aei'] = originator												# set the aei to the originator
		ae['ri'] = Utils.getIdFromOriginator(originator, idOnly=True)		# set the ri of the ae to the aei (TS-0001, 10.2.2.2)

		# Verify that parent is the CSEBase, else this is an error
		if not parentResource or parentResource.ty != T.CSEBase:
			return Result.errorResult(rsc = RC.invalidChildResourceType, dbg = 'Parent must be the CSE')

		return Result(status = True, data = originator)


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, resource: Resource) -> bool:
		# More De-registration functions happen in the AE's deactivate() method
		L.isDebug and L.logDebug(f'DeRegistering AE. aei: {resource.aei}')
		return True



	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr:Resource, originator:str) -> Result:
		L.isDebug and L.logDebug(f'Registering CSR. csi: {csr.csi}')

		# Check whether an AE with the same originator has already registered

		if originator != CSE.cseOriginator and Utils.hasRegisteredAE(originator):
			L.logWarn(dbg := f'Originator has already registered an AE: {originator}')
			return Result.errorResult(rsc = RC.operationNotAllowed, dbg = dbg)
		
		# Always replace csi with the originator (according to TS-0004, 7.4.4.2.1)
		if not CSE.importer.isImporting:	# ... except when the resource was just been imported
			csr['csi'] = originator
			csr['ri']  = Utils.getIdFromOriginator(originator)

		# Validate csi in csr
		if not (res := CSE.validator.validateCSICB(csr.csi, 'csi')).status:
			return res
		# Validate cb in csr
		if not (res := CSE.validator.validateCSICB(csr.cb, 'cb')).status:
			return res

		# send event
		CSE.event.remoteCSEHasRegistered(csr)	# type: ignore
		return Result.successResult()


	#
	#	Handle CSR deregistration
	#

	def handleCSRDeRegistration(self, csr:Resource) ->  bool:
		L.isDebug and L.logDebug(f'DeRegistering CSR. csi: {csr.csi}')
		# send event
		CSE.event.remoteCSEHasDeregistered(csr)	# type: ignore
		return True


	#
	#	Handle CSR Update
	#

	def handleCSRUpdate(self, csr:Resource, updateDict:JSON) -> bool:
		L.isDebug and L.logDebug(f'Updating CSR. csi: {csr.csi}')
		# send event
		CSE.event.remoteCSEUpdate(csr, updateDict)	# type: ignore
		return True


	#########################################################################

	#
	#	Handle CSEBaseAnnc registration
	#

	def handleCSEBaseAnncRegistration(self, cbA:Resource, originator:str) -> Result:
		L.isDebug and L.logDebug(f'Registering CSEBaseAnnc. csi: {cbA.csi}')

		# Check whether the same CSEBase has already registered (-> only once)
		if (lnk := cbA.lnk):
			if len(list := CSE.storage.searchByFragment({'lnk': lnk})) > 0:
				L.logDebug(dbg := f'CSEBaseAnnc with lnk: {lnk} already exists')
				return Result.errorResult(rsc = RC.conflict, dbg = dbg)

		# Assign a rn
		cbA.setResourceName(Utils.uniqueRN(f'{cbA.tpe}_{Utils.getIdFromOriginator(originator)}'))
		return Result.successResult()


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
		now = DateUtils.getResourceDate()
		resources = CSE.storage.searchByFilter(lambda r: (et := r.get('et'))  and et < now)
		for resource in resources:
			# try to retrieve the resource first bc it might have been deleted as a child resource
			# of an expired resource
			if not CSE.storage.hasResource(ri=resource.ri):
				continue
			L.isDebug and L.logDebug(f'Expiring resource (and child resouces): {resource.ri}')
			CSE.dispatcher.deleteResource(resource, withDeregistration = True)	# ignore result
			CSE.event.expireResource(resource) # type: ignore
				
		return True



	#########################################################################


	def _createACP(self, parentResource:Resource = None, rn:str = None, createdByResource:str = None, originators:List[str] = None, permission:Permission = None, selfOriginators:List[str] = None, selfPermission:Permission = None) -> Result:
		""" Create an ACP with some given defaults. """
		if not parentResource or not rn or not originators or permission is None:	# permission is an int
			return Result.errorResult(dbg = 'missing attribute(s)')

		# Remove existing ACP with that name first
		acpSrn = f'{CSE.cseRn}/{rn}'
		if (acpRes := CSE.dispatcher.retrieveResource(id = acpSrn)).rsc == RC.OK:
			CSE.dispatcher.deleteResource(acpRes.resource)	# ignore errors

		# Create the ACP
		selfPermission = selfPermission if selfPermission is not None else Permission(Configuration.get('cse.acp.pvs.acop'))

		origs = deepcopy(originators)
		origs.append(CSE.cseOriginator)	# always append cse originator

		selfOrigs = [ CSE.cseOriginator ]
		if selfOriginators:
			selfOrigs.extend(selfOriginators)

		acp = ACP({}, pi = parentResource.ri, rn = rn)
		acp.setCreatedInternally(createdByResource)
		acp.addPermission(origs, permission)
		acp.addSelfPermission(selfOrigs, selfPermission)

		if not (res := self.checkResourceCreation(acp, CSE.cseOriginator, parentResource)).status:
			# return res.errorResultCopy()
			return res
		return CSE.dispatcher.createResource(acp, parentResource = parentResource, originator = CSE.cseOriginator)


	def _removeACP(self, srn:str, resource:Resource) -> Result:
		""" Remove an ACP created during registration before. """
		if not (acpRes := CSE.dispatcher.retrieveResource(id=srn)).resource:
			L.isWarn and L.logWarn(f'Could not find ACP: {srn}')	# ACP not found, either not created or already deleted
		else:
			# only delete the ACP when it was created in the course of AE registration internally
			if  (createdWithRi := acpRes.resource.createdInternally()) and resource.ri == createdWithRi:
				return CSE.dispatcher.deleteResource(acpRes.resource)
		return Result(status = True, rsc = RC.deleted)

