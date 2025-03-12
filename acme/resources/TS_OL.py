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

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources.VirtualResource import VirtualResource
from ..resources.TSI import TSI


class TS_OL(VirtualResource):
	"""	This class implements the virtual <oldest> resource for <timeSeries> resources.
	"""

	resourceType = ResourceTypes.TS_OL
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	resourceName = 'ol'
	""" Possibility for virtual sub-classes to provide a fixed resource name. """


	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
	"""	A list of allowed child-resource types for this resource type. """

	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}
	""" A dictionary of the attributes and attribute policies for this resource type. 
		The attribute policies are assigned during startup by the `Importer`.
	"""

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
		if not (resource := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.TSI, oldest = True)):
			raise NOT_FOUND('no instance for <oldest>')
		CSE.dispatcher.deleteLocalResource(resource, originator, withDeregistration = True)
		return Result(rsc = ResponseStatusCode.DELETED, resource = resource)

	def hasAttributeDefined(self, name: str) -> bool:
		return name in TSI._attributes