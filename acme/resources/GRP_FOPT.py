#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Group fanOutPoint (GRP_FOPT) resource type. """

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import Result, Operation, CSERequest
from ..etc.ResponseStatusCodes import NOT_IMPLEMENTED
from ..helpers.PluginManager import requires
from ..runtime.Logging import Logging as L
from ..resources.VirtualResource import VirtualResource

if TYPE_CHECKING:
	from ..plugins.services.GroupManager import GroupManager

# TODO - Handle Group Request Target Members parameter
# TODO - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest is supported

@requires(groupManager='acme.plugins.services.GroupManager', required=False)
class GRP_FOPT(VirtualResource):
	""" Group fanOutPoint (GRP_FOPT) resource type. This is a virtual resource. """

	groupManager: Optional[GroupManager] = None
	""" GroupManager plugin instance. """

	def handleRetrieveRequest(self, request: Optional[CSERequest] = None, 
									id: Optional[str] = None, 
									originator: Optional[str] = None) -> Result:
		L.isDebug and L.logDebug(f'RETRIEVE resources from fopt. ID: {id}')
		if not self.groupManager:
			raise NOT_IMPLEMENTED(L.logWarn('GroupManager plugin is disabled, cannot handle fopt retrieve request.'))
		return self.groupManager.foptRequest(Operation.RETRIEVE, self, request, id, originator)	


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		L.isDebug and L.logDebug(f'CREATE resources at fopt. ID: {id}')
		if not self.groupManager:
			raise NOT_IMPLEMENTED(L.logWarn('GroupManager plugin is disabled, cannot handle fopt retrieve request.'))
		return self.groupManager.foptRequest(Operation.CREATE, self, request, id, originator)


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		L.isDebug and L.logDebug(f'UPDATE resources at fopt. ID: {id}')
		if not self.groupManager:
			raise NOT_IMPLEMENTED(L.logWarn('GroupManager plugin is disabled, cannot handle fopt retrieve request.'))
		return self.groupManager.foptRequest(Operation.UPDATE, self, request, id, originator)


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		L.isDebug and L.logDebug(f'DELETE resources at fopt. ID: {id}')
		if not self.groupManager:
			raise NOT_IMPLEMENTED(L.logWarn('GroupManager plugin is disabled, cannot handle fopt retrieve request.'))
		return self.groupManager.foptRequest(Operation.DELETE, self, request, id, originator)


