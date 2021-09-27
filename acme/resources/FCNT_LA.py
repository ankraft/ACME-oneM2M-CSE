#
#	FCNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource) for flexContainer
#

from __future__ import annotations
from typing import cast, Optional
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseCode as RC, Result, JSON, CSERequest
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *


class FCNT_LA(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.FCNT_LA, dct, pi, create=create, inheritACP=True, readOnly=True, rn='la', isVirtual=True)


	def handleRetrieveRequest(self, request:CSERequest=None, id:str=None, originator:str=None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		if L.isDebug: L.logDebug('Retrieving latest FCI from FCNT')
		if not (r := self._getLatest()):
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
		if L.isDebug: L.logDebug('Deleting latest FCI from FCNT')
		if not (r := self._getLatest()):
			return Result(rsc=RC.notFound, dbg='no instance for <latest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration=True)


	def _getLatest(self) -> Optional[Resource]:
		rs = self.retrieveParentResource().flexContainerInstances()	# ask parent for all FCI
		return cast(Resource, rs[-1]) if len(rs) > 0 else None	
