#
#	PCH_PCU.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannelURI for PollingChannel
#

from __future__ import annotations
from typing import cast
from ..etc.Types import AttributePolicyDict, RequestType, ResourceTypes as T, ResponseCode as RC, JSON, CSERequest, Result
from ..resources.Resource import Resource
from ..services.Logging import Logging as L
from ..services import CSE
from ..etc import DateUtils


class PCH_PCU(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.PCH_PCU, dct, pi=pi, create=create, inheritACP=True, readOnly=True, rn='pcu', isVirtual=True)
		

	def handleRetrieveRequest(self, request:CSERequest=None, id:str=None, originator:str=None) -> Result:
		""" Handle a RETRIEVE request. Return resource or block until available. 
		"""
		L.logDebug(f'Retrieving request from polling channel. Originator: {originator}')

		# Determine the request's timeout
		ret = DateUtils.fromAbsRelTimestamp(request.headers.requestExpirationTimestamp, CSE.request.requestExpirationDelta)	# with default

		# Return the response or time out
		if not (r := CSE.request.waitForPollingRequest(originator, None, ret)):
			L.logWarn(dbg := f'Request Expiration Timestamp reached. No request queued for originator: {self.getOriginator()}')
			return Result(status=False, rsc=RC.requestTimeout, dbg=dbg)
		# normal response
		return Result(status=True, responseRequest=r)


	def handleNotifyRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		"""	Handle a NOTIFY request to a PCU resource.
		"""

		# Check whether the request is allowed by this originator was done in the dispatcher

		from ..resources.PCH import PCH


		# Get parent PCH and add the request to the PCU's queue.
		if pch := self.retrieveParentResource():

			# TODO Not this request, but the request inside of PC!
			# if request.pc -> extract


			CSE.request.queueRequestForPCH(cast(PCH, pch), request=request, reqType=RequestType.RESPONSE)	# A Notification to PCU always contains a response to a previous request
		return Result(status=True, rsc=RC.OK)


	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. 
		"""
		return Result(rsc=RC.operationNotAllowed, dbg='CREATE operation not allowed for <pollingChanelURI> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle an UPDATE request. Fail with error code. 
		"""
		return Result(rsc=RC.operationNotAllowed, dbg='UPDATE operation not allowed for <pollingChanelURI> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. 
		"""
		return Result(rsc=RC.operationNotAllowed, dbg='DELETE operation not allowed for <pollingChanelURI> resource type')

