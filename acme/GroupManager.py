#
#	GroupManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource groups
#

from Logging import Logging
from typing import Tuple, Optional, Union
from flask import Request
from Constants import Constants as C
import CSE, Utils
from resources import FCNT, MgmtObj
from SecurityManager import operationsPermissions
from resources.Resource import Resource

class GroupManager(object):

	def __init__(self) -> None:
		# Add delete event handler because we like to monitor the resources in mid
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent) 		# type: ignore
		Logging.log('GroupManager initialized')


	def shutdown(self) -> None:
		Logging.log('GroupManager shut down')


	#########################################################################

	def validateGroup(self, group: Resource, originator: str) -> Tuple[bool, int, str]:

		# Get consistencyStrategy
		csy = group.csy

		# Check member types and group set type
		# Recursive for sub groups, if .../fopt. Check privileges of originator
		if not (res := self._checkMembersAndPrivileges(group, group.mt, group.csy, group.spty, originator))[0]:
			return res

		# Check for max members
		if group.hasAttribute('mnm'):		# only if mnm attribute is set
			try: 							# mnm may not be a number
				if len(group.mid) > int(group.mnm):
					return False, C.rcMaxNumberOfMemberExceeded, 'max number of members exceeded'
			except ValueError:
				return False, C.rcInvalidArguments, 'invalid arguments'

		group.dbUpdate()
		# TODO: check virtual resources
		return True, C.rcOK, None



	def _checkMembersAndPrivileges(self, group:Resource, mt: int, csy: int, spty: Union[int, str], originator: str) -> Tuple[bool, int, str]:

		# check for duplicates and remove them
		midsList = []		# contains the real mid list

		remoteResource:dict = None
		rsc 					= 0

		for mid in group['mid']:
			isLocalResource = True;
			#Check whether it is a local resource or not
			if Utils.isSPRelative(mid):
				targetCSE = '/%s' % mid.split('/')[0]
				if targetCSE != CSE.Configuration.get('cse.csi'):
					""" RETRIEVE member from a remote CSE """
					isLocalResource = False
					if (url := CSE.remote._getForwardURL(mid)) is None:
						return None, C.rcNotFound, 'forwarding URL not found for group member: %s' % mid
					Logging.log('Retrieve request to: %s' % url)
					remoteResource, rsc, _ = CSE.httpServer.sendRetrieveRequest(url, CSE.Configuration.get('cse.csi'))

			# get the resource and check it
			hasFopt = False
			if isLocalResource:
				hasFopt = mid.endswith('/fopt')
				id = mid[:-5] if len(mid) > 5 and hasFopt else mid 	# remove /fopt to retrieve the resource
				if (r := CSE.dispatcher.retrieveResource(id))[0] is None:
					return False, C.rcNotFound, r[2]
				resource = r[0]
			else:
				if remoteResource is None:
					if rsc == C.rcOriginatorHasNoPrivilege:  # CSE has no privileges for retrieving the member
						return False, C.rcReceiverHasNoPrivileges, 'wrong privileges for CSE to retrieve remote resource'
					else:  # Member not found
						return False, C.rcNotFound, 'remote resource not found: %s' % mid
				else:
					resource, _ = Utils.resourceFromJSON(remoteResource)

			# skip if ri is already in the list
			if isLocalResource:
				if (ri := resource.ri) in midsList:
					continue
			else:
				if mid in midsList:
					continue

			# check privileges
			if isLocalResource:
				if not CSE.security.hasAccess(originator, resource, C.permRETRIEVE):
					return False, C.rcReceiverHasNoPrivileges, 'wrong privileges for originator to retrieve local resource: %s' % mid

			# if it is a group + fopt, then recursively check members
			if (ty := resource.ty) == C.tGRP and hasFopt:
				if isLocalResource:
					if not (res := self._checkMembersAndPrivileges(resource, mt, csy, spty, originator))[0]:
						return res
				ty = resource.mt	# set the member type to the group's member type

			# check specializationType spty
			if spty is not None:
				if isinstance(spty, int):				# mgmtobj type
					if isinstance(resource, MgmtObj.MgmtObj) and ty != spty:
						return False, C.rcGroupMemberTypeInconsistent, 'resource and group member types mismatch: %d != %d for: %s' % (ty, spty, mid)
				elif isinstance(spty, str):				# fcnt specialization
					if isinstance(resource, FCNT.FCNT) and resource.cnd != spty:
						return False, C.rcGroupMemberTypeInconsistent, 'resource and group member specialization types mismatch: %s != %s for: %s' % (resource.cnd, spty, mid)

			# check type of resource and member type of group
			if not (mt == C.tMIXED or ty == mt):	# types don't match
				if csy == C.csyAbandonMember:		# abandon member
					continue
				elif csy == C.csySetMixed:			# change group's member type
					mt = C.tMIXED
					group['mt'] = C.tMIXED
				else:								# abandon group
					return False, C.rcGroupMemberTypeInconsistent, 'group consistency strategy and type "mixed" mismatch'

			# member seems to be ok, so add ri to the list
			if isLocalResource:
				midsList.append(ri if not hasFopt else ri + '/fopt')		# restore fopt for ri
			else:
				midsList.append(mid)	# remote resource appended with original memberID

		# ^^^ for end

		group['mid'] = midsList				# replace with a cleaned up mid
		group['cnm'] = len(midsList)
		group['mtv'] = True
		
		return True, C.rcOK, None




	def foptRequest(self, operation: int, fopt: Resource, request: Request, id: str, originator: str, ct:str = None, ty: int = None) -> Tuple[Union[Resource, dict], int, str]:
		"""	Handle requests to a fanOutPoint. 
		This method might be called recursivly, when there are groups in groups."""

		# get parent / group and check permissions
		group = fopt.retrieveParentResource()
		if group is None:
			return None, C.rcNotFound, 'group resource not found'

		# get the permission flags for the request operation
		permission = operationsPermissions[operation]

		#check access rights for the originator through memberAccessControlPolicies
		if CSE.security.hasAccess(originator, group, requestedPermission=permission, ty=ty, isCreateRequest=True if operation == C.opCREATE else False) == False:
			return None, C.rcOriginatorHasNoPrivilege, 'access denied'

		# get the rqi header field
		_, _, _, rqi, _ = Utils.getRequestHeaders(request)

		# check whether there is something after the /fopt ...
		_, _, tail = id.partition('/fopt/') if '/fopt/' in id else (_, _, '')
		Logging.logDebug('Adding additional path elements: %s' % tail)

		# walk through all members
		result = []
		tail = '/' + tail if len(tail) > 0 else '' # add remaining path, if any
		for mid in group.mid.copy():	# copy mid list because it is changed in the loop
			# Try to get the SRN and add the tail
			if (srn := Utils.structuredPathFromRI(mid)) is not None:
				mid = srn + tail
			else:
				mid = mid + tail
			# Invoke the request
			if operation == C.opRETRIEVE:
				if (res := CSE.dispatcher.handleRetrieveRequest(request, mid, originator))[0] is None:
					return res
			elif operation == C.opCREATE:
				if (res := CSE.dispatcher.handleCreateRequest(request, mid, originator, ct, ty))[0] is None:
					return res
			elif operation == C.opUPDATE:
				if (res := CSE.dispatcher.handleUpdateRequest(request, mid, originator, ct))[0] is None:
					return res 
			elif operation == C.opDELETE:
				if (res := CSE.dispatcher.handleDeleteRequest(request, mid, originator))[1] != C.rcDeleted:
					return res 
			else:
				return None, C.rcOperationNotAllowed, 'operation not allowed'
			result.append(res)

		# construct aggregated response
		if len(result) > 0:
			items = []
			for r in result:
				if r[0] is not None and isinstance(res, Resource):
					res, rsc, _ = r
					item = 	{ 'rsc' : rsc, 
							  'rqi' : rqi,
							  'pc'  : res.asJSON(),
							  'to'  : res.__srn__,
							  'rvi'	: '3'	# TODO constant?
							}
				else:	# e.g. when deleting
					_, rsc, _ = r
					item = 	{ 'rsc' : rsc, 
					  'rqi' : rqi,
					  'rvi'	: '3'	# TODO constant?
					}
				items.append(item)
			rsp = { 'm2m:rsp' : items}
			agr = { 'm2m:agr' : rsp }
		else:
			agr = {}

		return agr, C.rcOK, None # Response Status Code is OK regardless of the requested fanout operation




	#########################################################################


	def handleDeleteEvent(self, deletedResource: Resource) -> None:
		"""Handle a delete event. Check whether the deleted resource is a member
		of group. If yes, remove the member. This method is called by the event manager. """

		ri = deletedResource.ri
		groups = CSE.storage.searchByTypeFieldValue(C.tGRP, 'mid', ri)
		for group in groups:
			group['mid'].remove(ri)
			group['cnm'] = group.cnm - 1
			group.dbUpdate()

