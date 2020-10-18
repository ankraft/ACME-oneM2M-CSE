#
#	RequestManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Main request dispatcher. All external requests are routed through here.
#

import json
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





# TODO
#
#
#
#	Implement "ASYNC"




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

		if request.args.rt == ResponseType.blockingRequest or (request.args.rt == ResponseType.flexBlocking and self.flexBlockingBlocking):
			return CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		# TODO other nonBlocking 

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

		if request.args.rt == ResponseType.blockingRequest or (request.args.rt == ResponseType.flexBlocking and self.flexBlockingBlocking):
			return CSE.dispatcher.processCreateRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		# TODO other nonBlocking 

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

		if request.args.rt == ResponseType.blockingRequest or (request.args.rt == ResponseType.flexBlocking and self.flexBlockingBlocking):
			return CSE.dispatcher.processUpdateRequest(request, request.headers.originator)

		elif request.args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(request)

		# TODO other nonBlocking 

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

		# TODO other nonBlocking 

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)



	#########################################################################
	#
	#	<request> handling
	#

	def _createRequestResource(self, request:CSERequest, content:dict=None) -> Result:

		# Get initialized resource
		if (nres := REQ.createRequestResource(request, content)).resource is None:
			return Result(rsc=RC.badRequest, dbg=nres.dbg)

		# Register <request>
		if (cseres := Utils.getCSE()).resource is None:
			return Result(rsc=RC.badRequest, dbg=cseres.dbg)
		if (rres := CSE.registration.checkResourceCreation(nres.resource, request.headers.originator, cseres.resource)).rsc != RC.OK:
			return rres.errorResult()

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

		# Run operation in the background
		BackgroundWorkerPool.newActor(0.0, self._runNonBlockingRequestSync, 'request_%s' % request.headers.requestIdentifier).start(request=request, reqRi=reqres.resource.ri)

		if request.args.rt == ResponseType.nonBlockingRequestSynch:
			# Create the response content with the <request> ri 
			jsn:Dict[str, Any] = { 'm2m:uri' : reqres.resource.ri }
			return Result(jsn=jsn, rsc=RC.accepedNonBlockingRequestSynch)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % request.args.rt)


	def _runNonBlockingRequestSync(self, request:CSERequest, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
		"""

		# Execute the actual operation
		request.args.operation == Operation.RETRIEVE and (operationResult := CSE.dispatcher.processRetrieveRequest(request, request.headers.originator)) is not None
		request.args.operation == Operation.CREATE   and (operationResult := CSE.dispatcher.processCreateRequest(request, request.headers.originator)) is not None
		request.args.operation == Operation.UPDATE   and (operationResult := CSE.dispatcher.processUpdateRequest(request, request.headers.originator)) is not None
		request.args.operation == Operation.DELETE   and (operationResult := CSE.dispatcher.processDeleteRequest(request, request.headers.originator)) is not None

		# Retrieve the <request> resource
		if (res := CSE.dispatcher.retrieveResource(reqRi)).resource is None:	
			return True 														# No idea what we should do if this fails
		reqres = res.resource

		# Fill the <request>
		reqres['ors'] = {	# operationResult
			'rsc'	: operationResult.rsc,
			'rid'	: reqres.rid,
			'to'	: request.id,
			'fr'	: reqres.originator,
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
		return True

