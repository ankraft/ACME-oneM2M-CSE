#
#	Dispatcher.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Most internal requests are routed through here.
#

import sys, traceback, re, json
import isodate
from flask import Request
from typing import Any, List, Tuple, Union, Dict
from Logging import Logging
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T
from Types import FilterOperation
from Types import FilterUsage
from Types import ResponseType
from Types import Permission
from Types import Operation
from Types import DesiredIdentifierResultType
from Types import ResultContentType as RCN
from Types import ResponseCode as RC
from Types import Result
from Types import RequestArguments
from Types import RequestHeaders
from Types import RequestStatus
from Types import CSERequest
import CSE, Utils
from resources.Resource import Resource


class Dispatcher(object):

	def __init__(self) -> None:
		self.csi 				= Configuration.get('cse.csi')
		self.csiSlash 			= '%s/' % self.csi
		self.csiSlashLen 		= len(self.csiSlash)
		Logging.log('Dispatcher initialized')


	def shutdown(self) -> bool:
		Logging.log('Dispatcher shut down')
		return True



	# The "xxxRequest" methods handle http requests while the "xxxResource"
	# methods handle actions on the resources. Security/permission checking
	# is done for requests, not on resource actions.


	#########################################################################

	#
	#	Retrieve resources
	#

	def processRetrieveRequest(self, request:CSERequest, originator:str, id:str=None) -> Result:
		fopsrn, id = self._checkHybridID(request, id) # overwrite id if another is given

		# # overwrite id if another is given
		# if id is not None:
		# 	id = id
		# 	srn = None
		# else:
		# 	id = request.id
		# 	srn = request.srn
		# fopsrn, id = Utils.srnFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(fopsrn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleRetrieveRequest(request, fopsrn, request.headers.originator)

		permission = Permission.DISCOVERY if request.args.fu == 1 else Permission.RETRIEVE

		# check rcn & operation
		if permission == Permission.DISCOVERY and request.args.rcn not in [ RCN.discoveryResultReferences, RCN.childResourceReferences ]:	# Only allow those two
			return Result(rsc=RC.badRequest, dbg='invalid rcn: %d for fu: %d' % (request.args.rcn, request.args.fu))
		if permission == Permission.RETRIEVE and request.args.rcn not in [ RCN.attributes, RCN.attributesAndChildResources, RCN.childResources, RCN.attributesAndChildResourceReferences, RCN.originalResource, RCN.childResourceReferences]: # TODO
			return Result(rsc=RC.badRequest, dbg='invalid rcn: %d for fu: %d' % (request.args.rcn, request.args.fu))

		Logging.logDebug('Discover/Retrieve resources (fu: %d, drt: %s, handling: %s, conditions: %s, resultContent: %d, attributes: %s)' % (request.args.fu, request.args.drt, request.args.handling, request.args.conditions, request.args.rcn, str(request.args.attributes)))


		# Retrieve the target resource, because it is needed for some rcn (and the default)
		if request.args.rcn in [RCN.attributes, RCN.attributesAndChildResources, RCN.childResources, RCN.attributesAndChildResourceReferences, RCN.originalResource]:
			if (res := self.retrieveResource(id)).resource is None:
			 	return res
			if not CSE.security.hasAccess(originator, res.resource, permission):
				return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no permission (%d)' % permission)

			# if rcn == attributes then we can return here, whatever the result is
			if request.args.rcn == RCN.attributes:
				return res

			resource = res.resource	# root resource for the retrieval/discovery

			# if rcn == original-resource we retrieve the linked resource
			if request.args.rcn == RCN.originalResource:
				if resource is None:	# continue only when there actually is a resource
					return res
				if (lnk := resource.lnk) is None:	# no link attribute?
					return Result(rsc=RC.badRequest, dbg='missing lnk attribute in target resource')
				return self.retrieveResource(lnk, originator, raw=True)


		# do discovery
		# TODO simplify arguments
		if (res := self.discoverResources(id, originator, request.args.handling, request.args.fo, request.args.conditions, request.args.attributes, permission=permission)).lst is None:	# not found?
			return res.errorResult()

		# check and filter by ACP. After this allowedResources only contains the resources that are allowed
		allowedResources = []
		for r in res.lst:
			if CSE.security.hasAccess(originator, r, permission):
				allowedResources.append(r)

		#
		#	Handle more sophisticated RCN
		#

		if request.args.rcn == RCN.attributesAndChildResources:
			self._resourceTreeJSON(allowedResources, resource)	# the function call add attributes to the target resource
			return Result(resource=resource)

		elif request.args.rcn == RCN.attributesAndChildResourceReferences:
			self._resourceTreeReferences(allowedResources, resource, request.args.drt)	# the function call add attributes to the target resource
			return Result(resource=resource)

		elif request.args.rcn == RCN.childResourceReferences: 
			#childResourcesRef: dict  = { resource.tpe: {} }  # Root resource as a dict with no attribute
			childResourcesRef = self._resourceTreeReferences(allowedResources,  None, request.args.drt)
			return Result(resource=childResourcesRef)

		elif request.args.rcn == RCN.childResources:
			childResources: dict = { resource.tpe : {} } #  Root resource as a dict with no attribute
			self._resourceTreeJSON(allowedResources, childResources[resource.tpe]) # Adding just child resources
			return Result(resource=childResources)

		elif request.args.rcn == RCN.discoveryResultReferences: # URIList
			return Result(resource=self._resourcesToURIList(allowedResources, request.args.drt))

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
		return self.retrieveLocalResource(srn=id) if Utils.isStructured(id) else self.retrieveLocalResource(ri=id)


	def retrieveLocalResource(self, ri:str=None, srn:str=None) -> Result:
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
		Logging.logDebug('Discovering resources')

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
		allLen = len(attributes) if attributes is not None else 0
		if conditions is not None:
			allLen += ( len(conditions) +
			  (len(conditions.get('ty'))-1 if 'ty' in conditions else 0) +		# -1 : compensate for len(conditions) in line 1
			  (len(conditions.get('cty'))-1 if 'cty' in conditions else 0) +		# -1 : compensate for len(conditions) in line 1 
			  (len(conditions.get('lbl'))-1 if 'lbl' in conditions else 0) 		# -1 : compensate for len(conditions) in line 1 
			)

		# allLen = ((len(conditions) if conditions is not None else 0) +
		#   (len(attributes) if attributes is not None else 0) +
		#   (len(conditions.get('ty'))-1 if conditions is not None and 'ty' in conditions else 0) +		# -1 : compensate for len(conditions) in line 1
		#   (len(conditions.get('cty'))-1 if conditions is not None else 0) +		# -1 : compensate for len(conditions) in line 1 
		#   (len(conditions.get('lbl'))-1 if conditions is not None else 0) 		# -1 : compensate for len(conditions) in line 1 
		# )

		# Discover the resources
		discoveredResources = self._discoverResources(rootResource, originator, level, fo, allLen, dcrs=dcrs, conditions=conditions, attributes=attributes, permission=permission)

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


	def _discoverResources(self, rootResource:Resource, originator:str, level:int, fo:int, allLen:int, dcrs:list=None, conditions:dict=None, attributes:dict=None, permission:Permission=Permission.DISCOVERY) -> List[Resource]:
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
			if self._matchResource(r, conditions, attributes, fo, allLen) and CSE.security.hasAccess(originator, r, permission):
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

	def processCreateRequest(self, request:CSERequest, originator:str, id:str=None) -> Result:
		fopsrn, id = self._checkHybridID(request, id) # overwrite id if another is given

		# # overwrite id if another is given
		# if id is not None:
		# 	id = id
		# 	srn = None
		# else:
		# 	id = request.id
		# 	srn = request.srn
		# fopsrn, id = Utils.srnFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(fopsrn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleCreateRequest(request, fopsrn, request.headers.originator)

		ct 			= request.headers.contentType
		ty 			= request.headers.resourceType

		# Some Resources are not allowed to be created in a request, return immediately
		if ty in [ T.CSEBase, T.REQ ]:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# Get parent resource and check permissions
		if (res := CSE.dispatcher.retrieveResource(id)).resource is None:
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
			return parentResource.handleCreateRequest(request, id, originator)

		# Add new resource
		if (nres := Utils.resourceFromJSON(request.json, pi=parentResource.ri, ty=ty)).resource is None:	# something wrong, perhaps wrong type
			return Result(rsc=RC.badRequest, dbg=nres.dbg)
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
		if (res := CSE.dispatcher.createResource(nresource, parentResource, originator)).resource is None:
			CSE.registration.checkResourceDeletion(nresource) # deregister resource. Ignore result, we take this from the creation
			return res

		#
		# Handle RCN's
		#

		tpe = res.resource.tpe
		if request.args.rcn is None or request.args.rcn == RCN.attributes:	# Just the resource & attributes
			return res
		elif request.args.rcn == RCN.modifiedAttributes:
			jsonOrg = request.args.request.json[tpe]
			jsonNew = res.resource.asJSON()[tpe]
			return Result(resource={ tpe : Utils.resourceDiff(jsonOrg, jsonNew) }, rsc=res.rsc, dbg=res.dbg)
		elif request.args.rcn == RCN.hierarchicalAddress:
			return Result(resource={ 'm2m:uri' : Utils.structuredPath(res.resource) }, rsc=res.rsc, dbg=res.dbg)
		elif request.args.rcn == RCN.hierarchicalAddressAttributes:
			return Result(resource={ 'm2m:rce' : { Utils.noDomain(tpe) : res.resource.asJSON()[tpe], 'uri' : Utils.structuredPath(res.resource) }}, rsc=res.rsc, dbg=res.dbg)
		elif request.args.rcn == RCN.nothing:
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
					err = 'Invalid child resource type: %s' % T(resource.ty).value
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

	def processUpdateRequest(self, request:CSERequest, originator:str, id:str=None) -> Result: 
		fopsrn, id = self._checkHybridID(request, id) # overwrite id if another is given
		# # overwrite id if another is given
		# if id is not None:
		# 	id = id
		# 	srn = None
		# else:
		# 	id = request.id
		# 	srn = request.srn
		# fopsrn, id = Utils.srnFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(fopsrn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleUpdateRequest(request, fopsrn, request.headers.originator)

		# Get resource to update
		if (res := self.retrieveResource(id)).resource is None:
			Logging.log('Resource not found')
			return Result(rsc=RC.notFound, dbg=res.dbg)
		resource = res.resource
		if resource.readOnly:
			return Result(rsc=RC.operationNotAllowed, dbg='resource is read-only')

		# check permissions
		acpi = Utils.findXPath(request.json, list(request.json.keys())[0] + '/acpi')
		if acpi is not None:	# update of acpi attribute means check for self privileges!
			updateOrDelete = Permission.DELETE if acpi is None else Permission.UPDATE
			if CSE.security.hasAccess(originator, resource, updateOrDelete, checkSelf=True) == False:
				return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no privileges')
		elif CSE.security.hasAccess(originator, resource, Permission.UPDATE) == False:
			return Result(rsc=RC.originatorHasNoPrivilege, dbg='originator has no privileges')

		# Check for virtual resource
		if Utils.isVirtualResource(resource):
			return resource.handleUpdateRequest(request, id, originator)

		jsonOrg = resource.json.copy()	# Save for later

		# Check resource update with registration
		if (rres := CSE.registration.checkResourceUpdate(resource)).rsc != RC.OK:
			return rres.errorResult()

		if (res := self.updateResource(resource, request.json, originator=originator)).resource is None:
			return res.errorResult()
		resource = res.resource 	# re-assign resource (might have been changed during update)

		#
		# Handle RCN's
		#

		tpe = resource.tpe
		if request.args.rcn is None or request.args.rcn == RCN.attributes:
			return res
		elif request.args.rcn == RCN.modifiedAttributes:
			jsonNew = resource.json.copy()	
			# return only the diff. This includes those attributes that are updated with the same value. Luckily, 
			# all key/values that are touched in the update request are in the resource's __modified__ variable.
			return Result(resource={ tpe : Utils.resourceDiff(jsonOrg, jsonNew, modifiers=resource[Resource._modified]) }, rsc=res.rsc)
		elif request.args.rcn == RCN.nothing:
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

	def processDeleteRequest(self, request:CSERequest, originator:str, id:str=None) -> Result:
		fopsrn, id = self._checkHybridID(request, id) # overwrite id if another is given
		# if id is not None:
		# 	id = id
		# 	srn = None
		# else:
		# 	id = request.id
		# 	srn = request.srn
		# fopsrn, id = Utils.srnFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(fopsrn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleDeleteRequest(request, fopsrn, request.headers.originator)


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
		if request.args.rcn is None or request.args.rcn == RCN.nothing:
			result = None
		elif request.args.rcn == RCN.attributes:
			result = resource
		# resource and child resources, full attributes
		elif request.args.rcn == RCN.attributesAndChildResources:
			children = self.discoverChildren(id, resource, originator, request.args.handling, Permission.DELETE)
			self._childResourceTree(children, resource)	# the function call add attributes to the result resource. Don't use the return value directly
			result = resource
		# direct child resources, NOT the root resource
		elif request.args.rcn == RCN.childResources:
			children = self.discoverChildren(id, resource, originator, request.args.handling, Permission.DELETE)
			childResources: dict = { resource.tpe : {} }			# Root resource as a dict with no attributes
			self._resourceTreeJSON(children, childResources[resource.tpe])
			result = childResources
		elif request.args.rcn == RCN.attributesAndChildResourceReferences:
			children = self.discoverChildren(id, resource, originator, request.args.handling, Permission.DELETE)
			self._resourceTreeReferences(children, resource, request.args.drt)	# the function call add attributes to the result resource
			result = resource
		elif request.args.rcn == RCN.childResourceReferences: # child resource references
			children = self.discoverChildren(id, resource, originator, request.args.handling, Permission.DELETE)
			childResourcesRef: dict = { resource.tpe: {} }  # Root resource with no attribute
			self._resourceTreeReferences(children, childResourcesRef[resource.tpe], request.args.drt)
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


	#########################################################################
	#
	#	Internal methods for collecting resources and child resources into structures
	#

	#	Create a m2m:uril structure from a list of resources
	def _resourcesToURIList(self, resources:List[Resource], drt:int) -> dict:
		# cseid = '/' + Configuration.get('cse.csi') + '/'
		cseid = '/%s/' % self.csi
		lst = []
		for r in resources:
			lst.append(Utils.structuredPath(r) if drt == DesiredIdentifierResultType.structured else cseid + r.ri)
		return { 'm2m:uril' : lst }


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


	#########################################################################
	#
	#	Internal methods for ID handling
	#

	def _checkHybridID(self, request:CSERequest, id:str) -> Tuple[str, str]:
		"""	Return a corrected ID and SRN in case this is a hybrid ID.
			srn might be None. 
			Returns: (srn, id)
		"""
		if id is not None:
			return Utils.srnFromHybrid(None, id) # Hybrid
		return Utils.srnFromHybrid(request.srn, request.id) # Hybrid

