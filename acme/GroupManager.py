#
#	GroupManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource groups
#

from Logging import Logging
from typing import Union, List
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ConsistencyStrategy, Permission, Operation, ResponseCode as RC, CSERequest, JSON
import CSE, Utils
from resources import FCNT, MgmtObj
from resources.Resource import Resource
from resources.GRP_FOPT import GRP_FOPT
import resources.Factory as Factory


class GroupManager(object):

	def __init__(self) -> None:
		# Add delete event handler because we like to monitor the resources in mid
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent) 		# type: ignore
		Logging.log('GroupManager initialized')


	def shutdown(self) -> bool:
		Logging.log('GroupManager shut down')
		return True


	#########################################################################

	def validateGroup(self, group:Resource, originator:str) -> Result:

		# Get consistencyStrategy
		csy = group.csy

		# Check member types and group set type
		# Recursive for sub groups, if .../fopt. Check privileges of originator
		if not (res := self._checkMembersAndPrivileges(group, group.mt, group.csy, group.spty, originator)).status:
			return res

		# Check for max members
		if group.hasAttribute('mnm'):		# only if mnm attribute is set
			try: 							# mnm may not be a number
				if len(group.mid) > int(group.mnm):
					return Result(status=False, rsc=RC.maxNumberOfMemberExceeded, dbg='max number of members exceeded')
			except ValueError:
				return Result(status=False, rsc=RC.invalidArguments, dbg='invalid arguments')

		group.dbUpdate()
		# TODO: check virtual resources
		return Result(status=True)



	def _checkMembersAndPrivileges(self, group:Resource, mt:int, csy:int, spty:Union[int, str], originator:str) -> Result:

		# check for duplicates and remove them
		midsList = []		# contains the real mi

		remoteResource:JSON = None
		rsc 					= 0

		for mid in group['mid']:
			isLocalResource = True;
			#Check whether it is a local resource or not
			if Utils.isSPRelative(mid):
				targetCSE = f'/{mid.split("/")[0]}'
				if targetCSE != CSE.cseCsi:
					""" RETRIEVE member from a remote CSE """
					isLocalResource = False
					if (url := CSE.request._getForwardURL(mid)) is None:
						return Result(status=False, rsc=RC.notFound, dbg=f'forwarding URL not found for group member: {mid}')
					Logging.log(f'Retrieve request to: {url}')
					remoteResult = CSE.request.sendRetrieveRequest(url, CSE.cseCsi)

			# get the resource and check it
			hasFopt = False
			if isLocalResource:
				hasFopt = mid.endswith('/fopt')
				id = mid[:-5] if len(mid) > 5 and hasFopt else mid 	# remove /fopt to retrieve the resource
				if (res := CSE.dispatcher.retrieveResource(id)).resource is None:
					return Result(status=False, rsc=RC.notFound, dbg=res.dbg)
				resource = res.resource
			else:
				if remoteResult.dict is None or len(remoteResult.dict) == 0:
					if remoteResult.rsc == RC.originatorHasNoPrivilege:  # CSE has no privileges for retrieving the member
						return Result(status=False, rsc=RC.receiverHasNoPrivileges, dbg='wrong privileges for CSE to retrieve remote resource')
					else:  # Member not found
						return Result(status=False, rsc=RC.notFound, dbg=f'remote resource not found: {mid}')
				else:
					resource = Factory.resourceFromDict(remoteResult.dict).resource

			# skip if ri is already in th
			if isLocalResource:
				if (ri := resource.ri) in midsList:
					continue
			else:
				if mid in midsList:
					continue

			# check privileges
			if isLocalResource:
				if not CSE.security.hasAccess(originator, resource, Permission.RETRIEVE):
					return Result(status=False, rsc=RC.receiverHasNoPrivileges, dbg=f'wrong privileges for originator to retrieve local resource: {mid}')

			# if it is a group + fopt, then recursively check members
			if (ty := resource.ty) == T.GRP and hasFopt:
				if isLocalResource:
					if not (res := self._checkMembersAndPrivileges(resource, mt, csy, spty, originator)).status:
						return res
				ty = resource.mt	# set the member type to the group's member type

			# check specializationType spty
			if spty is not None:
				if isinstance(spty, int):				# mgmtobj type
					if isinstance(resource, MgmtObj.MgmtObj) and ty != spty:
						return Result(status=False, rsc=RC.groupMemberTypeInconsistent, dbg=f'resource and group member types mismatch: {ty:d} != {spty:d} for: {mid}')
				elif isinstance(spty, str):				# fcnt specialization
					if isinstance(resource, FCNT.FCNT) and resource.cnd != spty:
						return Result(status=False, rsc=RC.groupMemberTypeInconsistent, dbg=f'resource and group member specialization types mismatch: {resource.cnd} != {spty} for: {mid}')

			# check type of resource and member type of group
			if not (mt == T.MIXED or ty == mt):	# types don't match
				if csy == ConsistencyStrategy.abandonMember:		# abandon member
					continue
				elif csy == ConsistencyStrategy.setMixed:			# change group's member type
					mt = T.MIXED
					group['mt'] = T.MIXED
				else:								# abandon group
					return Result(status=False, rsc=RC.groupMemberTypeInconsistent, dbg='group consistency strategy and type "mixed" mismatch')

			# member seems to be ok, so add ri to th
			if isLocalResource:
				midsList.append(ri if not hasFopt else ri + '/fopt')		# restore fopt for ri
			else:
				midsList.append(mid)	# remote resource appended with original memberID

		# ^^^ for end

		group['mid'] = midsList				# replace with a cleaned up mid
		group['cnm'] = len(midsList)
		group['mtv'] = True
		
		return Result(status=True)




	def foptRequest(self, operation:Operation, fopt:GRP_FOPT, request:CSERequest, id:str, originator:str) -> Result:
		"""	Handle requests to a fanOutPoint. 
		This method might be called recursivly, when there are groups in groups."""

		# get parent / group and check permissions
		group = fopt.retrieveParentResource()
		if group is None:
			return Result(rsc=RC.notFound, dbg='group resource not found')

		# get the permission flags for the request operation
		permission = operation.permission()

		#check access rights for the originator through memberAccessControlPolicies
		if CSE.security.hasAccess(originator, group, requestedPermission=permission, ty=request.headers.resourceType, isCreateRequest=True if operation == Operation.CREATE else False) == False:
			return Result(rsc=RC.originatorHasNoPrivilege, dbg='access denied')

		# check whether there is something after the /fopt ...
		_, _, tail = id.partition('/fopt/') if '/fopt/' in id else (None, None, '')
		Logging.logDebug(f'Adding additional path elements: {tail}')

		# walk through all members
		resultList:list[Result] = []

		tail = '/' + tail if len(tail) > 0 else '' # add remaining path, if any
		for mid in group.mid.copy():	# copy mi because it is changed in the loop
			# Try to get the SRN and add the tail
			if (srn := Utils.structuredPathFromRI(mid)) is not None:
				mid = srn + tail
			else:
				mid = mid + tail
			# Invoke the request
			if operation == Operation.RETRIEVE:
				if (res := CSE.dispatcher.processRetrieveRequest(request, originator, mid)).resource is None:
					return res
			elif operation == Operation.CREATE:
				if (res := CSE.dispatcher.processCreateRequest(request, originator, mid)).resource is None:
					return res
			elif operation == Operation.UPDATE:
				if (res := CSE.dispatcher.processUpdateRequest(request, originator, mid)).resource is None:
					return res 
			elif operation == Operation.DELETE:
				if (res := CSE.dispatcher.processDeleteRequest(request, originator, mid)).rsc != RC.deleted:
					return res 
			else:
				return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')
			resultList.append(res)

		# construct aggregated response
		if len(resultList) > 0:
			items = []
			for result in resultList:
				if result.resource is not None and isinstance(result.resource, Resource):
					item = 	{ 'rsc' : result.rsc, 
							  'rqi' : request.headers.requestIdentifier,
							  'pc'  : result.resource.asDict() if isinstance(result.resource, Resource) else result.resource, # in case 'resource' is a dict
							  'to'  : result.resource[Resource._srn],
							  'rvi'	: '3'	# TODO constant? from conifguration
							}
				else:	# e.g. when deleting
					item = 	{ 'rsc' : result.rsc, 
					  'rqi' : request.headers.requestIdentifier,
					  'rvi'	: '3'	# TODO constant? from configuration
					}
				items.append(item)
			rsp = { 'm2m:rsp' : items}
			agr = { 'm2m:agr' : rsp }
		else:
			agr = {}

		return Result(resource=agr) # Response Status Code is OK regardless of the requested fanout operation




	#########################################################################


	def handleDeleteEvent(self, deletedResource:Resource) -> None:
		"""Handle a delete event. Check whether the deleted resource is a member
		of group. If yes, remove the member. This method is called by the event manager. """

		ri = deletedResource.ri
		groups = CSE.storage.searchByTypeFieldValue(T.GRP, 'mid', ri)
		for group in groups:
			group['mid'].remove(ri)
			group['cnm'] = group.cnm - 1
			group.dbUpdate()

