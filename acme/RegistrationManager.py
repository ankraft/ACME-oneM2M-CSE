#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resources and AE, CSE registrations
#

from copy import deepcopy
from Logging import Logging
from typing import List
from Constants import Constants as C
from Configuration import Configuration
from Types import ResourceTypes as T, Result, Permission, ResponseCode as RC, JSON, CSEType
from resources.Resource import Resource
import CSE, Utils
from resources import ACP
from helpers.BackgroundWorker import BackgroundWorkerPool



class RegistrationManager(object):

	def __init__(self) -> None:
		self.allowedCSROriginators 	= Configuration.get('cse.registration.allowedCSROriginators')
		self.allowedAEOriginators	= Configuration.get('cse.registration.allowedAEOriginators')

		self.startExpirationWorker()
		Logging.log('RegistrationManager initialized')


	def shutdown(self) -> bool:
		self.stopExpirationWorker()
		Logging.log('RegistrationManager shut down')
		return True


	#########################################################################

	#
	#	Handle new resources in general
	#

	def checkResourceCreation(self, resource:Resource, originator:str, parentResource:Resource=None) -> Result:
		if resource.ty == T.AE:
			if (originator := self.handleAERegistration(resource, originator, parentResource).originator) is None:	# assigns new originator
				return Result(rsc=RC.badRequest, dbg='cannot register AE')
		if resource.ty == T.REQ:
			if not self.handleREQRegistration(resource, originator):
				return Result(rsc=RC.badRequest, dbg='cannot register REQ')
		if resource.ty == T.CSR:
			if CSE.cseType == CSEType.ASN:
				return Result(rsc=RC.operationNotAllowed, dbg='cannot register to ASN CSE')
			if not self.handleCSRRegistration(resource, originator):
				return Result(rsc=RC.badRequest, dbg='cannot register CSR')

		# Test and set creator attribute.
		if (res := self.handleCreator(resource, originator)).rsc != RC.OK:
			return res

		return Result(originator=originator) # return (possibly new) originator


	def handleCreator(self, resource:Resource, originator:str) -> Result:
		"""	Check for set creator attribute as well as assign it to allowed resources.
		"""
		if resource.hasAttribute('cr'):
			if resource.ty not in C.creatorAllowed:
				return Result(rsc=RC.badRequest, dbg=f'"creator" attribute is not allowed for resource type: {resource.ty}')
			if resource.cr is not None:		# Check whether cr is set to a value. This is wrong
				Logging.logWarn('Setting "creator" attribute is not allowed.')
				return Result(rsc=RC.badRequest, dbg='setting "creator" attribute is not allowed')
			else:
				resource['cr'] = originator
				# fall-through
		return Result() # implicit OK


	def checkResourceUpdate(self, resource:Resource, updateDict:JSON) -> Result:
		if resource.ty == T.CSR:
			if not self.handleCSRUpdate(resource, updateDict):
				return Result(status=False, dbg='cannot update CSR')
		return Result(status=True)


	def checkResourceDeletion(self, resource:Resource) -> Result:
		if resource.ty == T.AE:
			if not self.handleAEDeRegistration(resource):
				return Result(status=False, dbg='cannot deregister AE')
		if resource.ty == T.REQ:
			if not self.handleREQDeRegistration(resource):
				return Result(status=False, dbg='cannot deregister REQ')
		if resource.ty == T.CSR:
			if not self.handleCSRDeRegistration(resource):
				return Result(status=False, dbg='cannot deregister CSR')
		return Result(status=True)



	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae:Resource, originator:str, parentResource:Resource) -> Result:
		""" This method creates a new originator for the AE registration, depending on the method choosen."""

		# check for empty originator and assign something
		if originator is None or len(originator) == 0:
			originator = 'C'

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not Utils.isAllowedOriginator(originator, self.allowedAEOriginators):
			Logging.logDebug('Originator not allowed')
			return Result(rsc=RC.appRuleValidationFailed)

		# Assign originator for the AE
		if originator == 'C':
			originator = Utils.uniqueAEI('C')
		elif originator == 'S':
			originator = Utils.uniqueAEI('S')
		elif originator is not None:
			originator = Utils.getIdFromOriginator(originator)
		# elif originator is None or len(originator) == 0:
		# 	originator = Utils.uniqueAEI('S')
		Logging.logDebug(f'Registering AE. aei: {originator}')

		ae['aei'] = originator					# set the aei to the originator
		ae['ri'] = Utils.getIdFromOriginator(originator, idOnly=True)		# set the ri of the ae to the aei (TS-0001, 10.2.2.2)

		# Verify that parent is the CSEBase, else this is an error
		if parentResource is None or parentResource.ty != T.CSEBase:
			return Result(rsc=RC.notAcceptable)

		return Result(originator=originator)


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, resource: Resource) -> bool:
		# More De-registration functions happen in the AE's deactivate() method
		Logging.logDebug(f'DeRegisterung AE. aei: {resource.aei}')
		return True



	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr:Resource, originator:str) -> bool:
		Logging.logDebug(f'Registering CSR. csi: {csr.csi}')
		# send event
		CSE.event.remoteCSEHasRegistered(csr)	# type: ignore
		return True


	#
	#	Handle CSR deregistration
	#

	def handleCSRDeRegistration(self, csr:Resource) ->  bool:
		Logging.logDebug(f'DeRegistering CSR. csi: {csr.csi}')
		# send event
		CSE.event.remoteCSEHasDeregistered(csr)	# type: ignore
		return True


	#
	#	Handle CSR Update
	#

	def handleCSRUpdate(self, csr:Resource, updateDict:JSON) -> bool:
		Logging.logDebug(f'Updating CSR. csi: {csr.csi}')
		# send event
		CSE.event.remoteCSEUpdate(csr, updateDict)	# type: ignore
		return True



	#########################################################################

	#
	#	Handle REQ registration
	#

	def handleREQRegistration(self, req:Resource, originator:str) -> bool:
		Logging.logDebug(f'Registering REQ: {req.ri}')
		# Add originator as creator to allow access
		req[req._originator] = originator
		return True


	#
	#	Handle REQ deregistration
	#

	def handleREQDeRegistration(self, resource: Resource) -> bool:
		Logging.logDebug(f'DeRegisterung REQ. ri: {resource.ri}')
		return True


	#########################################################################
	##
	##	Resource Expiration
	##

	def startExpirationWorker(self) -> None:
		# Start background worker to handle expired resources
		Logging.log('Starting expiration worker')
		if (interval := Configuration.get('cse.checkExpirationsInterval')) > 0:
			BackgroundWorkerPool.newWorker(interval, self.expirationDBWorker, 'expirationWorker', startWithDelay=True).start()


	def stopExpirationWorker(self) -> None:
		# Stop the expiration worker
		Logging.log('Stopping expiration worker')
		BackgroundWorkerPool.stopWorkers('expirationWorker')


	def expirationDBWorker(self) -> bool:
		Logging.logDebug('Looking for expired resources')
		now = Utils.getResourceDate()
		resources = CSE.storage.searchByFilter(lambda r: 'et' in r and (et := r['et']) is not None and et < now)
		for resource in resources:
			# try to retrieve the resource first bc it might have been deleted as a child resource
			# of an expired resource
			if not CSE.storage.hasResource(ri=resource.ri):
				continue
			Logging.logDebug(f'Expiring resource (and child resouces): {resource.ri}')
			CSE.dispatcher.deleteResource(resource, withDeregistration=True)	# ignore result
			CSE.event.expireResource(resource) # type: ignore
				
		return True




	#########################################################################


	def _createACP(self, parentResource:Resource=None, rn:str=None, createdByResource:str=None, originators:List[str]=None, permission:int=None, selfOriginators:List[str]=None, selfPermission:int=None) -> Result:
		""" Create an ACP with some given defaults. """
		if parentResource is None or rn is None or originators is None or permission is None:
			return Result(rsc=RC.badRequest, dbg='missing attribute(s)')

		# Remove existing ACP with that name first
		acpSrn = f'{CSE.cseRn}/{rn}'
		if (acpRes := CSE.dispatcher.retrieveResource(id=acpSrn)).rsc == RC.OK:
			CSE.dispatcher.deleteResource(acpRes.resource)	# ignore errors

		# Create the ACP
		selfPermission = selfPermission if selfPermission is not None else Configuration.get('cse.acp.pvs.acop')

		origs = deepcopy(originators)
		origs.append(CSE.cseOriginator)	# always append cse originator

		selfOrigs = [ CSE.cseOriginator ]
		if selfOriginators is not None:
			selfOrigs.extend(selfOriginators)


		acp = ACP.ACP(pi=parentResource.ri, rn=rn, createdInternally=createdByResource)
		acp.addPermission(origs, permission)
		acp.addSelfPermission(selfOrigs, selfPermission)

		if (res := self.checkResourceCreation(acp, CSE.cseOriginator, parentResource)).rsc != RC.OK:
			return res.errorResult()
		return CSE.dispatcher.createResource(acp, parentResource=parentResource, originator=CSE.cseOriginator)


	def _removeACP(self, srn:str, resource:Resource) -> Result:
		""" Remove an ACP created during registration before. """
		if (acpRes := CSE.dispatcher.retrieveResource(id=srn)).rsc != RC.OK:
			Logging.logWarn(f'Could not find ACP: {srn}')	# ACP not found, either not created or already deleted
		else:
			# only delete the ACP when it was created in the course of AE registration internally
			if  (ri := acpRes.resource.createdInternally()) is not None and resource.ri == ri:
				return CSE.dispatcher.deleteResource(acpRes.resource)
		return Result(rsc=RC.deleted)

