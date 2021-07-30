#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external requests are routed through here.
#

import requests, urllib.parse
from typing import Any, List, Tuple
from copy import deepcopy

from etc.Types import BasicType, DesiredIdentifierResultType, FilterOperation, FilterUsage, Operation, RequestArguments, RequestCallback, ResultContentType
from etc.Types import RequestStatus
from etc.Types import CSERequest
from etc.Types import RequestHandler
from etc.Types import JSON
from etc.Types import ResourceTypes as T
from etc.Types import ResponseCode as RC
from etc.Types import ResponseType
from etc.Types import Result
from etc.Types import CSERequest
from etc.Types import ContentSerializationType
from etc.Types import Parameters
from etc.Constants import Constants as C
from resources.REQ import REQ
from resources.Resource import Resource
from services.Logging import Logging as L
from services.Configuration import Configuration
import services.CSE as CSE, etc.Utils as Utils
from helpers.BackgroundWorker import BackgroundWorkerPool


class RequestManager(object):

	def __init__(self) -> None:
		self.enableTransit 					 = Configuration.get('cse.enableTransitRequests')
		self.flexBlockingBlocking			 = Configuration.get('cse.flexBlockingPreference') == 'blocking'

		self.requestHandlers:RequestHandler  = { 		# Map request handlers for operations in the RequestManager and the dispatcher
			Operation.RETRIEVE	: RequestCallback(self.retrieveRequest, CSE.dispatcher.processRetrieveRequest),
			Operation.DISCOVERY	: RequestCallback(self.retrieveRequest, CSE.dispatcher.processRetrieveRequest),
			Operation.CREATE	: RequestCallback(self.createRequest,   CSE.dispatcher.processCreateRequest),
			Operation.UPDATE	: RequestCallback(self.updateRequest,   CSE.dispatcher.processUpdateRequest),
			Operation.DELETE	: RequestCallback(self.deleteRequest,   CSE.dispatcher.processDeleteRequest),
		}

		L.log('RequestManager initialized')


	def shutdown(self) -> bool:
		L.log('RequestManager shut down')
		return True


	#########################################################################
	#
	#	RETRIEVE Request
	#

	def retrieveRequest(self, request:CSERequest) ->  Result:
		L.logDebug and L.logDebug(f'RETRIEVE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

		# handle transit requests
		if self.isTransitID(request.id):
			return self.handleTransitRetrieveRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		if request.args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: {request.args.rt}')



	#########################################################################
	#
	#	CREATE resources
	#

	def createRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'CREATE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

		# handle transit requests
		if self.isTransitID(request.id):
			return self.handleTransitCreateRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# Check contentType and resourceType
		if request.headers.contentType == None or request.headers.contentType == None:
			return Result(rsc=RC.badRequest, dbg='missing or wrong contentType or resourceType in request')

		if request.args.rt == ResponseType.blockingRequest:
			res = CSE.dispatcher.processCreateRequest(request, request.headers.originator)
			return res

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processCreateRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg=f'Unknown or unsupported ResponseType: {request.args.rt}')


	#########################################################################
	#
	#	UPDATE resources
	#

	def updateRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'UPDATE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

		# Don't update the CSEBase
		if request.id == CSE.cseRi:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for CSEBase')

		# handle transit requests
		if self.isTransitID(request.id):
			return self.handleTransitUpdateRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# Check contentType and resourceType
		if request.headers.contentType == None:
			return Result(rsc=RC.badRequest, dbg='missing or wrong content type in request')

		if request.args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processUpdateRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processUpdateRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg=f'Unknown or unsupported ResponseType: {request.args.rt}')


	#########################################################################
	#
	#	DELETE resources
	#


	def deleteRequest(self, request:CSERequest,) -> Result:
		L.isDebug and L.logDebug(f'DELETE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

		# Don't update the CSEBase
		if request.id == CSE.cseRi:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for CSEBase')

		# handle transit requests
		if self.isTransitID(request.id):
			return self.handleTransitDeleteRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		if request.args.rt == ResponseType.blockingRequest or (request.args.rt == ResponseType.flexBlocking and self.flexBlockingBlocking):
			return CSE.dispatcher.processDeleteRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processDeleteRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg=f'Unknown or unsupported ResponseType: {request.args.rt}')



	#########################################################################
	#
	#	<request> handling
	#

	def _createRequestResource(self, request:CSERequest) -> Result:

		# Get initialized resource
		if (nres := REQ.createRequestResource(request)).resource is None:
			return Result(rsc=RC.badRequest, dbg=nres.dbg)

		# Register <request>
		if (cseres := Utils.getCSE()).resource is None:
			return Result(rsc=RC.badRequest, dbg=cseres.dbg)
		if (rres := CSE.registration.checkResourceCreation(nres.resource, request.headers.originator, cseres.resource)).rsc != RC.OK:
			return rres.errorResult()
		
		# set the CSE.ri as indicator that this resource was created internally
		nres.resource.setCreatedInternally(cseres.resource.pi)

		# create <request>
		return CSE.dispatcher.createResource(nres.resource, cseres.resource, request.headers.originator)


	def _handleNonBlockingRequest(self, request:CSERequest ) -> Result:
		"""	This method creates a <request> resource, initiates the execution of the desired operation in
			the background, but immediately returns with the reference of the <request> resource that
			will contain the result of the operation.
		"""

		# Create the <request> resource first
		if (reqres := self._createRequestResource(request)).resource is None:
			return reqres

		# Synchronous handling
		if request.args.rt == ResponseType.nonBlockingRequestSynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(self._runNonBlockingRequestSync, name=f'request_{request.headers.requestIdentifier}').start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			return Result(dict={ 'm2m:uri' : reqres.resource.ri }, rsc=RC.acceptedNonBlockingRequestSynch)

		# Asynchronous handling
		if request.args.rt == ResponseType.nonBlockingRequestAsynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(self._runNonBlockingRequestAsync, name=f'request_{request.headers.requestIdentifier}').start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			return Result(dict={ 'm2m:uri' : reqres.resource.ri }, rsc=RC.acceptedNonBlockingRequestAsynch)

		# Error
		return Result(rsc=RC.badRequest, dbg=f'Unknown or unsupported ResponseType: {request.args.rt}')


	def _runNonBlockingRequestSync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
		"""
		L.isDebug and L.logDebug('Executing nonBlockingRequestSync')
		return self._executeOperation(request, reqRi).status


	def _runNonBlockingRequestAsync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
			In addition notify the notification targets.
		"""
		L.isDebug and L.logDebug('Executing nonBlockingRequestAsync')
		if not (result := self._executeOperation(request, reqRi)).status:
			return False

		L.isDebug and L.logDebug('Sending result notifications for nonBlockingRequestAsynch')
		# TODO move the notification to the notificationManager

		# The result contains the request resource  (the one from the actual operation).
		# So we can just copy the individual attributes
		originator = result.resource['ors/fr']
		responseNotification = {
			'm2m:rsp' : {
				'rsc'	:	result.resource['ors/rsc'],
				'rqi'	:	result.resource['ors/rqi'],
				'pc'	:	result.resource['ors/pc'],
				'to' 	:	result.resource['ors/to'],
				'fr' 	: 	originator,
				'rvi'	: 	request.headers.releaseVersionIndicator
			}
		}

		if (nus := request.headers.responseTypeNUs) is None:
			# RTU is not set, get POA's from the resp. AE.poa
			aes = CSE.storage.searchByFragment({ 'ty' : T.AE, 'aei' : originator })	# search all <AE>s for aei=originator
			if len(aes) != 1:
				L.isWarn and L.logWarn(f'Wrong number of AEs with aei: {originator} ({len(aes):d}): {str(aes)}')
				nus = aes[0].poa
			else:
				L.isDebug and L.logDebug(f'No RTU. Get NUS from originator ae: {aes[0].ri}')
				nus = aes[0].poa

		# send notifications.Ignore any errors here
		CSE.notification.sendNotificationWithDict(responseNotification, nus)

		return True


	def _executeOperation(self, request:CSERequest, reqRi:str) -> Result:
		"""	Execute a request operation and fill the respective request resource
			accordingly.
		"""
		# Execute the actual operation in the dispatcher
		operationResult = self.requestHandlers[request.op].dispatcherRequest(request, request.headers.originator)

		# Retrieve the <request> resource
		if (res := CSE.dispatcher.retrieveResource(reqRi)).resource is None:	
			return Result(status=False) 														# No idea what we should do if this fails
		reqres = res.resource

		# Fill the <request>
		reqres['ors'] = {	# operationResult
			'rsc'	: operationResult.rsc,
			'rqi'	: reqres.rid,
			'to'	: request.id,
			'fr'	: reqres.org,
			'ot'	: reqres['mi/ot'],
			'rset'	: reqres.et
		}
		if operationResult.rsc in [ RC.OK, RC.created, RC.updated, RC.deleted ] :			# OK, created, updated, deleted -> resource
			reqres['rs'] = RequestStatus.COMPLETED
			if operationResult.resource is not None:
				reqres['ors/pc'] = operationResult.resource.asDict()
		else:																				# Error
			reqres['rs'] = RequestStatus.FAILED
			if operationResult.dbg is not None:
				reqres['ors/pc'] = { 'm2m:dbg' : operationResult.dbg }

		# Update in DB
		reqres.dbUpdate()

		return Result(resource=reqres, status=True)


	###########################################################################

	#
	#	Handling of Transit requests. Forward requests to the resp. remote CSE's.
	#

	def handleTransitRetrieveRequest(self, request:CSERequest) -> Result:
		""" Forward a RETRIEVE request to a remote CSE """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		L.isInfo and L.log(f'Forwarding Retrieve/Discovery request to: {url}')
		return self.sendRetrieveRequest(url, request.headers.originator)


	def handleTransitCreateRequest(self, request:CSERequest) -> Result:
		""" Forward a CREATE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		L.isInfo and L.log(f'Forwarding Create request to: {url}')
		return self.sendCreateRequest(url, request.headers.originator, data=request.data, ty=request.headers.resourceType)


	def handleTransitUpdateRequest(self, request:CSERequest) -> Result:
		""" Forward an UPDATE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		L.isInfo and L.log(f'Forwarding Update request to: {url}')
		return self.sendUpdateRequest(url, request.headers.originator, data=request.data)


	def handleTransitDeleteRequest(self, request:CSERequest) -> Result:
		""" Forward a DELETE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		L.isInfo and L.log(f'Forwarding Delete request to: {url}')
		return self.sendDeleteRequest(url, request.headers.originator)


	def isTransitID(self, id:str) -> bool:
		""" Check whether an ID is a targeting a remote CSE via a CSR. """
		if Utils.isSPRelative(id):
			ids = id.split('/')
			return len(ids) > 0 and ids[0] != CSE.cseCsi[1:]
		elif Utils.isAbsolute(id):
			ids = id.split('/')
			return len(ids) > 2 and ids[2] != CSE.cseCsi[1:]
		return False


	def _getForwardURL(self, path:str) -> str:
		""" Get the new target URL when forwarding. """
		L.isDebug and L.logDebug(path)
		r, pe = CSE.remote.getCSRFromPath(path)
		L.isDebug and L.logDebug(str(r))
		if r is not None and (poas := r.poa) is not None and len(poas) > 0:
			return f'{poas[0]}/~/{"/".join(pe[1:])}'	# TODO check all available poas.
		return None


	###########################################################################

	#
	#	Handling requests.
	#
	#
	#	TODO	Is targetResource necessary?
	#	TODO	check whether url is actually an ri, then target that reource
	#	TODO	Add further transport protocols here
	#	TODO	Add method for notifications



	def sendRetrieveRequest(self, url:str, originator:str, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a RETRIEVE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendRetrieve() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.get, url, originator, parameters=parameters, ct=ct, targetResource=targetResource)
		L.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)


	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a CREATE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendCreate() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.post, url, originator, ty, data, parameters=parameters, ct=ct, targetResource=targetResource)
		L.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)


	def sendUpdateRequest(self, url:str, originator:str, data:Any, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a UPDATE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendUpdate() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.put, url, originator, data=data, parameters=parameters, ct=ct, targetResource=targetResource)
		L.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)


	def sendDeleteRequest(self, url:str, originator:str, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a DELETE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendDelete() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.delete, url, originator, parameters=parameters, ct=ct, targetResource=targetResource)
		L.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)

	###########################################################################
	#
	#	Various support methods
	#

	def handleRequest(self, request:CSERequest) -> Result:
		"""	Calls the fitting request handler for an operation and executes it.
		"""
		return self.requestHandlers[request.op].ownRequest(request)


	def deserializeContent(self, data:bytes, mediaType:str) -> Result:
		"""	Deserialize a data structure.
			Supported media serialization types are JSON and cbor.

			If successful then the Result.data contains a tuple (dict, contentType)
		"""
		dct = None
		ct = ContentSerializationType.getType(mediaType, default=CSE.defaultSerialization)
		if data is not None and len(data) > 0:
			try:
				if (dct := Utils.deserializeData(data, ct)) is None:
					return Result(rsc=RC.unsupportedMediaType, dbg=f'Unsupported media type for content-type: {ct}', status=False)
			except Exception as e:
				L.isWarn and L.logWarn('Bad request (malformed content?)')
				return Result(rsc=RC.badRequest, dbg=f'Malformed content? {str(e)}', status=False)
		
		return Result(status=True, data=(dct, ct))



	def fillAndValidateCSERequest(self, cseRequest:CSERequest) -> Result:
		"""	Fill a `cseRequest` object according to its request structure in the *req* attribute.
		"""

		def gget(dct:dict, key:str, default:Any=None, attributeType:BasicType=None, greedy:bool=True) -> Any:
			"""	Local helper to greedy check and return a key/value from a dictionary.

				If `dct` is None or `key` couldn't be found then the `default` is returned.

				This method might raise a *ValueError* exception if validation or conversion of the
				attribute/value fails.
			"""
			if dct is not None and (v := dct.get(key)) is not None:
				if greedy:
					del dct[key]
				if not (res := CSE.validator.validateAttribute(key, v, attributeType)).status:
					raise ValueError(f'attribute: {key}, value: {v} : {res.dbg}')
				if res.data in [ BasicType.nonNegInteger, BasicType.positiveInteger, BasicType.integer]:
					return int(v)
				# TODO further automatic conversions?
				return v
			return default

		try:
			# TY - resource type
			if (ty := gget(cseRequest.req, 'ty', greedy=False)) is not None:
				if not T.has(ty):
					return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'Unknown/unsupported resource type: {ty}', status=False)
				cseRequest.headers.resourceType = T(ty)


			# OP - operation
			if (op := gget(cseRequest.req, 'op', greedy=False)) is not None:
				if not Operation.isvalid(op):
					return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'Unknown/unsupported operation: {op}', status=False)
				cseRequest.op = Operation(op)
			else:
				L.logDebug(dbg := 'operation parameter is mandatory in request')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg)


			# FR - originator 
			if (fr := gget(cseRequest.req, 'fr', greedy=False)) is None and not (cseRequest.headers.resourceType == T.AE and cseRequest.op == Operation.CREATE):
				L.logDebug(dbg := 'From/Originator parameter is mandatory in request')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
			cseRequest.headers.originator = fr


			# TO - target
			if (to := gget(cseRequest.req, 'to', greedy=False)) is None:
				L.logDebug(dbg := 'To/Target parameter is mandatory in request')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
			cseRequest.id, cseRequest.csi, cseRequest.srn =  Utils.retrieveIDFromPath(to, CSE.cseRn, CSE.cseCsi)


			# Check identifiers
			if cseRequest.id is None and cseRequest.srn is None:
				return Result(rsc=RC.notFound, request=cseRequest, dbg='missing identifier', status=False)

			# OT - originating timestamp
			if (ot := gget(cseRequest.req, 'ot', greedy=False)) is not None:
				if (_ts := Utils.fromAbsRelTimestamp(ot)) == 0.0:
					L.logDebug(dbg := 'Error in provided Originating Timestamp')
					return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
				cseRequest.headers.originatingTimestamp = ot


			# RQI - requestIdentifier
			if (rqi := gget(cseRequest.req, 'rqi', greedy=False)) is None:
				L.logDebug(dbg := 'Request Identifier parameter is mandatory in request')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)		
			cseRequest.headers.requestIdentifier = rqi
		

			# RQET - requestExpirationTimestamp
			if (rqet := gget(cseRequest.req, 'rqet', greedy=False)) is not None:
				if (_ts := Utils.fromAbsRelTimestamp(rqet)) == 0.0:
					L.logDebug(dbg := 'Error in provided Request Expiration Timestamp')
					return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
				if _ts < Utils.utcTime():
					L.logDebug(dbg := 'Request timeout')
					return Result(request=cseRequest, rsc=RC.requestTimeout, dbg=dbg)
				cseRequest.headers.requestExpirationTimestamp = Utils.toISO8601Date(_ts)	# Re-assign "real" ISO8601 timestamp


			# RSET - resultExpirationTimestamp
			if (rset := gget(cseRequest.req, 'rset', greedy=False)) is not None:
				if (_ts := Utils.fromAbsRelTimestamp(rset)) == 0.0:
					L.logDebug(dbg := 'Error in provided Result Expiration Timestamp')
					return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
				if _ts < Utils.utcTime():
					L.logDebug(dbg := 'Result timeout')
					return Result(request=cseRequest, rsc=RC.requestTimeout, dbg=dbg)
				cseRequest.headers.resultExpirationTimestamp = Utils.toISO8601Date(_ts)	# Re-assign "real" ISO8601 timestamp


			# OET - operationExecutionTime
			if (oet := gget(cseRequest.req, 'oet', greedy=False)) is not None:
				if (_ts := Utils.fromAbsRelTimestamp(oet)) == 0.0:
					L.logDebug(dbg := 'Error in provided Operation Execution Time')
					return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
				cseRequest.headers.operationExecutionTime = Utils.toISO8601Date(_ts)	# Re-assign "real" ISO8601 timestamp


			# RVI - releaseVersionIndicator
			if (rvi := gget(cseRequest.req, 'rvi', greedy=False)) is None:
				L.logDebug(dbg := 'Release Version Indicator paraneter is mandatory in request')
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=dbg, status=False)
			if rvi not in C.supportedReleaseVersions:
				return Result(rsc=RC.releaseVersionNotSupported, request=cseRequest, dbg=f'Release version unsupported: {cseRequest.headers.releaseVersionIndicator}')
			cseRequest.headers.releaseVersionIndicator = rvi	


			# VSI - vendorInformation
			if (vsi := gget(cseRequest.req, 'vsi', greedy=False)) is not None:
				cseRequest.headers.vendorInformation = vsi	


			# RTU - responseTypeNUs
			if (rtu := gget(cseRequest.req, 'rtu', greedy=False)) is not None:
				cseRequest.headers.responseTypeNUs = rtu	#  TODO validate for url?

			#
			# Transfer filterCriteria: handling, conditions and attributes
			#

			cseRequest.args = RequestArguments()
			fc = deepcopy(cseRequest.req.get('fc'))	# copy because we will greedy consume attributes here


			# FU - Filter Usage
			cseRequest.args.fu = FilterUsage(gget(fc, 'fu', FilterUsage.conditionalRetrieval))
			if cseRequest.args.fu == FilterUsage.discoveryCriteria and cseRequest.op == Operation.RETRIEVE:	# correct operation if necessary
				cseRequest.op = Operation.DISCOVERY

			# DRT - Desired Identifier Result Type
			cseRequest.args.drt = DesiredIdentifierResultType(gget(fc, 'drt', DesiredIdentifierResultType.structured))	# 1=strucured, 2=unstructured


			# FO - Filter Operation
			cseRequest.args.fo = FilterOperation(gget(fc, 'fo', FilterOperation.AND))


			# RCN Result Content Type
			if (rcn := gget(cseRequest.req, 'rcn', greedy=False)) is not None: 
				try:
					rcn = ResultContentType(rcn)
				except ValueError as e:
					return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'Error validating rcn: {str(e)}')
			else:
				# assign defaults when not provided
				if cseRequest.args.fu != FilterUsage.discoveryCriteria:	
					# Different defaults for each operation
					if cseRequest.op in [ Operation.RETRIEVE, Operation.CREATE, Operation.UPDATE ]:
						rcn = ResultContentType.attributes
					elif cseRequest.op == Operation.DELETE:
						rcn = ResultContentType.nothing
				else:
					# discovery-result-references as default for Discovery operation
					rcn = ResultContentType.discoveryResultReferences


			# Validate rcn depending on operation
			if cseRequest.op == Operation.RETRIEVE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.attributesAndChildResources,
																	ResultContentType.attributesAndChildResourceReferences,
																	ResultContentType.childResourceReferences,
																	ResultContentType.childResources,
																	ResultContentType.originalResource ]:
				return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'rcn: {rcn:d} not allowed in RETRIEVE operation')
			elif cseRequest.op == Operation.DISCOVERY and rcn not in [ ResultContentType.childResourceReferences,
																	ResultContentType.discoveryResultReferences ]:
				return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'rcn: {rcn:d} not allowed in DISCOVERY operation')
			elif cseRequest.op == Operation.CREATE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.modifiedAttributes,
																	ResultContentType.hierarchicalAddress,
																	ResultContentType.hierarchicalAddressAttributes,
																	ResultContentType.nothing ]:
				return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'rcn: {rcn:d} not allowed in CREATE operation')
			elif cseRequest.op == Operation.UPDATE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.modifiedAttributes,
																	ResultContentType.nothing ]:
				return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'rcn: {rcn:d} not allowed in UPDATE operation')
			elif cseRequest.op == Operation.DELETE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.nothing,
																	ResultContentType.attributesAndChildResources,
																	ResultContentType.childResources,
																	ResultContentType.attributesAndChildResourceReferences,
																	ResultContentType.childResourceReferences ]:
				return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'rcn: {rcn:d} not allowed in DELETE operation')
			cseRequest.args.rcn = rcn


			# RT - responseType
			cseRequest.args.rt = ResponseType(gget(fc, 'rt', ResponseType.blockingRequest))


			# RP - resultPersistence (also as timestamp)
			if (rp := gget(fc, 'rp')) is not None: 
				cseRequest.args.rp = rp
				if (rpts := Utils.toISO8601Date(Utils.fromAbsRelTimestamp(rp))) == 0.0:
					return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'"{rp}" is not a valid value for rp')
				cseRequest.args.rpts = rpts
			else:
				cseRequest.args.rp = None
				cseRequest.args.rpts = None


			#
			#	Discovery and FilterCriteria
			#
			if fc is not None:	# only when there is a filterCriteria
				for h in [ 'lim', 'lvl', 'ofst', 'arp' ]:
					if (v := gget(fc, h)) is not None:
						cseRequest.args.handling[h] = v
				for h in [ 'crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr', 'cty', 'lbl' ]:
					if (v := gget(fc, h)) is not None:
						cseRequest.args.conditions[h] = v
				if 'ty' in fc:	# Special handling for ty since this will be an array here
					if (v := gget(fc, 'ty', attributeType=BasicType.list)) is not None:
						cseRequest.args.conditions['ty'] = v
				for h in list(fc.keys()):
					cseRequest.args.attributes[h] = gget(fc, h)


			# Copy primitive content
			# Check whether content is empty and operation is UPDATE or CREATE -> Error
			if (pc := cseRequest.req.get('pc')) is None or len(pc) < 1:
				if cseRequest.op in [ Operation.CREATE, Operation.UPDATE ]:
					return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'Missing primitive content or body in request for operation: {cseRequest.op}')
			cseRequest.dict = cseRequest.req.get('pc')

		# end of try..except
		except ValueError as e:
			return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=f'Error validating attribute/parameter: {str(e)}')


		# L.logWarn(str(cseRequest))
		return Result(status=True, request=cseRequest)

	###########################################################################

	#
	#	Utilities.
	#

	def getSerializationFromOriginator(self, originator:str) -> List[ContentSerializationType]:
		"""	Look for the content serializations of a registered originator.
			It is either an AE, a CSE or a CSR.
			Return a list of types.
		"""
		if originator is None or len(originator):
			return []
		# First check whether there is an AE with that originator
		if (l := len(aes := CSE.storage.searchByFragment({ 'aei' : originator }))) > 0:
			if l > 1:
				L.logErr(f'More then one AE with the same aei: {originator}')
				return []
			csz = aes[0].csz
		# Else try whether there is a CSE or CSR
		elif (l := len(cses := CSE.storage.searchByFragment({ 'csi' : Utils.getIdFromOriginator(originator) }))) > 0:
			if l > 1:
				L.logErr(f'More then one CSE with the same csi: {originator}')
				return []
			csz = cses[0].csz
		# Else just an empty list
		else:
			return []
		# Convert the poa to a list of ContentSerializationTypes
		return [ ContentSerializationType.getType(c) for c in csz]

