#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external requests are routed through here.
#

import requests, urllib.parse
from Logging import Logging as L
from Configuration import Configuration
from Types import DesiredIdentifierResultType, FilterOperation, FilterUsage, Operation, RequestArguments, ResultContentType
from Types import RequestStatus
from Types import CSERequest
from Types import RequestHandler
from Types import JSON
from Types import ResourceTypes as T
from Types import ResponseCode as RC
from Types import ResponseType
from Types import Result
from Types import CSERequest
from Types import ContentSerializationType
from Types import Parameters
from Constants import Constants as C
from resources.REQ import REQ
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool
import CSE, Utils
from typing import Any
from copy import deepcopy


class RequestManager(object):

	def __init__(self) -> None:
		self.enableTransit 					 = Configuration.get('cse.enableTransitRequests')
		self.flexBlockingBlocking			 = Configuration.get('cse.flexBlockingPreference') == 'blocking'
		self.requestHandlers:RequestHandler = { 		# Map request handlers for operations
			Operation.RETRIEVE	: self.retrieveRequest,
			Operation.CREATE	: self.createRequest,
			Operation.UPDATE	: self.updateRequest,
			Operation.DELETE	: self.deleteRequest
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
			aes = CSE.storage.searchByTypeFieldValue(ty=T.AE, field='aei', value=originator)
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
		# Execute the actual operation
		request.op == Operation.RETRIEVE and (operationResult := CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)) is not None
		request.op == Operation.CREATE   and (operationResult := CSE.dispatcher.processCreateRequest(request, request.headers.originator)) is not None
		request.op == Operation.UPDATE   and (operationResult := CSE.dispatcher.processUpdateRequest(request, request.headers.originator)) is not None
		request.op == Operation.DELETE   and (operationResult := CSE.dispatcher.processDeleteRequest(request, request.headers.originator)) is not None

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

	def handleRequest(self, operation:Operation, request:CSERequest) -> Result:
		"""	Calls the fitting request handler for an operation and executes it.
		"""
		return self.requestHandlers[operation](request)


	def deserializeContent(self, data:bytes, mediaType:str, operation:Operation) -> Result:
		"""	Deserialize a data structure.
			Supported media serialization types are JSON and cbor.

			If successful then the Result.data contains a tuple (dict, contentType)
		"""
		dct = None
		ct = ContentSerializationType.NA
		if data is not None and len(data) > 0:
			try:
				ct = ContentSerializationType.getType(mediaType, default=CSE.defaultSerialization)
				if (dct := Utils.deserializeData(data, ct)) is None:
					return Result(rsc=RC.unsupportedMediaType, dbg=f'Unsupported media type for content-type: {ct}', status=False)
			except Exception as e:
				L.isWarn and L.logWarn('Bad request (malformed content?)')
				return Result(rsc=RC.badRequest, dbg=f'Malformed content? {str(e)}', status=False)
		
		# Check whether content is empty and operation is UPDATE or CREATE -> Error
		elif operation in [ Operation.CREATE, Operation.UPDATE ]:
			L.logWarn(dbg := f'Missing content for operation: {operation.name}')
			return Result(rsc=RC.badRequest, dbg=dbg, status=False)
		
		return Result(status=True, data=(dct, ct))



	def fillAndValidateCSERequest(self, cseRequest:CSERequest) -> Result:
		"""	Fill a `cseRequest` object according to its request structure in the *req* attribute.
		"""

		def gget(dct:dict, key:str, default:Any=None) -> Any:	# TODO Move function to Utils?
			"""	Local helper to greedy check and return a key/value from a dictionary.

				This methiod might raise a `ValueError` exception if validation of attribute/value fails.
			"""
			if (v := dct.get(key)) is not None:
				del dct[key]
				if not (res := CSE.validator.validateAttribute(key, v)).status:
					raise ValueError(res.dbg)
				return v
			return default


		# Check identifiers
		if cseRequest.id is None and cseRequest.srn is None:
			return Result(rsc=RC.notFound, request=cseRequest, dbg='missing identifier', status=False)

		# Transfer resource type
		req = cseRequest.req
		_t = req.get('ty')
		if _t is not None:
			_tt = int(_t) if _t.isdigit() else ''
			if not T.has(_tt):
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'Unknown/unsupported resource type: {_t}', status=False)
			if not (res := CSE.validator.validateAttribute('ty', _tt)).status:
				return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
			cseRequest.headers.resourceType = T(_tt)

		# transfer operation
		cseRequest.op = req.get('op')
		if cseRequest.op is None:
			L.logDebug(dbg := 'operation parameter is mandatory in request')
			return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg)		
		if not (res := CSE.validator.validateAttribute('op', cseRequest.op)).status:
			return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)

		# Transfer and check originator 
		cseRequest.headers.originator = req.get('fr')	# default empty originator
		# Test whether originator is present except when registering an AE
		if cseRequest.headers.originator is None and not (cseRequest.headers.resourceType == T.AE and cseRequest.op == Operation.CREATE):
			L.logDebug(dbg := 'From/Originator parameter is mandatory in request')
			return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)		
		if cseRequest.headers.originator is not None and not (res := CSE.validator.validateAttribute('fr', cseRequest.headers.originator)).status:
			return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
		
		# Transfer and check requestIdentifier
		cseRequest.headers.requestIdentifier = req.get('rqi')
		if cseRequest.headers.requestIdentifier is None:
			L.logDebug(dbg := 'Request Identifier is mandatory in request')
			return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg)
		if not (res := CSE.validator.validateAttribute('rqi', cseRequest.headers.requestIdentifier)).status:
			return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
		
		# Transfer and check requestExpirationTimestamp
		cseRequest.headers.requestExpirationTimestamp = req.get('rqet')
		if cseRequest.headers.requestExpirationTimestamp is not None:
			if not (res := CSE.validator.validateAttribute('rqet', cseRequest.headers.requestExpirationTimestamp)).status:
				return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
			if (ts := Utils.fromAbsRelTimestamp(cseRequest.headers.requestExpirationTimestamp)) == 0.0:
				L.logDebug(dbg := 'Error in provided Request Expiration Timestamp')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
			if ts < Utils.utcTime():
				L.logDebug(dbg := 'Request timeout')
				return Result(request=cseRequest, rsc=RC.requestTimeout, dbg=dbg)
			cseRequest.headers.requestExpirationTimestamp = Utils.toISO8601Date(ts)	# Re-assign "real" ISO8601 timestamp
		
		# Transfer and check resultExpirationTimestamp
		cseRequest.headers.resultExpirationTimestamp = req.get('rset')
		if cseRequest.headers.resultExpirationTimestamp is not None:
			if not (res := CSE.validator.validateAttribute('rset', cseRequest.headers.resultExpirationTimestamp)).status:
				return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
			if (ts := Utils.fromAbsRelTimestamp(cseRequest.headers.resultExpirationTimestamp)) == 0.0:
				L.logDebug(dbg := 'Error in provided Result Expiration Timestamp')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
			if ts < Utils.utcTime():
				L.logDebug(dbg := 'Result timeout')
				return Result(request=cseRequest, rsc=RC.requestTimeout, dbg=dbg)
			cseRequest.headers.resultExpirationTimestamp = Utils.toISO8601Date(ts)	# Re-assign "real" ISO8601 timestamp

		# Transfer and check operationExecutionTime
		cseRequest.headers.operationExecutionTime = req.get('oet')	# TODO check when supported
		if cseRequest.headers.operationExecutionTime is not None:
			if not (res := CSE.validator.validateAttribute('oet', cseRequest.headers.operationExecutionTime)).status:
				return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
			if (ts := Utils.fromAbsRelTimestamp(cseRequest.headers.operationExecutionTime)) == 0.0:
				L.logDebug(dbg := 'Error in provided Operation Execution Time')
				return Result(request=cseRequest, rsc=RC.badRequest, dbg=dbg, status=False)
			cseRequest.headers.operationExecutionTime = Utils.toISO8601Date(ts)	# Re-assign "real" ISO8601 timestamp

		# Transfer and check releaseVersionIndicator
		cseRequest.headers.releaseVersionIndicator = req.get('rvi')	
		if cseRequest.headers.releaseVersionIndicator is None:
			L.logDebug(dbg := 'Release Version Indicator paraneter is mandatory in request')
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=dbg, status=False)
		if not (res := CSE.validator.validateAttribute('rvi', cseRequest.headers.releaseVersionIndicator)).status:
			return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)
		if cseRequest.headers.releaseVersionIndicator not in C.supportedReleaseVersions:
			return Result(rsc=RC.releaseVersionNotSupported, request=cseRequest, dbg=f'Release version not supported: {cseRequest.headers.releaseVersionIndicator}')

		# Transfer responseTypeNUs
		cseRequest.headers.responseTypeNUs = req.get('rtu')	#  TODO validate for url?
		if cseRequest.headers.responseTypeNUs is not None:
			if not (res := CSE.validator.validateAttribute('rtu', cseRequest.headers.responseTypeNUs)).status:
				return Result(request=cseRequest, rsc=res.rsc, dbg=res.dbg, status=False)

		#
		# Transfer filterCriteria: handling, conditions and attributes
		#

		cseRequest.args = RequestArguments()
		fc = deepcopy(req.get('fc'))	# copy because we will greedy consume attributes here

		# FU - Filter Usage
		try:
			if (fu := gget(fc, 'fu', FilterUsage.conditionalRetrieval)) is not None:
				cseRequest.args.fu = FilterUsage(int(fu))
				if cseRequest.args.fu == FilterUsage.discoveryCriteria and cseRequest.op == Operation.RETRIEVE:	# correct operation if necessary
					cseRequest.op = Operation.DISCOVERY
		except ValueError as e:
			return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=str(e))
	
		# DRT - Desired Identifier Result Type
		try:
			if (drt := gget(fc, 'drt', DesiredIdentifierResultType.structured)) is not None: # 1=strucured, 2=unstructured
				cseRequest.args.drt = DesiredIdentifierResultType(int(drt))
		except ValueError as e:
			return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=str(e))

		# FO - Filter Operation
		try:
			if (fo := gget(fc, 'fo', FilterOperation.AND)) is not None: 
				cseRequest.args.fo = FilterOperation(int(fo))
		except ValueError as e:
			return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=str(e))


		# RCN Result Content Type
		try:
			if (rcn := gget(fc, 'rcn')) is not None: 
				rcn = ResultContentType(int(rcn))
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
				return None, Operation.NA, f'rcn: {rcn:d} not allowed in RETRIEVE operation'
			elif cseRequest.op == Operation.DISCOVERY and rcn not in [ ResultContentType.childResourceReferences,
																	ResultContentType.discoveryResultReferences ]:
				return None, Operation.NA, f'rcn: {rcn:d} not allowed in DISCOVERY operation'
			elif cseRequest.op == Operation.CREATE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.modifiedAttributes,
																	ResultContentType.hierarchicalAddress,
																	ResultContentType.hierarchicalAddressAttributes,
																	ResultContentType.nothing ]:
				return None, Operation.NA, f'rcn: {rcn:d} not allowed in CREATE operation'
			elif cseRequest.op == Operation.UPDATE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.modifiedAttributes,
																	ResultContentType.nothing ]:
				return None, Operation.NA, f'rcn: {rcn:d} not allowed in UPDATE operation'
			elif cseRequest.op == Operation.DELETE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.nothing,
																	ResultContentType.attributesAndChildResources,
																	ResultContentType.childResources,
																	ResultContentType.attributesAndChildResourceReferences,
																	ResultContentType.childResourceReferences ]:
				return None, Operation.NA, f'rcn:  not allowed DELETE operation'

			cseRequest.args.rcn = rcn
		except ValueError as e:
			return Result(status=False, rsc=RC.badRequest, request=cseRequest, dbg=str(e))






		# continue here


		cseRequest.args.rt 		= gget(fc, 'rt', cseRequest.args.rt)
		cseRequest.args.rp 		= gget(fc, 'rp', cseRequest.args.rp)
		cseRequest.args.rpts 	= gget(fc, 'rpts', cseRequest.args.rpts)

		for h in [ 'lim', 'lvl', 'ofst', 'arp' ]:
			if (v := gget(fc, h)) is not None:
				cseRequest.args.handling[h] = v
		for h in [ 'crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr', 'ty', 'cty', 'lbl' ]:
			if (v := gget(fc, h)) is not None:
				cseRequest.args.conditions[h] = v
		for h in list(fc.keys()):
			cseRequest.args.attributes[h] = gget(fc, h)
		
		# Transfer primitive content
		cseRequest.dict = req.get('pc')

		return Result(status=True, request=cseRequest)



