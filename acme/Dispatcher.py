#
#	Dispatcher.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external and most internal requests are routed
#	through here.
#

from Logging import Logging
from Configuration import Configuration
from Constants import Constants as C
import CSE, Utils


class Dispatcher(object):

	def __init__(self):
		self.rootPath 		= Configuration.get('http.root')
		self.enableTransit 	= Configuration.get('cse.enableTransitRequests')
		Logging.log('Dispatcher initialized')


	def shutdown(self):
		Logging.log('Dispatcher shut down')



	# The "xxxRequest" methods handle http requests while the "xxxResource"
	# methods handle actions on the resources. Security/permission checking
	# is done for requests, not on resource actions.

	#
	#	Retrieve resources
	#

	def retrieveRequest(self, request):
		(originator, _, _, _, _) = Utils.getRequestHeaders(request)
		id = Utils.requestID(request, self.rootPath)
		Logging.logDebug('ID: %s, originator: %s' % (id, originator))

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitRetrieveRequest(request, id, originator) if self.enableTransit else (None, C.rcOperationNotAllowed)

		# handle fanoutPoint requests
		if (fanoutPointResource := Utils.fanoutPointResource(id)) is not None and fanoutPointResource.ty == C.tGRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.retrieveRequest(request, id, originator)

		# just a normal retrieve request
		return self.handleRetrieveRequest(request, id, originator)


	def handleRetrieveRequest(self, request, id, originator):
		try:
			attrs = self._getArguments(request)
			fu 			= attrs.get('fu')
			drt 		= attrs.get('drt')
			handling 	= attrs.get('__handling__')
			conditions 	= attrs.get('__conditons__')
			attributes 	= attrs.get('__attrs__')
			fo 			= attrs.get('fo')
			rcn 		= attrs.get('rcn')
		except Exception as e:
			return (None, C.rcInvalidArguments)


		if fu == 1 and rcn !=  C.rcnAttributes:	# discovery. rcn == Attributes is actually "normal retrieval"
			Logging.logDebug('Discover resources (fu: %s, drt: %s, handling: %s, conditions: %s, resultContent: %d, attributes: %s)' % (fu, drt, handling, conditions, rcn, str(attributes)))

			if rcn not in [C.rcnAttributesAndChildResourceReferences, C.rcnChildResourceReferences, C.rcnChildResources, C.rcnAttributesAndChildResources]:	# Only allow those two
				return (None, C.rcInvalidArguments)

			# do discovery
			(rs, _) = self.discoverResources(id, handling, conditions, attributes, fo)

			if rs is not None:
	
				# check and filter by ACP
				allowedResources = []
				for r in rs:
					if CSE.security.hasAccess(originator, r, C.permDISCOVERY):
						allowedResources.append(r)

				if rcn == C.rcnChildResourceReferences: # child resource references
					return (self._resourcesToURIList(allowedResources, drt), C.rcOK)	

				# quiet strange for discovery, since children might not be direct descendants...
				elif rcn == C.rcnAttributesAndChildResourceReferences: 
					(resource, res) = self.retrieveResource(id)
					if resource is None:
						return (None, res)
					self._resourceTreeReferences(allowedResources, resource, drt)	# the function call add attributes to the result resource
					return (resource, C.rcOK)

				# resource and child resources, full attributes
				elif rcn == C.rcnAttributesAndChildResources:
					(resource, res) = self.retrieveResource(id)
					if resource is None:
						return (None, res)
					self._childResourceTree(allowedResources, resource)	# the function call add attributes to the result resource
					return (resource, C.rcOK)

				# direct child resources, NOT the root resource
				elif rcn == C.rcnChildResources:
					resource = {  }			# empty 
					self._resourceTreeJSON(allowedResources, resource)
					return (resource, C.rcOK)
					# return (self._childResources(allowedResources), C.rcOK)

			return (None, C.rcNotFound)

		elif fu == 2 or rcn == C.rcnAttributes:	# normal retrieval
			Logging.logDebug('Get resource: %s' % id)
			(resource, res) = self.retrieveResource(id)
			if resource is None:
				return (None, res)
			if not CSE.security.hasAccess(originator, resource, C.permRETRIEVE):
				return (None, C.rcOriginatorHasNoPrivilege)
			if rcn == C.rcnAttributes:	# Just the resource & attributes
				return (resource, res)
			
			(rs, rc) = self.discoverResources(id, handling, rootResource=resource)
			if rs is  None:
				return (None, rc)

			# check and filter by ACP
			result = []
			for r in rs:
				if CSE.security.hasAccess(originator, r, C.permRETRIEVE):
					result.append(r)

			# Handle more sophisticated result content types
			if rcn == C.rcnAttributesAndChildResources:
				self._resourceTreeJSON(result, resource)	# the function call add attributes to the result resource
				return (resource, C.rcOK)

			elif rcn == C.rcnAttributesAndChildResourceReferences:
				self._resourceTreeReferences(result, resource, drt)	# the function call add attributes to the result resource
				return (resource, C.rcOK)
			elif rcn == C.rcnChildResourceReferences: # child resource references
				return (self._resourcesToURIList(result, drt), C.rcOK)

			return (None, C.rcInvalidArguments)
			# TODO check rcn. Allowed only 1, 4, 5 . 1= as now. If 4,5 check lim etc


		else:
			return (None, C.rcInvalidArguments)


	def retrieveResource(self, id):
		Logging.logDebug('Retrieve resource: %s' % id)
		if id is None:
			return (None, C.rcNotFound)
		oid = id
		csi = Configuration.get('cse.csi')
		if '/' in id:

			# when the id is in the format <cse RI>/<resource RI>
			if id.startswith(csi):
				id = id[len(csi)+1:]
				if not '/' in id:
					return self.retrieveResource(id)

			# elif id.startswith('-') or id.startswith('~'):	# remove shortcut (== csi) (Also the ~ makes it om2m compatible)
			if id.startswith('-') or id.startswith('~'):	# remove shortcut (== csi) (Also the ~ makes it om2m compatible)
				id = "%s/%s" % (csi, id[2:])
				return self.retrieveResource(id)

			# Check whether it is Unstructured-CSE-relativeResource-ID
			s = id.split('/')
			if len(s) == 2 and s[0] == Configuration.get('cse.ri'):
				# Logging.logDebug('Resource via Unstructured-CSE-relativeResource-ID')
				r = CSE.storage.retrieveResource(ri=s[1])
			else:
				# Assume it is a Structured-CSE-relativeResource-ID
				# Logging.logDebug('Resource via Structured-CSE-relativeResource-ID')
				r = CSE.storage.retrieveResource(srn=id)

		else: # only the cseid or ri
			if id == csi:
				# SP-relative-CSE-ID
				# Logging.logDebug('Resource via SP-relative-CSE-ID')
				r = CSE.storage.retrieveResource(csi=id)
			else:
				# Unstructured-CSE-relativeResource-ID
				# Logging.logDebug('Resource via Unstructured-CSE-relativeResource-ID')
				r = CSE.storage.retrieveResource(ri=id)
				if r is None:	# special handling for CSE. ID could be ri or srn...
					r = CSE.storage.retrieveResource(srn=id)
		if r is not None:
			return (r, C.rcOK)
		Logging.logDebug('Resource not found: %s' % oid)
		return (None, C.rcNotFound)


	def discoverResources(self, id, handling, conditions=None, attributes=None, fo=None, rootResource=None):
		if rootResource is None:
			(rootResource, _) = self.retrieveResource(id)
			if rootResource is None:
				return (None, C.rcNotFound)
		return (CSE.storage.discoverResources(rootResource, handling, conditions, attributes, fo), C.rcOK)


	#
	#	Add resources
	#

	def createRequest(self, request):
		(originator, ct, ty, _, _) = Utils.getRequestHeaders(request)
		id = Utils.requestID(request, self.rootPath)
		Logging.logDebug('ID: %s, originator: %s' % (id, originator))

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitCreateRequest(request, id, originator, ty) if self.enableTransit else (None, C.rcOperationNotAllowed)

		# handle fanoutPoint requests
		if (fanoutPointResource := Utils.fanoutPointResource(id)) is not None and fanoutPointResource.ty == C.tGRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.createRequest(request, id, originator, ct, ty)

		# just a normal create request
		return self.handleCreateRequest(request, id, originator, ct, ty)



	def handleCreateRequest(self, request, id, originator, ct, ty):
		Logging.logDebug('Adding new resource')

		if ct == None or ty == None:
			return (None, C.rcBadRequest)

		# Check whether the target contains a fanoutPoint in between or as the target
		# TODO: Is this called twice (here + in createRequest)?
		if (fanoutPointResource := Utils.fanoutPointResource(id)) is not None:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.createRequest(request, id, originator, ct, ty)

		# Get parent resource and check permissions
		(pr, res) = self.retrieveResource(id)
		if pr is None:
			Logging.log('Parent resource not found')
			return (None, C.rcNotFound)

		if CSE.security.hasAccess(originator, pr, C.permCREATE, ty=ty, isCreateRequest=True) == False:
			return (None, C.rcOriginatorHasNoPrivilege)

		# Add new resource
		#nr = resourceFromJSON(request.json, pi=pr['ri'], tpe=ty)	# Add pi
		if (nr := Utils.resourceFromJSON(request.json, pi=pr.ri, tpe=ty)) is None:	# something wrong, perhaps wrong type
			return (None, C.rcBadRequest)

		# # determine and add the srn
		# nr[nr._srn] = Utils.structuredPath(nr)

		# check whether the resource already exists
		if CSE.storage.hasResource(nr.ri, nr.__srn__):
			Logging.logWarn('Resource already registered')
			return (None, C.rcAlreadyExists)

		# Check resource creation
		if (res := CSE.registration.checkResourceCreation(nr, originator, pr))[1] != C.rcOK:
			return (None, res[1])
		originator = res[0]

		return self.createResource(nr, pr, originator)


	def createResource(self, resource, parentResource=None, originator=None):
		Logging.logDebug('Adding resource ri: %s, type: %d' % (resource.ri, resource.ty))

		if parentResource is not None:
			Logging.logDebug('Parent ri: %s' % parentResource.ri)
			if not parentResource.canHaveChild(resource):
				Logging.logWarn('Invalid child resource type')
				return (None, C.rcInvalidChildResourceType)

		# if not already set: determine and add the srn
		if resource.__srn__ is None:
			resource[resource._srn] = Utils.structuredPath(resource)

		# add the resource to storage
		if (res := CSE.storage.createResource(resource, overwrite=False))[1] != C.rcCreated:
			return (None, res[1])

		# Activate the resource
		# This is done *after* writing it to the DB, because in activate the resource might create or access other
		# resources that will try to read the resource from the DB.
		if not (res := resource.activate(originator))[0]: 	# activate the new resource
			CSE.storage.deleteResource(resource)
			return res

		# Could be that we changed the resource in the activate, therefore write it again
		if (res := CSE.storage.updateResource(resource))[0] is None:
			CSE.storage.deleteResource(resource)
			return res


		if parentResource is not None:
			parentResource.childAdded(resource, originator)		# notify the parent resource
		CSE.event.createResource(resource)	# send a create event

		return (resource, C.rcCreated) 	# everything is fine. resource created.



	#
	#	Update resources
	#

	def updateRequest(self, request):
		(originator, ct, _, _, _) = Utils.getRequestHeaders(request)
		id = Utils.requestID(request, self.rootPath)
		Logging.logDebug('ID: %s, originator: %s' % (id, originator))

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitUpdateRequest(request, id, originator) if self.enableTransit else (None, C.rcOperationNotAllowed)

		# handle fanoutPoint requests
		if (fanoutPointResource := Utils.fanoutPointResource(id)) is not None and fanoutPointResource.ty == C.tGRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.updateRequest(request, id, originator, ct)

		# just a normal retrieve request
		return self.handleUpdateRequest(request, id, originator, ct)


	def handleUpdateRequest(self, request, id, originator, ct):

		# get arguments
		try:
			attrs = self._getArguments(request)
			rcn   = attrs.get('rcn')
		except Exception as e:
			return (None, C.rcInvalidArguments)

		Logging.logDebug('Updating resource')
		if ct == None:
			return (None, C.rcBadRequest)

		# Get resource to update
		(r, _) = self.retrieveResource(id)	
		if r is None:
			Logging.log('Resource not found')
			return (None, C.rcNotFound)
		if r.readOnly:
			return (None, C.rcOperationNotAllowed)

		# check permissions
		jsn = request.json
		acpi = Utils.findXPath(jsn, list(jsn.keys())[0] + '/acpi')
		if acpi is not None:	# update of acpi attribute means check for self privileges!
			updateOrDelete = C.permDELETE if acpi is None else C.permUPDATE
			if CSE.security.hasAccess(originator, r, updateOrDelete, checkSelf=True) == False:
				return (None, C.rcOriginatorHasNoPrivilege)
		if CSE.security.hasAccess(originator, r, C.permUPDATE) == False:
			return (None, C.rcOriginatorHasNoPrivilege)

		jsonOrg = r.json.copy()
		if (result := self.updateResource(r, jsn, originator=originator))[0] is None:
			return (None, result[1])
		(r, rc) = result

		# only send the diff
		if rcn == C.rcnAttributes:
			return result
		if rcn == C.rcnModifiedAttributes:
			jsonNew = r.json.copy()
			result = { r.tpe : Utils.resourceDiff(jsonOrg, jsonNew) }
			return ( result if rc == C.rcUpdated else None, rc)
		return (None, C.rcNotImplemented)


	def updateResource(self, resource, json=None, doUpdateCheck=True, originator=None):
		Logging.logDebug('Updating resource ri: %s, type: %d' % (resource.ri, resource.ty))
		if doUpdateCheck:
			if not (res := resource.update(json, originator))[0]:
				return (None, res[1])
		else:
			Logging.logDebug('No check, skipping resource update')

		return CSE.storage.updateResource(resource)



	#
	#	Remove resources
	#

	def deleteRequest(self, request):
		(originator, _, _, _, _) = Utils.getRequestHeaders(request)
		id = Utils.requestID(request, self.rootPath)
		Logging.logDebug('ID: %s, originator: %s' % (id, originator))

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitDeleteRequest(id, originator) if self.enableTransit else (None, C.rcOperationNotAllowed)

		# handle fanoutPoint requests
		if (fanoutPointResource := Utils.fanoutPointResource(id)) is not None and fanoutPointResource.ty == C.tGRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.deleteRequest(request, id, originator)

		# just a normal delete request
		return self.handleDeleteRequest(request, id, originator)


	def handleDeleteRequest(self, request, id, originator):
		Logging.logDebug('Removing resource')

		# get resource to be removed and check permissions
		(r, _) = self.retrieveResource(id)
		if r is None:
			Logging.logDebug('Resource not found')
			return (None, C.rcNotFound)
		# if r.readOnly:
		# 	return (None, C.rcOperationNotAllowed)
		if CSE.security.hasAccess(originator, r, C.permDELETE) == False:
			return (None, C.rcOriginatorHasNoPrivilege)

		# Check resource deletion
		if not (res := CSE.registration.checkResourceDeletion(r, originator))[0]:
			return (None, C.rcBadRequest)

		# remove resource
		return self.deleteResource(r, originator)


	def deleteResource(self, resource, originator=None):
		Logging.logDebug('Removing resource ri: %s, type: %d' % (resource.ri, resource.ty))
		if resource is None:
			Logging.log('Resource not found')
		resource.deactivate(originator)	# deactivate it first
		# notify the parent resource
		parentResource = resource.retrieveParentResource()
		# (parentResource, _) = self.retrieveResource(resource['pi'])
		(_, rc) = CSE.storage.deleteResource(resource)
		CSE.event.deleteResource(resource)	# send a delete event
		if parentResource is not None:
			parentResource.childRemoved(resource, originator)
		return (resource, rc)


	#
	#	Utility methods
	#

	def subResources(self, pi, ty=None):
		return CSE.storage.subResources(pi, ty)


	def countResources(self):
		return CSE.storage.countResources()


	# All resources of a type
	def retrieveResourcesByType(self, ty):
		return CSE.storage.retrieveResource(ty=ty)


	#########################################################################

	#
	#	Internal methods
	#



	# Get the request arguments, or meaningful defaults.
	# Only a small subset is supported yet
	def _getArguments(self, request):
		result = { }

		args = request.args.copy()	# copy for greedy attributes checking 

		# basic attributes
		if (fu := args.get('fu')) is not None:
			fu = int(fu)
			del args['fu']
		else:
			fu = C.fuConditionalRetrieval
		result['fu'] = fu


		if (drt := args.get('drt')) is not None: # 1=strucured, 2=unstructured
			drt = int(drt)
			del args['drt']
		else:
			drt = C.drtStructured
		result['drt'] = drt

		if (rcn := args.get('rcn')) is not None: 
			rcn = int(rcn)
			del args['rcn']
		else:
			rcn = C.rcnAttributes if fu == C.fuConditionalRetrieval else C.rcnChildResourceReferences
		result['rcn'] = rcn

		# handling conditions
		handling = {}
		for c in ['lim', 'lvl', 'ofst']:	# integer parameters
			if c in args:
				handling[c] = int(args[c])
				del args[c]
		for c in ['arp']:
			if c in args:
				handling[c] = args[c]
				del args[c]
		result['__handling__'] = handling


		# conditions
		conditions = {}

		# TODO Check ty multiple times. Then -> "ty" : array?
		# also contentType 
		# Extra dictionary! as in attributes


		for c in ['crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbl', 'lbq', 'sza', 'szb', 'catr', 'patr']:
			if (x:= args.get(c)) is not None:
				conditions[c] = x
				del args[c]

		# get types (multi)
		conditions['ty'] = args.getlist('ty')
		args.poplist('ty')

		# get contentTypes (multi)
		conditions['cty'] = args.getlist('cty')
		args.poplist('cty')

		result['__conditons__'] = conditions

		# filter operation
		if (fo := args.get('fo')) is not None: # 1=AND, 2=OR
			fo = int(fo)
			del args['fo']
		else:
			fo = 1 # default
		result['fo'] = fo

		# all remaining arguments are treated as matching attributes
		result['__attrs__'] = args.copy()

		return result


	#	Create a m2m:uril structure from a list of resources
	def _resourcesToURIList(self, resources, drt):
		cseid = '/' + Configuration.get('cse.csi') + '/'
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
	def _resourceTreeJSON(self, rs, rootResource):
		rri = rootResource['ri'] if 'ri' in rootResource else None
		while True:		# go multiple times per level through the resources until the list is empty
			result = []
			handledTy = None
			idx = 0
			while idx < len(rs):
				r = rs[idx]

				if rri is not None and r.pi != rri:	# only direct children
					idx += 1
					continue
				if r.ty in [ C.tCNT_OL, C.tCNT_LA, C.tFCNT_OL, C.tFCNT_LA ]:	# Skip latest, oldest virtual resources
					idx += 1
					continue
				if handledTy is None:
					handledTy = r.ty					# this round we check this type
				if r.ty == handledTy:					# handle only resources of the currently handled type
					result.append(r)					# append the found resource 
					rs.remove(r)						# remove resource from the original list (greedy), but don't increment the idx
					rs = self._resourceTreeJSON(rs, r)	# check recursively whether this resource has children
				else:
					idx += 1							# next resource

			# add all found resources under the same type tag to the rootResource
			if len(result) > 0:
				rootResource[result[0].tpe] = [r.asJSON(embedded=False) for r in result]
				# TODO not all child resources are lists [...] Handle just to-1 relations
			else:
				break # end of list, leave while loop
		return rs # Return the remaining list


	# Retrieve child resource referenves of a resource and add them to a new target resource as "children"
	def _resourceTreeReferences(self, resources, targetResource, drt):
		if len(resources) == 0:
			return
		t = []
		for r in resources:
			if r.ty in [ C.tCNT_OL, C.tCNT_LA, C.tFCNT_OL, C.tFCNT_LA ]:	# Skip latest, oldest virtual resources
				continue
			t.append({ 'nm' : r['rn'], 'typ' : r['ty'], 'val' :  Utils.structuredPath(r) if drt == C.drtStructured else r.ri})
		targetResource['ch'] = t


	# Retrieve full child resources of a resource and add them to a new target resource
	def _childResourceTree(self, resource, targetResource):
		if len(resource) == 0:
			return
		result = {}
		self._resourceTreeJSON(resource, result)	# rootResource is filled with the result
		for k,v in result.items():			# copy child resources to result resource
			targetResource[k] = v

