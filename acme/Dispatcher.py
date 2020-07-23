#
#	Dispatcher.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external and most internal requests are routed
#	through here.
#

import sys, traceback, re
from flask import Request
from typing import Any, List, Tuple, Union
from Logging import Logging
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T
import CSE, Utils
from resources.Resource import Resource


class Dispatcher(object):

	def __init__(self) -> None:
		self.rootPath 			= Configuration.get('http.root')
		self.enableTransit 		= Configuration.get('cse.enableTransitRequests')
		self.spid 				= Configuration.get('cse.spid')
		self.csi 				= Configuration.get('cse.csi')
		self.cseid 				= Configuration.get('cse.ri')
		self.csern				= Configuration.get('cse.rn')
		self.csiLen 			= len(self.csi)
		self.cseidLen 			= len(self.cseid)

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

	def retrieveRequest(self, request: Request, _id: Tuple[str, str, str]) ->  Tuple[Union[Resource, dict], int, str]:
		originator, _, _, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('RETRIEVE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return None, C.rcNotFound, 'missing identifier'

		# handle transit requests
		if CSE.remote.isTransitID(id):
		 	return CSE.remote.handleTransitRetrieveRequest(request, id, originator) if self.enableTransit else (None, C.rcOperationNotAllowed, 'operation not allowed')

		# handle hybrid ids
		srn, id = self._buildSRNFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleRetrieveRequest(request, srn, originator)

		# just a normal retrieve request
		return self.handleRetrieveRequest(request, id, originator)


	def handleRetrieveRequest(self, request: Request, id: str, originator: str) ->  Tuple[Union[Resource, dict], int, str]:
		Logging.logDebug('Handle retrieve resource: %s' % id)

		try:
			attrs, msg = self._getArguments(request, C.opRETRIEVE)
			if attrs is None:
				return None, C.rcBadRequest, msg
			fu 			= attrs.get('fu')
			drt 		= attrs.get('drt')
			handling 	= attrs.get('__handling__')
			conditions 	= attrs.get('__conditons__')
			attributes 	= attrs.get('__attrs__')
			fo 			= attrs.get('fo')
			rcn 		= attrs.get('rcn')
		except Exception as e:
			#Logging.logWarn('Exception: %s' % traceback.format_exc())
			return None, C.rcInvalidArguments, 'invalid arguments (%s)' % str(e)

		operation = C.permDISCOVERY if fu == 1 else C.permRETRIEVE

		# check rcn & operation
		if operation == C.permDISCOVERY and rcn not in [ C.rcnDiscoveryResultReferences, C.rcnChildResourceReferences ]:	# Only allow those two
			return None, C.rcBadRequest, 'invalid rcn: %d for fu: %d' % (rcn, fu)
		if operation == C.permRETRIEVE and rcn not in [ C.rcnAttributes, C.rcnAttributesAndChildResources, C.rcnChildResources, C.rcnAttributesAndChildResourceReferences, C.rcnChildResourceReferences]: # TODO
			return None, C.rcBadRequest, 'invalid rcn: %d for fu: %d' % (rcn, fu)

		Logging.logDebug('Discover/Retrieve resources (fu: %d, drt: %s, handling: %s, conditions: %s, resultContent: %d, attributes: %s)' % (fu, drt, handling, conditions, rcn, str(attributes)))


		# Retrieve the target resource, because it is needed for some rcn (and the default)
		if rcn in [C.rcnAttributes, C.rcnAttributesAndChildResources, C.rcnChildResources, C.rcnAttributesAndChildResourceReferences]:
			if (res := self.retrieveResource(id))[0] is None:
			 	return res
			if not CSE.security.hasAccess(originator, res[0], operation):
				return None, C.rcOriginatorHasNoPrivilege, 'originator has no permission (%d)' % operation

			# if rcn == attributes then we can return here
			if rcn == C.rcnAttributes:
				return res
			resource = res[0]	# root resource for the retrieval/discovery

		# do discovery
		if (res := self.discoverResources(id, originator, handling, fo, conditions, attributes, operation=operation))[0] is None:	# not found?
			return res

		# check and filter by ACP. After this allowedResources only contains the resources that are allowed
		allowedResources = []
		for r in res[0]:
			if CSE.security.hasAccess(originator, r, operation):
				allowedResources.append(r)

		#
		#	Handle more sophisticated RCN
		#

		if rcn == C.rcnAttributesAndChildResources:
			self._resourceTreeJSON(allowedResources, resource)	# the function call add attributes to the target resource
			return resource, C.rcOK, None

		elif rcn == C.rcnAttributesAndChildResourceReferences:
			self._resourceTreeReferences(allowedResources, resource, drt)	# the function call add attributes to the target resource
			return resource, C.rcOK, None

		elif rcn == C.rcnChildResourceReferences: 
			#childResourcesRef: dict  = { resource.tpe: {} }  # Root resource as a dict with no attribute
			childResourcesRef = self._resourceTreeReferences(allowedResources,  None, drt)
			return childResourcesRef, C.rcOK, None

		elif rcn == C.rcnChildResources:
			childResources: dict = { resource.tpe : {} } #  Root resource as a dict with no attribute
			self._resourceTreeJSON(allowedResources, childResources[resource.tpe]) # Adding just child resources
			return childResources, C.rcOK, None

		elif rcn == C.rcnDiscoveryResultReferences: # URIList
			return self._resourcesToURIList(allowedResources, drt), C.rcOK, None

		else:
			return None, C.rcBadRequest, 'wrong rcn for RETRIEVE'






		# if fu == 1 and rcn !=  C.rcnAttributes:	# discovery. rcn == Attributes is actually "normal retrieval"
		# 	Logging.logDebug('Discover resources (fu: %s, drt: %s, handling: %s, conditions: %s, resultContent: %d, attributes: %s)' % (fu, drt, handling, conditions, rcn, str(attributes)))

		# 	if rcn not in [C.rcnDiscoveryResultReferences, C.rcnAttributesAndChildResourceReferences, C.rcnChildResourceReferences, C.rcnChildResources, C.rcnAttributesAndChildResources]:	# Only allow those two
		# 		return None, C.rcInvalidArguments, 'invalid arguments for rcn'

		# 	# do discovery
		# 	rs, _, msg = self.discoverResources(id, originator, handling, fo, conditions, attributes)

		# 	if rs is not None:
	
		# 		# check and filter by ACP
		# 		allowedResources = []
		# 		for r in rs:
		# 			if CSE.security.hasAccess(originator, r, C.permDISCOVERY):
		# 				allowedResources.append(r)

		# 		if rcn == C.rcnChildResourceReferences: # child resource references
		# 			return self._resourceTreeReferences(allowedResources, None, drt), C.rcOK, None
		# 		elif rcn == C.rcnDiscoveryResultReferences: # URIList
		# 			return self._resourcesToURIList(allowedResources, drt), C.rcOK, None
		# 		# quiet strange for discovery, since children might not be direct descendants...
		# 		elif rcn == C.rcnAttributesAndChildResourceReferences: 
		# 			resource, res, msg = self.retrieveResource(id)
		# 			if resource is None:
		# 				return None, res, msg
		# 			return self._resourceTreeReferences(allowedResources, resource, drt), C.rcOK, None	# the function call add attributes to the result resource

		# 		# resource and child resources, full attributes
		# 		elif rcn == C.rcnAttributesAndChildResources:
		# 			targetResource, res, msg = self.retrieveResource(id)
		# 			if targetResource is None:
		# 				return None, res, msg
		# 			self._childResourceTree(allowedResources, targetResource)	# the function call add attributes to the result resource. Don't use the return value directly
		# 			return targetResource, C.rcOK, None

		# 		# direct child resources, NOT the root resource
		# 		elif rcn == C.rcnChildResources:
		# 			target: dict = { }			# empty 
		# 			self._resourceTreeJSON(allowedResources, target)
		# 			return target, C.rcOK, None
		# 			# return (self._childResources(allowedResources), C.rcOK)

		# 	return None, C.rcNotFound, 'resource not found'

		# elif fu == 2 or rcn == C.rcnAttributes:	# normal retrieval
		# 	Logging.logDebug('Get resource: %s' % id)
		# 	resource, res, msg = self.retrieveResource(id)
		# 	if resource is None:
		# 		return None, res, msg
		# 	if not CSE.security.hasAccess(originator, resource, C.permRETRIEVE):
		# 		return None, C.rcOriginatorHasNoPrivilege, 'originator has no RETRIEVE permissions'

		# 	if rcn == C.rcnAttributes:	# Just the resource & attributes
		# 		return resource, res, msg

		# 	children = self.discoverChildren(id, resource, originator, handling)

		# 	# Handle more sophisticated result content types
		# 	if rcn == C.rcnAttributesAndChildResources:
		# 		self._resourceTreeJSON(children, resource)	# the function call add attributes to the result resource
		# 		return resource, C.rcOK, None

		# 	elif rcn == C.rcnAttributesAndChildResourceReferences:
		# 		self._resourceTreeReferences(children, resource, drt)	# the function call add attributes to the result resource
		# 		return resource, C.rcOK, None
		# 	elif rcn == C.rcnChildResourceReferences: # child resource references
		# 		childResourcesRef: dict  = { resource.tpe: {} }  # Root resource as a dict with no attribute
		# 		self._resourceTreeReferences(children,  childResourcesRef[resource.tpe], drt)
		# 		return childResourcesRef, C.rcOK, None
		# 	# direct child resources, NOT the root resource
		# 	elif rcn == C.rcnChildResources:
		# 		childResources: dict = { resource.tpe : {} } #  Root resource as a dict with no attribute
		# 		self._resourceTreeJSON(children, childResources[resource.tpe]) # Adding just child resources
		# 		return childResources, C.rcOK, None
		# 	else:
		# 		return None, C.rcBadRequest, 'wrong rcn for RETRIEVE'
		# 	# TODO check rcn. Allowed only 1, 4, 5, 6, 7, 8 . 1= as now. If 4,5 check lim etc


		# else:
		# 	return None, C.rcInvalidArguments, 'unknown filter usage (fu)'


	def retrieveResource(self, id: str = None) -> Tuple[Resource, int, str]:
		return self._retrieveResource(srn=id) if Utils.isStructured(id) else self._retrieveResource(ri=id)


	def _retrieveResource(self, ri: str = None, srn: str = None) -> Tuple[Resource, int, str]:
		Logging.logDebug('Retrieve resource: %s' % (ri if srn is None else srn))

		if ri is not None:
			r, rc, msg = CSE.storage.retrieveResource(ri=ri)		# retrieve via normal ID
		elif srn is not None:
			r, rc, msg = CSE.storage.retrieveResource(srn=srn) 	# retrieve via srn. Try to retrieve by srn (cases of ACPs created for AE and CSR by default)
		else:
			return None, C.rcNotFound, 'resource not found'

		if r is not None:
			# Check for virtual resource
			if r.ty != T.GRP_FOPT and Utils.isVirtualResource(r): # fopt is handled elsewhere
				return r.handleRetrieveRequest()
			return r, C.rcOK, None
		if msg is not None:
			Logging.logDebug('%s: %s' % (msg, ri))
		return None, rc, msg


	#########################################################################

	#
	#	Discover Resources
	#


	# def discoverResources(self, id, handling, fo, conditions=None, attributes=None, rootResource=None):
	# 	if rootResource is None:
	# 		(rootResource, _) = self.retrieveResource(id)
	# 		if rootResource is None:
	# 			return (None, C.rcNotFound)
	# 	return (CSE.storage.discoverResources(rootResource, handling, conditions, attributes, fo), C.rcOK)

	def discoverResources(self, id: str, originator: str, handling: dict, fo: int = 1, conditions: dict = None, attributes: dict = None, rootResource: Resource = None, operation:int=C.permDISCOVERY) -> Tuple[List[Resource], int, str]:
		if rootResource is None:
			rootResource, _, msg = self.retrieveResource(id)
			if rootResource is None:
				return None, C.rcNotFound, msg

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
				if (res := self.retrieveResource(srn))[0] is not None:
					if CSE.security.hasAccess(originator, res[0], operation):
						result.append(res[0])
			discoveredResources = result	

		return discoveredResources, C.rcOK, None

		# return CSE.storage.discoverResources(rootResource, handling, conditions, attributes, fo), C.rcOK


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
			if self._matchResource(r, conditions, attributes, fo, allLen) and CSE.security.hasAccess(originator, r, C.permDISCOVERY):
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
		if not ((fo == C.foOR  and found > 0) or 		# OR and found something
				(fo == C.foAND and allLen == found)		# AND and found everything
			   ): 
			return False

		return True


	#########################################################################

	#
	#	Add resources
	#

	def createRequest(self, request: Request, _id: Tuple[str, str, str]) -> Tuple[Union[Resource, dict], int, str]:
		originator, ct, ty, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('CREATE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return None, C.rcNotFound, 'missing identifier'

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitCreateRequest(request, id, originator, ty) if self.enableTransit else (None, C.rcOperationNotAllowed, 'operation not allowed')

		# handle hybrid id
		srn, id = self._buildSRNFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleCreateRequest(request, srn, originator, ct, ty)

		# just a normal create request
		return self.handleCreateRequest(request, id, originator, ct, ty)



	def handleCreateRequest(self, request: Request, id: str, originator: str, ct: str, ty: T) -> Tuple[Union[Resource, dict], int, str]:
		Logging.logDebug('Adding new resource')

		try:
			attrs, msg = self._getArguments(request, C.opCREATE)
			if attrs is None:
				return None, C.rcBadRequest, msg
			rcn   = attrs.get('rcn')
		except Exception as e:
			return None, C.rcInvalidArguments, str(e)

		if ct == None or ty == None:
			return None, C.rcBadRequest, 'ct or ty is missing in request'

		# CSEBase creation, return immediately
		if ty == T.CSEBase:
			return None, C.rcOperationNotAllowed, 'operation not allowed'

		# Get parent resource and check permissions
		pr, res, msg = self.retrieveResource(id)
		if pr is None:
			Logging.log('Parent resource not found')
			return None, C.rcNotFound,  'parent resource not found'
		if CSE.security.hasAccess(originator, pr, C.permCREATE, ty=ty, isCreateRequest=True, parentResource=pr) == False:
			if ty == T.AE:
				return None, C.rcSecurityAssociationRequired, 'security association required'
			else:
				return None, C.rcOriginatorHasNoPrivilege, 'originator has no privileges'

		# Check for virtual resource
		if Utils.isVirtualResource(pr):
			return pr.handleCreateRequest(request, id, originator, ct, ty)

		# Add new resource
		try:
			nr, msg = Utils.resourceFromJSON(request.json, pi=pr.ri, ty=ty)
			if nr is None:	# something wrong, perhaps wrong type
				return None, C.rcBadRequest, msg
		except Exception as e:
			Logging.logWarn('Bad request (malformed content?)')
			return None, C.rcBadRequest, str(e)

		# Check whether the parent allows the adding
		if not (cres := pr.childWillBeAdded(nr, originator))[0]:
			return None, cres[1], cres[2]

		# check whether the resource already exists
		if CSE.storage.hasResource(nr.ri, nr.__srn__):
			Logging.logWarn('Resource already registered')
			return None, C.rcConflict, 'resource already exists'

		# Check resource creation
		if (rres := CSE.registration.checkResourceCreation(nr, originator, pr))[1] != C.rcOK:
			return None, rres[1], rres[2]
		originator = rres[0]

		# Create the resource. If this fails we register everything
		if (result := self.createResource(nr, pr, originator))[0] is None:
			CSE.registration.checkResourceDeletion(nr, originator) # deregister resource. Ignore result, we take this from the creation
			return result

		#
		# Handle RCN's
		#

		tpe = result[0].tpe
		if rcn is None or rcn == C.rcnAttributes:	# Just the resource & attributes
			return result
		elif rcn == C.rcnModifiedAttributes:
			jsonOrg =request.json[tpe]
			jsonNew = result[0].asJSON()[tpe]
			return { tpe : Utils.resourceDiff(jsonOrg, jsonNew) }, result[1], result[2]
		elif rcn == C.rcnHierarchicalAddress:
			return { 'm2m:uri' : Utils.structuredPath(result[0]) }, result[1], result[2]
		elif rcn == C.rcnHierarchicalAddressAttributes:
			return { 'm2m:rce' : { Utils.noDomain(tpe) : result[0].asJSON()[tpe], 'uri' : Utils.structuredPath(result[0]) }}, result[1], result[2]
		elif rcn == C.rcnNothing:
			return None, result[1], result[2]
		else:
			return None, C.rcBadRequest, 'wrong rcn for CREATE'
		# TODO C.rcnDiscoveryResultReferences 


	def createResource(self, resource : Resource, parentResource : Resource = None, originator : str = None) -> Tuple[Resource, int, str]:
		Logging.logDebug('Adding resource ri: %s, type: %d' % (resource.ri, resource.ty))

		if parentResource is not None:
			Logging.logDebug('Parent ri: %s' % parentResource.ri)
			if not parentResource.canHaveChild(resource):
				if resource.ty == T.SUB:
					err = 'Parent resource is not subscribable'
					Logging.logWarn(err)
					return None, C.rcTargetNotSubscribable, err
				else:
					err = 'Invalid child resource type'
					Logging.logWarn(err)
					return None, C.rcInvalidChildResourceType, err

		# if not already set: determine and add the srn
		if resource.__srn__ is None:
			resource[resource._srn] = Utils.structuredPath(resource)

		# add the resource to storage
		if (res := resource.dbCreate(overwrite=False))[1] != C.rcCreated:
			return None, res[1], res[2]

		# Activate the resource
		# This is done *after* writing it to the DB, because in activate the resource might create or access other
		# resources that will try to read the resource from the DB.
		if not (res := resource.activate(parentResource, originator))[0]: 	# activate the new resource
			resource.dbDelete()
			return None, res[1], res[2]

		# Could be that we changed the resource in the activate, therefore write it again
		if (dres := resource.dbUpdate())[0] is None:
			resource.dbDelete()
			return dres

		if parentResource is not None:
			parentResource, _, _ = parentResource.dbReload()				# Read the resource again in case it was updated in the DB
			parentResource.childAdded(resource, originator)			# notify the parent resource

		# send a create event
		CSE.event.createResource(resource)	# type: ignore

		return resource, C.rcCreated, None 	# everything is fine. resource created.


	#########################################################################

	#
	#	Update resources
	#

	def updateRequest(self, request: Request, _id: Tuple[str, str, str]) -> Tuple[Union[Resource, dict], int, str]:
		originator, ct, _, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('UPDATE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return None, C.rcNotFound, 'missing identifier'

		# ID= cse.if, return immediately
		if id == self.cseid:
			return None, C.rcOperationNotAllowed, 'operation not allowed for CSEBase'

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitUpdateRequest(request, id, originator) if self.enableTransit else (None, C.rcOperationNotAllowed, 'operation not allowed')

		# handle hybrid id
		srn, id = self._buildSRNFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleUpdateRequest(request, srn, originator, ct)

		# just a normal update request
		return self.handleUpdateRequest(request, id, originator, ct)


	def handleUpdateRequest(self, request: Request, id: str, originator: str, ct: str) -> Tuple[Union[Resource, dict], int, str]: 

		# get arguments
		try:
			attrs, msg = self._getArguments(request, C.opUPDATE)
			if attrs is None:
				return None, C.rcBadRequest, msg
			rcn   = attrs.get('rcn')
		except Exception as e:
			return None, C.rcInvalidArguments, str(e)

		Logging.logDebug('Updating resource')
		if ct == None:
			return None, C.rcBadRequest, 'missing content type'

		# Get resource to update
		r, _, msg = self.retrieveResource(id)	
		if r is None:
			Logging.log('Resource not found')
			return None, C.rcNotFound, msg
		if r.readOnly:
			return None, C.rcOperationNotAllowed, 'resource is read-only'

		# check permissions
		try:
			jsn = request.json
		except Exception as e:
			Logging.logWarn('Bad request (malformed content?)')
			return None, C.rcBadRequest, str(e)

		acpi = Utils.findXPath(jsn, list(jsn.keys())[0] + '/acpi')
		if acpi is not None:	# update of acpi attribute means check for self privileges!
			updateOrDelete = C.permDELETE if acpi is None else C.permUPDATE
			if CSE.security.hasAccess(originator, r, updateOrDelete, checkSelf=True) == False:
				return None, C.rcOriginatorHasNoPrivilege, 'originator has no privileges'
		elif CSE.security.hasAccess(originator, r, C.permUPDATE) == False:
			return None, C.rcOriginatorHasNoPrivilege, 'originator has no privileges'

		# Check for virtual resource
		if Utils.isVirtualResource(r):
			return r.handleUpdateRequest(request, id, originator, ct)

		jsonOrg = r.json.copy()	# Save for later
		if (result := self.updateResource(r, jsn, originator=originator))[0] is None:
			return None, result[1], result[2]
		r, rc, msg = result

		#
		# Handle RCN's
		#

		tpe = r.tpe
		if rcn is None or rcn == C.rcnAttributes:
			return result
		elif rcn == C.rcnModifiedAttributes:
			jsonNew = r.json.copy()	
			return { tpe : Utils.resourceDiff(jsonOrg, jsonNew) }, result[1], None
		elif rcn == C.rcnNothing:
			return None, result[1], None
		# TODO C.rcnDiscoveryResultReferences 
		else:
			return None, C.rcBadRequest, 'wrong rcn for UPDATE'


	def updateResource(self, resource:Resource, json: dict = None, doUpdateCheck: bool = True, originator:str = None) -> Tuple[Resource, int, str]:
		Logging.logDebug('Updating resource ri: %s, type: %d' % (resource.ri, resource.ty))
		if doUpdateCheck:
			if not (res := resource.update(json, originator))[0]:
				return None, res[1], res[2]
		else:
			Logging.logDebug('No check, skipping resource update')

		# send a create event
		CSE.event.updateResource(resource)		# type: ignore
		return resource.dbUpdate()


	#########################################################################

	#
	#	Remove resources
	#

	def deleteRequest(self, request: Request, _id: Tuple[str, str, str]) -> Tuple[Union[Resource, dict], int, str]:
		originator, _, _, _, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('DELETE ID: %s, originator: %s' % (id if id is not None else srn, originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return None, C.rcNotFound, 'missing identifier'

		# ID= cse.if, return immediately
		if id == self.cseid:
			return None, C.rcOperationNotAllowed, 'operation not allowed for CSEBase'

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitDeleteRequest(id, originator) if self.enableTransit else (None, C.rcOperationNotAllowed, 'operation not allowed')

		# handle hybrid id
		srn, id = self._buildSRNFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleDeleteRequest(request, srn, originator)

		# just a normal delete request
		return self.handleDeleteRequest(request, id, originator)


	def handleDeleteRequest(self, request: Request, id: str, originator: str) -> Tuple[Resource, int, str]:
		Logging.logDebug('Removing resource')

		# get arguments
		try:
			attrs, msg = self._getArguments(request, C.opDELETE)
			if attrs is None:
				return None, C.rcBadRequest, msg
			rcn  		= attrs.get('rcn')
			drt 		= attrs.get('drt')
			handling 	= attrs.get('__handling__')
		except Exception as e:
			return None, C.rcInvalidArguments, str(e)

		# get resource to be removed and check permissions
		resource, _, msg = self.retrieveResource(id)
		if resource is None:
			Logging.logDebug('Resource not found')
			return None, C.rcNotFound, msg

		if CSE.security.hasAccess(originator, resource, C.permDELETE) == False:
			return None, C.rcOriginatorHasNoPrivilege, 'originator has no privileges'

		# Check for virtual resource
		if Utils.isVirtualResource(resource):
			return resource.handleDeleteRequest(request, id, originator)

		#
		# Handle RCN's first. Afterward the resource & children are no more
		#

		tpe = resource.tpe
		result: Any = None
		if rcn is None or rcn == C.rcnNothing:
			result = None
		elif rcn == C.rcnAttributes:
			result = resource
		# resource and child resources, full attributes
		elif rcn == C.rcnAttributesAndChildResources:
			children = self.discoverChildren(id, resource, originator, handling, C.permDELETE)
			self._childResourceTree(children, resource)	# the function call add attributes to the result resource. Don't use the return value directly
			result = resource
		# direct child resources, NOT the root resource
		elif rcn == C.rcnChildResources:
			children = self.discoverChildren(id, resource, originator, handling, c.permDELETE)
			childResources: dict = { resource.tpe : {} }			# Root resource as a dict with no attributes
			self._resourceTreeJSON(children, childResources[resource.tpe])
			result = childResources
		elif rcn == C.rcnAttributesAndChildResourceReferences:
			children = self.discoverChildren(id, resource, originator, handling, c.permDELETE)
			self._resourceTreeReferences(children, resource, drt)	# the function call add attributes to the result resource
			result = resource
		elif rcn == C.rcnChildResourceReferences: # child resource references
			children = self.discoverChildren(id, resource, originator, handling, c.permDELETE)
			childResourcesRef: dict = { resource.tpe: {} }  # Root resource with no attribute
			self._resourceTreeReferences(children, childResourcesRef[resource.tpe], drt)
			result = childResourcesRef
		# TODO C.rcnDiscoveryResultReferences
		else:
			return None, C.rcBadRequest, 'wrong rcn for DELETE'

		# remove resource
		ret = self.deleteResource(resource, originator, withDeregistration=True)
		return result, ret[1], ret[2]


	def deleteResource(self, resource: Resource, originator: str = None, withDeregistration: bool = False) -> Tuple[Resource, int, str]:
		Logging.logDebug('Removing resource ri: %s, type: %d' % (resource.ri, resource.ty))
		# if resource is None:
		# 	Logging.log('Resource not found')

		# Check resource deletion
		if withDeregistration:
			if not (res := CSE.registration.checkResourceDeletion(resource, originator))[0]:
				return None, C.rcBadRequest, res[2]

		resource.deactivate(originator)	# deactivate it first
		# notify the parent resource
		parentResource = resource.retrieveParentResource()
		_, rc, msg = resource.dbDelete()

		# send a delete event
		CSE.event.deleteResource(resource) 	# type: ignore

		if parentResource is not None:
			parentResource.childRemoved(resource, originator)
		return resource, rc, msg

	#########################################################################

	#
	#	Utility methods
	#

	def directChildResources(self, pi: str, ty: T = None) -> list:
		""" Return all child resources of resources. """
		return CSE.storage.directChildResources(pi, ty)


	def discoverChildren(self, id:str, resource:Resource, originator:str, handling:dict, operation:int) -> List[Resource]:
		rs, rc, _ = self.discoverResources(id, originator, handling, rootResource=resource, operation=operation)
		if rs is  None:
			return None
		# check and filter by ACP
		children = []
		for r in rs:
			if CSE.security.hasAccess(originator, r, operation):
				children.append(r)
		return children


	def countResources(self) -> int:
		""" Get total number of resources. """
		return CSE.storage.countResources()


	def retrieveResourcesByType(self, ty:T) -> List[Resource]:
		""" Retrieve all resources of a type. """
		# return CSE.storage.retrieveResourcesByType(ty)

		result = []
		rss = CSE.storage.retrieveResourcesByType(ty)
		for rs in (rss or []):
			r, _ = Utils.resourceFromJSON(rs)
			result.append(r)
		return result



	def _buildSRNFromHybrid(self, srn: str, id: str) -> Tuple[str, str]:
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
	def _getArguments(self, request: Request, operation: int = C.opRETRIEVE) -> Tuple[dict, str]:
		result: dict = { }

		# copy for greedy attributes checking
		args = request.args.copy()	 	# type: ignore

		# basic attributes
		if (fu := args.get('fu')) is not None:
			if not CSE.validator.validateRequestArgument('fu', fu)[0]:
				return None, 'error validating "fu" argument'
			fu = int(fu)
			del args['fu']
		else:
			fu = C.fuConditionalRetrieval
		if fu == C.fuDiscoveryCriteria and operation == C.opRETRIEVE:
			operation = C.opDISCOVERY
		result['fu'] = fu


		if (drt := args.get('drt')) is not None: # 1=strucured, 2=unstructured
			if not CSE.validator.validateRequestArgument('drt', drt)[0]:
				return None, 'error validating "drt" argument'
			drt = int(drt)
			del args['drt']
		else:
			drt = C.drtStructured
		result['drt'] = drt

		if (rcn := args.get('rcn')) is not None: 
			if not CSE.validator.validateRequestArgument('rcn', rcn)[0]:
				return None, 'error validating "rcn" argument'
			rcn = int(rcn)
			del args['rcn']
		else:
			if fu != C.fuDiscoveryCriteria:
				# Different defaults for each operation
				if operation in [ C.opRETRIEVE, C.opCREATE, C.opUPDATE ]:
					rcn = C.rcnAttributes
				elif operation == C.opDELETE:
					rcn = C.rcnNothing
			else:
				# discovery-result-references as default for Discovery operation
				rcn = C.rcnDiscoveryResultReferences

		# Check value of rcn depending on operation
		if operation == C.opRETRIEVE and rcn not in [ C.rcnAttributes,
													  C.rcnAttributesAndChildResources,
													  C.rcnAttributesAndChildResourceReferences,
													  C.rcnChildResourceReferences,
													  C.rcnChildResources ]:
			return None, 'rcn: %d not allowed in RETRIEVE operation' % rcn
		elif operation == C.opDISCOVERY and rcn not in [ C.rcnChildResourceReferences,
														 C.rcnDiscoveryResultReferences,
														 C.rcnAttributesAndChildResourceReferences,
													 	 C.rcnAttributesAndChildResources,
														 C.rcnChildResources ]:
			return None, 'rcn: %d not allowed in DISCOVERY operation' % rcn
		elif operation == C.opCREATE and rcn not in [ C.rcnAttributes,
													  C.rcnModifiedAttributes,
													  C.rcnHierarchicalAddress,
													  C.rcnHierarchicalAddressAttributes,
													  C.rcnNothing ]:
			return None, 'rcn: %d not allowed in CREATE operation' % rcn
		elif operation == C.opUPDATE and rcn not in [ C.rcnAttributes,
													  C.rcnModifiedAttributes,
													  C.rcnNothing ]:
			return None, 'rcn: %d not allowed in UPDATE operation' % rcn
		elif operation == C.opDELETE and rcn not in [ C.rcnAttributes,
													  C.rcnNothing,
													  C.rcnAttributesAndChildResources,
													  C.rcnChildResources,
													  C.rcnAttributesAndChildResourceReferences,
													  C.rcnChildResourceReferences ]:
			return None, 'rcn: %d not allowed DELETE operation' % rcn

		result['rcn'] = rcn


		# handling conditions
		handling = { }
		for c in ['lim', 'lvl', 'ofst']:	# integer parameters
			if c in args:
				v = args[c]
				if not CSE.validator.validateRequestArgument(c, v)[0]:
					return None, 'error validating "%s" argument' % c
				handling[c] = int(v)
				del args[c]
		for c in ['arp']:
			if c in args:
				v = args[c]
				if not CSE.validator.validateRequestArgument(c, v)[0]:
					return None, 'error validating "%s" argument' % c
				handling[c] = v # string
				del args[c]
		result['__handling__'] = handling


		# conditions
		conditions = {}

		# Extract and store other arguments
		for c in ['crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr']:
			if (v := args.get(c)) is not None:
				if not CSE.validator.validateRequestArgument(c, v)[0]:
					return None, 'error validating "%s" argument' % c
				conditions[c] = v
				del args[c]

		# get types (multi). Always create at least an empty list
		conditions['ty'] = []
		for e in args.getlist('ty'):
			for es in (t := e.split()):	# check for number
				if not CSE.validator.validateRequestArgument('ty', es)[0]:
					return None, 'error validating "ty" argument(s)'
			conditions['ty'].extend(t)
		args.poplist('ty')

		# get contentTypes (multi). Always create at least an empty list
		conditions['cty'] = []
		for e in args.getlist('cty'):
			for es in (t := e.split()):	# check for number
				if not CSE.validator.validateRequestArgument('cty', es)[0]:
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

		# filter operation
		if (fo := args.get('fo')) is not None: # 1=AND, 2=OR
			if not CSE.validator.validateRequestArgument('fo', fo)[0]:
				return None, 'error validating "fo" argument'
			fo = int(fo)
			del args['fo']
		else:
			fo = 1 # default
		result['fo'] = fo

		# all remaining arguments are treated as matching attributes
		for arg, val in args.items():
			if not CSE.validator.validateRequestArgument(arg, val)[0]:
				return None, 'error validating "%s" argument)' % arg

		# all arguments have passed, so add them
		result['__attrs__'] = args

		return result, None


	#	Create a m2m:uril structure from a list of resources
	def _resourcesToURIList(self, resources: List[Resource], drt: int) -> dict:
		# cseid = '/' + Configuration.get('cse.csi') + '/'
		cseid = '/%s/' % self.csi
		lst = []
		for r in resources:
			lst.append(Utils.structuredPath(r) if drt == C.drtStructured else cseid + r.ri)
		return { 'm2m:uril' : lst }


	# def _attributesAndChildResources(self, parentResource, resources):
	# 	result = parentResource.asJSON()
	# 	ch = []
	# 	for r in resources:
	# 		ch.append(r.asJSON(embedded=False))
	# 	result[parentResource.tpe]['ch'] = ch
	# 	return result

	# Recursively walk the results and build a sub-resource tree for each resource type
	def _resourceTreeJSON(self, resources: List[Resource], targetResource: Union[Resource, dict]) -> List[Resource]:
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


	def _resourceTreeReferences(self, resources: List[Resource], targetResource: Union[Resource, dict], drt: int) -> Union[Resource, dict]:
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
			ref = { 'nm' : r['rn'], 'typ' : r['ty'], 'val' :  Utils.structuredPath(r) if drt == C.drtStructured else r.ri}
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

