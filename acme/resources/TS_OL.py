#
#	TS_OL.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: oldest (virtual resource) for timeSeries
#

"""	This module implements the virtual <oldest> resource type for <timeSeries> resources.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from ..etc.Types import ResourceTypes, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires
from ..resources.VirtualResource import VirtualResource
from ..resources.TSI import TSI

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher

@requires(dispatcher='acme.services.Dispatcher')
class TS_OL(VirtualResource):
	"""	This class implements the virtual <oldest> resource for <timeSeries> resources.
	"""

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		""" Handle a RETRIEVE request.

			Args:
				request: The original request.
				id: Resource ID of the original request.
				originator: The request's originator.

			Return:
				The oldest <timeSeriesInstance> for the parent <timeSeries>, or an error `Result`.
		"""
		L.isDebug and L.logDebug('Retrieving oldest TSI from TS')
		return self.retrieveLatestOldest(request, originator, ResourceTypes.TSI, oldest = True)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. 

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('operation not allowed for <oldest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle an UPDATE request.			
	
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('operation not allowed for <oldest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request.

			Delete the oldest resource.

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Result object indicating success or failure.
		"""
		L.isDebug and L.logDebug('Deleting oldest TSI from TS')
		if not (resource := self.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.TSI, oldest = True)):
			raise NOT_FOUND('no instance for <oldest>')
		self.dispatcher.deleteLocalResource(resource, originator, withDeregistration = True)
		return Result(rsc = ResponseStatusCode.DELETED, resource = resource)

	def hasAttributeDefined(self, name: str) -> bool:
		return name in TSI._attributes	# type: ignore[attr-defined]