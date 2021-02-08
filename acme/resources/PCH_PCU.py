#
#	PCH_PCU.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannelURI for PollingChannel
#

from flask import Request
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC, JSON
import CSE, Utils
from .Resource import *
from Logging import Logging


class PCH_PCU(Resource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.PCH_PCU, dct, pi, create=create, inheritACP=True, readOnly=True, rn='pcu', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])






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

