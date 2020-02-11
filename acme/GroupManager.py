#
#	GroupManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource groups
#

from Logging import Logging
from Constants import Constants as C
import CSE, Utils
from resources import FCNT, MgmtObj



class GroupManager(object):

	def __init__(self):
		# Add delete event handler because we like to monitor the resources in mid
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent)
		Logging.log('GroupManager initialized')


	def shutdown(self):
		Logging.log('GroupManager shut down')


	#########################################################################

	def validateGroup(self, group, originator):

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
					return (False, C.rcMaxNumberOfMemberExceeded)
			except ValueError:
				return (False, C.rcInvalidArguments)


		# TODO: check virtual resources
		return (True, C.rcOK)



	def _checkMembersAndPrivileges(self, group, mt, csy, spty, originator):

		# check for duplicates and remove them
		midsList = []		# contains the real mid list

		for mid in group['mid']:

			# get the resource and check it
			id = mid[:-5] if (hasFopt := mid.endswith('/fopt')) else mid 	# remove /fopt to retrieve the resource
			if (r := CSE.dispatcher.retrieveResource(id))[0] is None:
				return (False, C.rcNotFound)
			resource = r[0]

			# skip if ri is already in the list
			if (ri := resource.ri) in midsList:
				continue

			# check privileges
			if not CSE.security.hasAccess(originator, resource, C.permRETRIEVE):
				return (False, C.rcReceiverHasNoPrivileges)

			# if it is a group + fopt, then recursively check members
			if (ty := resource.ty) == C.tGRP and hasFopt:
				if not (res := self._checkMembersAndPrivileges(resource, mt, csy, spty, originator))[0]:
					return res
				ty = resource.mt	# set the member type to the group's member type

			# check specializationType spty
			if spty is not None:
				if isinstance(spty, int):				# mgmtobj type
					if isinstance(resource, MgmtObj.MgmtObj) and ty != spty:
						return (False, C.rcGroupMemberTypeInconsistent)
				elif isinstance(spty, str):				# fcnt specialization
					if isinstance(resource, FCNT.FCNT) and resource.cnd != spty:
						return (False, C.rcGroupMemberTypeInconsistent)

			# check type of resource and member type of group
			if not (mt == C.tMIXED or ty == mt):	# types don't match
				if csy == C.csyAbandonMember:		# abandon member
					continue
				elif csy == C.csySetMixed:			# change group's member type
					mt = C.tMIXED
					group['mt'] = C.tMIXED
				else:								# abandon group
					return (False, C.rcGroupMemberTypeInconsistent)

			# member seems to be ok, so add ri to the list
			midsList.append(ri if not hasFopt else ri + '/fopt')		# restore fopt for ri

		group['mid'] = midsList				# replace with a cleaned up mid
		group['cnm'] = len(midsList)

		return (True, C.rcOK)




	def foptRequest(self, operation, fopt, request, id, originator, ct=None, ty=None):
		"""	Handle requests to a fanOutPoint. 
		This method might be called recursivly, when there are groups in groups."""

		# get parent / group
		group = fopt.retrieveParentResource()
		if group is None:
			return (None, C.rcNotFound)

		# get the rqi header field
		(_, _, _, rqi, _) = Utils.getRequestHeaders(request)

		# check whether there is something after the /fopt ...
		(_, _, tail) = id.partition('/fopt/') if '/fopt/' in id else (_, _, '')
		Logging.logDebug('Adding additional path elements: %s' % tail)


		# walk through all members
		result = []
		tail = '/' + tail if len(tail) > 0 else '' # add remaining path, if any
		for mid in group.mid:
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
				return (None, C.rcOperationNotAllowed)
			result.append(res)

		# construct aggregated response
		if len(result) > 0:
			items = []
			for r in result:
				item = 	{ 'rsc' : r[1], 
						  'rqi' : rqi,
						  'pc'  : r[0].asJSON(),
						  'to'  : r[0].__srn__
						}
				items.append(item)
			rsp = { 'm2m:rsp' : items}
			agr = { 'm2m:agr' : rsp }
		else:
			agr = {}

		# Different "ok" results per operation
		return (agr, [ C.rcOK, C.rcCreated, C.rcUpdated, C.rcDeleted ][operation])



	#########################################################################


	def handleDeleteEvent(self, deletedResource):
		"""Handle a delete event. Check whether the deleted resource is a member
		of group. If yes, remove the member."""

		ri = deletedResource.ri
		groups = CSE.storage.searchByTypeFieldValue(C.tGRP, 'mid', ri)
		for group in groups:
			group['mid'].remove(ri)
			group['cnm'] = group.cnm - 1
			CSE.storage.updateResource(group)

