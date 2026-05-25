#
#	FCNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource) for flexContainer
#

"""	This module implements the virtual <latest> resource type for <container> resources.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import ResourceTypes, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires
from ..resources.VirtualResource import VirtualResource
from ..resources.FCI import FCI

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher

@requires(dispatcher='acmecse.services.Dispatcher')
class FCNT_LA(VirtualResource):
	"""	This class implements the virtual <latest> resource for <flexContainer> resources.
	"""

	dispatcher: Dispatcher = None
	"""	Injected Dispatcher instance. """

	def handleRetrieveRequest(self, request: Optional[CSERequest] = None, 
									id: Optional[str] = None, 
									originator: Optional[str] = None) -> Result:
		""" Handle a RETRIEVE request.

			Args:
				request: The original request.
				id: Resource ID of the original request.
				originator: The request's originator.

			Return:
				The latest <flexContainerInstance> for the parent <flexContainer>, or an error `Result`.
		"""
		L.isDebug and L.logDebug('Retrieving latest FCI from FCNT')
		return self.retrieveLatestOldest(request, originator, ResourceTypes.FCI, oldest = False)


	def handleCreateRequest(self, request: CSERequest, id: str, originator: str) -> Result:
		""" Handle a CREATE request. 

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Raises:
				`OPERATION_NOT_ALLOWED`: Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('CREATE operation not allowed for <latest> resource type')


	def handleUpdateRequest(self, request: CSERequest, id: str, originator: str) -> Result:
		""" Handle an UPDATE request.			
	
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Raises:
				`OPERATION_NOT_ALLOWED`: Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('UPDATE operation not allowed for <latest> resource type')


	def handleDeleteRequest(self, request: CSERequest, id: str, originator: str) -> Result:
		""" Handle a DELETE request.

			Delete the latest resource.

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Result object indicating success or failure.
		"""
		L.isDebug and L.logDebug('Deleting latest FCI from FCNT')
		if not (resource := self.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.FCI)):
			raise NOT_FOUND('no instance for <latest>')
		self.dispatcher.deleteLocalResource(resource, originator, withDeregistration=True)
		return Result(rsc=ResponseStatusCode.DELETED, resource=resource)


	def hasAttributeDefined(self, name: str) -> bool:
		return name in FCI._attributes	# type: ignore[attr-defined]