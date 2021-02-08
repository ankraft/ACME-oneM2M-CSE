#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: fanOutPoint (virtual resource)
#

from Constants import Constants as C
import CSE
from .Resource import *
from Logging import Logging
from Types import ResourceTypes as T, Result, Operation, CSERequest, JSON


# TODO - Handle Group Request Target Members parameter
# TODO - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest is supported

class GRP_FOPT(Resource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.GRP_FOPT, dct, pi, create=create, inheritACP=True, readOnly=True, rn='fopt', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def handleRetrieveRequest(self, request:CSERequest=None, id:str=None, originator:str=None) -> Result:
		Logging.logDebug('Retrieving resources from fopt')
		return CSE.group.foptRequest(Operation.RETRIEVE, self, request, id, originator)	


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		Logging.logDebug('Creating resources at fopt')
		return CSE.group.foptRequest(Operation.CREATE, self, request, id, originator)


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		Logging.logDebug('Updating resources at fopt')
		return CSE.group.foptRequest(Operation.UPDATE, self, request, id, originator)


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		Logging.logDebug('Deleting resources at fopt')
		return CSE.group.foptRequest(Operation.DELETE, self, request, id, originator)


