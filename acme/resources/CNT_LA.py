#
#	CNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource)
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseStatusCode as RC, Result, JSON, CSERequest
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *


class CNT_LA(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.CNT_LA, dct, pi, create = create, inheritACP = True, readOnly = True, rn = 'la')


	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		if L.isDebug: L.logDebug('Retrieving latest CIN from CNT')

		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.CIN)):
			r = self	# no instance, so take self as a resource

		# Take the resource, either a CIN or self and check it # EXPERIMENTAL
		if not (res := CSE.notification.checkPerformBlockingRetrieve(r, originator, request, finished = lambda: self.dbReloadDict())).status:
			return res

		# Then retrieve it, either for the first time or again
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.CIN)):
			return Result.errorResult(rsc = RC.notFound, dbg = 'no instance for <latest>')
		
		# Do again some checks with the final resource, but no subscription checks!
		if not (res := r.willBeRetrieved(originator, request, subCheck = False)).status:
			return res





		# TODO in all _la, _ol

		# if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.CIN)):
		# 	return Result(status = False, rsc = RC.notFound, dbg = 'no instance for <latest>')
		# Do again some checks with the final resource, but no subscription checks!
		# if not (res := r.willBeRetrieved(originator, request, subCheck = False)).status:
		# 	return res

		return Result(status = True, rsc = RC.OK, resource = r)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. """
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'CREATE operation not allowed for <latest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a UPDATE request. Fail with error code. """
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'UPDATE operation not allowed for <latest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. """
		L.isDebug and L.logDebug('Deleting latest CIN from CNT')
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.CIN)):
			return Result.errorResult(rsc = RC.notFound, dbg='no instance for <latest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration = True)
