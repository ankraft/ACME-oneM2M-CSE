#
#	Dispatcher.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Most internal requests are routed through here.
#

from __future__ import annotations
from typing import List, Tuple, cast, Sequence, Optional

import operator
import sys
from copy import deepcopy

from ..helpers import TextTools
from ..etc.Constants import Constants
from ..etc.Types import FilterCriteria, FilterUsage, CSERequest, ResourceTypes, Operation
from ..etc.Types import FilterOperation, DesiredIdentifierResultType, Permission, ResultContentType
from ..etc.Types import Result, JSON
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException, exceptionFromRSC
from ..etc.ResponseStatusCodes import ORIGINATOR_HAS_NO_PRIVILEGE, NOT_FOUND, BAD_REQUEST
from ..etc.ResponseStatusCodes import REQUEST_TIMEOUT, OPERATION_NOT_ALLOWED, TARGET_NOT_SUBSCRIBABLE, INVALID_CHILD_RESOURCE_TYPE
from ..etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR, SECURITY_ASSOCIATION_REQUIRED, CONFLICT
from ..etc.Utils import localResourceID, isSPRelative, isStructured, resourceModifiedAttributes, filterAttributes, riFromID
from ..etc.Utils import srnFromHybrid, uniqueRI, noNamespace, riFromStructuredPath, csiFromSPRelative, toSPRelative, structuredPathFromRI
from ..helpers.TextTools import findXPath
from ..etc.DateUtils import waitFor, timeUntilTimestamp, timeUntilAbsRelTimestamp, getResourceDate
from ..services import CSE
from ..services.Configuration import Configuration
from ..resources.Factory import resourceFromDict
from ..resources.Resource import Resource
from ..resources.PCH_PCU import PCH_PCU
from ..resources.SMD import SMD
from ..services.Logging import Logging as L


