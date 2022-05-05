#
#	GroupManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource groups
#

from typing import cast, List
from ..etc.Types import ResourceTypes as T, Result, ConsistencyStrategy, Permission, Operation, ResponseStatusCode as RC, CSERequest, JSON
from ..etc import Utils as Utils
from ..resources.FCNT import FCNT
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource
from ..resources.GRP_FOPT import GRP_FOPT
from ..resources import Factory as Factory
from ..services.Logging import Logging as L
from ..services import CSE as CSE


class GroupManager(object):

	def __init__(self) -> None:
		# Add delete event handler because we like to monitor the resources in mid
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent) 		# type: ignore
		L.isInfo and L.log('GroupManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Group Manager.
		
			Returns:
				Boolean that indicates the operation
		"""
		L.isInfo and L.log('GroupManager shut down')
		return True


	#########################################################################

	def validateGroup(self, group:Resource, originator:str) -> Result:
		"""	Validate a group and its members (privileges and attribute).

			Args:
				group: The <group> resource
				originator: A request originator
			Return:
				Result object
		"""

		# Get consistencyStrategy
		csy = group.csy

		# Check member types and group set type
		# Recursive for sub groups, if .../fopt. Check privileges of originator
		if not (res := self._checkMembersAndPrivileges(group, originator)).status:
			return res

		# Check for max members
		if group.hasAttribute('mnm'):		# only if mnm attribute is set
			try: 							# mnm may not be a number
				if len(group.mid) > int(group.mnm):
					L.logDebug(dbg := 'max number of members exceeded')
					return Result.errorResult(rsc = RC.maxNumberOfMemberExceeded, dbg = dbg)
			except ValueError:
				L.logWarn(dbg := f'invalid argument or type: {group.mnm}')
				return Result.errorResult(rsc = RC.invalidArguments, dbg = dbg)


		group.dbUpdate()
		# TODO: check virtual resources
		# return Result(status = True, rsc = RC.OK)
		return Result.successResult()


	def _checkMembersAndPrivileges(self, group:Resource, originator:str) -> Result:
		"""	Internally check a groups member resources and privileges.
		
			Args:
				group: The group resource
				originator: The request's originator
			Return:
				Result object with status of the operation
			"""

		# check for duplicates and remove them
		midsList = []		# contains the real mi

		remoteResource:JSON = None
		rsc 				= 0

		for mid in group.mid:
			isLocalResource = True
			#Check whether it is a local resource or not
			if Utils.isSPRelative(mid):
				if Utils.csiFromSPRelative(mid) != CSE.cseCsi:
					# RETRIEVE member from a remote CSE
					isLocalResource = False
					if not (url := CSE.request._getForwardURL(mid)):
						return Result.errorResult(rsc = RC.notFound, dbg = f'forwarding URL not found for group member: {mid}')
					L.isDebug and L.logDebug(f'Retrieve request to: {url}')
					remoteResult = CSE.request.sendRetrieveRequest(url, CSE.cseCsi)

			# get the resource and check it
			hasFopt = False
			if isLocalResource:
				hasFopt = mid.endswith('/fopt')
				id = mid[:-5] if len(mid) > 5 and hasFopt else mid 	# remove /fopt to retrieve the resource
				if not (res := CSE.dispatcher.retrieveResource(id)).resource:
					return Result.errorResult(rsc = RC.notFound, dbg = res.dbg)
				resource = res.resource
			else:
				if not remoteResult.data or len(remoteResult.data) == 0:
					if remoteResult.rsc == RC.originatorHasNoPrivilege:  # CSE has no privileges for retrieving the member
						return Result.errorResult(rsc = RC.receiverHasNoPrivileges, dbg = 'insufficient privileges for CSE to retrieve remote resource')
					else:  # Member not found
						return Result.errorResult(rsc = RC.notFound, dbg = f'remote resource not found: {mid}')
				else:
					resource = Factory.resourceFromDict(cast(JSON, remoteResult.data)).resource

			# skip if ri is already in the list
			if isLocalResource:
				if (ri := resource.ri) in midsList:
					continue
			else:
				if mid in midsList:
					continue

			# check privileges
			if isLocalResource:
				if not CSE.security.hasAccess(originator, resource, Permission.RETRIEVE):
					return Result.errorResult(rsc = RC.receiverHasNoPrivileges, dbg = f'insufficient privileges for originator to retrieve local resource: {mid}')

			# if it is a group + fopt, then recursively check members
			if (ty := resource.ty) == T.GRP and hasFopt:
				if isLocalResource:
					if not (res := self._checkMembersAndPrivileges(resource, originator)).status:
						return res
				ty = resource.mt	# set the member type to the group's member type

			# check specializationType spty
			if (spty := group.spty):
				if isinstance(spty, int):				# mgmtobj type
					if isinstance(resource, MgmtObj) and ty != spty:
						return Result.errorResult(rsc = RC.groupMemberTypeInconsistent, dbg = f'resource and group member types mismatch: {ty} != {spty} for: {mid}')
				elif isinstance(spty, str):				# fcnt specialization
					if isinstance(resource, FCNT) and resource.cnd != spty:
						return Result.errorResult(rsc = RC.groupMemberTypeInconsistent, dbg = f'resource and group member specialization types mismatch: {resource.cnd} != {spty} for: {mid}')

			# check type of resource and member type of group
			mt = group.mt
			if not (mt == T.MIXED or ty == mt):	# types don't match
				csy = group.csy
				if csy == ConsistencyStrategy.abandonMember:		# abandon member
					continue
				elif csy == ConsistencyStrategy.setMixed:			# change group's member type
					mt = T.MIXED
					group['mt'] = T.MIXED
				else:												# abandon group
					return Result.errorResult(rsc = RC.groupMemberTypeInconsistent, dbg = 'group consistency strategy and type "mixed" mismatch')

			# member seems to be ok, so add ri to the list
			if isLocalResource:
				midsList.append(ri if not hasFopt else ri + '/fopt')		# restore fopt for ri
			else:
				midsList.append(mid)	# remote resource appended with original memberID

		# ^^^ for end

		group['mid'] = midsList				# replace with a cleaned up mid
		group['cnm'] = len(midsList)
		group['mtv'] = True
		
		# return Result(status = True, rsc = RC.OK)
		return Result.successResult()


	def foptRequest(self, operation:Operation, fopt:GRP_FOPT, request:CSERequest, id:str, originator:str) -> Result:
		"""	Handle requests to a fanOutPoint. This method might be called recursivly, when there are groups in groups.
		
			Args:
				operation: The operation type to perform on the group
				fopt: The <fopt> virtual resource
				request: The request to perform on the <fopt>
				id: The original target resource ID
				originator: The request originator
			Result:
				The request's Result object
		"""

		# get parent / group and check permissions
		if not (group := fopt.retrieveParentResource()):
			return Result.errorResult(rsc = RC.notFound, dbg = 'group resource not found')

		# get the permission flags for the request operation
		permission = operation.permission()

		#check access rights for the originator through memberAccessControlPolicies
		if CSE.security.hasAccess(originator, group, requestedPermission = permission, ty = request.headers.resourceType) == False:
			return Result.errorResult(rsc = RC.originatorHasNoPrivilege, dbg = 'insufficient privileges for originator')

		# check whether there is something after the /fopt ...

		# _, _, tail = id.partition('/fopt/') if '/fopt/' in id else (None, None, '')
		_, _, tail = id.partition('/fopt/')
		
		L.isDebug and L.logDebug(f'Adding additional path elements: {tail}')

		# walk through all members
		resultList:List[Result] = []

		tail = '/' + tail if len(tail) > 0 else '' # add remaining path, if any
		for mid in group.mid.copy():	# copy mi because it is changed in the loop
			# Try to get the SRN and add the tail
			if srn := Utils.structuredPathFromRI(mid):
				mid = srn + tail
			else:
				mid = mid + tail
			# Invoke the request
			if operation == Operation.RETRIEVE:
				if not (res := CSE.dispatcher.processRetrieveRequest(request, originator, mid)).resource:
					return res
			elif operation == Operation.CREATE:
				if not (res := CSE.dispatcher.processCreateRequest(request, originator, mid)).resource:
					return res
			elif operation == Operation.UPDATE:
				if not (res := CSE.dispatcher.processUpdateRequest(request, originator, mid)).resource:
					return res 
			elif operation == Operation.DELETE:
				if not (res := CSE.dispatcher.processDeleteRequest(request, originator, mid)).status:
					return res 
			else:
				return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'operation not allowed')
			resultList.append(res)

		# construct aggregated response
		if len(resultList) > 0:
			items = []
			for result in resultList:
				if result.resource and isinstance(result.resource, Resource):
					item = 	{ 'rsc' : result.rsc, 
							  'rqi' : request.headers.requestIdentifier,
							  'pc'  : result.resource.asDict() if isinstance(result.resource, Resource) else result.resource, # in case 'resource' is a dict
							  'to'  : result.resource[Resource._srn],
							  'rvi'	: CSE.releaseVersion
							}
				else:	# e.g. when deleting
					item = 	{ 'rsc' : result.rsc, 
							  'rqi' : request.headers.requestIdentifier,
							  'rvi'	: CSE.releaseVersion
							}
				items.append(item)
			rsp = { 'm2m:rsp' : items}
			agr = { 'm2m:agr' : rsp }
		else:
			agr = {}

		return Result(status = True, rsc = RC.OK, resource = agr) # Response Status Code is OK regardless of the requested fanout operation


	#########################################################################
	#
	#	Event Handler
	#

	def handleDeleteEvent(self, deletedResource:Resource) -> None:
		"""	Handle a delete event. Check whether the deleted resource is
			a member of a group. If yes, remove the member. This method is
			called by the event manager. 

			Args:
				deletedResource: The deleted resource to check
		"""
		L.isDebug and L.logDebug('Looking for and removing deleted resource from groups')

		ri = deletedResource.ri
		groups = CSE.storage.searchByFragment(	{ 'ty' : T.GRP }, 
												lambda r: (mid := r.get('mid')) and ri in mid)	# type: ignore # Filter all <grp> where mid contains ri
		for group in groups:
			L.isDebug and L.logDebug(f'Removing deleted resource: {ri} from group: {group.ri}')
			group['mid'].remove(ri)
			group['cnm'] = group.cnm - 1
			group.dbUpdate()

