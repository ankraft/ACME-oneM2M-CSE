#
#	FCNT_OL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: oldest (virtual resource) for flexContainer
#

from flask import Request
from Constants import Constants as C
from Types import ResourceTypes as T
import CSE, Utils
from .Resource import *
from Logging import Logging


class FCNT_OL(Resource):

	def __init__(self, jsn:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.FCNT_OL, jsn, pi, create=create, inheritACP=True, readOnly=True, rn='ol', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def handleRetrieveRequest(self, request:Request=None, id:str=None, originator:str=None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		Logging.logDebug('Retrieving oldest FCI from FCNT')
		if (r := self._getOldest()) is None:
			return Result(rsc=C.rcNotFound, dbg='no instance for <oldest>')
		return Result(resource=r)


	def handleCreateRequest(self, request:Request, id:str, originator:str, ct:str, ty:int) -> Result:
		""" Handle a CREATE request. Fail with error code. """
		return Result(rsc=C.rcOperationNotAllowed, dbg='operation not allowed for <oldest> resource type')


	def handleUpdateRequest(self, request:Request, id:str, originator:str, ct:str) -> Result:
		""" Handle a UPDATE request. Fail with error code. """
		return Result(rsc=C.rcOperationNotAllowed, dbg='operation not allowed for <oldest> resource type')


	def handleDeleteRequest(self, request:Request, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. """
		Logging.logDebug('Deleting oldest FCI from FCNT')
		if (r := self._getOldest()) is None:
			return Result(rsc=C.rcNotFound, dbg='no instance for <oldest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration=True)


	def _getOldest(self) -> Resource:
		pi = self['pi']
		rs = []
		if (parentResource := CSE.dispatcher.retrieveResource(pi).resource) is not None:
			rs = parentResource.flexContainerInstances()					# ask parent for all FCI
		return rs[0] if len(rs) > 0 else None