#
#	TS_LA.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource) for timeSeries
#

"""	This module implements the virtual <latest> resource type for <timeSeries> resources.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import ResourceTypes, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires
from ..resources.TSI import TSI
from ..resources.VirtualResource import VirtualResource

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher

@requires(dispatcher='acmecse.services.Dispatcher')
class TS_LA(VirtualResource):
	"""	This class implements the virtual <latest> resource for <timeSeries> resources.
	"""

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """


	def handleRetrieveRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
		""" Handle a RETRIEVE request.

			Args:
				request: The original request.
				id: Resource ID of the original request.
				originator: The request's originator.

			Return:
				The latest <timeSeriesInstance> for the parent <timeSeries>, or an error `Result`.
		"""
		L.isDebug and L.logDebug('Retrieving latest TSI from TS')
		return self.retrieveLatestOldest(request, originator, ResourceTypes.TSI, oldest = False)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. 

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('CREATE operation not allowed for <latest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle an UPDATE request.			
	
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('UPDATE operation not allowed for <latest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request.

			Delete the latest resource.

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Result object indicating success or failure.
		"""
		L.isDebug and L.logDebug('Deleting latest TSI from TS')
		if not (resource := self.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.TSI)):
			raise NOT_FOUND('no instance for <latest>')
		self.dispatcher.deleteLocalResource(resource, originator, withDeregistration = True)
		return Result(rsc = ResponseStatusCode.DELETED, resource = resource)

	def hasAttributeDefined(self, name: str) -> bool:
		return name in TSI._attributes	# type: ignore[attr-defined]