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
from resources.REQ import REQ
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool


import CSE, Utils
from flask import Request
from typing import Any, List, Tuple, Union, Dict





# TODO
#
#	Implement "noResponse"
#
# in REQ.py: configurable
#			minEt = Utils.getResourceDate(5) 	# TODO config
#			maxEt = Utils.getResourceDate(20) 	# TODO config
#




class RequestManager(object):

	def __init__(self) -> None:
		self.enableTransit 		= Configuration.get('cse.enableTransitRequests')
		self.cseri 				= Configuration.get('cse.ri')

		Logging.log('RequestManager initialized')


	def shutdown(self) -> bool:
		Logging.log('RequestManager shut down')
		return True


	#########################################################################
	#
	#	RETRIEVE Request
	#

	def retrieveRequest(self, request:Request, _id:Tuple[str, str, str]) ->  Result:
		requestHeaders, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('RETRIEVE ID: %s, originator: %s' % (id if id is not None else srn, requestHeaders.originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier')

		# handle transit requests
		if CSE.remote.isTransitID(id):
		 	return CSE.remote.handleTransitRetrieveRequest(request, id, requestHeaders.originator) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# handle hybrid ids
		srn, id = Utils.srnFromHybrid(srn, id) # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleRetrieveRequest(request, srn, requestHeaders.originator)

		# just a normal retrieve request
		return self.handleRetrieveRequest(request, id if id is not None else srn, requestHeaders.originator, requestHeaders)



	def handleRetrieveRequest(self, request:Request, id:str, originator:str, requestHeaders:RequestHeaders=None) -> Result:
		Logging.logDebug('Handle retrieve resource: %s' % id)

		try:
			_, msg, args = Utils.getRequestArguments(request, Operation.RETRIEVE)
			if args is None:
				return Result(rsc=RC.badRequest, dbg=msg)
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg='invalid arguments (%s)' % str(e))

		# if async: create request resource and proceed in a thread, also: return with REQ.ri
		# otherwise proceed normally

		if args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processRetrieveRequest(args, id, originator)
		elif args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(id, args, requestHeaders)

		# TODO other nonBlocking 


		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % args.rt)



	#########################################################################
	#
	#	CREATE resources
	#

	def createRequest(self, request:Request, _id:Tuple[str, str, str]) -> Result:
		requestHeaders, _ = Utils.getRequestHeaders(request)
		id, csi, srn = _id
		Logging.logDebug('CREATE ID: %s, originator: %s' % (id if id is not None else srn, requestHeaders.originator))

		# No ID, return immediately 
		if id is None and srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier')

		# handle transit requests
		if CSE.remote.isTransitID(id):
			return CSE.remote.handleTransitCreateRequest(request, id, requestHeaders.originator, requestHeaders.resourceType) if self.enableTransit else Result(rsc=RC.operationNotAllowed, dbg='operation not allowed')

		# handle hybrid id
		srn, id = Utils.srnFromHybrid(srn, id)  # Hybrid

		# handle fanout point requests
		if (fanoutPointResource := Utils.fanoutPointResource(srn)) is not None and fanoutPointResource.ty == T.GRP_FOPT:
			Logging.logDebug('Redirecting request to fanout point: %s' % fanoutPointResource.__srn__)
			return fanoutPointResource.handleCreateRequest(request, srn, requestHeaders.originator, requestHeaders.contentType, requestHeaders.resourceType)

		# just a normal create request
		return self.handleCreateRequest(request, id, requestHeaders.originator, requestHeaders.contentType, requestHeaders.resourceType, requestHeaders)


	def handleCreateRequest(self, request:Request, id:str, originator:str, ct:str, ty:T, requestHeaders:RequestHeaders=None) -> Result:
		Logging.logDebug('Adding new resource')

		try:
			_, msg, args = Utils.getRequestArguments(request, Operation.CREATE)
			if args is None:
				return Result(rsc=RC.badRequest, dbg=msg)
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg='invalid arguments (%s)' % str(e))

		if args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processCreateRequest(args, id, originator, ct, ty)
		elif args.rt in [ ResponseType.nonBlockingRequestSynch, ResponseType.nonBlockingRequestAsynch ]:
			return self._handleNonBlockingRequest(id, args, requestHeaders)

		# TODO other nonBlocking 

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % args.rt)



	#########################################################################

	#
	#	<request> handling
	#

	def _createRequestResource(self, arguments:RequestArguments, headers:RequestHeaders, operation:Operation, target:str, content:dict=None) -> Result:

		# Get initialized resource
		if (nres := REQ.createRequestResource(arguments, headers, operation, target, content)).resource is None:
			return Result(rsc=RC.badRequest, dbg=nres.dbg)

		# Register <request>
		if (cseres := Utils.getCSE()).resource is None:
			return Result(rsc=RC.badRequest, dbg=cseres.dbg)
		if (rres := CSE.registration.checkResourceCreation(nres.resource, headers.originator, cseres.resource)).rsc != RC.OK:
			return rres.errorResult()

		# create <request>
		return CSE.dispatcher.createResource(nres.resource, cseres.resource, headers.originator)


	def _handleNonBlockingRequest(self, id:str, args:RequestArguments, requestHeaders:RequestHeaders ) -> Result:
		"""	This method creates a <request> resource, initiates the execution of the desired operation in
			the background, but immediately returns with the reference of the <request> resource that
			will contain the result of the operation.
		"""

		# Create the <request> resource first
		if (reqres := self._createRequestResource(args, requestHeaders, args.operation, id)).resource is None:
			return reqres

		# Run operation in the background
		BackgroundWorkerPool.newActor(0.0, self._runNonBlockingRequestSync, 'request_%s' % requestHeaders.requestIdentifier).start(id=id, args=args, requestHeaders=requestHeaders, reqRi=reqres.resource.ri)

		if args.rt == ResponseType.nonBlockingRequestSynch:
			# Create the response content with the <request> ri 
			jsn:Dict[str, Any] = { 'm2m:uri' : reqres.resource.ri }
			return Result(jsn=jsn, rsc=RC.accepedNonBlockingRequestSynch)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % args.rt)


	def _runNonBlockingRequestSync(self, id:str, args:RequestArguments, requestHeaders:RequestHeaders, reqRi:str) -> bool:
		""" Execute the actual request and store the result in the respective <request> resource.
		"""

		args.operation == Operation.RETRIEVE and (result := CSE.dispatcher.processRetrieveRequest(args, id, requestHeaders.originator)) is not None
		args.operation == Operation.CREATE and (result := CSE.dispatcher.processCreateRequest(args, id, requestHeaders.originator, requestHeaders.contentType, requestHeaders.resourceType)) is not None

		# Retrieve the <request>
		if (reqres := CSE.dispatcher.retrieveResource(reqRi)).resource is None:	
			return True 														# No idea what we should do if this fails
		request = reqres.resource

		# Fill the <request>
		request['ors'] = {	# operationResult
			'rsc'	: result.rsc,
			'rid'	: request.rid,
			'to'	: id,
			'fr'	: request.originator,
			'ot'	: request['mi/ot'],
			'rset'	: request.et
		}
		if result.rsc == RC.OK:			# OK -> resource
			request['rs'] = RequestStatus.COMPLETED
			request['ors/pc'] = result.resource.asJSON()
		else:							# Error
			request['rs'] = RequestStatus.FAILED
			if result.dbg is not None:
				request['ors/pc'] = { 'm2m:dbg' : result.dbg }
		request.dbUpdate()

		return True

