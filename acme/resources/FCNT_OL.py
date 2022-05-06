#
#	FCNT_OL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: oldest (virtual resource) for flexContainer
#

from __future__ import annotations
from typing import cast, Optional
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseStatusCode as RC, Result, JSON, CSERequest
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *


class FCNT_OL(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:JSON=None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.FCNT_OL, dct, pi, create = create, inheritACP = True, readOnly = True, rn = 'ol')


	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		if L.isDebug: L.logDebug('Retrieving oldest FCI from FCNT')
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.FCI, oldest = True)):
			return Result.errorResult(rsc = RC.notFound, dbg = 'no instance for <oldest>')
		return Result(status = True, rsc = RC.OK, resource = r)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. """
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'operation not allowed for <oldest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a UPDATE request. Fail with error code. """
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'operation not allowed for <oldest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. """
		if L.isDebug: L.logDebug('Deleting oldest FCI from FCNT')
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.FCI, oldest = True)):
			return Result.errorResult(rsc = RC.notFound, dbg = 'no instance for <oldest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration = True)
