#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external requests are routed through here.
#

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
from resources.REQ import REQ
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool


import CSE, Utils
from flask import Request
from typing import Any, List, Tuple, Union, Dict


class RequestManager(object):

	def __init__(self) -> None:
		self.enableTransit 			= Configuration.get('cse.enableTransitRequests')
		self.cseri 					= Configuration.get('cse.ri')
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
		Logging.logDebug('RETRIEVE ID: %s, originator: %s' % (request.id if request.id is not None else request.srn, request.headers.originator))

		# handle transit requests
		if CSE.remote.isTransitID(request.id):
		 	return CSE.remote.handleTransitRetrieveRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		if request.args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)



	#########################################################################
	#
	#	CREATE resources
	#

	def createRequest(self, request:CSERequest) -> Result:
		Logging.logDebug('CREATE ID: %s, originator: %s' % (request.id if request.id is not None else request.srn, request.headers.originator))

		# handle transit requests
		if CSE.remote.isTransitID(request.id):
			return CSE.remote.handleTransitCreateRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# Check contentType and resourceType
		if request.headers.contentType == None or request.headers.contentType == None:
			return Result(rsc=RC.badRequest, dbg='missing or wrong contentType or resourceType in request')

		if request.args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processCreateRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processCreateRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)


	#########################################################################
	#
	#	UPDATE resources
	#

	def updateRequest(self, request:CSERequest) -> Result:
		Logging.logDebug('UPDATE ID: %s, originator: %s' % (request.id if request.id is not None else request.srn, request.headers.originator))

		# Don't update the CSEBase
		if request.id == self.cseri:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for CSEBase')

		# handle transit requests
		if CSE.remote.isTransitID(request.id):
			return CSE.remote.handleTransitUpdateRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

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

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)


	#########################################################################
	#
	#	DELETE resources
	#


	def deleteRequest(self, request:CSERequest,) -> Result:
		Logging.logDebug('DELETE ID: %s, originator: %s' % (request.id if request.id is not None else request.srn, request.headers.originator))

		# Don't update the CSEBase
		if request.id == self.cseri:
			return Result(rsc=RC.operationNotAllowed, dbg='operation not allowed for CSEBase')

		# handle transit requests
		if CSE.remote.isTransitID(request.id):
			return CSE.remote.handleTransitDeleteRequest(request) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		if request.args.rt == ResponseType.blockingRequest or (request.args.rt == ResponseType.flexBlocking and self.flexBlockingBlocking):
			return CSE.dispatcher.processDeleteRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		elif request.args.rt == ResponseType.flexBlocking:
			if self.flexBlockingBlocking:			# flexBlocking as blocking
				return CSE.dispatcher.processDeleteRequest(request, request.headers.originator)
			else:									# flexBlocking as non-blocking
				return self._handleNonBlockingRequest(request)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)



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

		jsn:Dict[str, Any] = None
		# Synchronous handling
		if request.args.rt == ResponseType.nonBlockingRequestSynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(0.0, self._runNonBlockingRequestSync, 'request_%s' % request.headers.requestIdentifier).start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			jsn = { 'm2m:uri' : reqres.resource.ri }
			return Result(jsn=jsn, rsc=RC.acceptedNonBlockingRequestSynch)

		# Asynchronous handling
		if request.args.rt == ResponseType.nonBlockingRequestAsynch:
			# Run operation in the background
			BackgroundWorkerPool.newActor(0.0, self._runNonBlockingRequestAsync, 'request_%s' % request.headers.requestIdentifier).start(request=request, reqRi=reqres.resource.ri)
			# Create the response content with the <request> ri 
			jsn = { 'm2m:uri' : reqres.resource.ri }
			return Result(jsn=jsn, rsc=RC.acceptedNonBlockingRequestAsynch)

		# Error
		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)


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
				Logging.logWarn('Wrong number of AEs with aei: %s (%d)' % (originator, len(aes)))
			else:
				Logging.logDebug('No RTU. Get NUS from originator ae: %s' % aes[0].ri)
				nus = aes[0].poa

		# send notifications.Ignore any errors here
		CSE.notification.sendNotificationWithJSON(responseNotification, nus)

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
				reqres['ors/pc'] = operationResult.resource.asJSON()
		else:																				# Error
			reqres['rs'] = RequestStatus.FAILED
			if operationResult.dbg is not None:
				reqres['ors/pc'] = { 'm2m:dbg' : operationResult.dbg }

		# Update in DB
		reqres.dbUpdate()

		return Result(resource=reqres, status=True)
