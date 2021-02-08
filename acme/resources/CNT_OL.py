#
#	CNT_OL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: oldest (virtual resource)
#

from typing import cast
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC, Result, JSON, CSERequest
import Utils, CSE
from .Resource import *
from Logging import Logging


class CNT_OL(Resource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CNT_OL, dct, pi, create=create, inheritACP=True, readOnly=True, rn='ol', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def handleRetrieveRequest(self, request:CSERequest=None, id:str=None, originator:str=None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		Logging.logDebug('Retrieving oldest CIN from CNT')
		if (r := self._getOldest()) is None:
			return Result(rsc=RC.notFound, dbg='no instance for <oldest>')
		return Result(resource=r)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. """
		return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for <oldest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a UPDATE request. Fail with error code. """
		return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for <oldest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the oldest resource. """
		Logging.logDebug('Deleting oldest CIN from CNT')
		if (r := self._getOldest()) is None:
			return Result(rsc=RC.notFound, dbg='no instance for <oldest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration=True)


	def _getOldest(self) -> Resource:
		pi = self['pi']
		rs = []
		if (parentResource := CSE.dispatcher.retrieveResource(pi).resource) is not None:
			rs = parentResource.contentInstances()				# ask parent for all CIN
		return cast(Resource, rs[0]) if len(rs) > 0 else None

