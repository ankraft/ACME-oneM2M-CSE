#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Group fanOutPoint (GRP_FOPT) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, Operation, CSERequest, JSON
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..resources.VirtualResource import VirtualResource
from ..resources.Resource import Resource

# TODO - Handle Group Request Target Members parameter
# TODO - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest is supported

class GRP_FOPT(VirtualResource):
	""" Group fanOutPoint (GRP_FOPT) resource type. This is a virtual resource. """

	def handleRetrieveRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
		L.isDebug and L.logDebug(f'RETRIEVE resources from fopt. ID: {id}')
		return CSE.groupResource.foptRequest(Operation.RETRIEVE, self, request, id, originator)	


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		L.isDebug and L.logDebug(f'CREATE resources at fopt. ID: {id}')
		return CSE.groupResource.foptRequest(Operation.CREATE, self, request, id, originator)


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		L.isDebug and L.logDebug(f'UPDATE resources at fopt. ID: {id}')
		return CSE.groupResource.foptRequest(Operation.UPDATE, self, request, id, originator)


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		L.isDebug and L.logDebug(f'DELETE resources at fopt. ID: {id}')
		return CSE.groupResource.foptRequest(Operation.DELETE, self, request, id, originator)


