#
#	CNT_OL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: oldest (virtual resource)
#

"""	This module implements the virtual <oldest> resource type for <container> resources.
"""

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..resources.VirtualResource import VirtualResource
from ..resources.Resource import Resource
from ..resources.CIN import CIN
from ..runtime import CSE
from ..runtime.Logging import Logging as L



class CNT_OL(VirtualResource):
	"""	This class implements the virtual <oldest> resource for <container> resources.
	"""

	resourceType = ResourceTypes.CNT_OL
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	resourceName = 'ol'
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
				The oldest <contentInstance> for the parent <container>, or an error `Result`.
		"""
		L.isDebug and L.logDebug('Retrieving oldest CIN from CNT')
		return self.retrieveLatestOldest(request, originator, ResourceTypes.CIN, oldest = True)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. 

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Raises:
				`OPERATION_NOT_ALLOWED`: Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('CREATE operation not allowed for <oldest> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle an UPDATE request.			
	
			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Raises:
				`OPERATION_NOT_ALLOWED`: Fails with error code for this resource type. 
		"""
		raise OPERATION_NOT_ALLOWED('UPDATE operation not allowed for <oldest> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request.

			Delete the oldest resource.

			Args:
				request: The request to process.
				id: The structured or unstructured resource ID of the target resource.
				originator: The request's originator.
			
			Return:
				Result object with the oldest instance.

			Raises:
				`NOT_FOUND`: If there is no oldest instance. 
		"""
		L.isDebug and L.logDebug('Deleting oldest CIN from CNT')
		if not (r := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.CIN, oldest = True)):
			raise NOT_FOUND('no instance for <oldest>')
		CSE.dispatcher.deleteLocalResource(r, originator, withDeregistration = True)
		return Result(rsc = ResponseStatusCode.DELETED, resource = r)


	def hasAttributeDefined(self, name: str) -> bool:
		return name in CIN._attributes