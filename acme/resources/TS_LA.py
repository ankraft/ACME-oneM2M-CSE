#
#	TS_LA.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource) for timeSeries
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseStatusCode as RC, Result, JSON, CSERequest
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *


class TS_LA(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.TS_LA, dct, pi, create = create, inheritACP = True, readOnly = True, rn = 'la')


	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		""" Handle a RETRIEVE request. Return resource """
		if L.isDebug: L.logDebug('Retrieving latest TSI from TS')
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.TSI)):
			return Result.errorResult(rsc = RC.notFound, dbg = 'no instance for <latest>')
		return Result(status = True, rsc = RC.OK, resource = r)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. """
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'CREATE operation not allowed for <latest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a UPDATE request. Fail with error code. """
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'UPDATE operation not allowed for <latest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. """
		if L.isDebug: L.logDebug('Deleting latest TSI from TS')
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, T.TSI)):
			return Result.errorResult(rsc = RC.notFound, dbg = 'no instance for <latest>')
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration = True)
