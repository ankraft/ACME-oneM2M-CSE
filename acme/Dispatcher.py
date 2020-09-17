#
#	Dispatcher.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external and most internal requests are routed
#	through here.
#

import sys, traceback, re, json
from flask import Request
from typing import Any, List, Tuple, Union
from Logging import Logging
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T
from Types import FilterOperation
from Types import FilterUsage
from Types import Permission
from Types import Operation
from Types import DesiredIdentifierResultType
from Types import ResultContentType as RCN
from Types import ResponseCode as RC
from Types import Result
import CSE, Utils
from resources.Resource import Resource


class Dispatcher(object):

	def __init__(self) -> None:
		self.rootPath 			= Configuration.get('http.root')
		self.enableTransit 		= Configuration.get('cse.enableTransitRequests')
		self.spid 				= Configuration.get('cse.spid')
		self.csi 				= Configuration.get('cse.csi')
		self.csiSlash 			= '%s/' % self.csi
		self.cseri 				= Configuration.get('cse.ri')
		self.csern				= Configuration.get('cse.rn')
		self.csiLen 			= len(self.csi)
		self.csiSlashLen 		= len(self.csiSlash)
		self.cseriLen 			= len(self.cseri)

		Logging.log('Dispatcher initialized')


	def shutdown(self) -> None:
		Logging.log('Dispatcher shut down')



	# The "xxxRequest" methods handle http requests while the "xxxResource"
	# methods handle actions on the resources. Security/permission checking
	# is done for requests, not on resource actions.


	#########################################################################

	#
	#	Retrieve resources
	#

	def retrieveRequest(self, request:Request, _id:Tuple[str, str, str]) ->  Result:
		originator, _, _, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('RETRIEVE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier')

		# handle transit requests
		if CSE.remote.isTransitID(id):
		 	return CSE.remote.handleTransitRetrieveRequest(request, id, originator) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# handle hybrid ids
		srn, id = self._buildSRNFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleRetrieveRequest(request, srn, originator)

		# just a normal retrieve request
		return self.handleRetrieveRequest(request, id if id is not None else srn, originator)


	def handleRetrieveRequest(self, request: Request, id: str, originator: str) -> Result:
		Logging.logDebug('Handle retrieve resource: %s' % id)

		try:
			attrs, msg = self._getArguments(request, Operation.RETRIEVE)
			if attrs is None:
				return Result(rsc=RC.badRequest, dbg=msg)
			fu 			= attrs.get('fu')
			drt 		= attrs.get('drt')
			handling 	= attrs.get('__handling__')
			conditions 	= attrs.get('__conditons__')
			attributes 	= attrs.get('__attrs__')
			fo 			= attrs.get('fo')
			rcn 		= attrs.get('rcn')
		except Exception as e:
			#Logging.logWarn('Exception: %s' % traceback.format_exc())
			return Result(rsc=RC.invalidArguments, dbg='invalid arguments (%s)' % str(e))

		permission = Permission.DISCOVERY if fu == 1 else Permission.RETRIEVE

		# check rcn & operation
		if permission == Permission.DISCOVERY and rcn not in [ RCN.discoveryResultReferences, RCN.childResourceReferences ]:	# Only allow those two
			return Result(rsc=RC.badRequest, dbg='invalid rcn: %d for fu: %d' % (rcn, fu))
		if permission == Permission.RETRIEVE and rcn not in [ RCN.attributes, RCN.attributesAndChildResources, RCN.childResources, RCN.attributesAndChildResourceReferences, RCN.originalResource, RCN.childResourceReferences]: # TODO
			return Result(rsc=RC.badRequest, dbg='invalid rcn: %d for fu: %d' % (rcn, fu))

		Logging.logDebug('Discover/Retrieve resources (fu: %d, drt: %s, handling: %s, conditions: %s, resultContent: %d, attributes: %s)' % (fu, drt, handling, conditions, rcn, str(attributes)))


		# Retrieve the target resource, because it is needed for some rcn (and the default)
		if rcn in [RCN.attributes, RCN.attributesAndChildResources, RCN.childResources, RCN.attributesAndChildResourceReferences, RCN.originalResource]:
			if (res := self.retrieveResource(id)).resource is None:
			 	return res
			if not CSE.security.hasAccess(originator, res.resource, permission):
				return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no permission (%d)' % permission)

			# if rcn == attributes then we can return here, whatever the result is
			if rcn == RCN.attributes:
				return res

			resource = res.resource	# root resource for the retrieval/discovery

			# if rcn == original-resource we retrieve the linked resource
			if rcn == RCN.originalResource:
				if resource is None:	# continue only when there actually is a resource
					return res
				if (lnk := resource.lnk) is None:	# no link attribute?
					return Result(rsc=RC.badRequest, dbg='missing lnk attribute in target resource')
				return self.retrieveResource(lnk, originator, raw=True)


		# do discovery
		if (res := self.discoverResources(id, originator, handling, fo, conditions, attributes, permission=permission)).lst is None:	# not found?
			return res.errorResult()

		# check and filter by ACP. After this allowedResources only contains the resources that are allowed
		allowedResources = []
		for r in res.lst:
			if CSE.security.hasAccess(originator, r, permission):
				allowedResources.append(r)

		#
		#	Handle more sophisticated RCN
		#

		if rcn == RCN.attributesAndChildResources:
			self._resourceTreeJSON(allowedResources, resource)	# the function call add attributes to the target resource
			return Result(resource=resource)

		elif rcn == RCN.attributesAndChildResourceReferences:
			self._resourceTreeReferences(allowedResources, resource, drt)	# the function call add attributes to the target resource
			return Result(resource=resource)

		elif rcn == RCN.childResourceReferences: 
			#childResourcesRef: dict  = { resource.tpe: {} }  # Root resource as a dict with no attribute
			childResourcesRef = self._resourceTreeReferences(allowedResources,  None, drt)
			return Result(resource=childResourcesRef)

		elif rcn == RCN.childResources:
			childResources: dict = { resource.tpe : {} } #  Root resource as a dict with no attribute
			self._resourceTreeJSON(allowedResources, childResources[resource.tpe]) # Adding just child resources
			return Result(resource=childResources)

		elif rcn == RCN.discoveryResultReferences: # URIList
			return Result(resource=self._resourcesToURIList(allowedResources, drt))

		else:
			return Result(rsc=RC.badRequest, dbg='wrong rcn for RETRIEVE')





	def retrieveResource(self, id:str=None, originator:str=None, raw:bool=False) -> Result:
		# If the ID is in SP-relative format then first check whether this is for the
		# local CSE. 
		# If yes, then adjust the ID and try to retrieve it. 
		# If no, then try to retrieve the resource from a connected (!) remote CSE.
		if id is not None:
			if id.startswith(self.csiSlash) and len(id) > self.csiSlashLen:		# TODO for all operations?
				id = id[self.csiSlashLen:]
			else:
				if Utils.isSPRelative(id):
					return CSE.remote.retrieveRemoteResource(id, originator, raw)
		return self._retrieveResource(srn=id) if Utils.isStructured(id) else self._retrieveResource(ri=id)


	def _retrieveResource(self, ri:str=None, srn:str=None) -> Result:
		Logging.logDebug('Retrieve resource: %s' % (ri if srn is None else srn))

		if ri is not None:
			res = CSE.storage.retrieveResource(ri=ri)		# retrieve via normal ID
		elif srn is not None:
			res = CSE.storage.retrieveResource(srn=srn) 	# retrieve via srn. Try to retrieve by srn (cases of ACPs created for AE and CSR by default)
		else:
			return Result(rsc=RC.notFound, dbg='resource not found')

		if (resource := res.resource) is not None:
			# Check for virtual resource
			if resource.ty != T.GRP_FOPT and Utils.isVirtualResource(resource): # fopt is handled elsewhere
				return resource.handleRetrieveRequest()
			return Result(resource=resource)
		if res.dbg is not None:
			Logging.logDebug('%s: %s' % (res.dbg, ri))
		return Result(rsc=res.rsc, dbg=res.dbg)


	#########################################################################
	#
	#	Discover Resources
	#

	def discoverResources(self, id:str, originator:str, handling:dict, fo:int=1, conditions:dict=None, attributes:dict=None, rootResource:Resource=None, permission:Permission=Permission.DISCOVERY) -> Result:
		if rootResource is None:
			if (res := self.retrieveResource(id)).resource is None:
				return Result(rsc=RC.notFound, dbg=res.dbg)
			rootResource = res.resource

		# get all direct children
		dcrs = self.directChildResources(id)

		# Slice the page (offset and limit)
		offset = handling['ofst'] if 'ofst' in handling else 1			# default: 1 (first resource
		limit = handling['lim'] if 'lim' in handling else sys.maxsize	# default: system max size or "maxint"
		dcrs = dcrs[offset-1:offset-1+limit]							# now dcrs only contains the desired child resources for ofst and lim

		# Get level
		level = handling['lvl'] if 'lvl' in handling else sys.maxsize	# default: system max size or "maxint"

		# a bit of optimization. This length stays the same.
		allLen = ((len(conditions) if conditions is not None else 0) +
		  (len(attributes) if attributes is not None else 0) +
		  (len(conditions.get('ty'))-1 if conditions is not None else 0) +		# -1 : compensate for len(conditions) in line 1
		  (len(conditions.get('cty'))-1 if conditions is not None else 0) +		# -1 : compensate for len(conditions) in line 1 
		  (len(conditions.get('lbl'))-1 if conditions is not None else 0) 		# -1 : compensate for len(conditions) in line 1 
		)

		# Discover the resources
		discoveredResources = self._discoverResources(rootResource, originator, level, fo, allLen, dcrs=dcrs, conditions=conditions, attributes=attributes)

		# NOTE: this list contains all results in the order they could be found while
		#		walking the resource tree.
		#		DON'T CHANGE THE ORDER. DON'T SORT.
		#		Because otherwise the tree cannot be correctly re-constructed otherwise

		# Apply ARP if provided
		if 'arp' in handling:
			arp = handling['arp']
			result = []
			for resource in discoveredResources:
				srn = '%s/%s' % (resource[Resource._srn], arp)
				if (res := self.retrieveResource(srn)).resource is not None:
					if CSE.security.hasAccess(originator, res.resource, permission):
						result.append(res.resource)
			discoveredResources = result	# re-assign the new resources to discoveredResources

		return Result(lst=discoveredResources)


	def _discoverResources(self, rootResource : Resource, originator : str, level : int, fo : int, allLen : int, dcrs : list = None, conditions : dict = None, attributes : dict = None) -> List[Resource]:
		if rootResource is None or level == 0:		# no resource or level == 0
			return []

		# get all direct children, if not provided
		if dcrs is None:
			if len(dcrs := self.directChildResources(rootResource.ri)) == 0:
				return []

		# Filter and add those left to the result
		discoveredResources = []
		for r in dcrs:

			# Exclude virtual resources
			if Utils.isVirtualResource(r):
				continue

			# check permissions and filter. Only then add a resource
			# First match then access. bc if no match then we don't need to check permissions (with all the overhead)
			if self._matchResource(r, conditions, attributes, fo, allLen) and CSE.security.hasAccess(originator, r, Permission.DISCOVERY):
				discoveredResources.append(r)

			# Iterate recursively over all (not only the filtered) direct child resources
			discoveredResources.extend(self._discoverResources(r, originator, level-1, fo, allLen, conditions=conditions, attributes=attributes))

		return discoveredResources


	def _matchResource(self, r : Resource, conditions : dict, attributes : dict, fo : int, allLen : int) -> bool:	
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
		if conditions is not None:

			# Types
			# Multiple occurences of ty is always OR'ed. Therefore we add the count of
			# ty's to found (to indicate that the whole set matches)
			if (tys := conditions.get('ty')) is not None:
				found += len(tys) if str(ty) in tys else 0
			if (ct := r.ct) is not None:
				found += 1 if (c_crb := conditions.get('crb')) is not None and (ct < c_crb) else 0
				found += 1 if (c_cra := conditions.get('cra')) is not None and (ct > c_cra) else 0

			if (lt := r.lt) is not None:
				found += 1 if (c_ms := conditions.get('ms')) is not None and (lt > c_ms) else 0
				found += 1 if (c_us := conditions.get('us')) is not None and (lt < c_us) else 0

			if (st := r.st) is not None:
				found += 1 if (c_sts := conditions.get('sts')) is not None and (str(st) > c_sts) else 0
				found += 1 if (c_stb := conditions.get('stb')) is not None and (str(st) < c_stb) else 0

			if (et := r.et) is not None:
				found += 1 if (c_exb := conditions.get('exb')) is not None and (et < c_exb) else 0
				found += 1 if (c_exa := conditions.get('exa')) is not None and (et > c_exa) else 0

			# Check labels similar to types
			rlbl = r.lbl
			if rlbl is not None and (lbls := conditions.get('lbl')) is not None:
				for l in lbls:
					if l in rlbl:
						found += len(lbls)
						break
			# special handling of label-list
			# if (lbl := r.lbl) is not None and (c_lbl := conditions.get('lbl')) is not None:
			# 	lbla = c_lbl.split()
			# 	fnd = 0
			# 	for l in lbla:
			# 		fnd += 1 if l in lbl else 0
			# 	found += 1 if (fo == 1 and fnd == len(lbl)) or (fo == 2 and fnd > 0) else 0	# fo==or -> find any label
				#	# TODO labelsQuery


			if ty in [ T.CIN, T.FCNT ]:	# special handling for CIN, FCNT
				if (cs := r.cs) is not None:
					found += 1 if (sza := conditions.get('sza')) is not None and (int(cs) >= int(sza)) else 0
					found += 1 if (szb := conditions.get('szb')) is not None and (int(cs) < int(szb)) else 0

			# ContentFormats
			# Multiple occurences of cnf is always OR'ed. Therefore we add the count of
			# cnf's to found (to indicate that the whole set matches)
			# Similar to types.
			if ty in [ T.CIN ]:	# special handling for CIN
				if (cnfs := conditions.get('cty')) is not None:
					found += len(cnfs) if r.cnf in cnfs else 0

			# TODO childLabels
			# TODO parentLabels
			# TODO childResourceType
			# TODO parentResourceType


			# Attributes:
			if attributes is not None:
				for name in attributes:
					val = attributes[name]
					if '*' in val:
						val = val.replace('*', '.*')
						found += 1 if (rval := r[name]) is not None and re.match(val, str(rval)) else 0
					else:
						found += 1 if (rval := r[name]) is not None and str(val) == str(rval) else 0

			# TODO childAttribute
			# TODO parentAttribute


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

	def createRequest(self, request: Request, _id: Tuple[str, str, str]) -> Result:
		originator, ct, ty, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('CREATE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier')

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitCreateRequest(request, id, originator, ty) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# handle hybrid id
		srn, id = self._buildSRNFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleCreateRequest(request, srn, originator, ct, ty)

		# just a normal create request
		return self.handleCreateRequest(request, id, originator, ct, ty)



	def handleCreateRequest(self, request:Request, id:str, originator:str, ct:str, ty:T) -> Result:
		Logging.logDebug('Adding new resource')

		try:
			attrs, msg = self._getArguments(request, Operation.CREATE)
			if attrs is None:
				return Result(rsc=RC.badRequest, dbg=msg)
			rcn   = attrs.get('rcn')
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg=str(e))

		if ct == None or ty == None:
			return Result(rsc=RC.badRequest, dbg='ct or ty is missing in request')

		# CSEBase creation, return immediately
		if ty == T.CSEBase:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# Get parent resource and check permissions
		if (res := self.retrieveResource(id)).resource is None:
			Logging.log('Parent resource not found')
			return Result(rsc=RC.notFound, dbg='parent resource not found')
		parentResource = res.resource

		if CSE.security.hasAccess(originator, parentResource, Permission.CREATE, ty=ty, isCreateRequest=True, parentResource=parentResource) == False:
			if ty == T.AE:
				return Result(rsc=RC.securityAssociationRequired, dbg='security association required')
			else:
				return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no privileges')

		# Check for virtual resource
		if Utils.isVirtualResource(parentResource):
			return parentResource.handleCreateRequest(request, id, originator, ct, ty)

		# Add new resource
		try:
			jsn = json.loads(Utils.removeCommentsFromJSON(request.get_data(as_text=True)))
			if (nres := Utils.resourceFromJSON(jsn, pi=parentResource.ri, ty=ty)).resource is None:	# something wrong, perhaps wrong type
				return Result(rsc=RC.badRequest, dbg=nres.dbg)
		except Exception as e:
			Logging.logWarn('Bad request (malformed content?)')
			return Result(rsc=RC.badRequest, dbg=str(e))
		nresource = nres.resource

		# Check whether the parent allows the adding
		if not (res := parentResource.childWillBeAdded(nresource, originator)).status:
			return res.errorResult()

		# check whether the resource already exists
		if CSE.storage.hasResource(nresource.ri, nresource.__srn__):
			Logging.logWarn('Resource already registered')
			return Result(rsc=RC.conflict, dbg='resource already exists')

		# Check resource creation
		if (rres := CSE.registration.checkResourceCreation(nresource, originator, parentResource)).rsc != RC.OK:
			return rres.errorResult()
		originator = rres.originator 	# originator might have changed during this check

		# Create the resource. If this fails we register everything
		if (res := self.createResource(nresource, parentResource, originator)).resource is None:
			CSE.registration.checkResourceDeletion(nresource) # deregister resource. Ignore result, we take this from the creation
			return res

		#
		# Handle RCN's
		#

		tpe = res.resource.tpe
		if rcn is None or rcn == RCN.attributes:	# Just the resource & attributes
			return res
		elif rcn == RCN.modifiedAttributes:
			jsonOrg =request.json[tpe]
			jsonNew = res.resource.asJSON()[tpe]
			return Result(resource={ tpe : Utils.resourceDiff(jsonOrg, jsonNew) }, rsc=res.rsc, dbg=res.dbg)
		elif rcn == RCN.hierarchicalAddress:
			return Result(resource={ 'm2m:uri' : Utils.structuredPath(res.resource) }, rsc=res.rsc, dbg=res.dbg)
		elif rcn == RCN.hierarchicalAddressAttributes:
			return Result(resource={ 'm2m:rce' : { Utils.noDomain(tpe) : res.resource.asJSON()[tpe], 'uri' : Utils.structuredPath(res.resource) }}, rsc=res.rsc, dbg=res.dbg)
		elif rcn == RCN.nothing:
			return Result(rsc=res.rsc, dbg=res.dbg)
		else:
			return Result(rsc=RC.badRequest, dbg='wrong rcn for CREATE')
		# TODO C.rcnDiscoveryResultReferences 


	def createResource(self, resource:Resource, parentResource:Resource=None, originator:str=None) -> Result:
		Logging.logDebug('Adding resource ri: %s, type: %d' % (resource.ri, resource.ty))

		if parentResource is not None:
			Logging.logDebug('Parent ri: %s' % parentResource.ri)
			if not parentResource.canHaveChild(resource):
				if resource.ty == T.SUB:
					err = 'Parent resource is not subscribable'
					Logging.logWarn(err)
					return Result(rsc=RC.targetNotSubscribable, dbg=err)
				else:
					err = 'Invalid child resource type'
					Logging.logWarn(err)
					return Result(rsc=RC.invalidChildResourceType, dbg=err)

		# if not already set: determine and add the srn
		if resource.__srn__ is None:
			resource[resource._srn] = Utils.structuredPath(resource)

		# add the resource to storage
		if (res := resource.dbCreate(overwrite=False)).rsc != RC.created:
			return res

		# Activate the resource
		# This is done *after* writing it to the DB, because in activate the resource might create or access other
		# resources that will try to read the resource from the DB.
		if not (res := resource.activate(parentResource, originator)).status: 	# activate the new resource
			resource.dbDelete()
			return res.errorResult()

		# Could be that we changed the resource in the activate, therefore write it again
		if (res := resource.dbUpdate()).resource is None:
			resource.dbDelete()
			return res

		if parentResource is not None:
			parentResource = parentResource.dbReload().resource		# Read the resource again in case it was updated in the DB
			parentResource.childAdded(resource, originator)			# notify the parent resource

		# send a create event
		CSE.event.createResource(resource)	# type: ignore

		return Result(resource=resource, rsc=RC.created) 	# everything is fine. resource created.


	#########################################################################

	#
	#	Update resources
	#

	def updateRequest(self, request:Request, _id:Tuple[str, str, str]) -> Result:
		originator, ct, _, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('UPDATE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier')

		# ID= cse.ri, return immediately
		if id == self.cseri:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for CSEBase')

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitUpdateRequest(request, id, originator) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# handle hybrid id
		srn, id = self._buildSRNFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleUpdateRequest(request, srn, originator, ct)

		# just a normal update request
		return self.handleUpdateRequest(request, id, originator, ct)


	def handleUpdateRequest(self, request:Request, id:str, originator:str, ct:str) -> Result: 

		# get arguments
		try:
			attrs, msg = self._getArguments(request, Operation.UPDATE)
			if attrs is None:
				return Result(rsc=RC.badRequest, dbg=msg)
			rcn = attrs.get('rcn')
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg=str(e))

		Logging.logDebug('Updating resource')
		if ct == None:
			return Result(rsc=RC.badRequest, dbg='missing or wrong content type in header')

		# Get resource to update
		if (res := self.retrieveResource(id)).resource is None:
			Logging.log('Resource not found')
			return Result(rsc=RC.notFound, dbg=res.dbg)
		resource = res.resource
		if resource.readOnly:
			return Result(rsc=RC.operationNotAllowed, dbg='resource is read-only')

		# check permissions
		try:
			#jsn = request.json
			jsn = json.loads(Utils.removeCommentsFromJSON(request.get_data(as_text=True)))
		except Exception as e:
			Logging.logWarn('Bad request (malformed content?)')
			return Result(rsc=RC.badRequest, dbg=str(e))

		acpi = Utils.findXPath(jsn, list(jsn.keys())[0] + '/acpi')
		if acpi is not None:	# update of acpi attribute means check for self privileges!
			updateOrDelete = Permission.DELETE if acpi is None else Permission.UPDATE
			if CSE.security.hasAccess(originator, resource, updateOrDelete, checkSelf=True) == False:
				return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no privileges')
		elif CSE.security.hasAccess(originator, resource, Permission.UPDATE) == False:
			return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no privileges')


		# Check for virtual resource
		if Utils.isVirtualResource(resource):
			return resource.handleUpdateRequest(request, id, originator, ct)

		jsonOrg = resource.json.copy()	# Save for later

		# Check resource update with registration
		if (rres := CSE.registration.checkResourceUpdate(resource)).rsc != RC.OK:
			return rres.errorResult()

		if (res := self.updateResource(resource, jsn, originator=originator)).resource is None:
			return res.errorResult()
		resource = res.resource 	# re-assign resource (might have been changed during update)

		#
		# Handle RCN's
		#

		tpe = resource.tpe
		if rcn is None or rcn == RCN.attributes:
			return res
		elif rcn == RCN.modifiedAttributes:
			jsonNew = resource.json.copy()	
			# return only the diff. This includes those attributes that are updated with the same value. Luckily, 
			# all key/values that are touched in the update request are in the resource's __modified__ variable.
			return Result(resource={ tpe : Utils.resourceDiff(jsonOrg, jsonNew, modifiers=resource[Resource._modified]) }, rsc=res.rsc)
		elif rcn == RCN.nothing:
			return Result(rsc=res.rsc)
		# TODO C.rcnDiscoveryResultReferences 
		else:
			return Result(rsc=RC.badRequest, dbg='wrong rcn for UPDATE')


	def updateResource(self, resource:Resource, json:dict=None, doUpdateCheck:bool=True, originator:str=None) -> Result:
		Logging.logDebug('Updating resource ri: %s, type: %d' % (resource.ri, resource.ty))
		if doUpdateCheck:
			if not (res := resource.update(json, originator)).status:
				return res.errorResult()
		else:
			Logging.logDebug('No check, skipping resource update')

		# send a create event
		CSE.event.updateResource(resource)		# type: ignore
		return resource.dbUpdate()


	#########################################################################

	#
	#	Remove resources
	#

	def deleteRequest(self, request: Request, _id: Tuple[str, str, str]) -> Result:
		originator, _, _, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('DELETE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier')

		# ID= cse.ri, return immediately
		if id == self.cseri:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for CSEBase')

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitDeleteRequest(id, originator) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# handle hybrid id
		srn, id = self._buildSRNFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleDeleteRequest(request, srn, originator)

		# just a normal delete request
		return self.handleDeleteRequest(request, id if id is not None else srn, originator)


	def handleDeleteRequest(self, request:Request, id:str, originator:str) -> Result:
		Logging.logDebug('Removing resource')

		# get arguments
		try:
			attrs, msg = self._getArguments(request, Operation.DELETE)
			if attrs is None:
				return Result(rsc=RC.badRequest, dbg=msg)
			rcn  		= attrs.get('rcn')
			drt 		= attrs.get('drt')
			handling 	= attrs.get('__handling__')
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg=str(e))

		# get resource to be removed and check permissions
		if (res := self.retrieveResource(id)).resource is None:
			Logging.logDebug('Resource not found: %s' % res.dbg)
			return Result(rsc=RC.notFound, dbg=res.dbg)
		resource = res.resource

		if CSE.security.hasAccess(originator, resource, Permission.DELETE) == False:
			return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no privileges')

		# Check for virtual resource
		if Utils.isVirtualResource(resource):
			return resource.handleDeleteRequest(request, id, originator)

		#
		# Handle RCN's first. Afterward the resource & children are no more
		#

		tpe = resource.tpe
		result: Any = None
		if rcn is None or rcn == RCN.nothing:
			result = None
		elif rcn == RCN.attributes:
			result = resource
		# resource and child resources, full attributes
		elif rcn == RCN.attributesAndChildResources:
			children = self.discoverChildren(id, resource, originator, handling, Permission.DELETE)
			self._childResourceTree(children, resource)	# the function call add attributes to the result resource. Don't use the return value directly
			result = resource
		# direct child resources, NOT the root resource
		elif rcn == RCN.childResources:
			children = self.discoverChildren(id, resource, originator, handling, Permission.DELETE)
			childResources: dict = { resource.tpe : {} }			# Root resource as a dict with no attributes
			self._resourceTreeJSON(children, childResources[resource.tpe])
			result = childResources
		elif rcn == RCN.attributesAndChildResourceReferences:
			children = self.discoverChildren(id, resource, originator, handling, Permission.DELETE)
			self._resourceTreeReferences(children, resource, drt)	# the function call add attributes to the result resource
			result = resource
		elif rcn == RCN.childResourceReferences: # child resource references
			children = self.discoverChildren(id, resource, originator, handling, Permission.DELETE)
			childResourcesRef: dict = { resource.tpe: {} }  # Root resource with no attribute
			self._resourceTreeReferences(children, childResourcesRef[resource.tpe], drt)
			result = childResourcesRef
		# TODO RCN.discoveryResultReferences
		else:
			return Result(rsc=RC.badRequest, dbg='wrong rcn for DELETE')

		# remove resource
		res = self.deleteResource(resource, originator, withDeregistration=True)
		return Result(resource=result, rsc=res.rsc, dbg=res.dbg)


	def deleteResource(self, resource:Resource, originator:str=None, withDeregistration:bool=False) -> Result:
		Logging.logDebug('Removing resource ri: %s, type: %d' % (resource.ri, resource.ty))
		# if resource is None:
		# 	Logging.log('Resource not found')

		# Check resource deletion
		if withDeregistration:
			if not (res := CSE.registration.checkResourceDeletion(resource)).status:
				return Result(rsc=RC.badRequest, dbg=res.dbg)

		resource.deactivate(originator)	# deactivate it first
		# notify the parent resource
		parentResource = resource.retrieveParentResource()
		res = resource.dbDelete()

		# send a delete event
		CSE.event.deleteResource(resource) 	# type: ignore

		if parentResource is not None:
			parentResource.childRemoved(resource, originator)
		return Result(resource=resource, rsc=res.rsc, dbg=res.dbg)

	#########################################################################

	#
	#	Utility methods
	#

	def directChildResources(self, pi: str, ty: T = None) -> List[Resource]:
		""" Return all child resources of resources. """
		return CSE.storage.directChildResources(pi, ty)


	def discoverChildren(self, id:str, resource:Resource, originator:str, handling:dict, permission:Permission) -> List[Resource]:
		if (resourceList := self.discoverResources(id, originator, handling, rootResource=resource, permission=permission).lst) is  None:
			return None
		# check and filter by ACP
		children = []
		for r in resourceList:
			if CSE.security.hasAccess(originator, r, permission):
				children.append(r)
		return children


	def countResources(self) -> int:
		""" Get total number of resources. """
		return CSE.storage.countResources()


	def retrieveResourcesByType(self, ty:T) -> List[Resource]:
		""" Retrieve all resources of a type. """

		result = []
		rss = CSE.storage.retrieveResourcesByType(ty)
		for rs in (rss or []):
			result.append(Utils.resourceFromJSON(rs).resource)
		return result


	def _buildSRNFromHybrid(self, srn:str, id:str) -> Tuple[str, str]:
		""" Handle Hybrid ID. """
		if id is not None:
			ids = id.split('/')
			if srn is None and len(ids) > 1  and ids[-1] in C.virtualResourcesNames: # Hybrid
				if (srn := Utils.structuredPathFromRI('/'.join(ids[:-1]))) is not None:
					srn = '/'.join([srn, ids[-1]])
					id = Utils.riFromStructuredPath(srn) # id becomes the ri of the fopt
		return srn, id


	#########################################################################

	#
	#	Internal methods
	#


	# Get the request arguments, or meaningful defaults.
	# Only a small subset is supported yet
	# Throws an exception when a wrong type is encountered. This is part of the validation
	def _getArguments(self, request:Request, operation:Operation=Operation.RETRIEVE) -> Tuple[dict, str]:
		result: dict = { }

		# copy for greedy attributes checking
		args = request.args.copy()	 	# type: ignore

		# FU - Filter Usage
		if (fu := args.get('fu')) is not None:
			if not CSE.validator.validateRequestArgument('fu', fu).status:
				return None, 'error validating \'fu\' argument'
			try:
				fu = FilterUsage(int(fu))
			except ValueError as exc:
				return None, '\'%s\' is not a valid value for fu' % fu
			del args['fu']
		else:
			fu = FilterUsage.conditionalRetrieval
		if fu == FilterUsage.discoveryCriteria and operation == Operation.RETRIEVE:
			operation = Operation.DISCOVERY
		result['fu'] = fu

		# DRT - Desired Identifier Result Type
		if (drt := args.get('drt')) is not None: # 1=strucured, 2=unstructured
			if not CSE.validator.validateRequestArgument('drt', drt).status:
				return None, 'error validating \'drt\' argument'
			try:
				drt = DesiredIdentifierResultType(int(drt))
			except ValueError as exc:
				return None, '\'%s\' is not a valid value for drt' % drt
			del args['drt']
		else:
			drt = DesiredIdentifierResultType.structured
		result['drt'] = drt

		# FO - Filter Operation
		if (fo := args.get('fo')) is not None: # 1=AND, 2=OR
			if not CSE.validator.validateRequestArgument('fo', fo).status:
				return None, 'error validating \'fo\' argument'
			try:
				fo = FilterOperation(int(fo))
			except ValueError as exc:
				return None, '\'%s\' is not a valid value for fo' % fo
			del args['fo']
		else:
			fo = FilterOperation.AND # default
		result['fo'] = fo

		if (rcn := args.get('rcn')) is not None: 
			if not CSE.validator.validateRequestArgument('rcn', rcn).status:
				return None, 'error validating \'rcn\' argument'
			rcn = int(rcn)
			del args['rcn']
		else:
			if fu != FilterUsage.discoveryCriteria:
				# Different defaults for each operation
				if operation in [ Operation.RETRIEVE, Operation.CREATE, Operation.UPDATE ]:
					rcn = RCN.attributes
				elif operation == Operation.DELETE:
					rcn = RCN.nothing
			else:
				# discovery-result-references as default for Discovery operation
				rcn = RCN.discoveryResultReferences

		# Check value of rcn depending on operation
		if operation == Operation.RETRIEVE and rcn not in [ RCN.attributes,
															RCN.attributesAndChildResources,
															RCN.attributesAndChildResourceReferences,
															RCN.childResourceReferences,
															RCN.childResources,
															RCN.originalResource ]:
			return None, 'rcn: %d not allowed in RETRIEVE operation' % rcn
		elif operation == Operation.DISCOVERY and rcn not in [ RCN.childResourceReferences,
															   RCN.discoveryResultReferences ]:
			return None, 'rcn: %d not allowed in DISCOVERY operation' % rcn
		elif operation == Operation.CREATE and rcn not in [ RCN.attributes,
															RCN.modifiedAttributes,
															RCN.hierarchicalAddress,
															RCN.hierarchicalAddressAttributes,
															RCN.nothing ]:
			return None, 'rcn: %d not allowed in CREATE operation' % rcn
		elif operation == Operation.UPDATE and rcn not in [ RCN.attributes,
															RCN.modifiedAttributes,
															RCN.nothing ]:
			return None, 'rcn: %d not allowed in UPDATE operation' % rcn
		elif operation == Operation.DELETE and rcn not in [ RCN.attributes,
															RCN.nothing,
															RCN.attributesAndChildResources,
															RCN.childResources,
															RCN.attributesAndChildResourceReferences,
															RCN.childResourceReferences ]:
			return None, 'rcn: %d not allowed DELETE operation' % rcn

		result['rcn'] = rcn


		# handling conditions
		handling = { }
		for c in ['lim', 'lvl', 'ofst']:	# integer parameters
			if c in args:
				v = args[c]
				if not CSE.validator.validateRequestArgument(c, v).status:
					return None, 'error validating "%s" argument' % c
				handling[c] = int(v)
				del args[c]
		for c in ['arp']:
			if c in args:
				v = args[c]
				if not CSE.validator.validateRequestArgument(c, v).status:
					return None, 'error validating "%s" argument' % c
				handling[c] = v # string
				del args[c]
		result['__handling__'] = handling


		# conditions
		conditions = {}

		# Extract and store other arguments
		for c in ['crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr']:
			if (v := args.get(c)) is not None:
				if not CSE.validator.validateRequestArgument(c, v).status:
					return None, 'error validating "%s" argument' % c
				conditions[c] = v
				del args[c]

		# get types (multi). Always create at least an empty list
		conditions['ty'] = []
		for e in args.getlist('ty'):
			for es in (t := e.split()):	# check for number
				if not CSE.validator.validateRequestArgument('ty', es).status:
					return None, 'error validating "ty" argument(s)'
			conditions['ty'].extend(t)
		args.poplist('ty')

		# get contentTypes (multi). Always create at least an empty list
		conditions['cty'] = []
		for e in args.getlist('cty'):
			for es in (t := e.split()):	# check for number
				if not CSE.validator.validateRequestArgument('cty', es).status:
					return None, 'error validating "cty" argument(s)'
			conditions['cty'].extend(t)
		args.poplist('cty')

		# get types (multi). Always create at least an empty list
		# NO validation of label. It is a list.
		conditions['lbl'] = []
		for e in args.getlist('lbl'):
			conditions['lbl'].append(e)
		args.poplist('lbl')

		result['__conditons__'] = conditions 	# store found conditions in result

		# all remaining arguments are treated as matching attributes
		for arg, val in args.items():
			if not CSE.validator.validateRequestArgument(arg, val).status:
				return None, 'error validating (unknown?) \'%s\' argument)' % arg

		# all arguments have passed, so add them
		result['__attrs__'] = args

		return result, None


	#	Create a m2m:uril structure from a list of resources
	def _resourcesToURIList(self, resources:List[Resource], drt:int) -> dict:
		# cseid = '/' + Configuration.get('cse.csi') + '/'
		cseid = '/%s/' % self.csi
		lst = []
		for r in resources:
			lst.append(Utils.structuredPath(r) if drt == DesiredIdentifierResultType.structured else cseid + r.ri)
		return { 'm2m:uril' : lst }


	# def _attributesAndChildResources(self, parentResource, resources):
	# 	result = parentResource.asJSON()
	# 	ch = []
	# 	for r in resources:
	# 		ch.append(r.asJSON(embedded=False))
	# 	result[parentResource.tpe]['ch'] = ch
	# 	return result

	# Recursively walk the results and build a sub-resource tree for each resource type
	def _resourceTreeJSON(self, resources:List[Resource], targetResource:Union[Resource, dict]) -> List[Resource]:
		rri = targetResource['ri'] if 'ri' in targetResource else None
		while True:		# go multiple times per level through the resources until the list is empty
			result = []
			handledTy = None
			idx = 0
			while idx < len(resources):
				r = resources[idx]

				if rri is not None and r.pi != rri:	# only direct children
					idx += 1
					continue
				if r.ty in C.virtualResources:	# Skip latest, oldest etc virtual resources
					idx += 1
					continue
				if handledTy is None:
					handledTy = r.ty					# this round we check this type
				if r.ty == handledTy:					# handle only resources of the currently handled type
					result.append(r)					# append the found resource 
					resources.remove(r)						# remove resource from the original list (greedy), but don't increment the idx
					resources = self._resourceTreeJSON(resources, r)	# check recursively whether this resource has children
				else:
					idx += 1							# next resource

			# add all found resources under the same type tag to the rootResource
			if len(result) > 0:
				# sort resources by type and then by lowercase rn
				if Configuration.get('cse.sortDiscoveredResources'):
					result.sort(key=lambda x:(x.ty, x.rn.lower()))
				targetResource[result[0].tpe] = [r.asJSON(embedded=False) for r in result]
				# TODO not all child resources are lists [...] Handle just to-1 relations
			else:
				break # end of list, leave while loop
		return resources # Return the remaining list


	def _resourceTreeReferences(self, resources:List[Resource], targetResource:Union[Resource, dict], drt: int) -> Union[Resource, dict]:
		""" Retrieve child resource references of a resource and add them to
			a new target resource as "children" """
		tp = 'ch'
		if targetResource is None:
			targetResource = { }
			tp = 'm2m:rrl'	# top level in dict, so add qualifier.

		t = []

		# sort resources by type and then by lowercase rn
		if Configuration.get('cse.sortDiscoveredResources'):
			resources.sort(key=lambda x:(x.ty, x.rn.lower()))
		
		for r in resources:
			if r.ty in [ T.CNT_OL, T.CNT_LA, T.FCNT_OL, T.FCNT_LA ]:	# Skip latest, oldest virtual resources
				continue
			ref = { 'nm' : r['rn'], 'typ' : r['ty'], 'val' :  Utils.structuredPath(r) if drt == DesiredIdentifierResultType.structured else r.ri}
			if r.ty == T.FCNT:
				ref['spty'] = r.cnd		# TODO Is this correct? Actually specializationID in TS-0004 6.3.5.29, but this seems to be wrong
			t.append(ref)
		targetResource[tp] = t
		return targetResource


	# Retrieve full child resources of a resource and add them to a new target resource
	def _childResourceTree(self, resources: List[Resource], targetResource: Union[Resource, dict]) -> None:
		if len(resources) == 0:
			return
		result: dict = {}
		self._resourceTreeJSON(resources, result)	# rootResource is filled with the result
		for k,v in result.items():			# copy child resources to result resource
			targetResource[k] = v

