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
from resources.REQ import REQ
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool


import CSE, Utils
from flask import Request
from typing import Any, List, Tuple, Union, Dict



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
	#	Retrieve Request
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
			return fanoutPointResource.handleRetrieveRequest(request, srn, requestHeaders.originator, requestHeaders)

		# just a normal retrieve request
		return self.handleRetrieveRequest(request, id if id is not None else srn, requestHeaders.originator, requestHeaders)



	def handleRetrieveRequest(self, request:Request, id:str, originator:str, requestHeaders:RequestHeaders=None) -> Result:
		Logging.logDebug('Handle retrieve resource: %s' % id)

		try:
			attrs, msg, args = Utils.getRequestArguments(request, Operation.RETRIEVE)
			if args is None:
				return Result(rsc=RC.badRequest, dbg=msg)
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg='invalid arguments (%s)' % str(e))

		# if async: create request resource and proceed in a thread, also: return with REQ.ri
		# otherwise proceed normally

		if args.rt == ResponseType.blockingRequest:
			return CSE.dispatcher.processRetrieveRequest(args, id, originator)
		elif args.rt == ResponseType.nonBlockingRequestSynch:
			return self.handleNonBlockingRequestSyncRetrieve(args, id, requestHeaders)


		# TODO other nonBlocking 
		# elif args.rt == ResponseType.nonBlockingRequestAsynch:
		# 	self._createRequestResource(args, requestHeaders, Operation.RETRIEVE, id)

		return Result(rsc=RC.badRequest, dbg='Unknown or unsupported ResponseType: %d' % args.rt)



	def handleNonBlockingRequestSyncRetrieve(self, args:RequestArguments, id:str, requestHeaders:RequestHeaders ) -> Result:
		# Create the <request> resource first
		if (reqres := self._createRequestResource(args, requestHeaders, Operation.RETRIEVE, id)).resource is None:
			return reqres

		# Run RETRIEVE in the background
		BackgroundWorkerPool.newActor(0.0, self._runNBRSyncRetrieve, 'retrieve').start(args=args, id=id, originator=requestHeaders.originator, reqRi=reqres.resource.ri)

		# Create the response content with the <request> ri 
		jsn:Dict[str, Any] = { 'm2m:rid' : reqres.resource.ri }
		return Result(jsn=jsn, rsc=RC.accepedNonBlockingRequestSynch)


	def _runNBRSyncRetrieve(self, args:RequestArguments, id:str, originator:str, reqRi:str) -> bool:
		# Run the actual request
		result = CSE.dispatcher.processRetrieveRequest(args, id, originator)

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



