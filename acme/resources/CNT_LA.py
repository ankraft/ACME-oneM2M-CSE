#
#	CNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource)
#

"""	This module implements the virtual <latest> resource type for <container> resources.
"""

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON, CSERequest, LocationSource
from ..etc.ResponseStatusCodes import ResponseStatusCode, OPERATION_NOT_ALLOWED, NOT_FOUND
from ..services import CSE
from ..services.Logging import Logging as L
from ..resources.VirtualResource import VirtualResource


class CNT_LA(VirtualResource):
	"""	This class implements the virtual <latest> resource for <container> resources.
	"""

	_li = '__li__'
	"""	Link to LCP from the parent <container> resource. """

	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
	"""	A list of allowed child-resource types for this resource type. """

	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}
	""" A dictionary of the attributes and attribute policies for this resource type. 
		The attribute policies are assigned during startup by the `Importer`.
	"""


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.CNT_LA, dct, pi, create = create, inheritACP = True, readOnly = True, rn = 'la')
				
		# Add to internal attributes to ignore in validation etc
		self._addToInternalAttributes(self._li)


	def handleRetrieveRequest(self, request:Optional[CSERequest] = None,
									id:Optional[str] = None,
									originator:Optional[str] = None) -> Result:
		""" Handle a RETRIEVE request.

			Args:
				request: The original request.
				id: Resource ID of the original request.
				originator: The request's originator.

			Return:
				The latest <contentInstance> for the parent <container>, or an error `Result`.
		"""
		L.isDebug and L.logDebug('Retrieving latest CIN from CNT')
		
		# Handle the request when the parent container's <locationPolicy> locationID is set
		# This might create a new CIN
		if (li := self.getLCPLink()) is not None:
			if (result := self.retrieveLatestOldest(request, originator, ResourceTypes.CIN, oldest = False)) is not None:
				CSE.location.handleLatestRetrieve(result.resource, li)

		return self.retrieveLatestOldest(request, originator, ResourceTypes.CIN, oldest = False)


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
				Result object with the latest resource.
			
			Raises:
				`NOT_FOUND`: If there is no latest instance. 
		"""
		L.isDebug and L.logDebug('Deleting latest CIN from CNT')
		if not (resource := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, ResourceTypes.CIN)):
			raise NOT_FOUND('no instance for <latest>')
		CSE.dispatcher.deleteLocalResource(resource, originator, withDeregistration = True)
		return Result(rsc = ResponseStatusCode.DELETED, resource = resource)


	def getLCPLink(self) -> str:
		"""	Retrieve a `LCP` (LocationPolicy) resource's resource ID.

			Return:
				The resource ID.
		"""
		return self[self._li]
	

	def setLCPLink(self, lcpRi:str) -> None:
		"""	Assign a resource ID of a `LCP` (LocationPolicy) resource to the latest resource.

			Args:
				lcpRi: The resource ID of an `LCP` resource.
		"""
		self.setAttribute(self._li, lcpRi, overwrite = True)
