#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: fanOutPoint (virtual resource)
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, Operation, CSERequest, JSON
from ..services.Logging import Logging as L
from ..services import CSE
from ..resources.VirtualResource import VirtualResource

# TODO - Handle Group Request Target Members parameter
# TODO - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest is supported

class GRP_FOPT(VirtualResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.GRP_FOPT, dct, pi, create = create, inheritACP = True, readOnly = True, rn = 'fopt')


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


