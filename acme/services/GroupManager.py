#
#	GroupManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource groups
#

"""	This module implements the group service manager functionality. """

from __future__ import annotations
from typing import cast, List

from ..etc.Types import ResourceTypes, Result, ConsistencyStrategy, Permission, Operation
from ..etc.Types import CSERequest, JSON, ResponseType
from ..etc.ResponseStatusCodes import MAX_NUMBER_OF_MEMBER_EXCEEDED, INVALID_ARGUMENTS, NOT_FOUND, RECEIVER_HAS_NO_PRIVILEGES
from ..etc.ResponseStatusCodes import ResponseStatusCode, GROUP_MEMBER_TYPE_INCONSISTENT, ORIGINATOR_HAS_NO_PRIVILEGE, REQUEST_TIMEOUT
from ..etc.ACMEUtils import structuredPathFromRI
from ..etc.IDUtils import isSPRelative, csiFromSPRelative
from ..etc.DateUtils import utcTime
from ..etc.Constants import RuntimeConstants as RC
from ..resources.FCNT import FCNT
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource
from ..resources.GRP_FOPT import GRP_FOPT
from ..resources.Factory import resourceFromDict
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration


class GroupManager(object):
	"""	Manager for the CSE's group service. 
	"""

	def __init__(self) -> None:
		"""	Initialization of the GroupManager.
		"""
		# Add delete event handler because we like to monitor the resources in mid
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent) 		# type: ignore

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		L.isInfo and L.log('GroupManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the GroupManager.
		
			Returns:
				*True* when shutdown is complete.
		"""
		L.isInfo and L.log('GroupManager shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the registration services.
		"""
		L.isDebug and L.logDebug('GroupManager restarted')


	#########################################################################

	def validateGroup(self, group:Resource, originator:str) -> None:
		"""	Validate a group and its members (privileges and attribute).

			Args:
				group: The <group> resource.
				originator: The request's originator.
			Return:
				`Result` instance.
		"""

		# Get consistencyStrategy
		csy = group.csy

		# Check member types and group set type
		# Recursive for sub groups, if .../fopt. Check privileges of originator
		self._checkMembersAndPrivileges(group, originator)

		# Check for max members
		if group.hasAttribute('mnm'):		# only if mnm attribute is set
			try: 							# mnm may not be a number
				if len(group.mid) > int(group.mnm):
					raise MAX_NUMBER_OF_MEMBER_EXCEEDED(L.logDebug('max number of members exceeded'))
			except ValueError:
				raise INVALID_ARGUMENTS(L.logWarn(f'invalid argument or type: {group.mnm}'))
			except:
				raise

		group.dbUpdate()
		# TODO: check virtual resources


	def _checkMembersAndPrivileges(self, group:Resource, originator:str) -> None:
		"""	Internally check a group's member resources and privileges.
		
			Args:
				group: The group resource.
				originator: The request's originator.
			Return:
				`Result` object with the status of the operation.
			"""

		# check for duplicates and remove them
		midsList = []		# contains the real mi

		remoteResource:JSON = None
		rsc 				= 0

		for mid in group.mid:
			isLocalResource = True
			#Check whether it is a local resource or not
			if isSPRelative(mid):
				if csiFromSPRelative(mid) != RC.cseCsi:
					# RETRIEVE member from a remote CSE
					isLocalResource = False
					# if not (url := CSE.request._getForwardURL(mid)):
					# 	raise NOT_FOUND(f'forwarding URL not found for group member: {mid}')
					L.isDebug and L.logDebug(f'Retrieve request to: {mid}')
					remoteResult = CSE.request.handleSendRequest(CSERequest(op = Operation.RETRIEVE,
																			to = mid, 
																			originator = RC.cseCsi)
																)[0].result	# there should be at least one result

			# get the resource and check it
			hasFopt = False
			if isLocalResource:
				hasFopt = mid.endswith('/fopt')
				id = mid[:-5] if len(mid) > 5 and hasFopt else mid 	# remove /fopt to retrieve the resource
				resource = CSE.dispatcher.retrieveResource(id)
			else:
				if not remoteResult.data or len(remoteResult.data) == 0:
					if remoteResult.rsc == ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE:  # CSE has no privileges for retrieving the member
						raise RECEIVER_HAS_NO_PRIVILEGES('insufficient privileges for CSE to retrieve remote resource')
					else:  # Member not found
						raise NOT_FOUND(f'remote resource not found: {mid}')
				else:
					resource = resourceFromDict(cast(JSON, remoteResult.data))

			# skip if ri is already in the list
			if isLocalResource:
				if (ri := resource.ri) in midsList:
					continue
			else:
				if mid in midsList:
					continue

			# check privileges
			if isLocalResource:
				if not CSE.security.hasAccess(originator, resource, Permission.RETRIEVE, resultResource = resource):
					raise RECEIVER_HAS_NO_PRIVILEGES(f'insufficient privileges for originator to retrieve local resource: {mid}')

			# if it is a group + fopt, then recursively check members
			if (ty := resource.ty) == ResourceTypes.GRP and hasFopt:
				if isLocalResource:
					self._checkMembersAndPrivileges(resource, originator)
				ty = resource.mt	# set the member type to the group's member type

			# check specializationType spty
			if (spty := group.spty):
				match spty:
					case int():		# mgmtobj type
						if isinstance(resource, MgmtObj) and ty != spty:
							raise GROUP_MEMBER_TYPE_INCONSISTENT(f'resource and group member types mismatch: {ty} != {spty} for: {mid}')
					case str():		# fcnt specialization
						if isinstance(resource, FCNT) and resource.cnd != spty:
							raise GROUP_MEMBER_TYPE_INCONSISTENT(f'resource and group member specialization types mismatch: {resource.cnd} != {spty} for: {mid}')

			# check type of resource and member type of group
			mt = group.mt
			if not (mt == ResourceTypes.MIXED or ty == mt):	# types don't match
				match group.csy:
					case ConsistencyStrategy.abandonMember:	# abandon member
						continue
					case ConsistencyStrategy.setMixed:		# change group's member type
						mt = ResourceTypes.MIXED
						group['mt'] = ResourceTypes.MIXED
					case _:
						raise GROUP_MEMBER_TYPE_INCONSISTENT('group consistency strategy and type "mixed" mismatch')

			# member seems to be ok, so add ri to the list
			if isLocalResource:
				midsList.append(ri if not hasFopt else ri + '/fopt')		# restore fopt for ri
			else:
				midsList.append(mid)	# remote resource appended with original memberID

		# ^^^ for end

		group.setAttribute('mid', midsList)				# replace with a cleaned up mid
		group.setAttribute('cnm', len(midsList))
		group.setAttribute('mtv', True)


	def foptRequest(self, operation:Operation, 
						  fopt:GRP_FOPT, 
						  request:CSERequest, 
						  id:str, 
						  originator:str) -> Result:
		"""	Handle requests to a <`GRP`>'s  <`GRP_FOPT`> fanOutPoint. This method might be called recursivly,
			in case there are groups in groups.
		
			Args:
				operation: The operation type to perform on the group.
				fopt: The <`GRP_FOPT`> virtual resource.
				request: The request to perform on the <`GRP_FOPT`>.
				id: The original target resource ID.
				originator: The request's originator.
			Return:
				`Result` instance.
		"""

		L.isDebug and L.logDebug(f'Performing fanOutPoint operation: {operation} on: {id}')

		# get parent / group and check permissions
		if not (groupResource := fopt.retrieveParentResource()):
			raise NOT_FOUND('group resource not found')

		# get the permission flags for the request operation
		permission = operation.permission()

		#check access rights for the originator through memberAccessControlPolicies
		if not CSE.security.hasAccess(originator, groupResource, requestedPermission = permission, ty = request.ty):
			raise ORIGINATOR_HAS_NO_PRIVILEGE('insufficient privileges for originator')
		

		# check whether there is something after the /fopt ...
		_, _, tail = id.partition('/fopt/')
		
		L.isDebug and L.logDebug(f'Adding additional path elements: {tail}')

		# walk through all members
		resultList:List[Result] = []

		tail = '/' + tail if len(tail) > 0 else '' # add remaining path, if any
		_mid = groupResource.mid.copy()	# copy mi because it is changed in the loop

		# Determine the timeout for aggregating requests.
		# If Result Expiration Timestamp is present in the request then use that one.
		# Else use the default configuration, if set to a value > 0
		if request.rset is not None:
			_timeoutTS = request._rsetUTCts
		elif Configuration.resource_grp_resultExpirationTime > 0:
			_timeoutTS = utcTime() + Configuration.resource_grp_resultExpirationTime
		else:
			_timeoutTS = 0

		for mid in _mid:	
			# Try to get the SRN and add the tail
			if srn := structuredPathFromRI(mid):
				mid = srn + tail
			else:
				mid = mid + tail
			# Invoke the request
			_result = CSE.request.processRequest(request, originator, mid)
			# Check for RSET expiration
			if _timeoutTS and _timeoutTS < utcTime():
				# Check for blocking request. Then raise a timeout
				if request.rt == ResponseType.blockingRequest:
					raise REQUEST_TIMEOUT(L.logDebug('Aggregation timed out'))
				# Otherwise just interrupt the aggregation
				break
			# Append the result
			resultList.append(_result)
			# import time
			# time.sleep(1.0)

		# construct aggregated response
		if len(resultList) > 0:
			items = []
			for result in resultList:
				item = 	{	'rsc' : result.rsc, 
							'rqi' : request.rqi,
							'rvi' : request.rvi,
						}
				if result.resource and isinstance(result.resource, Resource):
					item['pc'] = result.resource.asDict()

				items.append(item)
			rsp = { 'm2m:rsp' : items}
			agr = { 'm2m:agr' : rsp }
			
			# if the request is a flexBlocking request and the number of results is not equal to the number of members
			# then the request must be marked as incomplete. This will be removed later when adding to the <req> resource.
			if len(_mid) != len(resultList) and request.rt == ResponseType.flexBlocking:
				agr['acme:incomplete'] = True # type: ignore

		else:
			agr = {}

		return Result(rsc = ResponseStatusCode.OK, resource = agr) # Response Status Code is OK regardless of the requested fanout operation


	#########################################################################
	#
	#	Event Handler
	#

	def handleDeleteEvent(self, name:str, deletedResource:Resource) -> None:
		"""	Handle a CSE-internal delete event (ie. whenever a resource is deleted).
			Check whether the deleted resource is a member of a group. If yes, then remove the member.
			This method is called by the `EventManager`. 

			Args:
				deletedResource: The deleted resource to check.
		"""
		L.isDebug and L.logDebug('Looking for and removing deleted resource from groups')

		ri = deletedResource.ri
		groups = CSE.storage.searchByFragment(	{ 'ty' : ResourceTypes.GRP }, 
												lambda r: (mid := r.get('mid')) and ri in mid)	# type: ignore # Filter all <grp> where mid contains ri
		for group in groups:
			L.isDebug and L.logDebug(f'Removing deleted resource: {ri} from group: {group.ri}')
			group['mid'].remove(ri)
			group['cnm'] = group.cnm - 1
			group.dbUpdate(True)
