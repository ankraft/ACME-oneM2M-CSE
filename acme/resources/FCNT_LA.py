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
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources.VirtualResource import VirtualResource
from ..resources.Resource import Resource
from ..resources.FCI import FCI


class FCNT_LA(VirtualResource):
	"""	This class implements the virtual <latest> resource for <flexContainer> resources.
	"""

	resourceType = ResourceTypes.FCNT_LA
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	resourceName = 'la'
	""" Possibility for virtual sub-classes to provide a specific resource name. """


	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
	"""	A list of allowed child-resource types for this resource type. """

	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}
	""" A dictionary of the attributes and attribute policies for this resource type. 
		The attribute policies are assigned during startup by the `Importer`.
	"""


	def handleRetrieveRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
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


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. 

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Raises:
				`OPERATION_NOT_ALLOWED`: Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('CREATE operation not allowed for <latest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle an UPDATE request.			
	
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Raises:
				`OPERATION_NOT_ALLOWED`: Fails with error code for this resource type. 
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
		L.isDebug and L.logDebug('Deleting latest FCI from FCNT')
		if not (resource := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.FCI)):
			raise NOT_FOUND('no instance for <latest>')
		CSE.dispatcher.deleteLocalResource(resource, originator, withDeregistration = True)
		return Result(rsc = ResponseStatusCode.DELETED, resource = resource)


	def hasAttributeDefined(self, name: str) -> bool:
		return name in FCI._attributes