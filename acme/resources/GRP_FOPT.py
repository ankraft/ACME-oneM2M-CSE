#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: fanOutPoint (virtual resource)
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, Operation, CSERequest, JSON
from ..services.Logging import Logging as L
from ..services import CSE as CSE
from ..resources.Resource import *

# TODO - Handle Group Request Target Members parameter
# TODO - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest is supported

class GRP_FOPT(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.GRP_FOPT, dct, pi, create = create, inheritACP = True, readOnly = True, rn = 'fopt')


	def handleRetrieveRequest(self, request:CSERequest = None, id:str = None, originator:str = None) -> Result:
		if L.isDebug: L.logDebug('Retrieving resources from fopt')
		return CSE.group.foptRequest(Operation.RETRIEVE, self, request, id, originator)	


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		if L.isDebug: L.logDebug('Creating resources at fopt')
		return CSE.group.foptRequest(Operation.CREATE, self, request, id, originator)


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		if L.isDebug: L.logDebug('Updating resources at fopt')
		return CSE.group.foptRequest(Operation.UPDATE, self, request, id, originator)


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		if L.isDebug: L.logDebug('Deleting resources at fopt')
		return CSE.group.foptRequest(Operation.DELETE, self, request, id, originator)


