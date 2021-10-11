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
		L.isDebug and L.logDebug(f'RETRIEVE request for polling channel. Originator: {originator}')

		# Determine the request's timeout
		if request.headers.requestExpirationTimestamp:
			ret = DateUtils.timeUntilAbsRelTimestamp(request.headers.requestExpirationTimestamp)
			L.isDebug and L.logDebug(f'Polling timeout: {ret} seconds')
		else:
			ret = CSE.request.requestExpirationDelta
			L.isDebug and L.logDebug(f'Polling timeout: indefinite')

		# Return the response or time out
		if not (r := CSE.request.waitForPollingRequest(originator, None, timeout=ret)).status:
			L.logWarn(dbg := f'Request Expiration Timestamp reached. No request queued for originator: {self.getOriginator()}')
			return Result(status=False, rsc=RC.requestTimeout, dbg=dbg)
		if r.request.requestType == RequestType.REQUEST:
			r.request.pc = { 'm2m:rqp' : r.request.pc }
		elif r.request.requestType == RequestType.RESPONSE:
			r.request.pc = { 'm2m:rsp' : r.request.pc }
		L.logWarn

		# normal response
		return Result(status=True, embeddedRequest=r.request)


	# def handleReceivedNotifyRequest(self, request:CSERequest, id:str, originator:str) -> Result:
	# 	"""	Handle a NOTIFY request to a PCU resource.
	# 	"""
	# 	L.isDebug and L.logDebug(f'NOTIFY request for polling channel. Originator: {originator}')

	# 	# Check whether the request is allowed by this originator was done in the dispatcher

	# 	# Check content
	# 	if request.pc is None:
	# 		L.logDebug(dbg := f'Missing content/request in notification')
	# 		return Result(status=False, rsc=RC.badRequest, dbg=dbg)

	# 	from ..resources.PCH import PCH

	# 	# Get parent PCH and add the request to the PCU's queue.
	# 	if pch := self.retrieveParentResource():

	# 		# Fill various request attributes
	# 		nrequest 										= CSERequest()

	# 		if (pc := request.pc.get('m2m:sgn')) or (pc := request.pc.get('sgn')):	# A notification is a request
	# 			L.logWarn(pc.get('fr'))
	# 			nrequest.headers.originator					= pc.get('fr')
	# 			nrequest.headers.originatingTimestamp		= pc.get('or')
	# 			nrequest.headers.requestIdentifier			= pc.get('rqi')
	# 			nrequest.headers.releaseVersionIndicator	= pc.get('rvi')
	# 			nrequest.rsc								= pc.get('rsc')
	# 			nrequest.pc 								= pc.get('pc')
	# 			nrequest.requestType						= RequestType.REQUEST

	# 			CSE.request.queueRequestForPCH(cast(PCH, pch), request=nrequest, reqType=RequestType.RESPONSE)	# A Notification to PCU always contains a response to a previous request
	# 	return Result(status=True, rsc=RC.OK)


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

