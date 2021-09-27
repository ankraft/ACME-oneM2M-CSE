#
#	PCH_PCU.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannelURI for PollingChannel
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseCode as RC, JSON
from ..resources.Resource import *
from ..services.Logging import Logging


class PCH_PCU(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.PCH_PCU, dct, pi, create=create, inheritACP=True, readOnly=True, rn='pcu', isVirtual=True)



# TODO





	# def handleRetrieveRequest(self, request:Request=None, id:str=None, originator:str=None) -> Result:
	# 	""" Handle a RETRIEVE request. Return resource """
	# 	Logging.logDebug('Retrieving oldest FCI from FCNT')
	# 	if (r := self._getOldest()) is None:
	# 		return Result(rsc=RC.notFound, dbg='no instance for <oldest>')
	# 	return Result(resource=r)


	# def handleCreateRequest(self, request:Request, id:str, originator:str, ct:str, ty:int) -> Result:
	# 	""" Handle a CREATE request. Fail with error code. """
	# 	return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for <oldest> resource type')


	# def handleUpdateRequest(self, request:Request, id:str, originator:str, ct:str) -> Result:
	# 	""" Handle a UPDATE request. Fail with error code. """
	# 	return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for <oldest> resource type')


	# def handleDeleteRequest(self, request:Request, id:str, originator:str) -> Result:
	# 	""" Handle a DELETE request. Delete the latest resource. """
	# 	Logging.logDebug('Deleting oldest FCI from FCNT')
	# 	if (r := self._getOldest()) is None:
	# 		return Result(rsc=RC.notFound, dbg='no instance for <oldest>')
	# 	return CSE.dispatcher.deleteResource(r, originator, withDeregistration=True)

