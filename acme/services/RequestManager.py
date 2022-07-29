#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external requests are routed through here.
#

from __future__ import annotations
import urllib.parse
from typing import Any, List, Tuple, cast, Dict
from copy import deepcopy
from threading import Lock

from ..etc.Types import BasicType, DesiredIdentifierResultType, FilterOperation, FilterUsage, Operation, Permission, RequestCallback, RequestType, ResponseStatusCode, ResultContentType
from ..etc.Types import RequestStatus
from ..etc.Types import CSERequest
from ..etc.Types import RequestHandler
from ..etc.Types import ResourceTypes as T
from ..etc.Types import ResponseStatusCode as RC
from ..etc.Types import ResponseType
from ..etc.Types import Result
from ..etc.Types import CSERequest
from ..etc.Types import ContentSerializationType
from ..etc.Types import Parameters
from ..etc.Constants import Constants as C
from ..etc import Utils, DateUtils, RequestUtils
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..services import CSE as CSE
from ..resources.REQ import REQ
from ..resources.PCH import PCH
from ..helpers.BackgroundWorker import BackgroundWorkerPool


# This factor determines how often the monitor looks for expired request resources
expirationCheckFactor = 2.0

class RequestManager(object):

	def __init__(self) -> None:
		self.flexBlockingBlocking			 = Configuration.get('cse.flexBlockingPreference') == 'blocking'
		self.requestExpirationDelta			 = Configuration.get('cse.requestExpirationDelta')


		self.requestHandlers:RequestHandler  = { 		# Map request handlers for operations in the RequestManager and the dispatcher
			Operation.RETRIEVE	: RequestCallback(self.retrieveRequest, CSE.dispatcher.processRetrieveRequest),
			Operation.DISCOVERY	: RequestCallback(self.retrieveRequest, CSE.dispatcher.processRetrieveRequest),
			Operation.CREATE	: RequestCallback(self.createRequest,   CSE.dispatcher.processCreateRequest),
			Operation.NOTIFY	: RequestCallback(self.notifyRequest,   CSE.dispatcher.processNotifyRequest),
			Operation.UPDATE	: RequestCallback(self.updateRequest,   CSE.dispatcher.processUpdateRequest),
			Operation.DELETE	: RequestCallback(self.deleteRequest,   CSE.dispatcher.processDeleteRequest),
		}

		#
		#	Structures for pollingChannel requests
		#
		self._requestLock = Lock()													# Lock to access the following two dictionaries
		self._requests:Dict[str, List[ Tuple[CSERequest, RequestType] ] ] = {}		# Dictionary to map request originators to a list of reqeusts. Used for handling polling requests.
		self._rqiOriginator:Dict[str, str] = {}										# Dictionary to map requestIdentifiers to an originator of a request. Used for handling of polling requests.
		self._pcWorker = BackgroundWorkerPool.newWorker(self.requestExpirationDelta * expirationCheckFactor, self._cleanupPollingRequests, name='pollingChannelExpiration').start()

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)	# type: ignore

		L.isInfo and L.log('RequestManager initialized')


	def shutdown(self) -> bool:
		# Stop the PollingChannel Cleanup worker
		if self._pcWorker:
			self._pcWorker.stop()
		L.isInfo and L.log('RequestManager shut down')
		return True

	
	def restart(self) -> None:
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
	

	def configUpdate(self, key:str = None, value:Any = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.flexBlockingPreference', 'cse.requestExpirationDelta']:
			return
		# assign new values
		self.flexBlockingBlocking			 = Configuration.get('cse.flexBlockingPreference') == 'blocking'
		self.requestExpirationDelta			 = Configuration.get('cse.requestExpirationDelta')

		# restart expiration worker
		if self._pcWorker:
			self._pcWorker.restart(self.requestExpirationDelta * expirationCheckFactor)


	#########################################################################
	#
	# 	Incoming Requests
	#

	def handleRequest(self, request:CSERequest) -> Result:
		"""	Calls the fitting request handler for an operation and let that handle the request.

			Before the request is processed it will be determined whether it is blocking or
			non-blocking etc.

			Args:
				request: The incoming request.
			Return:
				Request result.
		"""
		CSE.event.requestReceived(request)	# type:ignore [attr-defined]
		return self.requestHandlers[request.op].ownRequest(request)


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
		

	# def handleReceivedNotifyRequest(self, targetResource:Resource, request:CSERequest, id:str, originator:str) -> Result:
	def handleReceivedNotifyRequest(self, id:str, request:CSERequest, originator:str) -> Result:
		"""	Handle a NOTIFY request to a PCU-enabled resource.
		"""
		L.isDebug and L.logDebug(f'NOTIFY request for polling channel. Originator: {originator}')

		# Check content
		if request.pc is None:
			return Result.errorResult(dbg = L.logDebug(f'Missing content/request in notification'))

		return self.sendNotifyRequest(id, originator = originator, data = request)



	#########################################################################
	#
	#	RETRIEVE Request
	#

	def retrieveRequest(self, request:CSERequest) ->  Result:
		L.isDebug and L.logDebug(f'RETRIEVE ID: {request.id if request.id else request.srn}, originator: {request.originator}')
		
		if request.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processRetrieveRequest(request, request.originator)

		elif request.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processRetrieveRequest(request, request	.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result.errorResult(dbg = 'Unknown or unsupported ResponseType: {request.rt}')



	#########################################################################
	#
	#	CREATE resources
	#

	def createRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'CREATE ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Check contentType and resourceType
		if request.ty == None:
			return Result.errorResult(dbg = 'missing or wrong resourceType in request')

		if request.rt == ResponseType.blockingRequest:
			res = CSE.dispatcher.processCreateRequest(request, request.originator)
			return res

		elif request.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processCreateRequest(request, request.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result.errorResult(dbg = f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	UPDATE resources
	#

	def updateRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'UPDATE ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Don't update the CSEBase
		if request.id == CSE.cseRi:
			return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'operation not allowed for CSEBase')

		# Check contentType and resourceType
		if request.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processUpdateRequest(request, request.originator)

		elif request.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processUpdateRequest(request, request.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result.errorResult(dbg = f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	DELETE resources
	#


	def deleteRequest(self, request:CSERequest,) -> Result:
		L.isDebug and L.logDebug(f'DELETE ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Don't delete the CSEBase
		if request.id == CSE.cseRi:
			return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'operation not allowed for CSEBase')

		if request.rt == ResponseType.blockingRequest or (request.rt == ResponseType.flexBlocking and self.flexBlockingBlocking):
			return CSE.dispatcher.processDeleteRequest(request, request.originator)

		elif request.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processDeleteRequest(request, request.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result.errorResult(dbg = f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	Notify resources
	#

	def notifyRequest(self, request:CSERequest) -> Result:
		L.isDebug and L.logDebug(f'NOTIFY ID: {request.id if request.id else request.srn}, originator: {request.originator}')

		# Check contentType and resourceType
		if request.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processNotifyRequest(request, request.originator)

		elif request.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processNotifyRequest(request, request.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result.errorResult(dbg = f'Unknown or unsupported ResponseType: {request.rt}')


	#########################################################################
	#
	#	<request> handling
	#

	def _createRequestResource(self, request:CSERequest) -> Result:

		# Get initialized resource
		if not (nres := REQ.createRequestResource(request)).resource:
			return Result.errorResult(dbg = nres.dbg)

		# Register <request>
		if not (cseres := Utils.getCSE()).resource:
			return Result.errorResult(dbg = cseres.dbg)
		if not (rres := CSE.registration.checkResourceCreation(nres.resource, request.originator, cseres.resource)).status:
			return rres.errorResultCopy()
		
		# set the CSE.ri as indicator that this resource was created internally
		nres.resource.setCreatedInternally(cseres.resource.pi)

		# create <request>
		return CSE.dispatcher.createResource(nres.resource, cseres.resource, request.originator)


	def _handleNonBlockingRequest(self, request:CSERequest) -> Result:
		"""	This method creates a <request> resource, initiates the execution of the desired operation in
			the background, but immediately returns with the reference of the <request> resource that
			will contain the result of the operation.
		"""

		# Create the <request> resource first
		if not (reqres := self._createRequestResource(request)).resource:
			return reqres

		# Synchronous handling
		if request.rt == ResponseType.nonBlockingRequestSynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(self._runNonBlockingRequestSync, name=f'request_{request.rqi}').start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			return Result(data = { 'm2m:uri' : reqres.resource.ri }, rsc=RC.acceptedNonBlockingRequestSynch)

		# Asynchronous handling
		if request.rt == ResponseType.nonBlockingRequestAsynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(self._runNonBlockingRequestAsync, name=f'request_{request.rqi}').start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			return Result(data = { 'm2m:uri' : reqres.resource.ri }, rsc=RC.acceptedNonBlockingRequestAsynch)

		# Error
		return Result.errorResult(dbg = f'Unknown or unsupported ResponseType: {request.rt}')


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
		# originator = result.resource['ors/fr']
		originator = CSE.cseCsi
		responseNotification = {
			'm2m:rsp' : {
				'rsc' : result.resource['ors/rsc'],
				'rqi' : result.resource['ors/rqi'],
				'pc'  : result.resource['ors/pc'],
				'to'  : result.resource['ors/to'],
				# 'fr'  : originator,
				'fr'  : result.resource['ors/fr'],
				'rvi' : request.rvi
			}
		}

		if (nus := request.rtu) is None:	# might be an empty list
			# RTU is not set, get POA's from the resp. AE.poa
			aes = CSE.storage.searchByFragment({ 'ty' : T.AE, 'aei' : originator })	# search all <AE>s for aei=originator
			if len(aes) != 1:
				L.isWarn and L.logWarn(f'Wrong number of AEs with aei: {originator} ({len(aes):d}): {str(aes)}')
				nus = aes[0].poa
			else:
				L.isDebug and L.logDebug(f'No RTU. Get NUS from originator ae: {aes[0].ri}')
				nus = aes[0].poa

		# send notifications.Ignore any errors here
		CSE.notification.sendNotificationWithDict(responseNotification, nus, originator=CSE.cseCsi)

		return True


	def _executeOperation(self, request:CSERequest, reqRi:str) -> Result:
		"""	Execute a request operation and fill the respective request resource
			accordingly.
		"""
		# Execute the actual operation in the dispatcher
		operationResult = self.requestHandlers[request.op].dispatcherRequest(request, request.originator)

		# Retrieve the <request> resource
		if not (res := CSE.dispatcher.retrieveResource(reqRi, originator=request.originator)).resource:
			return Result.errorResult() 														# No idea what we should do if this fails
		reqres = res.resource

		# Fill the <request>
		reqres['ors'] = {	# operationResult
			'rsc'	: operationResult.rsc,
			'rqi'	: reqres.rid,
			'to'	: request.originator,
			'fr'	: CSE.cseCsi,
			'ot'	: reqres['mi/ot'],
			'rset'	: reqres.et
		}
		if operationResult.rsc in [ RC.OK, RC.created, RC.updated, RC.deleted ] :			# OK, created, updated, deleted -> resource
			reqres['rs'] = RequestStatus.COMPLETED
			if operationResult.resource:
				reqres['ors/pc'] = operationResult.resource.asDict()
		else:																				# Error
			reqres['rs'] = RequestStatus.FAILED
			if operationResult.dbg:
				reqres['ors/pc'] = { 'm2m:dbg' : operationResult.dbg }

		# Update lt etc attributes
		reqres.update()

		# Update in DB
		reqres.dbUpdate()

		return Result(status = True, resource = reqres)


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
		return self.sendRetrieveRequest(uri = cast(str, request.id),
									    originator = request.originator,
										data = request.originalRequest,
										raw = True)


	def handleTransitCreateRequest(self, request:CSERequest) -> Result:
		""" Forward a CREATE request to a remote CSE. """
		
		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding CREATE request to: {request.id}')
		return self.sendCreateRequest(uri = request.id,
									  originator = request.originator,
									  data = request.originalRequest,
									  ty = request.ty,
									  raw = True)


	def handleTransitUpdateRequest(self, request:CSERequest) -> Result:
		""" Forward an UPDATE request to a remote CSE. """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding UPDATE request to: {request.id}')
		return self.sendUpdateRequest(uri = cast(str, request.id),
									  originator = request.originator,
									  data = request.originalRequest,
									  raw = True)


	def handleTransitDeleteRequest(self, request:CSERequest) -> Result:
		""" Forward a DELETE request to a remote CSE. """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding DELETE request to: {request.id}')
		return self.sendDeleteRequest(uri = cast(str, request.id),
									  originator = request.originator,
  									  data = request.originalRequest,
									  raw = True)


	def handleTransitNotifyRequest(self, request:CSERequest) -> Result:
		""" Forward a NOTIFY request to a remote CSE. """

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		L.isDebug and L.logDebug(f'Forwarding NOTIFY request to: {request.id}')
		return self.sendNotifyRequest(uri = cast(str, request.id),
							 		  originator = request.originator,
									  data = request.originalRequest,
									  raw = True)


	def isTransitID(self, id:str) -> bool:
		""" Check whether an ID is a targeting a remote CSE via a CSR.
		"""
		if Utils.isSPRelative(id):
			ids = id.split('/')
			return len(ids) > 0 and ids[0] != CSE.cseCsi[1:]
		elif Utils.isAbsolute(id):
			ids = id.split('/')
			return len(ids) > 2 and ids[2] != CSE.cseCsi[1:]
		return False


	def _getForwardURL(self, path:str) -> str:		# FIXME DELETE ME This may be removed due to the new request handling 
		""" Get the new target URL when forwarding. 
		"""
		# L.isDebug and L.logDebug(path)
		csr, pe = CSE.remote.getCSRFromPath(path)
		# L.isDebug and L.logDebug(csr)
		if csr and (poas := csr.poa) and len(poas) > 0:
			return f'{poas[0]}//{"/".join(pe[1:])}'	# TODO check all available poas.
		return None


	def _constructForwardURL(self, request:CSERequest) -> Result:
		"""	Construct the target URL for the forward request. Add the original
			arguments. The URL is returned in Result.data .
		"""
		if not (url := self._getForwardURL(request.id)):
			return Result.errorResult(rsc = RC.notFound, dbg = f'forward URL not found for id: {request.id}')
		if request.originalHttpArgs is not None and len(request.originalHttpArgs) > 0:	# pass on other arguments, for discovery. Only http
			url += '?' + urllib.parse.urlencode(request.originalHttpArgs)
		return Result(status = True, data = url)


	def _originatorToSPRelative(self, request:CSERequest) -> None:
		"""	Convert *from* to SP-relative format in the request. The *from* is converted in
			*request.originator* and *request.originalRequest*, but NOT in 
			*request.originalData*.
		
			See TS-0004, 7.3.2.6, Forwarding
		"""
		if Utils.isCSERelative(request.originator):
			request.originator = Utils.toSPRelative(request.originator)
			Utils.setXPath(request.originalRequest, 'fr', request.originator, overwrite=True)	# Also in the original request
			# Attn: not changed in originatData !


	##############################################################################
	#
	#	Request/Response async sequence helpers for Polling
	#
	#	All the requests for all PCU are stored in a single dictionary:
	#		originator : [ request* ]
	#


	def hasPollingRequest(self, originator:str, requestID:str=None, reqType:RequestType=RequestType.REQUEST) -> bool:
		"""	Check whether there is a pending request or response pending for the tuple (`originator`, `requestID`).
			This method is also used as a callback for periodic check whether a request or response is queued.
			If `requestID` is not None then the check is for a request with that ID. 
			Otherwise, `True` will be returned if there is any request for the `originator`.
		"""
		with self._requestLock:
			return (lst := self._requests.get(originator)) is not None and any(	 (r, t) for r,t in lst if (requestID is None or r.rqi == requestID) and (t == reqType) )

	
	def queuePollingRequest(self, request:CSERequest, reqType:RequestType=RequestType.REQUEST) -> None:
		"""	Add a new `request` to the polling request queue. The `reqType` specifies whether this request is 
			a oneM2M Request or Response.
		"""
		L.isDebug and L.logDebug(f'Add request to queue, reqestType: {reqType}')

		# Some checks
		if not request.rqet:		
			# Adding a default expiration if none is set in the request
			ret = DateUtils.getResourceDate(self.requestExpirationDelta)
			L.isDebug and L.logDebug(f'Request must have a "requestExpirationTimestamp". Adding a default one: {ret}')
			request.rqet = ret
			request._rqetUTCts = DateUtils.fromAbsRelTimestamp(ret)
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
										delay = request._rqetUTCts - DateUtils.utcTime() + 1.0,	# +1 second delay 
										name = f'unqueuePolling_{request.rqi}-{reqType}').start()
	

	def unqueuePollingRequest(self, originator:str, requestID:str, reqType:RequestType) -> CSERequest:
		"""	Remove a request for the `originator` and with the `requestID` from the polling request queue. 
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


	def waitForPollingRequest(self, originator:str, requestID:str, timeout:float, reqType:RequestType = RequestType.REQUEST, aggregate:bool = False) -> Result:
		"""	Busy waiting for a polling request.
			The function returns when there is a new or pending matching request in the queue, or when the `timeout` (in seconds)
			is met.
			
			Args:
				originator: Request originator to match.
				requestID: Request Identifier to match. Might be None to match all request IDs.
				reqType: Match request or response.
				aggregate: Boolean indicating whether all the available requests shall be returned in one aggregation, or separately.
			Return:
				 The function returns a Result object with the request or aggregated requests in the `request` attribute.
		"""
		L.isDebug and L.logDebug(f'Waiting for: {reqType} for originator: {originator}, requestID: {requestID}')

		if DateUtils.waitFor(timeout, lambda:self.hasPollingRequest(originator, requestID, reqType)):	# Wait until timeout, or the request of the correct type was found
			L.isDebug and L.logDebug(f'Received {reqType} request for originator: {originator}, requestID: {requestID}, aggregate: {aggregate}')

			if aggregate:
				lst:list[CSERequest] = []
				while True:
					if req := self.unqueuePollingRequest(originator, requestID, reqType):
						lst.append(req)
						continue
					# if fall through then there is no further request available.
					# build the aggregated request
					agrp = { 'm2m:agrp' : [ RequestUtils.requestFromResult(Result(request = each)).data for each in lst ] }
					return Result(status = True, resource = agrp, rsc = RC.OK)
				
			else:
				if req := self.unqueuePollingRequest(originator, requestID, reqType):
					return Result(status = True, request = req, rsc = req.rsc)
			# fall-through
		return Result.errorResult(rsc = RC.requestTimeout, dbg = L.logWarn(f'Timeout while waiting for: {reqType} for originator: {originator}, requestID: {requestID}'))


	def queueRequestForPCH(	self, 
							pchOriginator:str,
							operation:Operation = Operation.NOTIFY,
							data:Any = None,
							ty:T = None,
							rvi:str = None,
							request:CSERequest = None,
							parameters:CSERequest = None,
							reqType:RequestType = RequestType.REQUEST,
							originator:str = None) -> CSERequest:
		"""	Queue a (incoming) `request` or `data` for a <PCH>. It can be retrieved via the target's <PCU> child resource.

			If a `request` is passed then this object is queued. If no `request` but `data` is given then a new request object is created 
			for `data`.
		"""

		# Check required arguments
		if not request and not data:
			L.logErr('Internal error. queueRequestForPCH() needs either a request or data to enqueue.')
			return None

		# L.isDebug and L.logDebug(request)
		# If no request is given, we create one here.
		if not request:
			# Fill various request attributes
			request 				= CSERequest()
			request.id				= pchOriginator
			request.op 				= operation
			request.originator		= originator
			request.ty 				= ty
			request.ot				= DateUtils.getResourceDate()
			request.rqi				= Utils.uniqueRI()
			request.rvi				= rvi if rvi is not None else CSE.releaseVersion
			request.pc 				= data

		# Copy additional parameter attributes
		if parameters:
			request.ec = parameters.ec

		# Always mark the request as a REQUEST
		request.requestType = reqType

		# Convert "from" to SP-relative format in the request
		# See TS-0001, 7.3.2.6, Forwarding
		self._originatorToSPRelative(request)

		# L.isDebug and L.logDebug(request)

		L.isDebug and L.logDebug(f'Storing REQUEST for: {request.id} with ID: {request.rqi} pc:{request.pc} for polling')
		self.queuePollingRequest(request, reqType)
		return request
	

	def waitForResponseToPCH(self, request:CSERequest) -> Result:
		"""	Wait for a RESPONSE to a request.
		"""
		L.isDebug and L.logDebug(f'Waiting for RESPONSE with request ID: {request.rqi}')

		if (response := self.waitForPollingRequest(request.originator, request.rqi, timeout=CSE.request.requestExpirationDelta, reqType=RequestType.RESPONSE)).status:
			L.isDebug and L.logDebug(f'RESPONSE received ID: {response.request.rqi} rsc: {response.request.rsc}')
			if (o1 := Utils.toSPRelative(response.request.originator)) != (o2 := Utils.toSPRelative(request.id)):
				return Result.errorResult(dbg = L.logWarn(f'Received originator: {o1} is different from original target originator: {o2}'))
			return Result(status = True, rsc = response.request.rsc, request = response.request)
		
		return Result.errorResult(rsc = RC.requestTimeout, dbg = response.dbg)


	def _cleanupPollingRequests(self) -> bool:
		with self._requestLock:
			# Search all entries in the queue and remove those that have expired in the past
			# Remove those requests also from 
			now = DateUtils.utcTime()
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
	#	Handling sending requests.
	#
	#

	# TODO id????


	def sendRetrieveRequest(self, uri:str, originator:str, data:Any = None, ct:ContentSerializationType = None, appendID:str = '', raw:bool = False) -> Result:
		"""	Send a RETRIEVE request via the appropriate channel or transport protocol.
		"""
		L.isDebug and L.logDebug(f'Sending RETRIEVE request to: {uri} id: {appendID}')

		for url, csz, rvi, pch, noriginator, to in self.resolveTargetURIetc(uri, 
															   appendID = appendID,
															   originator = originator,
															   permission = Permission.RETRIEVE,
															   raw = raw):

			# Send the request via a PCH, if present
			if pch:
				request = self.queueRequestForPCH(pch.getOriginator(), Operation.RETRIEVE, originator = noriginator, rvi = rvi)
				return self.waitForResponseToPCH(request)

			# Otherwise send it via one of the bindings
			if not ct and not (ct := RequestUtils.determineSerialization(url, csz, CSE.defaultSerialization)):
				continue

			if Utils.isHttpUrl(url):
				CSE.event.httpSendRetrieve() # type: ignore [attr-defined]
				return CSE.httpServer.sendHttpRequest(Operation.RETRIEVE, 
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			elif Utils.isMQTTUrl(url):
				CSE.event.mqttSendRetrieve()	# type: ignore [attr-defined]
				return CSE.mqttClient.sendMqttRequest(Operation.RETRIEVE, 
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			return Result.errorResult(dbg = L.logWarn(f'unsupported url scheme: {url}'))

		return Result.errorResult(rsc = RC.notFound, dbg = f'No target found for uri: {uri}')


	def sendCreateRequest(self, uri:str, originator:str, ty:T = None, data:Any = None, ct:ContentSerializationType = None, appendID:str = '', raw:bool = False, noAccessIsError:bool = False) -> Result:
		"""	Send a CREATE request via the appropriate channel or transport protocol.
		"""
		L.isDebug and L.logDebug(f'Sending CREATE request to: {uri} id: {appendID}')

		for url, csz, rvi, pch, noriginator, to in self.resolveTargetURIetc(uri, appendID = appendID, originator = originator, permission = Permission.CREATE, noAccessIsError = noAccessIsError, raw = raw):

			# Send the request via a PCH, if present
			if pch:
				if isinstance(data, CSERequest):
					request = self.queueRequestForPCH(pch.getOriginator(), Operation.CREATE, request = data, originator = noriginator, rvi = rvi)
				else:
					request = self.queueRequestForPCH(pch.getOriginator(), Operation.CREATE,  data = data, originator = noriginator, rvi = rvi)

				return self.waitForResponseToPCH(request)

			# Otherwise send it via one of the bindings
			if not ct and not (ct := RequestUtils.determineSerialization(url, csz, CSE.defaultSerialization)):
				continue

			if Utils.isHttpUrl(url):
				CSE.event.httpSendCreate() # type: ignore [attr-defined]
				return CSE.httpServer.sendHttpRequest(Operation.CREATE,
													  url,
													  originator = noriginator,
													  to = to,
													  ty = ty,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			elif Utils.isMQTTUrl(url):
				CSE.event.mqttSendCreate()	# type: ignore [attr-defined]
				return CSE.mqttClient.sendMqttRequest(Operation.CREATE,
													  url,
													  originator = noriginator,
													  to = to,
													  ty = ty,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			return Result.errorResult(dbg = L.logWarn(f'unsupported url scheme: {url}'))
		
		return Result.errorResult(rsc = RC.notFound, dbg = f'No target found for uri: {uri}')


	def sendUpdateRequest(self, uri:str, originator:str, data:Any, ct:ContentSerializationType = None, appendID:str = '', raw:bool = False) -> Result:
		"""	Send an UPDATE request via the appropriate channel or transport protocol.
		"""
		L.isDebug and L.logDebug(f'Sending UPDATE request to: {uri} id: {appendID}')

		for url, csz, rvi, pch, noriginator, to in self.resolveTargetURIetc(uri, appendID = appendID, originator = originator, permission = Permission.UPDATE, raw = raw):

			# Send the request via a PCH, if present
			if pch:
				if isinstance(data, CSERequest):
					request = self.queueRequestForPCH(pch.getOriginator(), Operation.UPDATE, request = data, originator = noriginator, rvi = rvi)
				else:
					request = self.queueRequestForPCH(pch.getOriginator(), Operation.UPDATE, data = data, originator = noriginator, rvi = rvi)
				return self.waitForResponseToPCH(request)

			# Otherwise send it via one of the bindings
			if not ct and not (ct := RequestUtils.determineSerialization(url, csz, CSE.defaultSerialization)):
				continue
			
			if Utils.isHttpUrl(url):
				CSE.event.httpSendUpdate() # type: ignore [attr-defined]
				return CSE.httpServer.sendHttpRequest(Operation.UPDATE,
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			elif Utils.isMQTTUrl(url):
				CSE.event.mqttSendUpdate()	# type: ignore [attr-defined]
				return CSE.mqttClient.sendMqttRequest(Operation.UPDATE,
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			return Result.errorResult(dbg = L.logWarn(f'unsupported url scheme: {url}'))
		
		return Result.errorResult(rsc = RC.notFound, dbg = f'No target found for uri: {uri}')


	def sendDeleteRequest(self, uri:str, originator:str, data:Any = None, ct:ContentSerializationType = None, appendID:str = '', raw:bool = False) -> Result:
		"""	Send a DELETE request via the appropriate channel or transport protocol.
		"""
		L.isDebug and L.logDebug(f'Sending DELETE request to: {uri} id: {appendID}')

		for url, csz, rvi, pch, noriginator, to in self.resolveTargetURIetc(uri, appendID = appendID, originator = originator, permission = Permission.DELETE, raw = raw):

			# Send the request via a PCH, if present
			if pch:
				request = self.queueRequestForPCH(pch.getOriginator(), Operation.DELETE, originator = noriginator, rvi = rvi)
				return self.waitForResponseToPCH(request)

			# Otherwise send it via one of the bindings
			if not ct and not (ct := RequestUtils.determineSerialization(url, csz, CSE.defaultSerialization)):
				continue

			if Utils.isHttpUrl(url):
				CSE.event.httpSendDelete() # type: ignore [attr-defined]
				return CSE.httpServer.sendHttpRequest(Operation.DELETE,
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			elif Utils.isMQTTUrl(url):
				CSE.event.mqttSendDelete()	# type: ignore [attr-defined]
				return CSE.mqttClient.sendMqttRequest(Operation.DELETE,
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			return Result.errorResult(dbg = L.logWarn(f'unsupported url scheme: {url}'))

		return Result.errorResult(rsc = RC.notFound, dbg = f'No target found for uri: {uri}')


	def sendNotifyRequest(self, uri:str, originator:str, data:Any = None, parameters:CSERequest = None, ct:ContentSerializationType = None, appendID:str = '', noAccessIsError:bool = False, raw:bool = False) -> Result:
		"""	Send a NOTIFY request via the appropriate channel or transport protocol.
		"""
		L.isDebug and L.logDebug(f'Sending NOTIFY request to: {uri} + id: {appendID} for Originator: {originator}')

		if (resolved := self.resolveTargetURIetc(uri, appendID = appendID, originator = originator, permission = Permission.NOTIFY, noAccessIsError = noAccessIsError, raw = raw)) is None:
			return Result.errorResult()

		for url, csz, rvi, pch, noriginator, to in resolved:

			# Send the request via a PCH, if present
			if pch:
				if isinstance(data, CSERequest):
					request = self.queueRequestForPCH(pch.getOriginator(), 
													  Operation.NOTIFY, 
													  request = data, 
													  parameters = parameters, 
													  originator = noriginator,
													  rvi = rvi)
				else:
					request = self.queueRequestForPCH(pch.getOriginator(), 
													  Operation.NOTIFY,
													  data = data, 
  													  parameters = parameters, 
													  originator = noriginator,
													  rvi = rvi)
				return self.waitForResponseToPCH(request)

			# Otherwise send it via one of the bindings
			if not ct and not (ct := RequestUtils.determineSerialization(url, csz, CSE.defaultSerialization)):
				continue
		
			# Get the content if data is a CSERequest
			if isinstance(data, CSERequest):
				data = data.pc

			if Utils.isHttpUrl(url):
				CSE.event.httpSendNotify() # type: ignore [attr-defined]
				return CSE.httpServer.sendHttpRequest(Operation.NOTIFY,
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  parameters = parameters,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			elif Utils.isMQTTUrl(url):
				CSE.event.mqttSendNotify()	# type: ignore [attr-defined]
				return CSE.mqttClient.sendMqttRequest(Operation.NOTIFY,
													  url,
													  originator = noriginator,
													  to = to,
													  data = data,
													  parameters = parameters,
													  ct = ct,
													  rvi = rvi,
													  raw = raw)
			elif Utils.isAcmeUrl(url):
				CSE.event.acmeNotification(url, noriginator, data)	# type: ignore [attr-defined]
				return Result.successResult()

			return Result.errorResult(dbg = L.logWarn(f'unsupported url scheme: {url}'))
		
		return Result.errorResult(rsc = RC.notFound, dbg = f'No target found for uri: {uri}')


	###########################################################################
	#
	#	Various support methods
	#

	def deserializeContent(self, data:bytes, mediaType:str) -> Result:
		"""	Deserialize a data structure.
			Supported media serialization types are JSON and cbor.

			If successful then the Result.data contains a tuple (dict, contentType)
		"""
		dct = None
		ct = ContentSerializationType.getType(mediaType, default = CSE.defaultSerialization)
		if data:
			try:
				if (dct := RequestUtils.deserializeData(data, ct)) is None:
					return Result(status = False, rsc = RC.unsupportedMediaType, dbg = f'Unsupported media type for content-type: {ct.name}', data = (None, ct))
			except Exception as e:
				L.isWarn and L.logWarn('Bad request (malformed content?)')
				return Result(status = False, rsc = RC.badRequest, dbg = f'Malformed content? {str(e)}', data = (None, ct))
		
		return Result(status = True, data = (dct, ct))



	def fillAndValidateCSERequest(self, cseRequest:CSERequest, isResponse:bool = False) -> Result:
		"""	Fill a `cseRequest` object according to its request structure in the *req* attribute.
		"""
		# ! Cannot be in RequestUtils bc to prevent circular import of CSE and validator

		def gget(dct:dict, attribute:str, default:Any = None, attributeType:BasicType = None, checkSubType:bool = False, greedy:bool = True) -> Any:
			"""	Local helper to greedy check and return a key/value from a dictionary.

				If `dct` is None or `attribute` couldn't be found then the `default` is returned.

				This method might raise a *ValueError* exception if validation or conversion of the
				attribute/value fails.
			"""
			if dct and (value := dct.get(attribute)) is not None:	# v may be int
				if greedy:
					del dct[attribute]
				if not (res := CSE.validator.validateAttribute(attribute, value, attributeType, rtype = T.REQRESP)).status:
					raise ValueError(f'attribute: {attribute}, value: {value} : {res.dbg}')
					
				newValue = res.data[1] #type: ignore [index]

				# Test sub-values if they are a list
				if attributeType == BasicType.list and checkSubType:
					newValueList = []
					for v in newValue:
						if not (res := CSE.validator.validateAttribute(attribute, v, rtype = T.REQRESP)).status:
							raise ValueError(f'attribute: {attribute}, value: {value} : {res.dbg}')
						newValueList.append(res.data[1]) #type: ignore [index]
					return newValueList

				return newValue	#type: ignore [index]
			return default


		try:
			errorResult = None
			# TODO check whether we can return ealier if errorResult is set

			# RQI - requestIdentifier
			# Check as early as possible
			if (rqi := gget(cseRequest.originalRequest, 'rqi', greedy = False)):
				cseRequest.rqi = rqi
			else:
				errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('Request Identifier parameter is mandatory in request'))

			# RVI - releaseVersionIndicator
			if not (rvi := gget(cseRequest.originalRequest, 'rvi', greedy = False)):
				errorResult = Result.errorResult(rsc = RC.releaseVersionNotSupported, request = cseRequest, dbg = L.logDebug(f'Release Version Indicator is missing in request, falling back to RVI=\'1\'. But Release Version \'1\' is not supported. Use RVI with one of {CSE.supportedReleaseVersions}.'))
			else:
				if rvi in CSE.supportedReleaseVersions:
					cseRequest.rvi = rvi	
				else:
					errorResult = Result.errorResult(rsc = RC.releaseVersionNotSupported, request = cseRequest, dbg = L.logDebug(f'Release version unsupported: {rvi}'))
		
			# OP - operation
			if (op := gget(cseRequest.originalRequest, 'op', greedy = False)) is not None:	# op is an int
				if Operation.isvalid(op):
					cseRequest.op = Operation(op)
				else:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug(f'Unknown/unsupported operation: {op}'))
			elif not isResponse:
				errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('operation parameter is mandatory in request'))

			# TY - resource type
			if (ty := gget(cseRequest.originalRequest, 'ty', greedy = False)) is not None:	# ty is an int
				if T.has(ty):
					cseRequest.ty = T(ty)
				else:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug(f'Unknown/unsupported resource type: {ty}'))

			# FR - originator 
			if not (fr := gget(cseRequest.originalRequest, 'fr', greedy = False)) and not isResponse and not (cseRequest.ty == T.AE and cseRequest.op == Operation.CREATE):
				errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('From/Originator parameter is mandatory in request'))
			else:
				cseRequest.originator = fr

			# TO - target
			if not (to := gget(cseRequest.originalRequest, 'to', greedy = False)) and not isResponse:
				errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('To/Target parameter is mandatory in request'))
			else:
				cseRequest.to = to
				if to:
					cseRequest.id, cseRequest.csi, cseRequest.srn, dbg = Utils.retrieveIDFromPath(to, CSE.cseRn, CSE.cseCsi, CSE.cseSpid)
					if dbg:
						return Result.errorResult(request = cseRequest, dbg = dbg)

			# Check identifiers
			if not isResponse and not cseRequest.id and not cseRequest.srn:
				errorResult = Result.errorResult(rsc = RC.notFound, request = cseRequest, dbg = L.logDebug('missing identifier (no id nor srn)'))

			# OT - originating timestamp
			if ot := gget(cseRequest.originalRequest, 'ot', greedy = False):
				if (_ts := DateUtils.fromAbsRelTimestamp(ot)) == 0.0:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('Error in provided Originating Timestamp'))
				else:
					cseRequest.ot = ot

			# RQET - requestExpirationTimestamp
			if rqet := gget(cseRequest.originalRequest, 'rqet', greedy=False):
				if (_ts := DateUtils.fromAbsRelTimestamp(rqet)) == 0.0:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('Error in provided Request Expiration Timestamp'))
				else:
					if _ts < DateUtils.utcTime():
						errorResult = Result.errorResult(request = cseRequest, rsc = RC.requestTimeout, dbg = L.logDebug('Request timeout'))
					else:
						cseRequest._rqetUTCts = _ts		# Re-assign "real" ISO8601 timestamp
						cseRequest.rqet = DateUtils.toISO8601Date(_ts)

			# RSET - resultExpirationTimestamp
			if (rset := gget(cseRequest.originalRequest, 'rset', greedy=False)):
				if (_ts := DateUtils.fromAbsRelTimestamp(rset)) == 0.0:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('Error in provided Result Expiration Timestamp'))
				else:
					if _ts < DateUtils.utcTime():
						errorResult = Result.errorResult(request = cseRequest, rsc = RC.requestTimeout, dbg = L.logDebug('Result timeout'))
					else:
						cseRequest.rset = DateUtils.toISO8601Date(_ts)	# Re-assign "real" ISO8601 timestamp

			# OET - operationExecutionTime
			if (oet := gget(cseRequest.originalRequest, 'oet', greedy=False)):
				if (_ts := DateUtils.fromAbsRelTimestamp(oet)) == 0.0:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug('Error in provided Operation Execution Time'))
				else:
					cseRequest.oet = DateUtils.toISO8601Date(_ts)	# Re-assign "real" ISO8601 timestamp

			# RVI - releaseVersionIndicator
			if  (rvi := gget(cseRequest.originalRequest, 'rvi', greedy=False)):
				if rvi not in CSE.supportedReleaseVersions:
					errorResult = Result.errorResult(rsc = RC.releaseVersionNotSupported, 
													 request = cseRequest, 
													 dbg = L.logDebug(f'Release version unsupported: {rvi}'))
				else:
					cseRequest.rvi = rvi	
			else:
				errorResult = Result.errorResult(rsc = RC.releaseVersionNotSupported, 
												 request = cseRequest, 
												 dbg = L.logDebug(f'Release Version Indicator is missing in request, falling back to RVI=\'1\'. But Release Version \'1\' is not supported. Use RVI with one of {CSE.supportedReleaseVersions}.'))

			# VSI - vendorInformation
			if (vsi := gget(cseRequest.originalRequest, 'vsi', greedy=False)):
				cseRequest.vsi = vsi	

			# DRT - Desired Identifier Result Type
			cseRequest.drt = DesiredIdentifierResultType(gget(cseRequest.originalRequest, 'drt', DesiredIdentifierResultType.structured, greedy = False))	# 1=strucured, 2=unstructured

			#
			# Transfer filterCriteria: handling, conditions and attributes
			#

			fc = deepcopy(cseRequest.originalRequest.get('fc'))	# copy because we will greedy consume attributes here

			# FU - Filter Usage
			cseRequest.fc.fu = FilterUsage(gget(fc, 'fu', FilterUsage.conditionalRetrieval))
			if cseRequest.fc.fu == FilterUsage.discoveryCriteria and cseRequest.op == Operation.RETRIEVE:	# correct operation if necessary
				cseRequest.op = Operation.DISCOVERY

			# FO - Filter Operation
			cseRequest.fc.fo = FilterOperation(gget(fc, 'fo', FilterOperation.AND))


			# RCN Result Content Type
			if (rcn := gget(cseRequest.originalRequest, 'rcn', greedy = False)) is not None: 	# rcn is an int
				try:
					rcn = ResultContentType(rcn)
				except ValueError as e:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug(f'Error validating rcn: {str(e)}'))
			else:
				# assign defaults when not provided
				if cseRequest.fc.fu != FilterUsage.discoveryCriteria:	
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
				errorResult = Result(status = False, rsc = RC.badRequest, request = cseRequest, dbg = L.logDebug(f'rcn: {rcn} not allowed in RETRIEVE operation'))
			elif cseRequest.op == Operation.DISCOVERY and rcn not in [ ResultContentType.childResourceReferences,
																	ResultContentType.discoveryResultReferences ]:
				errorResult = Result(status = False, rsc = RC.badRequest, request = cseRequest, dbg = L.logDebug(f'rcn: {rcn} not allowed in DISCOVERY operation'))
			elif cseRequest.op == Operation.CREATE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.modifiedAttributes,
																	ResultContentType.hierarchicalAddress,
																	ResultContentType.hierarchicalAddressAttributes,
																	ResultContentType.nothing ]:
				errorResult = Result(status = False, rsc = RC.badRequest, request = cseRequest, dbg = L.logDebug(f'rcn: {rcn} not allowed in CREATE operation'))
			elif cseRequest.op == Operation.UPDATE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.modifiedAttributes,
																	ResultContentType.nothing ]:
				errorResult = Result(status = False, rsc = RC.badRequest, request = cseRequest, dbg = L.logDebug(f'rcn: {rcn} not allowed in UPDATE operation'))
			elif cseRequest.op == Operation.DELETE and rcn not in [ ResultContentType.attributes,
																	ResultContentType.nothing,
																	ResultContentType.attributesAndChildResources,
																	ResultContentType.childResources,
																	ResultContentType.attributesAndChildResourceReferences,
																	ResultContentType.childResourceReferences ]:
				errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug(f'rcn: {rcn} not allowed in DELETE operation'))
			cseRequest.rcn = rcn


			# RT - responseType: RTV responseTypeValue, RTU/NU responseTypeNUs
			if (rt := gget(cseRequest.originalRequest, 'rt', greedy = False)) is not None: # rt is an int
				cseRequest.rt = ResponseType(gget(rt, 'rtv', ResponseType.blockingRequest, greedy = False))
				# TODO nu should only be set when responseType=non-blocking async
				if (nu := gget(rt, 'nu', greedy = False)) is not None:
					cseRequest.rtu = nu	#  TODO validate for url?

			# RP - resultPersistence (also as timestamp)
			if (rp := gget(cseRequest.originalRequest, 'rp', greedy=False)): 
				cseRequest.rp = rp
				if (rpts := DateUtils.toISO8601Date(DateUtils.fromAbsRelTimestamp(rp))) == 0.0:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug(f'"{rp}" is not a valid value for rp'))
				else:
					cseRequest._rpts = rpts
			else:
				cseRequest.rp = None
				cseRequest._rpts = None

			#
			#	Discovery and FilterCriteria
			#
			if fc:	# only when there is a filterCriteria, copy the available attribute to the FilterCriteria structure
				for h in [ 'lim', 'lvl', 'ofst', 'arp' ]:
					if (v := gget(fc, h)) is not None:	# may be int
						cseRequest.fc.set(h, v)
				for h in [ 'crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr' ]:
					if (v := gget(fc, h)) is not None:	# may be int
						cseRequest.fc.set(h, v)
				for h in [ 'lbl', 'cty' ]: # different handling of list attributes
					if (v := gget(fc, h, attributeType = BasicType.list, checkSubType = False)) is not None:
						cseRequest.fc.set(h, v)
				for h in [ 'ty' ]: # different handling of list attributes that are normally non-lists
					if (v := gget(fc, h, attributeType = BasicType.list, checkSubType = True)) is not None:	# may be int
						cseRequest.fc.set(h, v)
				for h in list(fc.keys()): # All remaining attributes
					cseRequest.fc.attributes[h] = gget(fc, h)

			# Copy rsc
			if (rsc := gget(cseRequest.originalRequest, 'rsc', greedy = False)): 
				cseRequest.rsc = ResponseStatusCode(rsc)

			# Copy primitive content
			# Check whether content is empty and operation is UPDATE or CREATE -> Error
			if not (pc := cseRequest.originalRequest.get('pc')):
				if cseRequest.op in [ Operation.CREATE, Operation.UPDATE ]:
					errorResult = Result.errorResult(request = cseRequest, dbg = L.logDebug(f'Missing primitive content or body in request for operation: {cseRequest.op}'))
			else:
				cseRequest.pc = cseRequest.originalRequest.get('pc')	# The reqeust.pc contains the primitive content
				if not (res := CSE.validator.validatePrimitiveContent(cseRequest.pc)).status:
					L.isDebug and L.logDebug(res.dbg)
					res.request = cseRequest
					errorResult = res

		# end of try..except
		except ValueError as e:
			
			return Result.errorResult(request = cseRequest, dbg = L.logDebug(f'Error getting or validating attribute/parameter: {str(e)}'))

		# Return the error or success result 
		return errorResult if errorResult else Result(status = True, rsc = cseRequest.rsc, request = cseRequest, data = cseRequest.pc)


	def dissectRequestFromBytes(self, data:bytes, contenType:str, isResponse:bool=False) -> Result:
		"""	Dissect a request in a byte string and build up a . Return it in `Result.request` .
		"""
		cseRequest = CSERequest()
		cseRequest.originalData = data
		cseRequest.mediaType = contenType.lower()

		# De-Serialize the content
		if not (contentResult := self.deserializeContent(cseRequest.originalData, cseRequest.mediaType)).status:
			_, cseRequest.ct = contentResult.data	# type: ignore[assignment] # Actual, .data contains a tuple
			return Result(status = False, rsc = contentResult.rsc, request = cseRequest, dbg = contentResult.dbg, )
		cseRequest.originalRequest, cseRequest.ct = contentResult.data	# type: ignore[assignment] # Actual, .data contains a tuple

		# Validate the request
		try:
			if not (res := self.fillAndValidateCSERequest(cseRequest, isResponse)).status:
				#return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=res.status)
				return res
		except Exception as e:
			import traceback
			traceback.print_exc()
			return Result(status = False, rsc = RC.badRequest, request = cseRequest, dbg = f'invalid arguments/attributes ({str(e)})', )
		
		return res


	###########################################################################

	#
	#	Utilities
	#

	def getSerializationFromOriginator(self, originator:str) -> List[ContentSerializationType]:
		"""	Look for the content serializations of a registered originator.
			It is either an AE, a CSE or a CSR.
			Return a list of types.
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
		elif (l := len(cses := CSE.storage.searchByFragment({ 'csi' : Utils.getIdFromOriginator(originator) }))) > 0:
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


	def resolveTargetURIetc(self, 
							uri:str, 
							permission:Permission, 
							appendID:str = '', 
							originator:str = None,
							noAccessIsError:bool = False,
							raw:bool = False) -> list[ Tuple[str, list[str], str, PCH, str, str ] ]:
		"""	Resolve the real URL and more message parameters for a request and a target,
		
			Args:
				uri: Target resource ID or a URL for a target.
				permission: The necessary permissions for the about-to-be performed operation.
				appendID: Optional extra ID to determine the target.
				originator: The request originator.
				noAccessIsError: Ignore or handle permission errors.
				raw: This is intended for a *raw* request. Ignore permission checks.
			Return:
				The results could differ:

				The result is a list of tuples of (real url including the protocol, list of allowed contentSerializations,
				target supported release version, PollingChannel resource, originator with adapted scope).
				
				Or, return a list of (url, None, None, None, originator), containing only one element, if the URI is
				already a URL. We cannot determine the preferred serializations in this case. and we don't know the target entity.
				
				Return a list of (None, list of allowed contentSerializations, srv, PollingChannel resource,
				originator with adapted scope), containing only one element, if the target resourec is not
				request reachable and has a PollingChannel as a child resource.

				Otherwise, return a list of the mentioned tuples.

				In case of an error, an empty list is returned. 
				If *noAccessIsError* is *True* and access is not permitted then *None* is returned.
		"""

		def getTargetReleaseVersion(srv:list) -> str:
			if (srv := targetResource.srv):
				return sorted(srv)[-1]	# return highest srv
			return CSE.releaseVersion
				
		#L.logWarn(uri)

		# TODO check whether noAccessIsError is needed anymore

		if Utils.isURL(uri):	# The uri is a direct URL
			return [ (uri, None, None, None, originator, None) ]


		# targetResource will be assigned the real resource that offers the POA
		# It may be an AE, CSE, CSR.
		targetResource = None

		if Utils.isSPRelative(uri) or Utils.isAbsolute(uri):
			if uri.startswith(f'{CSE.cseCsi}/'):	# If this the local CSE
				targetResource = Utils.getCSE().resource
			elif (t := CSE.remote.getCSRFromPath(uri)):
				targetResource, _ = t
			# HACK if the target is a /csi/something AND there is no extra ID given, we add that extra ID to address the resource on that CSE
			if not appendID:
				appendID = uri
			#L.logWarn(targetResource)
			#L.logWarn(uri)

		# The uri is an indirect resource with poa, retrieve one or more URIs from it
		if not targetResource and not (targetResource := CSE.dispatcher.retrieveResource(uri).resource):
			L.isWarn and L.logWarn(f'Resource not found to get URL: {uri}')
			return []
		
		# Checking permissions
		if not uri.startswith(f'{CSE.cseCsi}/'):	# TODO make a utility out of this
			if originator == CSE.cseCsi:
				L.isDebug and L.logDebug(f'Originator: {originator} is CSE -> Permission granted.')
			elif not raw and not CSE.security.hasAccess(originator, targetResource, permission):
				L.isWarn and L.logWarn(f'Originator: {originator} has no permission: {permission} for {targetResource.ri}')
				if noAccessIsError:
					return None
				return []

		# Check requestReachability
		# If the target is NOT reachable then try to retrieve a potential
		pollingChannelResources = []
		if targetResource.rr == False:
			L.isDebug and L.logDebug(f'Target: {uri} is not requestReachable. Trying <PCH>.')
			if not len(pollingChannelResources := CSE.dispatcher.directChildResources(targetResource.ri, T.PCH)):
				L.isWarn and L.logWarn(f'Target: {uri} is not requestReachable and does not have a <PCH>.')
				return []
			# Take the first resource and return it. There should hopefully only be one, but we don't check this here
			return [ (None, 
					  targetResource.csz,
					  getTargetReleaseVersion(targetResource.srv),
					  cast(PCH, pollingChannelResources[0]),
					  originator,
					  uri) ]

		# Use the poa of a target resource
		if not targetResource.poa:	# check that the resource has a poa
			L.isWarn and L.logWarn(f'Resource {uri} has no "poa" attribute')
			return []
		
		resultList:List[Tuple[str, List[str], str, PCH, str, str]] = []
		
		for p in targetResource.poa:
			if Utils.isHttpUrl(p) and p[-1] != '/':	# Special handling for http urls
				p += '/'
			resultList.append((f'{p}{appendID}', 
							   targetResource.csz, 
							   getTargetReleaseVersion(targetResource.srv), 
							   None,
							   Utils.toSPRelative(originator) if targetResource.ty in [ T.CSEBase, T.CSR ] and targetResource.csi != CSE.cseCsi else originator,
							   f'{uri}{appendID}'))
		# L.logWarn(result)
		return resultList