# TODO NOTIFY optimize local resource notifications
# TODO handle config update
class Dispatcher(object):

	__slots__ = (
		'csiSlashLen',
		'sortDiscoveryResources',

		'_eventCreateResource',
		'_eventCreateChildResource',
		'_eventUpdateResource',
		'_eventDeleteResource',
	)

	def __init__(self) -> None:
		self.csiSlashLen 				= len(CSE.cseCsiSlash)
		self.sortDiscoveryResources 	= Configuration.get('cse.sortDiscoveredResources')

		self._eventCreateResource = CSE.event.createResource			# type: ignore [attr-defined]
		self._eventCreateChildResource = CSE.event.createChildResource	# type: ignore [attr-defined]
		self._eventUpdateResource = CSE.event.updateResource			# type: ignore [attr-defined]
		self._eventDeleteResource = CSE.event.deleteResource			# type: ignore [attr-defined]

		L.isInfo and L.log('Dispatcher initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Dispatcher servide.
			
			Return:
				Boolean indicating the success.
		"""
		L.isInfo and L.log('Dispatcher shut down')
		return True



	# The "xxxRequest" methods handle http requests while the "xxxResource"
	# methods handle actions on the resources. Security/permission checking
	# is done for requests, not on resource actions.


	#########################################################################

	#
	#	Retrieve resources
	#

	def processRetrieveRequest(self, request:CSERequest, 
									 originator:str, 
									 id:Optional[str] = None) -> Result:
		"""	Process a RETRIEVE request. Retrieve and discover resource(s).

			Args:
				request: The incoming request.
				originator: The requests originator.
				id: Optional ID of the request.
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug(f'Process RETRIEVE request for id: {request.id}|{request.srn}')

		# handle transit requests first
		if localResourceID(request.id) is None and localResourceID(request.srn) is None:
			return CSE.request.handleTransitRetrieveRequest(request)

		srn, id = self._checkHybridID(request, id) # overwrite id if another is given


		# Check attributeList in Content
		attributeList:JSON = None
		if request.pc is not None:
			L.isDebug and L.logDebug(f'Found Content for RETRIEVE: {request.pc}')
			if (attributeList := request.pc.get('m2m:atrl')) is None:
				raise BAD_REQUEST(L.logWarn(f'Only "m2m:atrl" is allowed in Content for RETRIEVE.'))
			CSE.validator.validateAttribute('atrl', attributeList)
		
		# Handle operation execution time and check request expiration
		self._handleOperationExecutionTime(request)
		self._checkRequestExpiration(request)

		# handle fanout point requests
		if (fanoutPointResource := self._getFanoutPointResource(srn)) and fanoutPointResource.ty == ResourceTypes.GRP_FOPT:
			L.isDebug and L.logDebug(f'Redirecting request to fanout point: {fanoutPointResource.getSrn()}')
			return fanoutPointResource.handleRetrieveRequest(request, srn, request.originator)

		# Handle PollingChannelURI RETRIEVE
		if (pollingChannelURIRsrc := self._getPollingChannelURIResource(srn)):		# We need to check the srn here
			if not CSE.security.hasAccessToPollingChannel(originator, pollingChannelURIRsrc):
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has not RETRIEVE privileges to <pollingChannelURI>: {id}'))
			L.isDebug and L.logDebug(f'Redirecting request <PCU>: {pollingChannelURIRsrc.getSrn()}')
			return pollingChannelURIRsrc.handleRetrieveRequest(request, id, originator)


		# EXPERIMENTAL
		# Handle latest and oldest RETRIEVE
		if (laOlResource := self._latestOldestResource(srn)):		# We need to check the srn here
			# Check for virtual resource
			if laOlResource.isVirtual(): 
				
				#TODO checks & tests
				# TODO Add special "getLT" function. necessary for firtual resources!!!!! then used in blocking retrieve check
				laOlResource.willBeRetrieved(originator, request) 


				# TODO directchildren & virtual: only la and ol are monitored.
				# after adding instance: update lt of ol and al resources.

				# add oldestRi and latestRi internal attributes con con, ts, fc


				res = laOlResource.handleRetrieveRequest(request = request, originator = originator)
				if not CSE.security.hasAccess(originator, res.resource, Permission.RETRIEVE):
					raise ORIGINATOR_HAS_NO_PRIVILEGE(f'originator has no permission for {Permission.RETRIEVE}')
				return res

		# The permission also indicates whether this is RETRIEVE or DISCOVERY
		permission = Permission.DISCOVERY if request.fc.fu == FilterUsage.discoveryCriteria else Permission.RETRIEVE

		L.isDebug and L.logDebug(f'Discover/Retrieve resources (rcn: {request.rcn}, fu: {request.fc.fu.name}, drt: {request.drt.name}, fc: {str(request.fc)}, rcn: {request.rcn.name}, attributes: {str(request.fc.attributes)}, sqi: {request.sqi})')

		#
		#	Normal Retrieve
		# 	 Retrieve the target resource, because it is needed for some rcn (and the default)
		#

		rcn = request.rcn
		# Check semantic discovery (sqi present and False)
		if request.sqi is not None and not request.sqi:
			# Get all accessible semanticDescriptors
			_resources = self.discoverResources(id, originator, filterCriteria = FilterCriteria(ty = [ResourceTypes.SMD]))
			L.isDebug and L.logDebug(f'Direct discovered SMD: {_resources}')

			# Execute semantic resource discovery
			_resources = CSE.semantic.executeSemanticDiscoverySPARQLQuery(originator, request.fc.smf, cast(Sequence[SMD], _resources))
			return Result(rsc = ResponseStatusCode.OK, resource = self._resourcesToURIList(_resources, request.drt))

		else:
			if rcn in [ ResultContentType.attributes, 
						ResultContentType.attributesAndChildResources, 
						ResultContentType.childResources, 
						ResultContentType.attributesAndChildResourceReferences, 
						ResultContentType.originalResource ]:
				resource = self.retrieveResource(id, originator, request)

				if not CSE.security.hasAccess(originator, resource, permission):
					raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has no {permission} privileges for resource: {resource.ri}'))

				# if rcn == "attributes" then we can return here, whatever the result is
				if rcn == ResultContentType.attributes:
					resource.willBeRetrieved(originator, request)	# resource instance may be changed in this call
					
					# partial retrieve?
					return self._partialFromResource(resource, attributeList)

				# if rcn == original-resource we retrieve the linked resource
				if rcn == ResultContentType.originalResource:
					# Some checks for resource validity
					if not resource.isAnnounced():
						raise BAD_REQUEST(L.logDebug(f'Resource {resource.ri} is not an announced resource'))
					if not (lnk := resource.lnk):	# no link attribute?
						raise INTERNAL_SERVER_ERROR('internal error: missing lnk attribute in target resource')

					# Retrieve and check the linked-to request
					linkedResource = self.retrieveResource(lnk, originator, request)
					
					# Normally, we would do some checks here and call "willBeRetrieved", 
					# but we don't have to, because the resource is already checked during the
					# retrieveResource call by the hosting CSE

					# partial retrieve?
					return self._partialFromResource(linkedResource, attributeList)
			
			#
			#	Semantic query request
			#	This is indicated by rcn = semantic content
			#
			if rcn == ResultContentType.semanticContent:
				L.isDebug and L.logDebug('Performing semantic discovery / query')
				# Validate SPARQL in semanticFilter
				CSE.semantic.validateSPARQL(request.fc.smf)

				# Get all accessible semanticDescriptors
				resources = self.discoverResources(id, originator, filterCriteria = FilterCriteria(ty = [ResourceTypes.SMD]))
				
				# Execute semantic query
				res = CSE.semantic.executeSPARQLQuery(request.fc.smf, cast(Sequence[SMD], resources))
				L.isDebug and L.logDebug(f'SPARQL query result: {res.data}')
				return Result(rsc = ResponseStatusCode.OK, data = { 'm2m:qres' : res.data })

		#
		#	Discovery request
		#
		resources = self.discoverResources(id, originator, request.fc, permission = permission)

		# check and filter by ACP. After this allowedResources only contains the resources that are allowed
		allowedResources = []
		for r in resources:
			if CSE.security.hasAccess(originator, r, permission):
				try:
					r.willBeRetrieved(originator, request)	# resource instance may be changed in this call
					allowedResources.append(r)
				except:
					continue

		#
		#	Handle more sophisticated RCN
		#

		if rcn == ResultContentType.attributesAndChildResources:
			self.resourceTreeDict(allowedResources, resource)	# the function call add attributes to the target resource
			return Result(rsc = ResponseStatusCode.OK, resource = resource)

		elif rcn == ResultContentType.attributesAndChildResourceReferences:
			self._resourceTreeReferences(allowedResources, resource, request.drt, 'ch')	# the function call add attributes to the target resource
			return Result(rsc = ResponseStatusCode.OK, resource = resource)

		elif rcn == ResultContentType.childResourceReferences: 
			childResourcesRef = self._resourceTreeReferences(allowedResources, None, request.drt, 'm2m:rrl')
			return Result(rsc = ResponseStatusCode.OK, resource = childResourcesRef)

		elif rcn == ResultContentType.childResources:
			childResources:JSON = { resource.tpe : {} } #  Root resource as a dict with no attribute
			self.resourceTreeDict(allowedResources, childResources[resource.tpe]) # Adding just child resources
			return Result(rsc = ResponseStatusCode.OK, resource = childResources)

		elif rcn == ResultContentType.discoveryResultReferences: # URIList
			return Result(rsc = ResponseStatusCode.OK, resource = self._resourcesToURIList(allowedResources, request.drt))

		else:
			raise BAD_REQUEST(f'unsuppored rcn: {rcn} for RETRIEVE')


	def retrieveResource(self, id:str, 
							   originator:Optional[str] = None, 
							   request:Optional[CSERequest] = None, 
							   postRetrieveHook:Optional[bool] = False) -> Resource:
		"""	Retrieve a resource locally or from remote CSE.

			Args:
				id:	If the *id* is in SP-relative format then first check whether this is for the local CSE.
					If yes, then adjust the ID and try to retrieve it.
					If no, then try to retrieve the resource from a connected (!) remote CSE.
				originator:	The originator of the request.
				postRetrieveHook: Only when retrieving localls, invoke the Resource's *willBeRetrieved()* callback.
			Return:
				Result instance.

		"""
		if id:
			if id.startswith(CSE.cseCsiSlash) and len(id) > self.csiSlashLen:		# TODO for all operations?
				id = id[self.csiSlashLen:]
			else:
				# Retrieve from remote
				if isSPRelative(id):
					return CSE.remote.retrieveRemoteResource(id, originator)

		# TODO use Utils.riFromID()

		
		# Retrieve locally
		if isStructured(id):
			resource = self.retrieveLocalResource(srn = id, originator = originator, request = request) 
		else:
			resource = self.retrieveLocalResource(ri = id, originator = originator, request = request)
		if postRetrieveHook:
			resource.willBeRetrieved(originator, request, subCheck = False)
		return resource


	def retrieveLocalResource(self, ri:Optional[str] = None, 
									srn:Optional[str] = None, 
									originator:Optional[str] = None, 
									request:Optional[CSERequest] = None) -> Resource:
		L.isDebug and L.logDebug(f'Retrieve local resource: {ri}|{srn} for originator: {originator}')

		if ri:
			return CSE.storage.retrieveResource(ri = ri)		# retrieve via normal ID
		elif srn:
			return CSE.storage.retrieveResource(srn = srn) 	# retrieve via srn. Try to retrieve by srn (cases of ACPs created for AE and CSR by default)
		else:
			raise NOT_FOUND(f'resource: {ri}|{srn} not found')

		# EXPERIMENTAL remove this
		# if resource := cast(Resource, result.resource):	# Resource found
		# 	# Check for virtual resource
		# 	if resource.ty not in [T.GRP_FOPT, T.PCH_PCU] and resource.isVirtual(): # fopt, PCU are handled elsewhere
		# 		return resource.handleRetrieveRequest(request=request, originator=originator)	# type: ignore[no-any-return]
		# 	return result
		# # error
		# L.isDebug and L.logDebug(f'{result.dbg}: ri:{ri} srn:{srn}')



	#########################################################################
	#
	#	Discover Resources
	#

	def discoverResources(self,
						  id:str,
						  originator:str, 
						  filterCriteria:Optional[FilterCriteria] = None,
						  rootResource:Optional[Resource] = None, 
						  permission:Optional[Permission] = Permission.DISCOVERY) -> List[Resource]:
		L.isDebug and L.logDebug('Discovering resources')

		if not rootResource:
			rootResource = self.retrieveResource(id)
		
		if not filterCriteria:
			filterCriteria = FilterCriteria()

		# Apply defaults. This is not done in the FilterCriteria class bc there we only store he provided values
		lvl:int = filterCriteria.lvl if filterCriteria.lvl is not None else sys.maxsize
		fo:FilterOperation = filterCriteria.fo if filterCriteria.fo is not None else FilterOperation.AND
		ofst:int = filterCriteria.ofst if filterCriteria.ofst is not None else 1
		lim:int = filterCriteria.lim if filterCriteria.lim is not None else sys.maxsize

		# get all direct children and slice the page (offset and limit)
		dcrs = self.directChildResources(id)[ofst-1:ofst-1 + lim]	# now dcrs only contains the desired child resources for ofst and lim

		# a bit of optimization. This length stays the same.
		allLen = len(filterCriteria.attributes) if filterCriteria.attributes else 0
		if (criteriaAttributes := filterCriteria.criteriaAttributes()):
			allLen += ( len(criteriaAttributes) +
			  (len(_v)-1 if (_v := criteriaAttributes.get('ty'))  is not None else 0) +		# -1 : compensate for len(conditions) in line 1
			  (len(_v)-1 if (_v := criteriaAttributes.get('cty')) is not None else 0) +		# -1 : compensate for len(conditions) in line 1 
			  (len(_v)-1 if (_v := criteriaAttributes.get('lbl')) is not None else 0) 		# -1 : compensate for len(conditions) in line 1 
			)

		# Discover the resources
		discoveredResources = self._discoverResources(rootResource, 
													  originator, 
													  level = lvl, 
													  fo = fo, 
													  allLen = allLen, 
													  dcrs = dcrs, 
													  filterCriteria = filterCriteria,
													  permission = permission)

		# NOTE: this list contains all results in the order they could be found while
		#		walking the resource tree.
		#		DON'T CHANGE THE ORDER. DON'T SORT.
		#		Because otherwise the tree cannot be correctly re-constructed otherwise

		# Apply ARP if provided
		if filterCriteria.arp:
			_resources = []
			for resource in discoveredResources:
				# Check existence and permissions for the .../{arp} resource
				srn = f'{resource.getSrn()}/{filterCriteria.arp}'
				_res = self.retrieveResource(srn)
				if CSE.security.hasAccess(originator, _res, permission):
					_resources.append(_res)
			discoveredResources = _resources	# re-assign the new resources to discoveredResources

		return discoveredResources


	def _discoverResources(self, rootResource:Resource,
								 originator:str, 
								 level:int, 
								 fo:int, 
								 allLen:int, 
								 dcrs:Optional[list[Resource]] = None, 
								 filterCriteria:Optional[FilterCriteria] = None,
								 permission:Optional[Permission] = Permission.DISCOVERY) -> list[Resource]:
		if not rootResource or level == 0:		# no resource or level == 0
			return []

		# get all direct children, if not provided
		if not dcrs:
			if len(dcrs := self.directChildResources(rootResource.ri)) == 0:
				return []
		

		# Filter and add those left to the result
		discoveredResources = []
		for resource in dcrs:

			# Exclude virtual resources
			if resource.isVirtual():
				continue

			# check permissions and filter. Only then add a resource
			# First match then access. bc if no match then we don't need to check permissions (with all the overhead)
			if self._matchResource(resource, 
								   fo, 
								   allLen, 
								   filterCriteria) and CSE.security.hasAccess(originator, resource, permission):
				discoveredResources.append(resource)

			# Iterate recursively over all (not only the filtered!) direct child resources
			discoveredResources.extend(self._discoverResources(resource, 
															   originator, 
															   level-1, 
															   fo, 
															   allLen, 
															   filterCriteria = filterCriteria,
															   permission = permission))

		return discoveredResources


	def _matchResource(self, r:Resource, fo:int, allLen:int, filterCriteria:FilterCriteria) -> bool:	
		""" Match a filter to a resource. """

		# TODO: Implement a couple of optimizations. Can we determine earlier that a match will fail?

		ty = r.ty

		# get the parent resource
		#
		#	TODO when determines how the parentAttribute is actually encoded
		#
		# pr = None
		# if (pi := r.get('pi')) is not None:
		# 	pr = storage.retrieveResource(ri=pi)

		# The matching works like this: go through all the conditions, compare them, and
		# increment 'found' when matching. For fo=AND found must equal all conditions.
		# For fo=OR found must be > 0.
		found = 0

		# check conditions
		if filterCriteria:

			# Types
			# Multiple occurences of ty is always OR'ed. Therefore we add the count of
			# ty's to found (to indicate that the whole set matches)
			if tys := filterCriteria.ty:
				found += len(tys) if ty in tys else 0	
			if ct := r.ct:
				found += 1 if (c_crb := filterCriteria.crb) and (ct < c_crb) else 0
				found += 1 if (c_cra := filterCriteria.cra) and (ct > c_cra) else 0
			if lt := r.lt:
				found += 1 if (c_ms := filterCriteria.ms) and (lt > c_ms) else 0
				found += 1 if (c_us := filterCriteria.us) and (lt < c_us) else 0
			if (st := r.st) is not None:	# st is an int
				found += 1 if (c_sts := filterCriteria.sts) is not None and (st > c_sts) else 0	# st is an int
				found += 1 if (c_stb := filterCriteria.stb) is not None and (st < c_stb) else 0
			if et := r.et:
				found += 1 if (c_exb := filterCriteria.exb) and (et < c_exb) else 0
				found += 1 if (c_exa := filterCriteria.exa) and (et > c_exa) else 0

			# Check labels similar to types
			resourceLbl = r.lbl
			if resourceLbl and (lbls := filterCriteria.lbl):
				for l in lbls:
					if l in resourceLbl:
						found += len(lbls)
						break

			if ResourceTypes.isInstanceResource(ty):	# special handling for instance resources
				if (cs := r.cs) is not None:	# cs is an int
					found += 1 if (sza := filterCriteria.sza) is not None and cs >= sza else 0	# sizes ares ints
					found += 1 if (szb := filterCriteria.szb) is not None and cs < szb else 0

			# ContentFormats
			# Multiple occurences of cnf is always OR'ed. Therefore we add the count of
			# cnf's to found (to indicate that the whole set matches)
			# Similar to types.
			if ty in [ ResourceTypes.CIN ]:	# special handling for CIN
				if filterCriteria.cty:
					found += len(filterCriteria.cty) if r.cnf in filterCriteria.cty else 0

		# TODO childLabels
		# TODO parentLabels
		# TODO childResourceType
		# TODO parentResourceType

		# Attributes:
		for name, value in filterCriteria.attributes.items():
			if isinstance(value, str) and '*' in value:
				found += 1 if (rval := r[name]) is not None and TextTools.simpleMatch(str(rval), value) else 0
			else:
				found += 1 if (rval := r[name]) is not None and str(value) == str(rval) else 0

		# TODO childAttribute
		# TODO parentAttribute

		# Advanced query
		if filterCriteria.aq:
			found += 1 if CSE.script.runComparisonQuery(filterCriteria.aq, r) else 0


		# L.isDebug and L.logDebug(f'fo: {fo}, found: {found}, allLen: {allLen}')
		# Test whether the OR or AND criteria is fullfilled
		if not ((fo == FilterOperation.OR  and found > 0) or 		# OR and found something
				(fo == FilterOperation.AND and allLen == found)		# AND and found everything
			   ): 
			return False

		return True


	#########################################################################
	#
	#	Add resources
	#

	def processCreateRequest(self, request:CSERequest, 
								   originator:str, 
								   id:Optional[str] = None) -> Result:
		"""	Process a CREATE request. Create and register resource(s).

			Args:
				request: The incoming request.
				originator: The requests originator.
				id: Optional ID of the request.
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug(f'Process CREATE request for id: {request.id}|{request.srn}')

		# handle transit requests first
		if localResourceID(request.id) is None and localResourceID(request.srn) is None:
			return CSE.request.handleTransitCreateRequest(request)

		srn, id = self._checkHybridID(request, id) # overwrite id if another is given
		if not id and not srn:
			# if not (id := request.id):
			# 	return Result.errorResult(rsc = RC.notFound, dbg = L.logDebug('resource not found'))
			raise NOT_FOUND(L.logDebug('resource not found'))

		# Handle operation execution time and check request expiration
		self._handleOperationExecutionTime(request)
		self._checkRequestExpiration(request)

		# handle fanout point requests
		if (fanoutPointRsrc := self._getFanoutPointResource(srn)) and fanoutPointRsrc.ty == ResourceTypes.GRP_FOPT:
			L.isDebug and L.logDebug(f'Redirecting request to fanout point: {fanoutPointRsrc.getSrn()}')
			return fanoutPointRsrc.handleCreateRequest(request, srn, request.originator)

		if (ty := request.ty) is None:	# Check for type parameter in request, integer
			raise BAD_REQUEST(L.logDebug('type parameter missing in CREATE request'))

		# Some Resources are not allowed to be created in a request, return immediately
		if not ResourceTypes.isRequestCreatable(ty):
			raise OPERATION_NOT_ALLOWED(f'CREATE not allowed for type: {ty}')

		# Get parent resource and check permissions
		L.isDebug and L.logDebug(f'Get parent resource and check permissions: {id}')
		parentResource = CSE.dispatcher.retrieveResource(id)

		if not CSE.security.hasAccess(originator, parentResource, Permission.CREATE, ty = ty, parentResource = parentResource):
			if ty == ResourceTypes.AE:
				raise SECURITY_ASSOCIATION_REQUIRED('security association required')
			else:
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has no CREATE privileges for resource: {parentResource.ri}'))

		# Check for virtual resource
		if parentResource.isVirtual():
			return parentResource.handleCreateRequest(request, id, originator)	# type: ignore[no-any-return]

		# Create resource from the dictionary
		newResource = resourceFromDict(deepcopy(request.pc), pi = parentResource.ri, ty = ty)

		# Check whether the parent allows the adding
		parentResource.childWillBeAdded(newResource, originator)

		# Check resource creation
		newOriginator = CSE.registration.checkResourceCreation(newResource, originator, parentResource)

		# check whether the resource already exists, either via ri or srn
		# hasResource() may actually perform the test in one call, but we want to give a distinguished debug message
		if CSE.storage.hasResource(ri = newResource.ri):
			raise CONFLICT(L.logWarn(f'Resource with ri: {newResource.ri} already exists'))
		if CSE.storage.hasResource(srn = newResource.getSrn()):
			raise CONFLICT(L.logWarn(f'Resource with structured id: {newResource.getSrn()} already exists'))

		# originator might have changed during this check. Result.data contains this new originator
		originator = newOriginator 			# ! Don't try to optimize and rmove this. REALLY!
		request.originator = newOriginator	

		# Create the resource. If this fails we de-register everything
		try:
			_resource = CSE.dispatcher.createLocalResource(newResource, parentResource, originator, request = request)
		except ResponseException as e:
			CSE.registration.checkResourceDeletion(newResource) # deregister resource. Ignore result, we take this from the creation
			raise e

		# Post-creation
		CSE.registration.postResourceCreation(_resource)

		#
		# Handle RCN's
		#
		tpe = _resource.tpe
		rcn = request.rcn
		if rcn is None or rcn == ResultContentType.attributes:	# Just the resource & attributes, integer
			return Result(rsc = ResponseStatusCode.CREATED, resource = _resource)

		elif rcn == ResultContentType.modifiedAttributes:
			dictOrg = request.pc[tpe]
			dictNew = _resource.asDict()[tpe]
			return Result(resource = { tpe : resourceModifiedAttributes(dictOrg, dictNew, request.pc[tpe]) }, 
						  rsc = ResponseStatusCode.CREATED)

		elif rcn == ResultContentType.hierarchicalAddress:
			return Result(resource = { 'm2m:uri' : _resource.structuredPath() }, 
						  rsc = ResponseStatusCode.CREATED)

		elif rcn == ResultContentType.hierarchicalAddressAttributes:
			return Result(resource = { 'm2m:rce' : { noNamespace(tpe) : _resource.asDict()[tpe], 'uri' : _resource.structuredPath() }},
						  rsc = ResponseStatusCode.CREATED)

		elif rcn == ResultContentType.nothing:
			return Result(rsc = ResponseStatusCode.CREATED)

		else:
			raise BAD_REQUEST('wrong rcn for CREATE')
		# TODO C.rcnDiscoveryResultReferences 


	def createResourceFromDict(self, dct:JSON, 
									 parentID:str, 
									 ty:ResourceTypes, 
									 originator:str) -> Tuple[str, str, str]:
		# TODO doc
		# Create locally
		if (pID := localResourceID(parentID)) is not None:
			L.isDebug and L.logDebug(f'Creating local resource with ID: {pID} originator: {originator}')

			# Get the unstructured resource ID if necessary
			pID = riFromStructuredPath(pID) if isStructured(pID) else pID

			# Retrieve the parent resource
			parentResource = self.retrieveLocalResource(ri = pID, originator = originator)

			# Build a resource instance
			resource = resourceFromDict(dct, ty = ty, pi = pID)

			# Check Permission
			if not CSE.security.hasAccess(originator, parentResource, Permission.CREATE, ty = ty, parentResource = parentResource):
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has no CREATE privileges for resource: {parentResource.ri}'))

			# Create it locally
			createdResource = self.createLocalResource(resource, parentResource, originator = originator)

			resRi = createdResource.ri
			resCsi = CSE.cseCsi
		
		# Create remotely
		else:
			L.isDebug and L.logDebug(f'Creating remote resource with ID: {pID} originator: {originator}')
			res = CSE.request.handleSendRequest(CSERequest(to = (pri := toSPRelative(parentID)),
														   originator = originator,
														   ty = ty,
														   pc = dct)
											   )[0].result	# there should be at least one result

			# The request might have gone through normally and returned, but might still have failed on the remote CSE.
			# We need to set the status and the dbg attributes and return
			if res.rsc != ResponseStatusCode.CREATED:
				_exc = exceptionFromRSC(res.rsc)	# Get exception class from rsc
				if _exc:
					raise _exc(dbg = res.request.pc.get('dbg'))	# type:ignore[call-arg]
				raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')

			resRi = findXPath(res.request.pc, '{*}/ri')
			resCsi = csiFromSPRelative(pri)
		
		# Return success and created resource and its (resouce ID, CSE-ID, parent ID)
		return (resRi, resCsi, pID)


	def createLocalResource(self,
							resource:Resource,
							parentResource:Resource = None,
							originator:Optional[str] = None,
							request:Optional[CSERequest] = None) -> Resource:
		L.isDebug and L.logDebug(f'CREATING resource ri: {resource.ri}, type: {resource.ty}')

		if parentResource:
			L.isDebug and L.logDebug(f'Parent ri: {parentResource.ri}')
			if not parentResource.canHaveChild(resource):
				if resource.ty == ResourceTypes.SUB:
					raise TARGET_NOT_SUBSCRIBABLE(L.logWarn('Parent resource is not subscribable'))
				else:
					raise INVALID_CHILD_RESOURCE_TYPE(L.logWarn(f'Invalid child resource type: {ResourceTypes(resource.ty).value}'))

		# if not already set: determine and add the srn
		if not resource.getSrn():
			resource.setSrn(resource.structuredPath())

		# add the resource to storage
		resource.dbCreate(overwrite = False)
		
		# Set release version to the resource, of available
		if request and request.rvi:
			resource.setRVI(request.rvi)

		# Activate the resource
		# This is done *after* writing it to the DB, because in activate the resource might create or access other
		# resources that will try to read the resource from the DB.
		try:
			resource.activate(parentResource, originator) 	# activate the new resource
		except:
			resource.dbDelete()
			raise
		
		# Could be that we changed the resource in the activate, therefore write it again
		try:
			resource.dbUpdate(True)	# with an event
		except:
			resource.dbDelete()
			raise

		if parentResource:
			try:
				parentResource = parentResource.dbReload()		# Read the resource again in case it was updated in the DB
			except:
				self.deleteLocalResource(resource)
				raise
			parentResource.childAdded(resource, originator)			# notify the parent resource

			# Send event for parent resource
			self._eventCreateChildResource(parentResource)
		
		# send a create event
		self._eventCreateResource(resource)

		return resource


	#########################################################################
	#
	#	Update resources
	#

	def processUpdateRequest(self, request:CSERequest, 
								   originator:str, 
								   id:Optional[str] = None) -> Result: 
		"""	Process a UPDATE request. Update resource(s).

			Args:
				request: The incoming request.
				originator: The requests originator.
				id: Optional ID of the request.
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug(f'Process UPDATE request for id: {request.id}|{request.srn}')

		# handle transit requests first
		if localResourceID(request.id) is None and localResourceID(request.srn) is None:
			return CSE.request.handleTransitUpdateRequest(request)

		fopsrn, id = self._checkHybridID(request, id) # overwrite id if another is given

		# Unknown resource ?
		if not id and not fopsrn:
			raise NOT_FOUND(L.logDebug('resource not found'))

		# Handle operation execution time and check request expiration
		self._handleOperationExecutionTime(request)
		self._checkRequestExpiration(request)

		# handle fanout point requests
		if (fanoutPointResource := self._getFanoutPointResource(fopsrn)) and fanoutPointResource.ty == ResourceTypes.GRP_FOPT:
			L.isDebug and L.logDebug(f'Redirecting request to fanout point: {fanoutPointResource.getSrn()}')
			return fanoutPointResource.handleUpdateRequest(request, fopsrn, request.originator)

		# Get resource to update
		resource = self.retrieveResource(id)

		if resource.readOnly:
			raise OPERATION_NOT_ALLOWED('resource is read-only')

		# Some Resources are not allowed to be updated in a request, return immediately
		if ResourceTypes.isInstanceResource(resource.ty):
			raise OPERATION_NOT_ALLOWED(f'UPDATE not allowed for type: {resource.ty}')

		#
		#	Permission check
		#	If this is an 'acpi' update?
		if not CSE.security.checkAcpiUpdatePermission(request, resource, originator):	#  == False indicates that this is NOT an ACPI update. In this case we need a normal permission check
			if not CSE.security.hasAccess(originator, resource, Permission.UPDATE):
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has no UPDATE privileges for resource: {resource.ri}'))


		# Check for virtual resource
		if resource.isVirtual():
			return resource.handleUpdateRequest(request, id, originator)	# type: ignore[no-any-return]

		dictOrg = deepcopy(resource.dict)	# Save for later
		resource = self.updateLocalResource(resource, deepcopy(request.pc), originator = originator)

		# Check resource update with registration
		CSE.registration.checkResourceUpdate(resource, deepcopy(request.pc))

		#
		# Handle RCN's
		#

		tpe = resource.tpe
		if request.rcn is None or request.rcn == ResultContentType.attributes:	# rcn is an int
			return Result(rsc = ResponseStatusCode.UPDATED, resource = resource)
			
		elif request.rcn == ResultContentType.modifiedAttributes:
			dictNew = deepcopy(resource.dict)
			requestPC = request.pc[tpe]
			# return only the modified attributes. This does only include those attributes that are updated differently, or are
			# changed by the CSE, then from the original request. Luckily, all key/values that are touched in the update request
			#  are in the resource's __modified__ variable.
			return Result(rsc = ResponseStatusCode.UPDATED,
						  resource = { tpe : resourceModifiedAttributes(dictOrg, dictNew, requestPC, modifiers = resource[Constants.attrModified]) })
		elif request.rcn == ResultContentType.nothing:
			return Result(rsc = ResponseStatusCode.UPDATED)

		# TODO C.rcnDiscoveryResultReferences 

		else:
			raise BAD_REQUEST('wrong rcn for UPDATE')


	def updateLocalResource(self, resource:Resource, 
								  dct:Optional[JSON] = None, 
								  doUpdateCheck:Optional[bool] = True, 
								  originator:Optional[str] = None) -> Resource:
		"""	Update a resource in the CSE. Call update() and updated() callbacks on the resource.
		
			Args:
				resource: Resource to update.
				dct: JSON dictionary with the updated attributes.
				doUpdateCheck: Enable/disable a call to update().
				originator: The request's originator.
			Return:
				Updated resource.
		"""
		L.isDebug and L.logDebug(f'Updating resource ri: {resource.ri}, type: {resource.ty}')
		if doUpdateCheck:
			resource.willBeUpdated(dct, originator)
			resource.update(dct, originator) # TODO TRY
		else:
			L.isDebug and L.logDebug('No check, skipping resource update')

		# Signal a successful update so that further actions can be taken
		resource.updated(dct, originator)

		# Update and send an update event
		resource.dbUpdate(True)
		self._eventUpdateResource(resource)
		return resource


	def updateResourceFromDict(self, dct:JSON, 
									 id:str, 
									 originator:Optional[str] = None, 
									 resource:Optional[Resource] = None) -> Resource:
		# TODO doc

		# Update locally
		if (rID := localResourceID(id)) is not None:
			L.isDebug and L.logDebug(f'Updating local resource with ID: {id} originator: {originator}')

			# Retrieve the resource if not given
			if resource is None:
				resource = self.retrieveLocalResource(rID, originator = originator)
			
			# Check Permission
			if not CSE.security.hasAccess(originator, resource, Permission.UPDATE):
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has no UPDATE privileges for resource: {resource.ri}'))

			# Update it locally
			updatedResource = self.updateLocalResource(resource, dct, originator = originator)

		# Update remotely
		else:
			L.isDebug and L.logDebug(f'Updating remote resource with ID: {id} originator: {originator}')
			result = CSE.request.handleSendRequest(CSERequest(op = Operation.UPDATE,
															  to = id, 
															  originator = originator, 
															  pc = dct)
												  )[0].result	# there should be at least one result
		
			# The request might have gone through normally and returned, but might still have failed on the remote CSE.
			# We need to set the status and the dbg attributes and return
			if result.rsc != ResponseStatusCode.UPDATED:
				_exc = exceptionFromRSC(result.rsc)	# Get exception class from rsc
				if _exc:
					raise _exc(dbg = result.request.pc.get('dbg'))	# type:ignore[call-arg]
				raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {result.rsc}')
			
			updatedResource = result.resource

		# Return updated resource 
		return updatedResource


	#########################################################################
	#
	#	Delete resources
	#

	def processDeleteRequest(self, request:CSERequest, 
								   originator:str, 
								   id:Optional[str] = None) -> Result:
		"""	Process a DELETE request. Delete resource(s).

			Args:
				request: The incoming request.
				originator: The requests originator.
				id: Optional ID of the request.
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug(f'Process DELETE request for id: {request.id}|{request.srn}')

		# handle transit requests
		if localResourceID(request.id) is None and localResourceID(request.srn) is None:
			return CSE.request.handleTransitDeleteRequest(request)

		fopsrn, id = self._checkHybridID(request, id) # overwrite id if another is given

		# Unknown resource ?
		if not id and not fopsrn:
			raise NOT_FOUND(L.logDebug('resource not found'))

		# Handle operation execution time and check request expiration
		self._handleOperationExecutionTime(request)
		self._checkRequestExpiration(request)

		# handle fanout point requests
		if (fanoutPointRsrc := self._getFanoutPointResource(fopsrn)) and fanoutPointRsrc.ty == ResourceTypes.GRP_FOPT:
			L.isDebug and L.logDebug(f'Redirecting request to fanout point: {fanoutPointRsrc.getSrn()}')
			return fanoutPointRsrc.handleDeleteRequest(request, fopsrn, request.originator)

		# get resource to be removed and check permissions
		resource = self.retrieveResource(id)

		if not CSE.security.hasAccess(originator, resource, Permission.DELETE):
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'originator: {originator} has no DELETE privileges for resource: {resource.ri}')

		# Check for virtual resource
		if resource.isVirtual():
			return resource.handleDeleteRequest(request, id, originator)	# type: ignore[no-any-return]

		#
		# Handle RCN's first. Afterward the resource & children are no more
		#

		resultContent:Resource|JSON = None
		if request.rcn is None or request.rcn == ResultContentType.nothing:	# rcn is an int
			resultContent = None

		elif request.rcn == ResultContentType.attributes:
			resultContent = resource

		# resource and child resources, full attributes
		elif request.rcn == ResultContentType.attributesAndChildResources:
			children = self.discoverChildren(id, resource, originator, request.fc, Permission.DELETE)
			self._childResourceTree(children, resource)	# the function call add attributes to the result resource. Don't use the return value directly
			resultContent = resource

		# direct child resources, NOT the root resource
		elif request.rcn == ResultContentType.childResources:
			children = self.discoverChildren(id, resource, originator, request.fc, Permission.DELETE)
			childResources:JSON = { resource.tpe : {} }			# Root resource as a dict with no attributes
			self.resourceTreeDict(children, childResources[resource.tpe])
			resultContent = childResources

		elif request.rcn == ResultContentType.attributesAndChildResourceReferences:
			children = self.discoverChildren(id, resource, originator, request.fc, Permission.DELETE)
			self._resourceTreeReferences(children, resource, request.drt, 'ch')	# the function call add attributes to the result resource
			resultContent = resource

		elif request.rcn == ResultContentType.childResourceReferences: # child resource references
			children = self.discoverChildren(id, resource, originator, request.fc, Permission.DELETE)
			childResourcesRef = self._resourceTreeReferences(children, None, request.drt, 'm2m:rrl')
			resultContent = childResourcesRef
			
		# TODO RCN.discoveryResultReferences
		else:
			raise BAD_REQUEST('wrong rcn for DELETE')

		# remove resource
		self.deleteLocalResource(resource, originator, withDeregistration = True)

		# Some post-deletion stuff
		CSE.registration.postResourceDeletion(resource)

		return Result(resource = resultContent, rsc = ResponseStatusCode.DELETED)


	def deleteLocalResource(self, resource:Resource, 
								  originator:Optional[str] = None, 
								  withDeregistration:Optional[bool] = False, 
								  parentResource:Optional[Resource] = None, 
								  doDeleteCheck:Optional[bool] = True) -> None:
		L.isDebug and L.logDebug(f'Removing resource ri: {resource.ri}, type: {resource.ty}')

		resource.deactivate(originator)	# deactivate it first

		# Check resource deletion
		if withDeregistration:
			CSE.registration.checkResourceDeletion(resource)

		# Retrieve the parent resource now, because we need it later
		if not parentResource:
			parentResource = resource.retrieveParentResource()

		# delete the resource from the DB. Save the result to return later
		try:
			resource.dbDelete()
		except NOT_FOUND as e:
			L.isDebug and L.logDebug(f'Cannot delete resource: {e.dbg}')
		except:
			L.logErr('deleteLocalResource')
			raise
		finally:
			# send a delete event
			self._eventDeleteResource(resource)
			# Now notify the parent resource
			if doDeleteCheck and parentResource:
				parentResource.childRemoved(resource, originator)


	def deleteResource(self, id:str,  originator:Optional[str] = None) -> None:
		# TODO doc

		
		# Update locally
		if (rID := localResourceID(id)) is not None:
			L.isDebug and L.logDebug(f'Deleting local resource with ID: {id} originator: {originator}')

			# Retrieve the resource
			resource = self.retrieveLocalResource(rID, originator = originator)
			
			if id in [ CSE.cseRi, CSE.cseRi, CSE.cseRn ]:
				raise OPERATION_NOT_ALLOWED(dbg = 'DELETE operation is not allowed for CSEBase')

			# Check Permission
			if not CSE.security.hasAccess(originator, resource, Permission.DELETE):
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator: {originator} has no DELETE access to: {resource.ri}'))

			# delete it locally
			self.deleteLocalResource(resource, originator = originator)

		# Delete remotely
		else:
			L.isDebug and L.logDebug(f'Deleting remote resource with ID: {id} originator: {originator}')
			res = CSE.request.handleSendRequest(CSERequest(op = Operation.DELETE,
														   to = id, 
														   originator = originator))[0].result	# there should be at least one result
		
			# The request might have gone through normally and returned, but might still have failed on the remote CSE.
			# We need to set the status and the dbg attributes and return
			if res.rsc != ResponseStatusCode.DELETED:
				_exc = exceptionFromRSC(res.rsc)	# Get exception class from rsc
				if _exc:
					raise _exc(dbg = res.request.pc.get('dbg'))	# type:ignore[call-arg]
				raise INTERNAL_SERVER_ERROR(f'unknown/unsupported RSC: {res.rsc}')


	#########################################################################
	#
	#	Notify
	#

	def processNotifyRequest(self, request:CSERequest, 
								   originator:Optional[str], 
								   id:Optional[str] = None) -> Result:
		"""	Process a NOTIFY request. Send notifications to resource(s).

			Args:
				request: The incoming request.
				originator: The requests originator.
				id: Optional ID of the request.
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug(f'Process NOTIFY request for id: {request.id}|{request.srn}')

		# handle transit requests
		if localResourceID(request.id) is None:
			return CSE.request.handleTransitNotifyRequest(request)

		srn, id = self._checkHybridID(request, id) # overwrite id if another is given

		# Handle operation execution time and check request expiration
		self._handleOperationExecutionTime(request)
		self._checkRequestExpiration(request)

		# get resource to be notified and check permissions
		targetResource = self.retrieveResource(id)
		# if targetResource.ty != ResourceTypes.PCH_PCU:
		# 	raise INTERNAL_SERVER_ERROR(L.logErr(f'target resource: {id} must be a PCU. Is: {targetResource.ty}'))

		# Security checks below

		
		# Check for <pollingChannelURI> resource
		# This is also the only resource type supported that can receive notifications, yet
		if targetResource.ty == ResourceTypes.PCH_PCU :
			if not CSE.security.hasAccessToPollingChannel(originator, targetResource): # type:ignore[arg-type]
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator: {originator} has not access to <pollingChannelURI>: {id}'))
			targetResource.handleNotifyRequest(request, originator)
			return Result(rsc = ResponseStatusCode.OK)

		if ResourceTypes.isNotificationEntity(targetResource.ty):
			if not CSE.security.hasAccess(originator, targetResource, Permission.NOTIFY):
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator has no NOTIFY privilege for: {id}'))
			#  A Notification to one of these resources will always be a Received Notify Request
			return CSE.request.handleReceivedNotifyRequest(id, request = request, originator = originator)
		
		if targetResource.ty == ResourceTypes.CRS:
			try:
				targetResource.handleNotification(request, originator)
				return Result(rsc = ResponseStatusCode.OK)
			except ResponseException as e:
				L.isWarn and L.logWarn(f'error handling notificatuin: {e.dbg}')
				raise

		# error
		raise BAD_REQUEST(L.logDebug(f'Unsupported resource type: {targetResource.ty} for notifications.'))


	def notifyLocalResource(self, ri:str, 
								  originator:str, 
								  content:JSON) -> Result:
		# TODO doc

		L.isDebug and L.logDebug(f'Sending NOTIFY to local resource: {ri}')
		resource = self.retrieveLocalResource(ri, originator = originator)
		
		# Check Permission
		if not CSE.security.hasAccess(originator, resource, Permission.NOTIFY):
			raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator: {originator} has no NOTIFY access to: {resource.ri}'))
		
		# Send notification
		try:
			resource.handleNotification(CSERequest(to = ri,
												   id = ri,
												   op = Operation.NOTIFY,
												   originator = originator,
												   ot = getResourceDate(),
												   rqi = uniqueRI(),
												   rvi = CSE.releaseVersion,
												   pc = content),
										   originator)
			return Result(rsc = ResponseStatusCode.OK)
		except ResponseException as e:
			L.isWarn and L.logWarn(f'error handling notificatuin: {e.dbg}')
			raise
		


	#########################################################################
	#
	#	Public Utility methods
	#

	def directChildResources(self, pi:str, 
								   ty:Optional[ResourceTypes] = None) -> list[Resource]:
		"""	Return all child resources of a resource, optionally filtered by type.
			An empty list is returned if no child resource could be found.
		"""
		return cast(List[Resource], CSE.storage.directChildResources(pi, ty))


	def directChildResourcesRI(self, pi:str, 
			    					 ty:Optional[ResourceTypes] = None) -> list[str]:
		"""	Return the resourceIdentifiers of all child resources of a resource, optionally filtered by type.
			An empty list is returned if no child resource could be found.
		"""
		return CSE.storage.directChildResourcesRI(pi, ty)
	

	def countDirectChildResources(self, pi:str, ty:Optional[ResourceTypes] = None) -> int:
		"""	Return the number of all child resources of resource, optionally filtered by type. 
		"""
		return CSE.storage.countDirectChildResources(pi, ty)


	def hasDirectChildResource(self, pi:str, 
			    					 ri:str) -> bool:
		"""	Check if a resource has a direct child resource with a given resourceID
		"""
		return riFromID(ri) in self.directChildResourcesRI(pi)
	

	def retrieveLatestOldestInstance(self, pi:str, 
										   ty:ResourceTypes, 
										   oldest:Optional[bool] = False) -> Optional[Resource]:
		"""	Get the latest or oldest x-Instance resource for a parent.

			This is done by searching through all resources once to find the fitting resource 
			(parent + type)	with the latest or oldest *ct* attribute.

			Args:
				pi: parent resourceIdentifier
				ty: resource type to look for
				oldest: switch between oldest and latest search
			
			Return:
				Resource
		"""
		# TODO: Check if it's using mongodb to access retrieveLatestOldestResource()
  
		hit:Tuple[JSON, str] = None

		# If using mongodb, use other functions and return immediately the result
		if CSE.storage.isMongoDB():
			return CSE.storage.retrieveLatestOldestResource(oldest, int(ty), pi)
  
		op = operator.gt if oldest else operator.lt

		# This function used as a mapper to search through all resources and
		# determines the newest CIN resource for this parent
		# This should be a bit faster than getting all the CIN, instantiating them, 
		# and throwig them all away etc
		def determineLatest(res:JSON) -> bool:
			nonlocal hit
			if res['pi'] == pi and res['ty'] == ty:
				ct = res['ct']
				if not hit or op(hit[1], ct):
					hit = ( res, ct )
			return False

		# Search through the resources with the mapping functions
		CSE.storage.searchByFilter(filter = determineLatest)
		if not hit:
			return None
		# Instantiate and return resource
		return resourceFromDict(hit[0])


	def discoverChildren(self, id:str, 
							   resource:Resource, 
							   originator:str, 
							   filterCriteria:FilterCriteria, 
							   permission:Permission) -> Optional[list[Resource]]:
		# TODO documentation
		resources = self.discoverResources(id, originator, filterCriteria = filterCriteria, rootResource = resource, permission = permission)

		# check and filter by ACP
		children = []
		for r in resources:
			if CSE.security.hasAccess(originator, r, permission):
				children.append(r)
		return children


	def countResources(self, ty:ResourceTypes|Tuple[ResourceTypes, ...]=None) -> int:
		""" Return total number of resources.
			Optional filter by type.
		"""

		# Count all resources
		if ty is None:	# ty is an int
			return CSE.storage.countResources()
		
		# Count all resources of the given types
		if isinstance(ty, tuple):
			cnt = 0
			for t in ty:
				cnt += len(CSE.storage.retrieveResourcesByType(t))
			return cnt

		# Count all resources of a specific type
		# TODO: SAMUEL: This can be optimized
		return len(CSE.storage.retrieveResourcesByType(ty))


	def retrieveResourcesByType(self, ty:ResourceTypes) -> list[Resource]:
		""" Retrieve all resources of a type. 

			Args:
				ty: Resouce type to search for.
			Return:
				A list of retrieved `Resource` objects. This list might be empty.
		"""
		result = []
		rss = CSE.storage.retrieveResourcesByType(ty)
		for rs in (rss or []):
			result.append(resourceFromDict(rs))
		return result


	def retrieveResourceWithPermission(self, ri:str, originator:str, permission:Permission) -> Resource:
		"""	Retrieve a resource and check access for an originator.

			Args:
				ri: Resource ID of the resource to be retrieved.
				originator: The originator to check the permission for.
				permission: The permission to check.

			Return:
				The retrieved resource.
			
			Raises:
				`NOT_FOUND`: In case the resource could not be found.
				`ORIGINATOR_HAS_NO_PRIVILEGE`: In case the originator has not the required permission to the resoruce.

		"""
		resource = CSE.dispatcher.retrieveResource(riFromID(ri), originator)
		if not CSE.security.hasAccess(originator, resource, permission):
			raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'originator has no access to the resource: {ri}'))
		return resource
	

	def deleteChildResources(self, parentResource:Resource, 
								   originator:str, 
								   ty:Optional[ResourceTypes] = None,
								   doDeleteCheck:Optional[bool] = True) -> None:
		"""	Remove all child resources of a parent recursively. 

			If *ty* is set only the resources of this type are removed.
		"""
		# Remove directChildResources
		rs = self.directChildResources(parentResource.ri)
		for r in rs:
			if ty is None or r.ty == ty:	# ty is an int
				#parentResource.childRemoved(r, originator)	# recursion here
				self.deleteLocalResource(r, originator, parentResource = parentResource, doDeleteCheck = doDeleteCheck)

	#########################################################################
	#
	#	Request execution utilities
	#

	def _handleOperationExecutionTime(self, request:CSERequest) -> None:
		"""	Handle operation execution time and request expiration. If the OET is set then
			wait until the provided timestamp is reached.

			Args:
				request: The request to check.
		"""
		if request.oet:
			# Calculate the dealy
			delay = timeUntilAbsRelTimestamp(request.oet)
			L.isDebug and L.logDebug(f'Waiting: {delay:.4f} seconds until delayed execution')
			# Just wait some time
			waitFor(delay)	


	def _checkRequestExpiration(self, request:CSERequest) -> None:
		"""	Check request expiration timeout if a request timeout is give.

			Args:
				request: The request to check.

			Raises:
				`REQUEST_TIMEOUT`: In case the request is expired 
		"""
		if request._rqetUTCts is not None and timeUntilTimestamp(request._rqetUTCts) <= 0.0:
			raise REQUEST_TIMEOUT(L.logDebug('request timed out'))



	#########################################################################
	#
	#	Internal methods for collecting resources and child resources into structures
	#

	def _resourcesToURIList(self, resources:list[Resource], drt:int) -> JSON:
		"""	Create a m2m:uril structure from a list of resources.
		"""
		cseid = f'{CSE.cseCsi}/'	# SP relative. csi already starts with a "/"
		lst = []
		for r in resources:
			lst.append(r.structuredPath() if drt == DesiredIdentifierResultType.structured else cseid + r.ri)
		return { 'm2m:uril' : lst }


	def resourceTreeDict(self, resources:list[Resource], targetResource:Resource|JSON) -> list[Resource]:
		"""	Recursively walk the results and build a sub-resource tree for each resource type.
		"""
		rri = targetResource['ri'] if 'ri' in targetResource else None
		while True:		# go multiple times per level through the resources until the list is empty
			result = []
			handledTy = None
			handledTPE = None
			idx = 0
			while idx < len(resources):
				r = resources[idx]

				if rri and r.pi != rri:	# only direct children
					idx += 1
					continue
				if r.isVirtual():	# Skip latest, oldest etc virtual resources
					idx += 1
					continue
				if handledTy is None:					# ty is an int
					handledTy = r.ty					# this round we check this type
					handledTPE = r.tpe					# ... and this TPE (important to distinguish specializations in mgmtObj and fcnt )
				if r.ty == handledTy and r.tpe == handledTPE:		# handle only resources of the currently handled type and TPE!
					result.append(r)					# append the found resource 
					resources.remove(r)						# remove resource from the original list (greedy), but don't increment the idx
					resources = self.resourceTreeDict(resources, r)	# check recursively whether this resource has children
				else:
					idx += 1							# next resource

			# add all found resources under the same type tag to the rootResource
			if len(result) > 0:
				# sort resources by type and then by lowercase rn
				if self.sortDiscoveryResources:
					# result.sort(key=lambda x:(x.ty, x.rn.lower()))
					result.sort(key = lambda x: (x.ty, x.ct) if ResourceTypes.isInstanceResource(x.ty) else (x.ty, x.rn.lower()))
				targetResource[result[0].tpe] = [r.asDict(embedded = False) for r in result]
				# TODO not all child resources are lists [...] Handle just to-1 relations
			else:
				break # end of list, leave while loop
		return resources # Return the remaining list


	def _resourceTreeReferences(self, resources:list[Resource], 
									  targetResource:Resource|JSON, 
									  drt:Optional[DesiredIdentifierResultType] = DesiredIdentifierResultType.structured,
									  tp:Optional[str] = 'm2m:rrl') -> Resource|JSON:
		""" Retrieve child resource references of a resource and add them to
			a new target resource as "children" """
		if not targetResource:
			targetResource = { }

		t = []

		# sort resources by type and then by lowercase rn
		if self.sortDiscoveryResources:
			resources.sort(key = lambda x:(x.ty, x.rn.lower()))
		
		for r in resources:
			if ResourceTypes.isVirtualResource(r.ty):	# Skip virtual resources
				continue
			ref = { 'nm' : r['rn'], 
					'typ' : r['ty'], 
					'val' : toSPRelative(r.structuredPath() if drt == DesiredIdentifierResultType.structured else r.ri)
			}
			if r.ty == ResourceTypes.FCNT:
				ref['spty'] = r.cnd		# TODO Is this correct? Actually specializationID in TS-0004 6.3.5.29, but this seems to be wrong
			t.append(ref)

		# The following reflects a current inconsistency in the standard.
		# If this list of childResourceReferences is for rcn=5 (attributesAndChildResourceReferences), then the structure
		# is -> 'ch' : [ <listOfChildResourceRef> ]
		# If this list of childResourceReferences is for rcn=6 (childResourceReferences), then the structure 
		# is -> '{ 'rrl' : { 'rrf' : [ <listOfChildResourceRef> ]}}  ( an extra rrf struture )
		targetResource[tp] = { "rrf" : t } if tp == 'm2m:rrl' else t
		return targetResource


	# Retrieve full child resources of a resource and add them to a new target resource
	def _childResourceTree(self, resources:list[Resource], targetResource:Resource|JSON) -> None:
		if len(resources) == 0:
			return
		result:JSON = {}
		self.resourceTreeDict(resources, result)	# rootResource is filled with the result
		for k,v in result.items():			# copy child resources to result resource
			targetResource[k] = v


	#########################################################################
	#
	#	Internal methods for ID handling
	#

	def _checkHybridID(self, request:CSERequest, id:str) -> Tuple[str, str]:
		"""	Return a corrected *id* and *srn* in case this is a hybrid ID.

			Args:
				request: A request object that provides *id* and *srn*. *srn* might be None.
				id: An ID which might be None. If it is not None, then it will be taken to generate the *srn*.
			Return:
				Tuple of *srn* and *id*
		"""
		if id:
			srn = id if isStructured(id) else None # Overwrite srn if id is strcutured. This is a bit mixed up sometimes
			return srnFromHybrid(srn, id) # Hybrid
			# return srnFromHybrid(None, id) # Hybrid
		return srnFromHybrid(request.srn, request.id) # Hybrid



	def _getPollingChannelURIResource(self, id:str) -> Optional[PCH_PCU]:
		"""	Check whether the target is a PollingChannelURI resource and return it.

			Args:
				id: Target resource ID
			Return:
				Return either the virtual PollingChannelURI resource or None.
		"""
		if not id:
			return None
		if id.endswith('pcu'):
			# Convert to srn
			if not isStructured(id):
				if not (id := structuredPathFromRI(id)):
					return None

			resource = CSE.dispatcher.retrieveResource(id)
			if resource.ty == ResourceTypes.PCH_PCU:
				return cast(PCH_PCU, resource)


			# Fallthrough
		return None

	
	def _getFanoutPointResource(self, id:str) -> Optional[Resource]:
		"""	Check whether the target resource contains a fanoutPoint along its path is a fanoutPoint.

			Args:
				id: the target's resource ID.
			Return:
				Return either the virtual fanoutPoint resource, or None in case of an error.
		"""
		# Convert to srn
		if not isStructured(id):
			if not (id := structuredPathFromRI(id)):
				return None
		# from here on id is a srn
		nid = None
		if id.endswith('/fopt'):
			nid = id
		else:
			(head, found, _) = id.partition('/fopt/')
			if found:
				nid = head + '/fopt'

		if nid:
			try:
				return CSE.dispatcher.retrieveResource(nid)
			except:
				pass
		return None


	def _latestOldestResource(self, id:str) -> Optional[Resource]:
		"""	Check whether the target is a latest or oldest virtual resource and return it.

			Args:
				id: Target resource ID
			Return:
				Return either the virtual resource, or None in case of an error.
		"""
		if not id:
			return None
		if id.endswith(('la', 'ol')):
			# Convert to srn
			if not isStructured(id):
				if not (id := structuredPathFromRI(id)):
					return None
			if (resource := CSE.dispatcher.retrieveResource(id)) and ResourceTypes.isLatestOldestResource(resource.ty):
				return resource
		# Fallthrough
		return None


	def _partialFromResource(self, resource:Resource, attributeList:JSON) -> Result:
		if attributeList:
			# Validate that the attribute(s) are actual resouce attributes
			for a in attributeList:
				if not resource.hasAttributeDefined(a):
					raise BAD_REQUEST(L.logWarn(f'Undefined attribute: {a} in partial retrieve for resource type: {resource.ty}'))
			
			# Filter the attribute(s)
			tpe = resource.tpe
			return Result(resource = { tpe : filterAttributes(resource.asDict()[tpe], attributeList) }, 
						  rsc = ResponseStatusCode.OK)
		return Result(resource = resource, 
					  rsc = ResponseStatusCode.OK)
