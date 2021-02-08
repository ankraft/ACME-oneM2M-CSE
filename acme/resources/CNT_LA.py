#
#	CNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource)
#

from typing import cast
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC, Result, JSON, CSERequest
import CSE, Utils
from .Resource import *
from Logging import Logging


class CNT_LA(Resource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CNT_LA, dct, pi, create=create, inheritACP=True, readOnly=True, rn='la', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def handleRetrieveRequest(self, request:CSERequest=None, id:str=None, originator:str=None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		Logging.logDebug('Retrieving latest CIN from CNT')
		if (r := self._getLatest()) is None:
			return Result(rsc=RC.notFound, dbg='no instance for <latest>')
		return Result(resource=r)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. """
		return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for <latest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a UPDATE request. Fail with error code. """
		return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for <latest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. """
		Logging.logDebug('Deleting latest CIN from CNT')
		if (r := self._getLatest()) is None:
			return Result(rsc=RC.notFound, dbg='no instance for <latest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration=True)


	def _getLatest(self) -> Resource:
		pi = self['pi']
		rs = []
		if (parentResource := CSE.dispatcher.retrieveResource(pi).resource) is not None:
			rs = parentResource.contentInstances()		# ask parent for all CIN
		return cast(Resource, rs[-1]) if len(rs) > 0 else None			
