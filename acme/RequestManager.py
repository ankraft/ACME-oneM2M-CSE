#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external requests are routed through here.
#

import requests, urllib.parse
from Logging import Logging
from Configuration import Configuration
from Types import Operation
from Types import RequestArguments
from Types import RequestHeaders
from Types import RequestStatus
from Types import ResourceTypes as T
from Types import ResponseCode as RC
from Types import ResponseType
from Types import Result
from Types import CSERequest
from Types import ContentSerializationType
from Types import Parameters
from resources.REQ import REQ
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool


import CSE, Utils
from flask import Request
from typing import Any, List, Tuple, Union, Dict


class RequestManager(object):

	def __init__(self) -> None:
		self.enableTransit 			= Configuration.get('cse.enableTransitRequests')
		self.flexBlockingBlocking	= Configuration.get('cse.flexBlockingPreference') == 'blocking'

		Logging.log('RequestManager initialized')


	def shutdown(self) -> bool:
		Logging.log('RequestManager shut down')
		return True


	#########################################################################
	#
	#	RETRIEVE Request
	#

	def retrieveRequest(self, request:CSERequest) ->  Result:
		Logging.logDebug(f'RETRIEVE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

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
		Logging.logDebug(f'CREATE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

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
		Logging.logDebug(f'UPDATE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

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
		Logging.logDebug(f'DELETE ID: {request.id if request.id is not None else request.srn}, originator: {request.headers.originator}')

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
			BackgroundWorkerPool.newActor(0.0, self._runNonBlockingRequestSync, f'request_{request.headers.requestIdentifier}').start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			return Result(dict={ 'm2m:uri' : reqres.resource.ri }, rsc=RC.acceptedNonBlockingRequestSynch)

		# Asynchronous handling
		if request.args.rt == ResponseType.nonBlockingRequestAsynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(0.0, self._runNonBlockingRequestAsync, f'request_{request.headers.requestIdentifier}').start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			return Result(dict={ 'm2m:uri' : reqres.resource.ri }, rsc=RC.acceptedNonBlockingRequestAsynch)

		# Error
		return Result(rsc=RC.badRequest, dbg=f'Unknown or unsupported ResponseType: {request.args.rt}')


	def _runNonBlockingRequestSync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
		"""
		Logging.logDebug('Executing nonBlockingRequestSync')
		return self._executeOperation(request, reqRi).status


	def _runNonBlockingRequestAsync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
			In addition notify the notification targets.
		"""
		Logging.logDebug('Executing nonBlockingRequestAsync')
		if not (result := self._executeOperation(request, reqRi)).status:
			return False

		Logging.logDebug('Sending result notifications for nonBlockingRequestAsynch')
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
				Logging.logWarn(f'Wrong number of AEs with aei: {originator} ({len(aes):d}): {str(aes)}')
				nus = aes[0].poa
			else:
				Logging.logDebug(f'No RTU. Get NUS from originator ae: {aes[0].ri}')
				nus = aes[0].poa

		# send notifications.Ignore any errors here
		CSE.notification.sendNotificationWithDict(responseNotification, nus)

		return True


	def _executeOperation(self, request:CSERequest, reqRi:str) -> Result:
		"""	Execute a request operation and fill the respective request resource
			accordingly.
		"""
		# Execute the actual operation
		request.args.operation == Operation.RETRIEVE and (operationResult := CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)) is not None
		request.args.operation == Operation.CREATE   and (operationResult := CSE.dispatcher.processCreateRequest(request, request.headers.originator)) is not None
		request.args.operation == Operation.UPDATE   and (operationResult := CSE.dispatcher.processUpdateRequest(request, request.headers.originator)) is not None
		request.args.operation == Operation.DELETE   and (operationResult := CSE.dispatcher.processDeleteRequest(request, request.headers.originator)) is not None

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
		Logging.log(f'Forwarding Retrieve/Discovery request to: {url}')
		return self.sendRetrieveRequest(url, request.headers.originator)


	def handleTransitCreateRequest(self, request:CSERequest) -> Result:
		""" Forward a CREATE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Create request to: {url}')
		return self.sendCreateRequest(url, request.headers.originator, data=request.data, ty=request.headers.resourceType)


	def handleTransitUpdateRequest(self, request:CSERequest) -> Result:
		""" Forward an UPDATE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Update request to: {url}')
		return self.sendUpdateRequest(url, request.headers.originator, data=request.data)


	def handleTransitDeleteRequest(self, request:CSERequest) -> Result:
		""" Forward a DELETE request to a remote CSE. """
		if (url := self._getForwardURL(request.id)) is None:
			return Result(rsc=RC.notFound, dbg=f'forward URL not found for id: {request.id}')
		if len(request.originalArgs) > 0:	# pass on other arguments, for discovery
			url += '?' + urllib.parse.urlencode(request.originalArgs)
		Logging.log(f'Forwarding Delete request to: {url}')
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
		Logging.logDebug(path)
		r, pe = CSE.remote.getCSRFromPath(path)
		Logging.logDebug(str(r))
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
		Logging.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)


	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a CREATE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendCreate() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.post, url, originator, ty, data, parameters=parameters, ct=ct, targetResource=targetResource)
		Logging.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)


	def sendUpdateRequest(self, url:str, originator:str, data:Any, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a UPDATE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendUpdate() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.put, url, originator, data=data, parameters=parameters, ct=ct, targetResource=targetResource)
		Logging.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)


	def sendDeleteRequest(self, url:str, originator:str, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:
		"""	Send a DELETE request via the appropriate channel or transport protocol.
		"""
		if Utils.isHttpUrl(url):
			CSE.event.httpSendDelete() # type: ignore
			return CSE.httpServer.sendHttpRequest(requests.delete, url, originator, parameters=parameters, ct=ct, targetResource=targetResource)
		Logging.logWarn(dbg := f'unsupported url scheme: {url}')
		return Result(status=True, rsc=RC.badRequest, dbg=dbg)

