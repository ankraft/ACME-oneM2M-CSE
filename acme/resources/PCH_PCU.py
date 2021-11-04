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
from ..etc.Types import AttributePolicyDict, Operation, RequestType, ResourceTypes as T, ResponseStatusCode as RC, JSON, CSERequest, Result
from ..resources.Resource import Resource
from ..services.Logging import Logging as L
from ..services import CSE
from ..etc import DateUtils, Utils


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
		

	def handleRetrieveRequest(self, request:CSERequest=None, _:str=None, originator:str=None) -> Result:
		""" Handle a RETRIEVE request. Return resource or block until available. At the PCU, only received requests are retrieved, otherwise
			this function does not return until a reqeust timeout occurs. Only the AE's originator has access to this virtual resource.
		"""
		L.isDebug and L.logDebug(f'RETRIEVE request for polling channel. Originator: {originator}')

		# Determine the request's timeout
		if request.headers.requestExpirationTimestamp:
			ret = DateUtils.timeUntilTimestamp(request.headers._retUTCts)
			L.isDebug and L.logDebug(f'Polling timeout: {ret} seconds')
		else:
			ret = CSE.request.requestExpirationDelta
			L.isDebug and L.logDebug(f'Polling timeout: indefinite')

		# Return the response or time out
		if not (r := CSE.request.waitForPollingRequest(originator, None, timeout=ret)).status:
			L.logWarn(dbg := f'Request Expiration Timestamp reached. No request queued for originator: {self.getOriginator()}')
			return Result(status=False, rsc=RC.requestTimeout, dbg=dbg)
		
		return Result(status=True, rsc=RC.OK, request=request, embeddedRequest=r.request)


	def handleNotifyRequest(self, request:CSERequest, originator:str) -> Result:
		"""	Handle a NOTIFY request to a PCU resource. At the PCU, only Responses are delivered. This method is called
			when a notification is directed to a non-request-reachable target.
		"""
		L.isDebug and L.logDebug(f'NOTIFY request for polling channel. Originator: {originator}')

		# Check whether the request is allowed by this originator was done in the dispatcher

		# Check content
		if request.pc is None:
			L.logDebug(dbg := f'Missing content/request in notification')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		
		# Validate the response
		if not (r := CSE.validator.validatePrimitiveContent(request.pc)).status:
			L.isDebug and L.logDebug(r.dbg)
			return r

		if (innerPC := cast(JSON, Utils.findXPath(request.pc, 'm2m:rsp'))) is None:
			L.logDebug(dbg := f'Noification to PCU must contain a Response (m2m:rsp)')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		
		if not innerPC.get('fr'):
			L.isDebug and L.logDebug(f'Adding originator: {request.headers.originator} to request')
			innerPC['fr'] = request.headers.originator

		nrequest 									= CSERequest()
		nrequest.originalRequest = innerPC
		nrequest.pc 			 = innerPC.get('pc')

		if not (res := CSE.request.fillAndValidateCSERequest(nrequest, isResponse=True)).status:
			return res
		# L.logWarn(res.request)

		# Enqueue the reqeust
		CSE.request.queueRequestForPCH(self.getOriginator(), request=res.request, reqType=RequestType.RESPONSE)	# A Notification to PCU always contains a response to a previous request
		
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

