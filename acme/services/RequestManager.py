#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	RequestManager module.
	
	Main request dispatcher. All external requests are routed through here.
"""

from __future__ import annotations
from typing import Any, List, Tuple, cast, Dict, Optional, Union

import urllib.parse
from copy import deepcopy
from threading import Lock

from ..etc.Types import JSON, BasicType, DesiredIdentifierResultType, FilterOperation, ResourceTypes
from ..etc.Types import FilterUsage, Operation, RequestCallback, RequestType
from ..etc.Types import ResponseStatusCode, ResultContentType, RequestStatus, CSERequest, RequestHandler
from ..etc.Types import ResourceTypes, ResponseStatusCode, ResponseType, Result, EventCategory
from ..etc.Types import CSERequest, ContentSerializationType, RequestResponseList, RequestResponse
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.ResponseStatusCodes import BAD_REQUEST, NOT_FOUND, REQUEST_TIMEOUT, RELEASE_VERSION_NOT_SUPPORTED
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED, REQUEST_TIMEOUT, TARGET_NOT_REACHABLE
from ..etc.DateUtils import getResourceDate, fromAbsRelTimestamp, utcTime, waitFor, toISO8601Date, fromDuration
from ..etc.RequestUtils import requestFromResult, determineSerialization, deserializeContent
from ..etc.IDUtils import isCSERelative, toSPRelative, isValidCSI, isValidAEI, uniqueRI, isAbsolute, isSPRelative, localResourceID, getIdFromOriginator
from ..etc.ACMEUtils import compareIDs, getIDFromPath
from ..etc.ACMEUtils import isStructured, structuredPathFromRI
from ..etc.Utils import isAcmeUrl, isCoAPUrl, isHttpUrl, isMQTTUrl, isWSUrl
from ..etc.Utils import isURL
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.TextTools import setXPath
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..resources.Resource import Resource
from ..resources.CSEBase import getCSE
from ..resources.REQ import REQ
from ..resources.PCH import PCH
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..runtime.Logging import Logging as L

# Type definition
TargetDetails = List[ 						#type: ignore[misc]
					Tuple[str, 				# Real target URL,incl protocol			
						  List[str],		# allowed content serializations
						  str, 				# Target's supported release version
						  PCH, 				# PollingChannel resource, if this is to be used 
						  str, 				# Originator with adapted scope
						  str, 				# Targets ID (to)
						  ResourceTypes,	# Target's resource type
						  bool				# True if the target is a direct URL
				] ]	


# This factor determines how often the monitor looks for expired request resources
expirationCheckFactor = 2.0

class RequestManager(object):
	"""	RequestManager class.
	"""

	__slots__ = (
		'_requestLock',
		'_requests',
		'_rqiOriginator',
		'_pcWorker',
		'_receivedResponses',
		'_receivedResponsesLock',


		'requestHandlers',
		'flexBlockingBlocking',
		'requestExpirationDelta',
		'maxExpirationDelta',
		'sendToFromInResponses',
		'enableRequestRecording',

		'_eventRequestReceived',
		'_eventRequestReceived',
		'_eventCoAPSendRetrieve',
		'_eventCoAPSendCreate',
		'_eventCoAPSendUpdate',
		'_eventCoAPSendDelete',
		'_eventCoAPSendNotify',
		'_eventHttpSendRetrieve',
		'_eventHttpSendCreate',
		'_eventHttpSendUpdate',
		'_eventHttpSendDelete',
		'_eventHttpSendNotify',
		'_eventMqttSendRetrieve',
		'_eventMqttSendCreate',
		'_eventMqttSendUpdate',
		'_eventMqttSendDelete',
		'_eventMqttSendNotify',
		'_eventWsSendRetrieve',
		'_eventWsSendCreate',
		'_eventWsSendUpdate',
		'_eventWsSendDelete',
		'_eventWsSendNotify',
		'_eventAcmeSendNotify',
	)

	def __init__(self) -> None:

		# Configuration values
		self._assignConfig()	

		#
		#	Structures for pollingChannel requests
		#
		self._requestLock = Lock()
		""" Lock to access the following two dictionaries."""

		self._requests:Dict[str, List[ Tuple[CSERequest, RequestType] ] ] = {}
		""" Dictionary to map request originators to a list of reqeests. Used for handling polling requests."""
		
		self._rqiOriginator:Dict[str, str] = {}
		""" Dictionary to map requestIdentifiers to an originator of a request. Used for handling of polling requests."""
		
		self._pcWorker = BackgroundWorkerPool.newWorker(self.requestExpirationDelta * expirationCheckFactor, self._cleanupPollingRequests, name='pollingChannelExpiration').start()
		""" Worker to clean up expired polling requests."""

		self._receivedResponses:Dict[str, Tuple[Result, str]] = {}
		""" Dictionary to store received responses for non-blocking requests."""

		self._receivedResponsesLock = Lock()
		""" Lock to access the received responses dictionary."""

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)	# type: ignore

		# Optimized access to events
		self._eventRequestReceived = CSE.event.requestReceived		# type:ignore [attr-defined]
		""" Event for received requests. """

		self._eventCoAPSendRetrieve = CSE.event.coapSendRetrieve 	# type: ignore [attr-defined]
		""" Event for sending a RETRIEVE request via CoAP. """

		self._eventCoAPSendCreate = CSE.event.coapSendCreate		# type: ignore [attr-defined]
		""" Event for sending a CREATE request via CoAP. """

		self._eventCoAPSendUpdate = CSE.event.coapSendUpdate		# type: ignore [attr-defined]
		""" Event for sending an UPDATE request via CoAP. """

		self._eventCoAPSendDelete = CSE.event.coapSendDelete		# type: ignore [attr-defined]
		""" Event for sending a DELETE request via CoAP. """

		self._eventCoAPSendNotify = CSE.event.coapSendNotify		# type: ignore [attr-defined]
		""" Event for sending a NOTIFY request via CoAP. """

		self._eventHttpSendRetrieve = CSE.event.httpSendRetrieve 	# type: ignore [attr-defined]
		""" Event for sending a RETRIEVE request via HTTP. """

		self._eventHttpSendCreate = CSE.event.httpSendCreate		# type: ignore [attr-defined]
		""" Event for sending a CREATE request via HTTP. """

		self._eventHttpSendUpdate = CSE.event.mqttSendUpdate		# type: ignore [attr-defined]
		""" Event for sending an UPDATE request via HTTP. """

		self._eventHttpSendDelete = CSE.event.httpSendDelete		# type: ignore [attr-defined]
		""" Event for sending a DELETE request via HTTP. """

		self._eventHttpSendNotify = CSE.event.httpSendNotify		# type: ignore [attr-defined]
		""" Event for sending a NOTIFY request via HTTP. """

		self._eventMqttSendRetrieve = CSE.event.mqttSendRetrieve	# type: ignore [attr-defined]
		""" Event for sending a RETRIEVE request via MQTT. """

		self._eventMqttSendCreate = CSE.event.mqttSendCreate		# type: ignore [attr-defined]
		""" Event for sending a CREATE request via MQTT. """

		self._eventMqttSendUpdate = CSE.event.httpSendUpdate		# type: ignore [attr-defined]
		""" Event for sending an UPDATE request via MQTT. """

		self._eventMqttSendDelete = CSE.event.mqttSendDelete		# type: ignore [attr-defined]
		""" Event for sending a DELETE request via MQTT. """

		self._eventMqttSendNotify = CSE.event.mqttSendNotify		# type: ignore [attr-defined]
		""" Event for sending a NOTIFY request via MQTT. """

		self._eventWsSendRetrieve = CSE.event.wsSendRetrieve		# type: ignore [attr-defined]
		""" Event for sending a RETRIEVE request via WebSocket. """

		self._eventWsSendCreate = CSE.event.wsSendCreate			# type: ignore [attr-defined]
		""" Event for sending a CREATE request via WebSocket. """

		self._eventWsSendUpdate = CSE.event.wsSendUpdate			# type: ignore [attr-defined]
		""" Event for sending an UPDATE request via WebSocket. """

		self._eventWsSendDelete = CSE.event.wsSendDelete			# type: ignore [attr-defined]
		""" Event for sending a DELETE request via WebSocket. """

		self._eventWsSendNotify = CSE.event.wsSendNotify			# type: ignore [attr-defined]
		""" Event for sending a NOTIFY request via WebSocket. """
		
		self._eventAcmeSendNotify = CSE.event.acmeNotification		# type: ignore [attr-defined]
		""" Event for sending a NOTIFY request via ACME internally. """


		# Map request handlers and events for operations in the RequestManager and the dispatcher
		self.requestHandlers:RequestHandler = { 		
			Operation.RETRIEVE	: RequestCallback(self.retrieveRequest, 
												  CSE.dispatcher.processRetrieveRequest, 
												  self._sendRequest,
												  self._eventCoAPSendRetrieve,
												  self._eventHttpSendRetrieve,
												  self._eventMqttSendRetrieve,
												  self._eventWsSendRetrieve),
												#   self.sendRetrieveRequest),
			Operation.DISCOVERY	: RequestCallback(self.retrieveRequest, 
												  CSE.dispatcher.processRetrieveRequest, 
												  self._sendRequest,
												  self._eventCoAPSendRetrieve,
												  self._eventHttpSendRetrieve,
												  self._eventMqttSendRetrieve,
												  self._eventWsSendRetrieve),
												#   self.sendRetrieveRequest),
			Operation.CREATE	: RequestCallback(self.createRequest,
												  CSE.dispatcher.processCreateRequest,
												  self._sendRequest,
												  self._eventCoAPSendCreate,
												  self._eventHttpSendCreate,
												  self._eventMqttSendCreate,
												  self._eventWsSendCreate),
												#   self.sendCreateRequest),
			Operation.UPDATE	: RequestCallback(self.updateRequest,
												  CSE.dispatcher.processUpdateRequest,
												  self._sendRequest,
												  self._eventCoAPSendUpdate,
												  self._eventHttpSendUpdate,
												  self._eventMqttSendUpdate,
												  self._eventWsSendUpdate),
												#   self.sendUpdateRequest),
			Operation.DELETE	: RequestCallback(self.deleteRequest,
												  CSE.dispatcher.processDeleteRequest,
												  self._sendRequest,
												  self._eventCoAPSendDelete,
												  self._eventHttpSendDelete,
												  self._eventMqttSendDelete,
												  self._eventWsSendDelete),
												#   self.sendDeleteRequest),
			Operation.NOTIFY	: RequestCallback(self.notifyRequest,
												  CSE.dispatcher.processNotifyRequest,
												  self._sendRequest,
												  self._eventCoAPSendNotify,
												  self._eventHttpSendNotify,
												  self._eventMqttSendNotify,
												  self._eventWsSendNotify),
												#   self.sendNotifyRequest),
		}

		L.isInfo and L.log('RequestManager initialized')


	def shutdown(self) -> bool:
		# Stop the PollingChannel Cleanup worker
		if self._pcWorker:
			self._pcWorker.stop()
		L.isInfo and L.log('RequestManager shut down')
		return True

	
	def restart(self, name:str) -> None:
		"""	Restart the registrationManager service.
		"""
		# Terminate waiting request and pollingQueue actors
		BackgroundWorkerPool.removeWorkers('request_*')
		BackgroundWorkerPool.removeWorkers('unqueuePolling_*')

		# empty polling channel queues
		with self._requestLock:
			self._requests = {}
			self._rqiOriginator = {}
		L.logDebug('RequestManager restarted')
	

	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.flexBlockingBlocking = Configuration.cse_flexBlockingPreference == 'blocking'
		self.requestExpirationDelta = Configuration.cse_requestExpirationDelta
		self.maxExpirationDelta = Configuration.cse_maxExpirationDelta
		self.sendToFromInResponses = Configuration.cse_sendToFromInResponses
		self.enableRequestRecording	= Configuration.cse_operation_requests_enable


	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in ( 'cse.flexBlockingPreference', 
				 		'cse.requestExpirationDelta', 
						'cse.maxExpirationDelta', 
						'cse.operation.requests.enable'):
			return

		# Configuration values
		self._assignConfig()

		# restart expiration worker
		if self._pcWorker:
			self._pcWorker.restart(self.requestExpirationDelta * expirationCheckFactor)


	#########################################################################
	#
	# 	Incoming Requests
	#

	def handleRequest(self, request:Union[CSERequest, JSON]) -> Result:
		"""	Calls the fitting request handler for an operation and let that handle the request.

			Before the request is processed it will be determined whether it is blocking or
			non-blocking etc.

			Args:
				request: The incoming request.
			Return:
				Request result.
		"""
		# Convert JSON to CSERequest
		if isinstance(request, dict):
			request = CSE.request.fillAndValidateCSERequest(request)
		# L.logDebug(f'Handling request: {request}')

		# Send event
		self._eventRequestReceived(request)

		# Validate partial RETRIEVE first
		# partial RETRIEVE: convert single fragment ID
		if '#' in request.to:
			to, _, attr = request.to.partition('#')
			request.id = to
			request.to = to
			request.pc = { 'm2m:atrl': [ attr ] }

		# Check that the operation is actually allowed
		if request.pc and 'm2m:atrl' in request.pc:
			if request.op != Operation.RETRIEVE:
				return Result(rsc = ResponseStatusCode.BAD_REQUEST, 
							  dbg = L.logWarn(f'Partial retrieve is only valid for RETRIEVE (was: {request.op})'))
			if request.rcn not in [ ResultContentType.attributes, ResultContentType.originalResource ]:
				return Result(rsc = ResponseStatusCode.BAD_REQUEST,
							  dbg = L.logWarn(f'Partial retrieve is only valid for rcn=1 or rcn=7 (was: {request.rcn})'))

		# Call the appropriate request function
		try:
			res = self.requestHandlers[request.op].ownRequest(request)
		except ResponseException as e:
			res = Result(rsc = e.rsc, dbg = e.dbg, request = e.data)

		# Add to requests database
		self.recordRequest(request, res)

		return res


	def processRequest(self, request:CSERequest, originator:str, id:str) -> Result:
		"""	Calls the fitting request process handler for an operation and call it.

			This will directly handle the request. 

			Args:
				originator: The request originator.
				id: The structured or unstructured resource id.
			Result:
				Request result
		"""
		return self.requestHandlers[request.op].dispatcherRequest(request, originator, id)
	

	def handleReceivedNotifyRequest(self, id:str, request:CSERequest, originator:str) -> Result:
		"""	Handle a NOTIFY request to resource.
		"""
		L.isDebug and L.logDebug(f'NOTIFY request to resource: {id}. Originator: {originator}')

		# Check content
		if request.pc is None:
			raise BAD_REQUEST(L.logDebug(f'Missing content/request in notification'))

		# Forward the notification as received to the target
		#return self.handleSendRequest(CSERequest(op = Operation.NOTIFY,
		#										 to = id,
		#										 originator = originator,
		#										 pc = request.originalRequest)
		#							 )[0].result	# there should be at least one result

		return self.handleSendRequest(request)[0].result  # there should be at least one result


	#########################################################################
	#
	#	RETRIEVE Request
	#

	def retrieveRequest(self, request:CSERequest) ->  Result:
		L.isDebug and L.logDebug(f'RETRIEVE ID: {request.id if request.id else request.srn}, originator: {request.originator}')
		
		match request.rt:
			case ResponseType.blockingRequest | ResponseType.noResponse:	# "no reponse" is always handled as blocking
				return CSE.dispatcher.processRetrieveRequest(request, request.originator)
			case ResponseType.nonBlockingRequestSynch | ResponseType.nonBlockingRequestAsynch:
				return self._handleNonBlockingRequest(request)
			case ResponseType.flexBlocking:
				if self.flexBlockingBlocking:			# flexBlocking as blocking
					return CSE.dispatcher.processRetrieveRequest(request, request.originator)
				else:									# flexBlocking as non-blocking
					return self._handleNonBlockingRequest(request)

		raise BAD_REQUEST(f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	CREATE resources
	#

	def createRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'CREATE ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Check contentType and resourceType
		if request.ty == None:
			raise BAD_REQUEST('missing or wrong resourceType in request')

		match request.rt:
			case ResponseType.blockingRequest | ResponseType.noResponse:	# "no reponse" is always handled as blocking
				return CSE.dispatcher.processCreateRequest(request, request.originator)
			case ResponseType.nonBlockingRequestSynch | ResponseType.nonBlockingRequestAsynch:
				return self._handleNonBlockingRequest(request)
			case ResponseType.flexBlocking:
				if self.flexBlockingBlocking:			# flexBlocking as blocking
					return CSE.dispatcher.processCreateRequest(request, request.originator)
				else:									# flexBlocking as non-blocking
					return self._handleNonBlockingRequest(request)

		raise BAD_REQUEST(f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	UPDATE resources
	#

	def updateRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'UPDATE ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Don't update the CSEBase
		if request.id == RC.cseRi:
			raise OPERATION_NOT_ALLOWED('operation not allowed for CSEBase')

		# Check contentType and resourceType
		match request.rt:
			case ResponseType.blockingRequest | ResponseType.noResponse:	# "no reponse" is always handled as blocking
				return CSE.dispatcher.processUpdateRequest(request, request.originator)
			case ResponseType.nonBlockingRequestSynch | ResponseType.nonBlockingRequestAsynch:
				return self._handleNonBlockingRequest(request)
			case ResponseType.flexBlocking:
				if self.flexBlockingBlocking:			# flexBlocking as blocking
					return CSE.dispatcher.processUpdateRequest(request, request.originator)
				else:									# flexBlocking as non-blocking
					return self._handleNonBlockingRequest(request)

		raise BAD_REQUEST(f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	DELETE resources
	#


	def deleteRequest(self, request:CSERequest,) -> Result:
		L.isDebug and L.logDebug(f'DELETE ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Don't delete the CSEBase
		if request.id in [ RC.cseRi, RC.cseRn ]:
			raise OPERATION_NOT_ALLOWED('DELETE operation is not allowed for CSEBase')

		match request.rt:
			case ResponseType.blockingRequest | ResponseType.noResponse:	# "no reponse" is always handled as blocking	
				return CSE.dispatcher.processDeleteRequest(request, request.originator)
			case ResponseType.nonBlockingRequestSynch | ResponseType.nonBlockingRequestAsynch:
				return self._handleNonBlockingRequest(request)
			case ResponseType.flexBlocking:								# flexBlocking as non-blocking
				if self.flexBlockingBlocking:			# flexBlocking as blocking
					return CSE.dispatcher.processDeleteRequest(request, request.originator)
				else:									# flexBlocking as non-blocking
					return self._handleNonBlockingRequest(request)
			
		raise BAD_REQUEST(f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	Notify resources
	#

	def notifyRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'NOTIFY ID: {request.id if request.id else request.srn}, originator: {request.originator}')


		match request.rt:
			case ResponseType.blockingRequest | ResponseType.noResponse:	# "no reponse" is always handled as blocking	
				return CSE.dispatcher.processNotifyRequest(request, request.originator)
			case ResponseType.nonBlockingRequestSynch | ResponseType.nonBlockingRequestAsynch:
				return self._handleNonBlockingRequest(request)
			case ResponseType.flexBlocking:
				if self.flexBlockingBlocking:			# flexBlocking as blocking
					return CSE.dispatcher.processNotifyRequest(request, request.originator)
				else:									# flexBlocking as non-blocking
					return self._handleNonBlockingRequest(request)

		raise BAD_REQUEST(f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	<request> handling
	#

	def _createRequestResource(self, request:CSERequest) -> Resource:

		# Get initialized resource
		resource = REQ.createRequestResource(request)

		# Register <request>
		cseres = getCSE()
		CSE.registration.checkResourceCreation(resource, request.originator, cseres)
		
		# set the CSE.ri as indicator that this resource was created internally
		resource.setCreatedInternally(cseres.pi)

		# create <request>
		return CSE.dispatcher.createLocalResource(resource, cseres, request.originator)


	def _handleNonBlockingRequest(self, request:CSERequest) -> Result:
		"""	This method creates a <request> resource, initiates the execution of the desired operation in
			the background, but immediately returns with the reference of the <request> resource that
			will contain the result of the operation.
		"""

		L.isDebug and L.logDebug(f'handleNonBlockingRequest: {request.rqi}')

		# Create the <request> resource first
		resource =  self._createRequestResource(request)

		# Synchronous handling
		if request.rt == ResponseType.nonBlockingRequestSynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(self._runNonBlockingRequestSync, 
										  name = f'request_{request.rqi}').start(request = request, reqRi = resource.ri)
			# Create the response content with the <request> ri 
			return Result(data = { 'm2m:uri' : resource.ri }, rsc = ResponseStatusCode.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)

		# Asynchronous handling
		if request.rt == ResponseType.nonBlockingRequestAsynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(self._runNonBlockingRequestAsync, name = f'request_{request.rqi}').start(request = request, reqRi = resource.ri)
			# Create the response content with the <request> ri 
			return Result(data = { 'm2m:uri' : resource.ri }, rsc = ResponseStatusCode.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)

		# Error
		raise BAD_REQUEST(f'Unknown or unsupported ResponseType: {request.rt}')


	def _runNonBlockingRequestSync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
		"""
		L.isDebug and L.logDebug('Executing nonBlockingRequestSync')
		self._executeOperation(request, reqRi)
		return True


	def _runNonBlockingRequestAsync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
			In addition notify the notification targets.
		"""
		L.isDebug and L.logDebug('Executing nonBlockingRequestAsync')
		_originalRtu = request.rtu
		request.rtu = None	# remove and store RTU. We don't want to forward this attribute
		try:
			req = self._executeOperation(request, reqRi)
		except ResponseException:
			return False
		request.rtu = _originalRtu	# restore RTU

		L.isDebug and L.logDebug('Sending result notifications for nonBlockingRequestAsynch')
		# TODO move the notification to the notificationManager

		# The result contains the request resource  (the one from the actual operation).
		# So we can just copy the individual attributes
		# originator = result.resource['ors/fr']
		# originator = RC.cseCsi
		to = req['ors/to']
		responseNotification = {
			'm2m:rsp' : {
				'rsc' : req['ors/rsc'],
				'rqi' : req['ors/rqi'],
				'pc' : req['ors/pc'],
				'to'  : to,
				# 'fr'  : originator,
				'fr' : req['ors/fr'],
				'rvi' : request.rvi	# This is the rvi from the original request
		}}

		if (nus := request.rtu) is None:	# might be an empty list
			# RTU is not set, get POA's from the resp. AE.poa
			# aes = CSE.storage.searchByFragment({ 'ty' : ResourceTypes.AE, 'aei' : to })	# search all <AE>s for aei=originator
			# if len(aes) != 1:
			# 	L.isWarn and L.logWarn(f'Wrong number of AEs with aei: {to} ({len(aes):d}): {str(aes)}')
			# 	nus = aes[0].poa
			# else:
			# 	L.isDebug and L.logDebug(f'No RTU. Get NUS from originator ae: {aes[0].ri}')
			# 	nus = aes[0].poa
			L.isDebug and L.logDebug(f'No RTU. Get NUS from originator ae: {to}')
			nus = [ to ]

		# send notifications.Ignore any errors here
		CSE.notification.sendNotificationWithDict(responseNotification, nus, originator = RC.cseCsi)

		return True


	def _executeOperation(self, request:CSERequest, reqRi:str) -> REQ:
		"""	Execute a request operation and fill the respective request resource
			accordingly.

			Args:
				request: The request to execute.
				reqRi: The <request> resource id.
			
			Return:	
				The <request> resource.
		"""
		# Execute the actual operation in the dispatcher
		pc = None
		try:
			try:
				operationResult = self.requestHandlers[request.op].dispatcherRequest(request, request.originator)
			except REQUEST_TIMEOUT:
				pass
			except ResponseException as e:
				raise e

			# attributes set below in the request
			rs = RequestStatus.COMPLETED
			rsc = operationResult.rsc

			# Check whether the response contains a resource
			if operationResult.resource:
				if isinstance(operationResult.resource, Resource):
					pc = operationResult.resource.asDict()
				else:
					# Handle and remove the internal incomplete indicator
					if operationResult.resource.get('acme:incomplete'):
						rs = RequestStatus.PARTIALLY_COMPLETED
						del operationResult.resource['acme:incomplete']
					pc = operationResult.resource
			
			# Check whether the response is a request. This could be the
			# case when forwarding a request to a remote CSE.
			elif operationResult.request:
				pc = operationResult.request.pc

		
		except ResponseException as e:
			# attributes set below in the request
			rs = RequestStatus.FAILED
			rsc = e.rsc
			if e.dbg:
				pc = { 'm2m:dbg' : e.dbg }

		# Retrieve the <request> resource
		reqres = cast(REQ, CSE.dispatcher.retrieveResource(reqRi, originator = request.originator))

		# Fill the <request>
		reqres['ors'] = {	# operationResult
			'rsc' : rsc,				# set response status code
			'rqi' : reqres.rid,			# request ID
			'to' : request.originator,	# request originator
			'fr' : RC.cseCsi,			# from: hosting CSE
			'ot' : reqres['mi/ot'],		# timestamp
			'rset' : reqres.et,			# expiration timestamp
		}
		reqres['rs'] = rs				# update request status

		if pc:
			reqres['ors/pc'] = pc		# assign content

		# Update lt etc attributes
		reqres.update()

		# Update in DB
		reqres.dbUpdate(True)

		return reqres


	###########################################################################
	#
	#	Handling of Transit requests. Forward requests to the resp. remote CSE's.
	#

	def handleTransitRetrieveRequest(self, request:CSERequest) -> Result:
		""" Forward a RETRIEVE request to a remote CSE """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		# L.isDebug and L.logDebug(f'Forwarding RETRIEVE/DISCOVERY request to: {res.data}')
		L.isDebug and L.logDebug(f'Forwarding RETRIEVE/DISCOVERY request to: {request.id}')
		return self.handleSendRequest(request)[0].result		# there should be at least one result


	def handleTransitCreateRequest(self, request:CSERequest) -> Result:
		""" Forward a CREATE request to a remote CSE. """
		
		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding CREATE request to: {request.id}')
		return self.handleSendRequest(request)[0].result	# there should be at least one result


	def handleTransitUpdateRequest(self, request:CSERequest) -> Result:
		""" Forward an UPDATE request to a remote CSE. """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding UPDATE request to: {request.id}')
		return self.handleSendRequest(request)[0].result	# there should be at least one result


	def handleTransitDeleteRequest(self, request:CSERequest) -> Result:
		""" Forward a DELETE request to a remote CSE. """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding DELETE request to: {request.id}')
		return self.handleSendRequest(request)[0].result	# there should be at least one result


	def handleTransitNotifyRequest(self, request:CSERequest) -> Result:
		""" Forward a NOTIFY request to a remote CSE. """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding NOTIFY request to: {request.id}')
		return self.handleSendRequest(request)[0].result	# there should be at least one result


	def _originatorToSPRelative(self, request:CSERequest) -> None:
		"""	Convert *from* to SP-relative format in the request. The *from* is converted in
			*request.originator* and *request.originalRequest*, but NOT in 
			*request.originalData*.
		
			See TS-0004, 7.3.2.6, Forwarding
		"""
		if isCSERelative(request.originator):
			request.originator = toSPRelative(request.originator)
			if request.originalRequest:
				setXPath(request.originalRequest, 'fr', request.originator, overwrite = True)	# Also in the original request
			# Attn: not changed in originatData !


	##############################################################################
	#
	#	Request/Response async sequence helpers for Polling
	#
	#	All the requests for all PCU are stored in a single dictionary:
	#		originator : [ request* ]
	#

	def hasPollingRequest(self, originator:str, requestID:str = None, reqType:RequestType = RequestType.REQUEST) -> bool:
		"""	Check whether there is a pending request or response pending for the tuple (*originator*, *requestID*).
			This method is also used as a callback for periodic check whether a request or response is queued.
			If *requestID* is not *None* then the check is for a request with that ID. 
			Otherwise, *True* will be returned if there is any request for the *originator*.
		"""
		with self._requestLock:
			return (lst := self._requests.get(originator)) is not None and any(	 (r, t) for r,t in lst if (requestID is None or r.rqi == requestID) and (t == reqType) )

	
	def queuePollingRequest(self, request:CSERequest, reqType:RequestType=RequestType.REQUEST) -> None:
		"""	Add a new *request* to the polling request queue. 
		
			The *reqType* specifies whether this request is a oneM2M Request or Response.
		"""
		L.isDebug and L.logDebug(f'Add request to queue, reqestType: {reqType}')

		# Some checks
		if not request.rqet:		
			# Adding a default expiration if none is set in the request
			ret = getResourceDate(self.requestExpirationDelta)
			L.isDebug and L.logDebug(f'Request must have a "requestExpirationTimestamp". Adding a default one: {ret}')
			request.rqet = ret
			request._rqetUTCts = fromAbsRelTimestamp(ret)
		
		# Why don't we handle the Result Expiration Timestamo request parameter here? Because it must be
		# greater than the Request Expiration Timestamp, so the reqeust expires at that timestamp first anyway.

		if not request.rqi:
			L.logErr(f'Request must have a "requestIdentifier". Ignored. {request}', showStackTrace=False)
			return
		
		# If no id? Try to determine it via the requestID
		if not request.id and reqType == RequestType.RESPONSE:
			with self._requestLock:
				request.id = self._rqiOriginator.pop(request.rqi)	# get and remove from dictionary

		if not request.id:
			L.logErr(f'Request must have a target originator. Ignored. {request}', showStackTrace=False)
			return
		
		# Add to queue
		with self._requestLock:
			if not (originator := request.id) in self._requests:
				self._requests[originator] = [ (request, reqType) ]
			else:
				self._requests[originator].append( (request, reqType) )
			# store mapping between RQI and request originator
			self._rqiOriginator[request.rqi] = request.originator

			if reqType == RequestType.RESPONSE:
				del self._rqiOriginator[request.rqi]

		
		# Start an actor to remove the request after the timeout		
		BackgroundWorkerPool.newActor(	lambda: self.unqueuePollingRequest(originator, request.rqi, reqType), 
										delay = request._rqetUTCts - utcTime() + 1.0,	# +1 second delay 
										name = f'unqueuePolling_{request.rqi}-{reqType}').start()
	

	def unqueuePollingRequest(self, originator:str, requestID:str, reqType:RequestType) -> CSERequest:
		"""	Remove a request for the *originator* and with the *requestID* from the polling request queue. 
		"""
		L.isDebug and L.logDebug(f'Unqueuing polling request, originator: {originator}, requestID: {requestID}')
		with self._requestLock:
			resultRequest = None
			if lst := self._requests.get(originator):
				requests = []
				
				# extract the queried request or the first one found, and build a new list for the remaining
				# Building a new list is faster than extracting and removing elements in place
				for r,t in lst:	
					if (requestID is None or requestID == r.rqi) and t == reqType and not resultRequest:	# Either get an uspecified reuqest, or a specific one
						resultRequest = r
					else:
						requests.append( (r, t) )
				if requests:
					self._requests[originator] = requests
				else:
					del self._requests[originator]
				
			if resultRequest:
				BackgroundWorkerPool.stopWorkers(f'unqueuePolling_{resultRequest.rqi}-{reqType}')
					
			return resultRequest


	def waitForPollingRequest(self, originator:str, 
									requestID:str, 
									timeout:float, 
									reqType:Optional[RequestType] = RequestType.REQUEST, 
									aggregate:Optional[bool] = False) -> Result:
		"""	Busy waiting for a polling request.
			The function returns when there is a new or pending matching request in the queue, or when the
			*timeout* (in seconds) is met.
			
			Args:
				originator: Request originator to match.
				requestID: Request Identifier to match. Might be *None* to match all request IDs.
				timeout: Timeout in seconds for the polling request to wait.
				reqType: Match request or response.
				aggregate: Boolean indicating whether all the available requests shall be returned in one aggregation, or separately.
			Return:
				 The function returns a Result object with the request or aggregated requests in the `request` attribute.
		"""
		L.isDebug and L.logDebug(f'Waiting for: {reqType} for originator: {originator}, requestID: {requestID}')

		if waitFor(timeout, lambda:self.hasPollingRequest(originator, requestID, reqType)):	# Wait until timeout, or the request of the correct type was found
			L.isDebug and L.logDebug(f'Received {reqType} request for originator: {originator}, requestID: {requestID}, aggregate: {aggregate}')

			if aggregate:
				lst:list[CSERequest] = []
				while True:
					if req := self.unqueuePollingRequest(originator, requestID, reqType):
						lst.append(req)
						continue
					# if fall through then there is no further request available.
					# build the aggregated request
					agrp = { 'm2m:agrp' : [ requestFromResult(Result(request = each)).data for each in lst ] }
					return Result(resource = agrp, rsc = ResponseStatusCode.OK)
				
			else:
				if req := self.unqueuePollingRequest(originator, requestID, reqType):
					return Result(request = req, rsc = req.rsc)
			# fall-through
		raise REQUEST_TIMEOUT(L.logWarn(f'Timeout while waiting for: {reqType} for originator: {originator}, requestID: {requestID}'))


	def queueRequestForPCH(	self, 
							operation:Operation,
							pchOriginator:str,
							content:JSON = None,
							ty:ResourceTypes = None,
							rvi:str = None,
							request:CSERequest = None,
							reqType:RequestType = RequestType.REQUEST,
							ec:EventCategory = None,
							originator:str = None) -> Optional[CSERequest]:
		"""	Queue a (incoming) *request* or *content* for a <PCH>. It can be retrieved via the target's <PCU> 
			child resource.

			If a *request* is passed then this object is queued. If no *request* but *data* is given then a new request object is created 
			for *content*.
		"""

		# Check required arguments
		if not request and not content:
			L.logErr('Internal error. queueRequestForPCH() needs either a request or data to enqueue.')
			return None

		# L.isDebug and L.logDebug(request)
		# If no request is given, we create one here.
		if not request:
			# Fill various request attributes
			request = CSERequest(id = pchOriginator,
				 				 op = operation,
				 				 originator = originator,
				 				 ty = ty, 
				 				 ot = getResourceDate(),
				 				 rqi = uniqueRI(),
				 				 rvi = rvi if rvi is not None else RC.releaseVersion,
				 				 pc = content,
								 # Copy additional parameter attributes
								 ec = ec)
		else:
			# If the request has no rqi, then create one
			if not request.rqi:
				request.rqi = uniqueRI()
			# If the request has no id, then use the to field
			if not request.id:
				request.id = request.to

		# Always mark the request as a REQUEST
		request.requestType = reqType

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Storing REQUEST for: {request.id} with rqi: {request.rqi} pc:{request.pc} for polling')
		self.queuePollingRequest(request, reqType)
		return request

	
	def waitForResponseToPCH(self, request:CSERequest) -> Result:
		"""	Wait for a RESPONSE to a request.
		"""
		L.isDebug and L.logDebug(f'Waiting for RESPONSE with request ID: {request.rqi}')

		try: 
			response = self.waitForPollingRequest(request.originator, request.rqi, timeout=self.requestExpirationDelta, reqType=RequestType.RESPONSE)
		except ResponseException:
			raise
	
		L.isDebug and L.logDebug(f'RESPONSE received ID: {response.request.rqi} rsc: {response.request.rsc}')
		if not compareIDs(response.request.originator, request.id):
			raise BAD_REQUEST(L.logWarn(f'Received originator: {response.request.originator} is different from original target originator: {request.id}'))
		return Result(rsc = response.request.rsc, request = response.request)


	def _cleanupPollingRequests(self) -> bool:
		with self._requestLock:
			# Search all entries in the queue and remove those that have expired in the past
			# Remove those requests also from 
			now = utcTime()
			for originator, requests in list(self._requests.items()):
				nList = []
				for tup in list(requests):				# Test all requests for expiration
					if tup[0]._rqetUTCts > now:	# not expired
						nList.append(tup)				# add the request tupple again to the list if it hasnt expired
					else:
						L.isDebug and L.logDebug(f'Remove old polling request: {tup}')
						# Also remove the requestID - originator mapping
						if (rqi := tup[0].rqi) in self._rqiOriginator:
							del self._rqiOriginator[rqi]
				if len(nList) > 0:	# Add the lists again if there still more requests for this originator
					self._requests[originator] = nList
				else:				# remove the entry
					del self._requests[originator]
		return True
					
	
	###########################################################################
	#
	#	Request/Response async sequence helpers for polling asynch responses


	def waitForResponse(self, rqi:str, timeOut:float) -> Tuple[ Optional[Result], Optional[str] ]:
		"""	Wait for a response with a specific requestIdentifier *rqi*.

		"""
		resp = None
		info = None

		def _receivedResponse() -> bool:
			nonlocal resp, info
			with self._receivedResponsesLock:
				if not self._receivedResponses:
					return False
				if rqi in self._receivedResponses:
					resp, info = self._receivedResponses.pop(rqi)	# return the response (in a Result object), and remove it from the dict.
					return True
			return False
			
		if not waitFor(timeOut, _receivedResponse):
			return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, 
						  dbg = 'Target not reachable or timeout'), None
		# resp.data = resp.request.pc					# Add the pc to the data, since components excepct this. 
													# TODO perhaps unify the use of response values throughout the CSE
		CSE.event.responseReceived(resp.request)	# type:ignore [attr-defined]
		return resp, info


	def addResponse(self, response:Result, info:Optional[str] = None) -> None:
		"""	Add a response and topic to the response dictionary. The key is the *rqi* (requestIdentifier) of
			the response. 
		"""
		if (rqi := response.request.rqi):
			L.isDebug and L.logDebug(f'Adding response for rqi: {rqi}')
			with self._receivedResponsesLock:
				self._receivedResponses[rqi] = (response, info)


	###########################################################################
	#
	#	Sending Requests
	#

	def handleSendRequest(self, request:CSERequest) -> RequestResponseList:

		if request.op is None:
			raise BAD_REQUEST(L.logErr('request is missing operation attribute'))
		
		# Set outgoing flag for recording
		request._outgoing = True

		# Call the appropriate request function
		try:
			# The following line, at the moment, always calls the same function that
			# handles the send request. This is a leftover from when there were 
			# different functions to handle the send requests.
			# Perhaps this could be simplified sometime later when we know that no
			# further function is needed.
			res = self.requestHandlers[request.op].sendRequest(request)
		except ResponseException as e:
			res = [ RequestResponse(request, Result(rsc = e.rsc, dbg = e.dbg, request = e.data)) ]

		# Add to requests database
		for r in res:
			self.recordRequest(r.request, r.result)

		return res


	def _sendRequest(self, request:CSERequest) -> RequestResponseList:
		"""	Send a request via the appropriate channel or transport protocol.
		"""
		L.isDebug and L.logDebug(f'Sending {request.op.name} request to: {request.to}')

		# Determine all the details for one or multiple targets
		if not (resolved := self.determineTargetDetails(request)):	# empty list?
			raise BAD_REQUEST(L.logWarn('cannot determine target details for the request'))
		results:RequestResponseList = []
		for url, csz, rvi, pch, requestOriginator, to, targetType, isDirectURL in resolved:

			# Some adjustments to the originat request
			_request = request.convertToR1Target(rvi) 
			_request.rvi = rvi
			_request.ot = request.ot if request.ot is not None else getResourceDate()
			_request.originator = requestOriginator
			_request.to = urllib.parse.unquote(_request.to)	# unquote URL
			if _request.id is None:
				_request.id = to
			_request.id = urllib.parse.unquote(_request.id)	# unquote URL

			# Send the request via a PCH, if present
			if pch:
				_result = self.waitForResponseToPCH(self.queueRequestForPCH(request.op,
																			pchOriginator = pch.getOriginator(), 
																			content = request.pc,
																			ec = _request.ec,
																			originator = _request.originator,
																			rvi = _request.rvi,
																			request = request))
				results.append( RequestResponse(_request, _result) )
				continue

			# Small optimization: if the target is a local resource and is NOT a normal notification receiving resource, then handle the request directly
			if request.op == Operation.NOTIFY and \
				(_id := localResourceID(to)) is not None and \
				not ResourceTypes.isNotificationEntity(targetType) and \
				targetType != ResourceTypes.UNKNOWN:
					_result = CSE.dispatcher.notifyLocalResource(_id, requestOriginator, request.pc)
					results.append( RequestResponse(request, _result) )
					continue

			ct = request.ct
			if not ct and not (ct := determineSerialization(url, csz, RC.defaultSerialization)):
				L.isWarn and L.logWarn(f'Cannot determine content serialization for url: {url}')
				continue		
			_request.ct = ct

			# Otherwise send it via one of the bindings
			match url:
				case _ if isHttpUrl(url):
					self.requestHandlers[_request.op].httpEvent()	# send event
					results.append( RequestResponse(_request, CSE.httpServer.sendHttpRequest(_request, url, isDirectURL)) )
					continue
			
				case _ if isMQTTUrl(url):
					self.requestHandlers[_request.op].mqttEvent()	# send event
					results.append( RequestResponse(_request, CSE.mqttClient.sendMqttRequest(_request, url, isDirectURL)) )
					continue

				case _ if isCoAPUrl(url):
					self.requestHandlers[_request.op].coapEvent()	# send event
					results.append( RequestResponse(_request, CSE.coapServer.sendCoAPRequest(_request, url, isDirectURL)) )
					continue

				case _ if isWSUrl(url):
					self.requestHandlers[_request.op].wsEvent()	# send event
					try:
						results.append( RequestResponse(_request, CSE.webSocketServer.sendWSRequest(_request, url, isDirectURL)) )
					except TARGET_NOT_REACHABLE as e:
						L.logWarn(f'WS request to unreachable target with url: {url}. Looking for next poa.')
					continue

				# Special handling for ACME internal events.
				# This might be more generalize when other opeations are supported as well
				case _ if isAcmeUrl(url) and request.op == Operation.NOTIFY:
					self._eventAcmeSendNotify(url, _request)	# Don't wait for any real result
					results.append( RequestResponse(_request, Result(rsc = ResponseStatusCode.OK)) )
					continue

			raise BAD_REQUEST(L.logWarn(f'unsupported url scheme: {url}'))
		
		if not len(results):
			raise NOT_FOUND(f'No target found for uri: {request.to}')
		return results


	###########################################################################
	#
	#	Various support methods
	#


	def fillAndValidateCSERequest(self, cseRequest:Union[CSERequest, JSON], 
			       						isResponse:Optional[bool] = False) -> CSERequest:
		"""	Fill a *cseRequest* object according to its request structure in the *Result.request* attribute.
		"""
		# ! Cannot be in RequestUtils bc to prevent circular import of CSE and validator

		def gget(dct:dict, 
				 attribute:str, 
				 default:Optional[Any] = None, 
				 attributeType:Optional[BasicType] = None, 
				 checkSubType:Optional[bool] = False, 
				 greedy:Optional[bool] = True) -> Any:
			"""	Local helper to greedy check and return a key/value from a dictionary.

				If `dct` is None or `attribute` couldn't be found then the `default` is returned.

				This method might raise a *ValueError* exception if validation or conversion of the
				attribute/value fails.
			"""
			if dct and (value := dct.get(attribute)) is not None:	# v may be int
				if greedy:
					del dct[attribute]
				try:
					_, newValue = CSE.validator.validateAttribute(attribute, value, attributeType, rtype = ResourceTypes.REQRESP)
				except ResponseException as e:
					e.dbg = f'attribute: {attribute}, value: {value} : {e.dbg}'
					e.data = cseRequest
					raise e

				# Test request (!) sub-values if they are a list
				# ATTN DON'T remove this, because this is different from validation
				if attributeType == BasicType.list and checkSubType:
					newValueList = []
					for v in newValue:
						try:
							_, _nv = CSE.validator.validateAttribute(attribute, v, rtype = ResourceTypes.REQRESP)
						except ResponseException as e:
							raise BAD_REQUEST(f'attribute: {attribute}, value: {value} : {e.dbg}', data = cseRequest)
						newValueList.append(_nv) #type: ignore [index]
					return newValueList

				return newValue
			return default

		if isinstance(cseRequest, dict):
			cseRequest = CSERequest(originalRequest = cseRequest, pc = cseRequest.get('pc'))

		try:

			earlyError:str = None

			# Determine RSC as soon as possible. This determines whether this is a request or a response.
			if (rsc := gget(cseRequest.originalRequest, 'rsc', greedy = False)): 
				cseRequest.rsc = ResponseStatusCode(rsc)
				cseRequest.requestType = RequestType.RESPONSE	# This is a response if there is an rsc
				isResponse = True

			# FR - originator 
			# if not (fr := gget(cseRequest.originalRequest, 'fr', greedy = False)) and not isResponse and not (cseRequest.ty == ResourceTypes.AE and cseRequest.op == Operation.CREATE):
			# 	raise BAD_REQUEST(L.logDebug('from/originator parameter is mandatory in request'), data = cseRequest)
			# else:
			# 	cseRequest.originator = fr
			cseRequest.originator = gget(cseRequest.originalRequest, 'fr', greedy = False)

			# RQI - requestIdentifier
			# Check as early as possible
			if (rqi := gget(cseRequest.originalRequest, 'rqi', greedy = False)):
				cseRequest.rqi = rqi
			else:
				earlyError = L.logDebug('request identifier parameter is mandatory in request')

			# TO - target
			if not (to := gget(cseRequest.originalRequest, 'to', greedy = False)) and not isResponse:
				earlyError = L.logDebug('to/target parameter is mandatory in request')
			else:
				cseRequest.to = to
				if to:
					# A response doesn't need to have a 'to' parameter.
					# But if it has then it must only be an originator, ie. an AE-ID or a CSE-ID
					if isResponse:
						if isValidCSI(to) or isValidAEI(to):
							cseRequest.id = to
							cseRequest.csi = to
							cseRequest.srn = None
						else:
							earlyError = L.logWarn(f'invalid CSE-ID or AE-ID for "to" parameter in response: {to}. ')
					else:
						cseRequest.id, cseRequest.csi, cseRequest.srn, dbg = getIDFromPath(to)
						if dbg:
							raise BAD_REQUEST(f'"to": {dbg}', data = cseRequest)

			if earlyError:
				raise BAD_REQUEST(earlyError, data = cseRequest)


			# RVI - releaseVersionIndicator
			if not (rvi := gget(cseRequest.originalRequest, 'rvi', greedy = False)):
				raise RELEASE_VERSION_NOT_SUPPORTED(L.logDebug(f'release Version Indicator is missing in request, falling back to RVI=\'1\'. But Release Version \'1\' is not supported. Use RVI with one of {RC.supportedReleaseVersions}.'), 
													data = cseRequest)
			else:
				if rvi in RC.supportedReleaseVersions:
					cseRequest.rvi = rvi	
				else:
					raise RELEASE_VERSION_NOT_SUPPORTED(L.logDebug(f'release version unsupported: {rvi}'), data = cseRequest)
		
			# OP - operation
			if (op := gget(cseRequest.originalRequest, 'op', greedy = False)) is not None:	# op is an int
				if Operation.isvalid(op):
					cseRequest.op = Operation(op)
				else:
					raise BAD_REQUEST(L.logDebug(f'unknown/unsupported operation: {op}'), data = cseRequest)
			elif not isResponse:
				raise BAD_REQUEST(L.logDebug('operation parameter is mandatory in request'), data = cseRequest)

			# TY - resource type
			if (ty := gget(cseRequest.originalRequest, 'ty', greedy = False)) is not None:	# ty is an int
				if ResourceTypes.has(ty):
					cseRequest.ty = ResourceTypes(ty)
				else:
					raise BAD_REQUEST(L.logDebug(f'unknown/unsupported resource type: {ty}'), data = cseRequest)

			# Late check for Originator happens here, because we need to know the resource type and operation
			if not cseRequest.originator and not isResponse and not (cseRequest.ty == ResourceTypes.AE and cseRequest.op == Operation.CREATE):
				raise BAD_REQUEST(L.logDebug('from/originator parameter is mandatory in request'), data = cseRequest)

			# Check identifiers
			if not isResponse and not cseRequest.id and not cseRequest.srn:
				raise NOT_FOUND(L.logDebug('missing identifier (no id nor srn)'), data = cseRequest)

			# OT - originating timestamp
			if ot := gget(cseRequest.originalRequest, 'ot', greedy = False):
				if (_ts := fromAbsRelTimestamp(ot)) == 0.0:
					raise BAD_REQUEST(L.logDebug('error in provided Originating Timestamp'), data = cseRequest)
				else:
					cseRequest.ot = ot

			# RQET - requestExpirationTimestamp
			if rqet := gget(cseRequest.originalRequest, 'rqet', greedy=False):
				if (_ts := fromAbsRelTimestamp(rqet)) == 0.0:
					raise BAD_REQUEST(L.logDebug('error in provided Request Expiration Timestamp'), data = cseRequest)
				else:
					if _ts < utcTime():
						raise REQUEST_TIMEOUT(L.logDebug(f'request timeout reached: rqet {_ts} < {utcTime()}'), data = cseRequest)
					else:
						cseRequest._rqetUTCts = _ts		# Re-assign "real" ISO8601 timestamp
						cseRequest.rqet = toISO8601Date(_ts)

			# RSET - resultExpirationTimestamp
			if (rset := gget(cseRequest.originalRequest, 'rset', greedy=False)):
				if (_ts := fromAbsRelTimestamp(rset)) == 0.0:
					raise BAD_REQUEST(L.logDebug('error in provided Result Expiration Timestamp'), data = cseRequest)
				else:
					if _ts < utcTime():
						raise REQUEST_TIMEOUT(L.logDebug(f'result timeout reached: rset {_ts} < {utcTime()}'), data = cseRequest)
					else:
						cseRequest._rsetUTCts = _ts	# Re-assign "real" ISO8601 timestamp
						# Re-assign "real" ISO8601 timestamp
						try: 
							cseRequest.rset = int(rset)	# type: ignore [assignment]
						except ValueError:
							cseRequest.rset = toISO8601Date(_ts)

			# OET - operationExecutionTime
			if (oet := gget(cseRequest.originalRequest, 'oet', greedy=False)):
				if (_ts := fromAbsRelTimestamp(oet)) == 0.0:
					raise BAD_REQUEST(L.logDebug('error in provided Operation Execution Time'), data = cseRequest)
				else:
					cseRequest.oet = toISO8601Date(_ts)	# Re-assign "real" ISO8601 timestamp

				# EXPERIMENTAL: check if the operation execution time is after rqet or rset
				# see: https://git.onem2m.org/issues/issues/-/issues/217
				if cseRequest.rqet and _ts >= cseRequest._rqetUTCts:
					raise BAD_REQUEST(L.logDebug(f'operation execution time is before request expiration time: oet {_ts} >= rqet {cseRequest._rqetUTCts}'), data = cseRequest)
				if cseRequest.rset and _ts >= cseRequest._rsetUTCts:
					raise BAD_REQUEST(L.logDebug(f'operation execution time is before result expiration time: oet {_ts} >= rset {cseRequest._rsetUTCts}'), data = cseRequest)


			# RVI - releaseVersionIndicator
			if  (rvi := gget(cseRequest.originalRequest, 'rvi', greedy=False)):
				if rvi not in RC.supportedReleaseVersions:
					raise RELEASE_VERSION_NOT_SUPPORTED(L.logDebug(f'release version unsupported: {rvi}'), data = cseRequest)
				else:
					cseRequest.rvi = rvi	
			else:
				raise RELEASE_VERSION_NOT_SUPPORTED(L.logDebug(f'Release Version Indicator is missing in request, falling back to RVI=\'1\'. But release version \'1\' is not supported. Use RVI with one of {RC.supportedReleaseVersions}.'))

			# VSI - vendorInformation
			if (vsi := gget(cseRequest.originalRequest, 'vsi', greedy=False)):
				cseRequest.vsi = vsi	

			# DRT - Desired Identifier Result Type
			cseRequest.drt = DesiredIdentifierResultType(gget(cseRequest.originalRequest, 'drt', DesiredIdentifierResultType.structured, greedy = False))	# 1=strucured, 2=unstructured

			#
			# Transfer filterCriteria: handling, conditions and attributes
			#

			fcAttrs = deepcopy(cseRequest.originalRequest.get('fc'))	# copy because we will greedy consume attributes here

			# FU - Filter Usage
			cseRequest.fc.fu = FilterUsage(gget(fcAttrs, 'fu', FilterUsage.conditionalRetrieval))
			if cseRequest.fc.fu == FilterUsage.discoveryCriteria and cseRequest.op == Operation.RETRIEVE:	# correct operation if necessary
				cseRequest.op = Operation.DISCOVERY

			# FO - Filter Operation
			cseRequest.fc.fo = FilterOperation(gget(fcAttrs, 'fo', FilterOperation.AND))


			# RCN Result Content Type
			if (rcn := gget(cseRequest.originalRequest, 'rcn', greedy = False)) is not None: 	# rcn is an int
				try:
					rcn = ResultContentType(rcn)
				except ValueError as e:
					raise BAD_REQUEST(L.logDebug(f'error validating rcn: {str(e)}'), data = cseRequest)
			else:
				# assign defaults when not provided
				if cseRequest.fc.fu != FilterUsage.discoveryCriteria:	
					# Different defaults for each operation
					match cseRequest.op:
						case Operation.RETRIEVE | Operation.CREATE | Operation.UPDATE:
							rcn = ResultContentType.attributes
						case Operation.DELETE:
							rcn = ResultContentType.nothing
				else:
					# discovery-result-references as default for Discovery operation
					rcn = ResultContentType.discoveryResultReferences

			# SQI - Semantic Query Indicator
			if (v := gget(cseRequest.originalRequest, 'sqi', greedy = False)) is not None:
				if cseRequest.op != Operation.RETRIEVE:
					raise BAD_REQUEST(L.logDebug('sqi request attribute is only allowed for RETRIEVE operations'), data = cseRequest)
				else:
					cseRequest.sqi = v


			# Validate rcn depending on operation
			if rcn and not rcn.validForOperation(cseRequest.op):
				raise BAD_REQUEST(L.logDebug(f'rcn: {rcn} not allowed in {cseRequest.op.name} operation'), data = cseRequest)
			cseRequest.rcn = rcn


			# RT - responseType: RTV responseTypeValue, RTU/NU responseTypeNUs
			if (rt := gget(cseRequest.originalRequest, 'rt', greedy = False)) is not None: # rt is an int
				cseRequest.rt = ResponseType(gget(rt, 'rtv', ResponseType.blockingRequest, greedy = False))
				if (nu := gget(rt, 'nu', greedy = False)) is not None:
					cseRequest.rtu = nu	#  TODO validate for url?
				if cseRequest.rtu and cseRequest.rt != ResponseType.nonBlockingRequestAsynch:
					raise BAD_REQUEST(L.logDebug('nu is only allowed when rt=nonBlockingRequestAsynchronous'), data = cseRequest)

			# RP - resultPersistence (also as timestamp)
			if (rp := gget(cseRequest.originalRequest, 'rp', greedy=False)): 
				cseRequest.rp = rp
				if (rpts := toISO8601Date(fromAbsRelTimestamp(rp))) == 0.0:
					raise BAD_REQUEST(L.logDebug(f'"{rp}" is not a valid value for rp'), data = cseRequest)
				else:
					cseRequest._rpts = rpts
			else:
				cseRequest.rp = None
				cseRequest._rpts = None

			#
			#	Discovery and FilterCriteria
			#
			if fcAttrs:	# only when there is a filterCriteria, copy the available attribute to the FilterCriteria structure
				for h in ( 'lim', 'lvl', 'ofst', 'arp',
						   'crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr',
						   'smf', 
						   'aq'):
					if (v := gget(fcAttrs, h)) is not None:	# may be int
						cseRequest.fc.set(h, v)
				for h in ( 'lbl', 'cty' ): # different handling of list attributes
					if (v := gget(fcAttrs, h, attributeType = BasicType.list, checkSubType = False)) is not None:
						cseRequest.fc.set(h, v)
				for h in ( 'ty', ): # different handling of list attributes that are normally non-lists
					if (v := gget(fcAttrs, h, attributeType = BasicType.list, checkSubType = True)) is not None:	# may be int
						cseRequest.fc.set(h, v)

				# Handling of geo-query attributes
				match len([a for a in ('gmty', 'geom', 'gsf') if a in fcAttrs]):
					case 0:
						pass
					case 1 | 2:
						raise BAD_REQUEST(L.logDebug('gmty, geom and gsf must be specified together'), data = cseRequest)
					case 3:
						if (v := gget(fcAttrs, 'gmty')) is not None:
							cseRequest.fc.gmty = v
						geom = fcAttrs.get('geom')
						if (v := gget(fcAttrs, 'geom')) is not None:
							cseRequest.fc.geom = geom
							cseRequest.fc._geom = v
						if (v := gget(fcAttrs, 'gsf')) is not None:
							cseRequest.fc.gsf = v
				
				# Copy all remaining attributes as filter criteria!

				for h in list(fcAttrs.keys()): 
					cseRequest.fc.attributes[h] = gget(fcAttrs, h)

			# Copy primitive content
			# Check whether content is empty and operation is UPDATE or CREATE -> Error
			if not cseRequest.originalRequest.get('pc'):
				if cseRequest.op in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ]:
					raise BAD_REQUEST(L.logDebug(f'Missing primitive content or body in request for operation: {cseRequest.op}'), data = cseRequest)
			else:
				cseRequest.pc = cseRequest.originalRequest.get('pc')	# The reqeust.pc contains the primitive content
				try:
					CSE.validator.validatePrimitiveContent(cseRequest.pc)
				except ResponseException as e:
					L.isDebug and L.logDebug(e.dbg)
					e.data = cseRequest
					raise e
			
			# Check whether none or all of sqi, smf and rcn=semantic content is set, otherwise error
			if cseRequest.sqi and cseRequest.rcn != ResultContentType.semanticContent:
				raise BAD_REQUEST(L.logDebug('Wrong ResultContentType for sqi == True (must be semanticContent)'), data = cseRequest)
			if cseRequest.sqi is not None and not cseRequest.sqi and cseRequest.rcn != ResultContentType.discoveryResultReferences:
				raise BAD_REQUEST(L.logDebug('Wrong ResultContentType for sqi == False (must be discoveryResultReferences)'), data = cseRequest)
			
			# if [ cseRequest.fc.smf is not None, 
			# 	 cseRequest.rcn == ResultContentType.semanticContent].count(True) not in [ 0, 2 ]:
			# 	return Result.errorResult(request = cseRequest, dbg = L.logDebug('smf and rcn=smantic-content must be specifed together, or not at all'))
			# if cseRequest.sqi and not (cseRequest.fc.smf and cseRequest.rcn == ResultContentType.semanticContent):
			# 	return Result.errorResult(request = cseRequest, dbg = L.logDebug('sqi must not be specifed without smf and rcn=smantic-content'))

			# ma - maxAge
			if (ma := gget(cseRequest.originalRequest, 'ma', greedy = False)): 
				try:
					cseRequest.ma = ma
					cseRequest._ma = fromDuration(ma)
				except Exception as e:
					raise BAD_REQUEST(L.logDebug('Wrong format for ma'), data = cseRequest)
				
		# end of try..except
		except ValueError as e:
			raise BAD_REQUEST(L.logDebug(f'Error getting or validating attribute/parameter: {str(e)}'), data = cseRequest)

		# Return the success result 
		return cseRequest


	def dissectRequestFromBytes(self, data:bytes, 
									  contenType:ContentSerializationType, 
									  isResponse:Optional[bool] = False) -> Result:
		"""	Dissect a request in a byte string and build up a CSERequest instance.

			Args:
				data: The data to dissect.
				contenType: The content type of the data.
				isResponse: If True then the data is a response, otherwise it is a request.

			Return:
				A Result instance with the dissected request in `Result.request`. The `Result.data` contains the *pc* of the request.
		"""
		cseRequest = CSERequest()
		cseRequest.originalData = data
		cseRequest.ct = contenType


		# De-Serialize the content
		try:
			cseRequest.originalRequest = deserializeContent(cseRequest.originalData, cseRequest.ct)
		except ResponseException as e:
			# re-use the exception and raise it again
			e.data = cseRequest
			raise e

		# Validate the request
		try:
			self.fillAndValidateCSERequest(cseRequest, isResponse)
		except ResponseException as e:
			# re-use the exception and raise it again
			e.data = cseRequest
			raise e
		
		return Result(data = cseRequest.pc, rsc = cseRequest.rsc, request = cseRequest)


	###########################################################################

	#
	#	Utilities
	#

	def getSerializationFromOriginator(self, originator:str) -> List[ContentSerializationType]:
		"""	Get for the content serializations of a registered originator.

			It is either an AE, a CSE or a CSR.

			Args:
				originator: The originator to check.
			Return:
				List of ContentSerializationTypes.
		"""
		if not originator:
			return []
		# First check whether there is an AE with that originator
		if (l := len(aes := CSE.storage.searchByFragment({ 'aei' : originator }))) > 0:
			if l > 1:
				L.logErr(f'More then one AE with the same aei: {originator}')
				return []
			csz = aes[0].csz
		# Else try whether there is a CSE or CSR
		elif (l := len(cses := CSE.storage.searchByFragment({ 'csi' : getIdFromOriginator(originator) }))) > 0:
			if l > 1:
				L.logErr(f'More then one CSE with the same csi: {originator}')
				return []
			csz = cses[0].csz
		# Else just an empty list
		else:
			return []
		# Convert the poa to a list of ContentSerializationTypes
		if not csz:
			return []
		return [ ContentSerializationType.getType(c) for c in csz]


	def determineTargetDetails(self, request:CSERequest) -> Optional[TargetDetails]:
		"""	Resolve the real URL and more message parameters for a request and a target,
		
			Args:
				request: The request from which the target details are taken from.
			
			Notes:
				A successful determination may include the type of the target resource. This is different from the request content's
				resource type.

			Return:
				The results could differ:

				The result is a list of tuples of (real url including the protocol, list of allowed contentSerializations,
				target supported release version, PollingChannel resource, originator with adapted scope, target uri, 
				determined target resource type).
				
				Or, return a list of (url, None, None, None, originator, None, UNKNOWN), containing only one element, if the URI is
				already a URL. We cannot determine the preferred serializations in this case. and we don't know the target entity.
				
				Return a list of (None, list of allowed contentSerializations, srv, PollingChannel resource,
				originator with adapted scope, target, uri, determined target resource type), containing only one element, if the target resourec is not
				request reachable and has a PollingChannel as a child resource.

				Otherwise, return a list of the mentioned tuples.

				In case of an error, an empty list is returned. 
		"""

		def getTargetReleaseVersion(srv:list) -> str:
			if (srv := targetResource.srv):
				return sorted(srv)[-1]	# return highest srv
			return RC.releaseVersion
				
		originator = request.originator
		uri = request.to
		if request._directURL:
			uri = request._directURL

		if isURL(uri):	# The uri is a direct URL
			L.isDebug and L.logDebug(f'Direct URL: {uri}')
			return [ (uri, 
					  None, 
					  RC.releaseVersion, 
					  None, 
					  originator, 
					  uri, 
					  ResourceTypes.UNKNOWN,
					  True) ]


		# targetResource will be assigned the real resource that offers the POA
		# It may be an AE, CSE, CSR.
		targetResource = None
		targetResourceType:ResourceTypes = ResourceTypes.UNKNOWN
		isForwardedRequest = False

		if isSPRelative(uri) or isAbsolute(uri):
			if (ri := localResourceID(uri)) is not None:	# If this the local CSE

				try:
					resource = CSE.dispatcher.retrieveResource(ri)
				except ResponseException as e:
					L.logWarn(f'Cannot retrieve local resource: {ri}: {e.dbg}')
					return []
				targetResourceType = resource.ty	# no matter what, store the resource type, if available
				if ResourceTypes.isNotificationEntity(targetResourceType):	# has a poa
					targetResource = resource
				else:
					targetResource = getCSE()			# for all other resources without a poa is the CSE responsible
			elif (t := CSE.remote.getCSRFromPath(uri)): # target is a registering CSE
				targetResource, _ = t
				isForwardedRequest = True
			elif CSE.remote.registrarCSE:	# just send it up to the registrar CSE, if any
				targetResource = CSE.remote.registrarCSE
				isForwardedRequest = True

		isForwardedRequest and L.isDebug and L.logDebug(f'Forwarded request to: {uri}')

		# If not found: The uri is an indirect resource with poa, retrieve one or more URIs from it
		if not targetResource and not (targetResource := CSE.dispatcher.retrieveResource(uri)):
			L.isWarn and L.logWarn(f'Resource not found to get URL: {uri}')
			return []
		
		# Checking permissions
		permission = request.op.permission()
		if not uri.startswith(RC.cseCsiSlash):	# TODO make a utility out of this
			if originator == RC.cseCsi:
				L.isDebug and L.logDebug(f'Originator: {originator} is CSE -> Permission granted.')
			elif not isForwardedRequest and not CSE.security.hasAccess(originator, targetResource, permission, request = request, resultResource = targetResource):
				L.isWarn and L.logWarn(f'Originator: {originator} has no permission: {permission} for {targetResource.ri}')
				return []

		# Check requestReachability
		# If the target is NOT reachable then try to retrieve a pollingChannel
		pollingChannelResources = []
		if targetResource.rr == False and targetResource.ri != RC.cseRi:
			L.isDebug and L.logDebug(f'Target: {uri} is not requestReachable. Trying <PCH>.')
			if not len(pollingChannelResources := CSE.dispatcher.retrieveDirectChildResources(targetResource.ri, ResourceTypes.PCH)):
				L.isWarn and L.logWarn(f'Target: {uri} is not requestReachable and does not have a <PCH>.')
				return []
			# Take the first resource and return it. There should hopefully only be one, but we don't check this here
			return [ (None, 
					  targetResource.csz,
					  getTargetReleaseVersion(targetResource.srv),
					  cast(PCH, pollingChannelResources[0]),
					  originator,
					  uri,
					  targetResourceType,
					  False) ]

		# Use the poa of a target resource
		if not targetResource.poa:	# check that the resource has a poa
			L.isWarn and L.logWarn(f'Resource {uri} has no "poa" attribute')
			return []
		
		# TODO define a type for the result list
		resultList:List[Tuple[str, List[str], str, PCH, str, str, ResourceTypes, bool]] = []
		
		for p in targetResource.poa:
			if isHttpUrl(p) and p[-1] != '/':	# Special handling for http urls
				p += '/'
			resultList.append((f'{p}', 
							   targetResource.csz, 
							   getTargetReleaseVersion(targetResource.srv), 
							   None,
							   toSPRelative(originator) if targetResource.ty in [ ResourceTypes.CSEBase, ResourceTypes.CSR ] and targetResource.csi != RC.cseCsi else originator,
							   uri,
							   targetResourceType,
							   False))
		# L.logWarn(resultList)
		return resultList


##############################################################################
#
#	Requests recording
#

	def recordRequest(self, request:Optional[CSERequest], result:Result) -> None:

		# Recoding enabled or disabled?
		if not self.enableRequestRecording or not request:
			return
		
		# Construct and store request & response
		match _resource := result.resource:
			case Resource():
				pc = _resource.asDict()
			case dict():
				pc = _resource
			case x if result.data:
				pc = result.data # type:ignore
			case _:
				pc = None
		
		# Determine the structure address
		if not (srn := request.srn):
			srn = request.id if request.id else request.to
			if not isStructured(srn):
				srn = structuredPathFromRI(srn)
		
		# Map virtual resource names 
		if srn and srn.endswith( ('/la', '/ol', '/pcu', '/fopt') ) and isinstance(result.resource, Resource):
			rid = f'{result.resource.pi}/{srn.rsplit("/", 1)[1]}'
		elif request.id:
			rid = request.id
		else:
			rid = 'unknown'
		
		# Map the response
		match request.rt:
			case ResponseType.noResponse:
				response = {}
			case _:
				# Blocking request, so we have a response
				response =  { 'rsc': result.rsc,
							'rqi': request.rqi,
							'pc': pc,
							'dbg': result.dbg,
							'ot': result.request.ot if result.request and result.request.ot else getResourceDate(),
							}
		if request.rset:
			response['rset'] = request.rset

		
		request.fillOriginalRequest(update = True)

		# Store the request
		CSE.storage.addRequest(request.op,
							   rid, 
							   srn,
							   request.originator if request.originator else 'unknown',
							   request._outgoing,
							   request.ot if request.ot else toISO8601Date(request._ot),	# Only convert now to ISO8601 to avoid unnecessary conversions
							   request.originalRequest,
							   response)
	