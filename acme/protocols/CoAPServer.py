#
#	CoapServer.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" CoAP Server binding to the ACME CSE. """

from __future__ import annotations
from typing import Optional, Any, cast
import os, logging, urllib, socket
import isodate

from ..etc.ResponseStatusCodes import ResponseException
from ..etc.ResponseStatusCodes import BAD_REQUEST, REQUEST_TIMEOUT, REQUEST_TIMEOUT, TARGET_NOT_REACHABLE, INTERNAL_SERVER_ERROR, NO_CONTENT

from ..etc.Types import Operation, Result, CSERequest, JSON, ContentSerializationType, ResponseType
from ..etc.Types import ResponseType, ResultContentType, DesiredIdentifierResultType, RequestType
from ..etc.Utils import renameThread
from ..etc.DateUtils import getResourceDate, timeUntilAbsRelTimestamp
from ..etc.IDUtils import uniqueRI
from ..etc.RequestUtils import fromHttpURL, requestFromResult, serializeData, createRequestResultFromURI, fillRequestWithArguments
from ..etc.RequestUtils import toCoAPPath, contentAsString, createPositiveResponseResult, deserializeData
from ..etc.ResponseStatusCodes import ResponseStatusCode
from ..helpers.TextTools import toHex
from ..helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from ..helpers.TextTools import findXPath
from ..helpers.MultiDict import MultiDict
from ..helpers.CoAPthonTools import registerOneM2MContentTypes, registerOneM2MOptions, newCoAPOption, operationsMethodsMap
from ..helpers.ACMELRUCache import ACMELRUCache
from ..runtime.Configuration import Configuration
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..etc.Constants import RuntimeConstants as RC

from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.server.coap import CoAP
from coapthon.layers.requestlayer import RequestLayer as CoapthonRequestLayer
from coapthon.messages.request import Request as CoaptthonRequest
from coapthon.messages.response import Response as CoapthonResponse
from coapthon.messages.option import Option as CoapthonOption

from coapthon.transaction import Transaction as CoapthonTransaction

# TODO  support DTLS sockets
# TODO Add R5 support (FETCH requests)
# TODO log requests for error cases. Perhaps non necessary here


class ACMECoAPHandler(object):
	"""	ACME CoAP request handler.
	"""

	__slots__ = (
		'coapServer',

		'_eventCoAPRetrieve',
		'_eventCoAPCreate',
		'_eventCoAPNotify',
		'_eventCoAPUpdate',
		'_eventCoAPDelete',
	)
	"""	Slots of the ACME CoAP Handler. """


	def __init__(self, coapServer:ACMECoAPServer = None) -> None:
		"""	Initialization of the ACME CoAP Resource.
		
			Args:
				coapServer: The CoAP server object.
		"""

		# Optimize event handling
		self._eventCoAPRetrieve =  CSE.event.coapRetrieve			# type: ignore [attr-defined]
		"""	Event to trigger when a CoAP retrieve request is received. """
		self._eventCoAPCreate = CSE.event.coapCreate				# type: ignore [attr-defined]
		"""	Event to trigger when a CoAP create request is received. """
		self._eventCoAPNotify =  CSE.event.coapNotify				# type: ignore [attr-defined]
		"""	Event to trigger when a CoAP notify request is received. """
		self._eventCoAPUpdate = CSE.event.coapUpdate				# type: ignore [attr-defined]
		"""	Event to trigger when a CoAP update request is received. """
		self._eventCoAPDelete = CSE.event.coapDelete				# type: ignore [attr-defined]
		"""	Event to trigger when a CoAP delete request is received. """


	def handleGET(self, request:CoaptthonRequest, response:CoapthonResponse, options:MultiDict) -> None:
		"""	Handle a GET request.

			Args:
				request: The CoAP request.
				response: The CoAP response.
				options: The options of the request.
		"""
		L.enableScreenLogging and renameThread('CO_R')
		L.isDebug and L.logDebug('CoAP GET request received')
		self._eventCoAPRetrieve()
		self._handleRequest(request, response, Operation.RETRIEVE, options = options)


	def handleFETCH(self, request:CoaptthonRequest, response:CoapthonResponse, options:MultiDict) -> None:
		"""	Handle a FETCH request.

			Args:
				request: The CoAP request.
				response: The CoAP response.
				options: The options of the request.
		"""
		L.enableScreenLogging and renameThread('CO_R')
		L.isDebug and L.logDebug('CoAP FETCH request received')
		# TODO handle FETCH requests differently. For R5
		self._eventCoAPRetrieve()
		self._handleRequest(request, response, Operation.RETRIEVE)


	def handlePOST(self, request:CoaptthonRequest, response:CoapthonResponse, options:MultiDict) -> None:
		"""	Handle a POST request.

			Args:
				request: The CoAP request.
				response: The CoAP response.
				options: The options of the request.
		"""
		# We need to distinguish between CREATE and NOTIFY requests already here
		if defines.OptionRegistry.oneM2M_TY.number in options:	# type:ignore[attr-defined]
			L.enableScreenLogging and renameThread('CO_C')
			L.isDebug and L.logDebug('CoAP POST request received')
			self._eventCoAPCreate()
			self._handleRequest(request, response, Operation.CREATE, options)
		else:
			L.enableScreenLogging and renameThread('CO_N')
			L.isDebug and L.logDebug('CoAP POST/NOTIFY request received')
			self._eventCoAPCreate()
			self._handleRequest(request, response, Operation.NOTIFY, options)


	def handlePUT(self, request:CoaptthonRequest, response:CoapthonResponse, options:MultiDict) -> None:
		"""	Handle a PUT request.

			Args:
				request: The CoAP request.
				response: The CoAP response.
				options: The options of the request.
		"""
		L.enableScreenLogging and renameThread('CO_U')
		L.isDebug and L.logDebug('CoAP PUT request received')
		self._eventCoAPUpdate()
		self._handleRequest(request, response, Operation.UPDATE, options = options)


	def handleDELETE(self, request:CoaptthonRequest, response:CoapthonResponse, options:MultiDict) -> None:
		"""	Handle a DELETE request.

			Args:
				request: The CoAP request.
				response: The CoAP response.
				options: The options of the request.
		"""
		L.enableScreenLogging and renameThread('CO_D')
		L.isDebug and L.logDebug('CoAP DELETE request received')
		self._eventCoAPDelete()
		self._handleRequest(request, response, Operation.DELETE, options = options)


	def _handleRequest(self, request:CoaptthonRequest, response:CoapthonResponse, operation:Operation, options:Optional[MultiDict] = None) -> CoapthonResponse:
		"""	Handle a CoAP request.

			Args:
				request: The CoAP request.
				response: The CoAP response.
				operation: The operation of the request.
				options: The options of the request.

			Returns:
				The CoAP response.
		"""
		L.isDebug and L.logDebug(f'==> COAP Request: {request.uri_path}') 	# path = request.path  w/o the root
		L.isDebug and L.logDebug(f'Operation: {operation.name}')
		L.isDebug and L.logDebug(f'Source: {request.source}')
		L.isDebug and L.logDebug(f'Options: {optionsToDict(request.options)}')
		if request.payload:
			L.isDebug and L.logDebug(f'Payload: {request.payload!r}')	# TODO print hex payload

		# TODO log request

		# Dissect the request
		try:
			dissectResult = self._dissectRequest(request, operation, options)
		except ResponseException as e:
			return self._prepareResponse(Result(rsc = e.rsc, 
									   	 request = e.data, 
										 dbg = e.dbg), 
										response)
		
		# Send and error message when the CSE is shutting down, or the coap server is stopped
		if CSE.coapServer.isPaused:
			# Return an error if the server is stopped
			return self._prepareResponse(Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
												request = dissectResult.request, 
												dbg = 'CoAP server not running'),
										 response)

		# Handle the request. Returns a Result object. 
		responseResult = CSE.request.handleRequest(dissectResult.request)

		if dissectResult.request.rt == ResponseType.noResponse:
			raise NO_CONTENT()

		# Prepare the response and return it
		try:
			return self._prepareResponse(responseResult, response, originalRequest = dissectResult.request)
		except ResponseException as e:
			return self._prepareResponse(Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
												request = dissectResult.request, 
												dbg = e.dbg),
										response)
	

	def _dissectRequest(self, request:CoaptthonRequest, operation:Operation, options:Optional[MultiDict] = None) -> Result:
		"""	Dissect a CoAP request.

			Args:
				request: The CoAP request.
				operation: The operation of the request.
				options: The options of the request.

			Returns:
				The result of the dissection. Contains a CSERequest object.

			Raises:
				ResponseException: If the request is invalid.
		"""
		req:JSON = {}
		cseRequest = CSERequest()

		# Small optimization to avoid constant iteration through the options array of the request
		if options is None:
			options = dissectOptions(request.options)
		
		#
		#	Process options
		#

		# Assign the operation
		req['op'] = operation

		# URI to oneM2M resource ID. Replace special oneM2M tokens
		req['to'] = fromHttpURL(request.uri_path)

		# assign the transmitted options
		for option in options.keys():
			match option:

				# Get and translate content encoding
				case defines.OptionRegistry.CONTENT_TYPE.number:
					cseRequest.ct = ContentSerializationType.fromCoAP(options.getOne(option))
					if cseRequest.ct == ContentSerializationType.UNKNOWN:
						cseRequest.ct = RC.defaultSerialization

				# media type of the response. The default is the content type of the request
				case defines.OptionRegistry.ACCEPT.number:
					cseRequest.coapAccept = ContentSerializationType.fromCoAP(options.getOne(option))	

				# From / Originator
				case defines.OptionRegistry.oneM2M_FR.number:	# type:ignore[attr-defined]
					req['fr'] = options.getOne(option)
				
				# Ignore uri_path
				case defines.OptionRegistry.URI_PATH.number:
					pass
			
				# type
				case defines.OptionRegistry.oneM2M_TY.number:	# type:ignore[attr-defined]
					req['ty'] = options.getOne(option)

				# rqi
				case defines.OptionRegistry.oneM2M_RQI.number:	# type:ignore[attr-defined]
					req['rqi'] = options.getOne(option)

				# rvi
				case defines.OptionRegistry.oneM2M_RVI.number:	# type:ignore[attr-defined]
					req['rvi'] = options.getOne(option)
		
				# rqet
				case defines.OptionRegistry.oneM2M_RQET.number:	# type:ignore[attr-defined]
					req['rqet'] = options.getOne(option)
		
				# rset
				case defines.OptionRegistry.oneM2M_RSET.number:	# type:ignore[attr-defined]
					req['rset'] = options.getOne(option)

				# oet
				case defines.OptionRegistry.oneM2M_OET.number:	# type:ignore[attr-defined]
					req['oet'] = options.getOne(option)

				# vsi
				case defines.OptionRegistry.oneM2M_VSI.number:	# type:ignore[attr-defined]
					req['vsi'] = options.getOne(option)

				# ot
				case defines.OptionRegistry.oneM2M_OT.number:	# type:ignore[attr-defined]
					req['ot'] = options.getOne(option)

				# rtu / RTURI
				case defines.OptionRegistry.oneM2M_RTURI.number:	# type:ignore[attr-defined]
					rtu = options.getOne(option)
					rt = dict()
					rt['nu'] = rtu.split('&')		
					req['rt'] = rt					# req.rt.rtu. This might be overwritten later

		#
		# Post processing of option assignments
		#

		# Fill the coapAccept with the ct if it is not set
		if cseRequest.coapAccept is None or cseRequest.coapAccept == ContentSerializationType.UNKNOWN:
			cseRequest.coapAccept = cseRequest.ct

		# Copy the payload to the originalData
		cseRequest.originalData = request.payload

		# Extract the query arguments. Multiple arguments or values separated by '+'
		# are stored in a list
		args = MultiDict()
		for q in options.get(defines.OptionRegistry.URI_QUERY.number, []):
			_p = q.split('=')
			if len(_p) == 2:
				# It could be that the value is a list of values separated by '+'.
				# In this case we need to split it and add it as a list.
				# If there is no '+' in the value, it is a single value but after the split still 
				# contained in a list.
				qs = urllib.parse.unquote(_p[1])
				args[_p[0]] = qs

		# Extract the request arguments and copy them into the request, including the PC
		fillRequestWithArguments(args, req, cseRequest, sep = '+')

		# do validation and copying of attributes of the whole request
		try:
			CSE.request.fillAndValidateCSERequest(cseRequest)
		except REQUEST_TIMEOUT as e:
			raise e
		except ResponseException as e:
			e.dbg = f'invalid arguments/attributes: {e.dbg}'
			raise e

		# Finally, return the dissected request
		return Result(request = cseRequest)


	def _prepareResponse(self, result:Result, 
					  		   response:CoapthonResponse,
							   originalRequest:Optional[CSERequest] = None) -> CoapthonResponse:
		"""	Prepare a CoAP response.
		
			Args:
				result: The result of the request.
				response: The CoAP response.
				originalRequest: The original request.

			Returns:
				The prepared CoAP response.
		"""
		content:str|bytes|JSON = ''
		if not result.request:
			result.request = CSERequest()
		
		#  Copy a couple of attributes from the originalRequest to the new request
		result.request.ct = RC.defaultSerialization	# default serialization
		if originalRequest:

			# Determine contentType for the response. Check the 'accept' header first, then take the
			# original request's contentType. If this is not possible, the fallback is still the
			# CSE's default
			result.request.originator = originalRequest.originator
			if originalRequest.coapAccept:																# accept / contentType
				result.request.ct = originalRequest.coapAccept
			elif csz := CSE.request.getSerializationFromOriginator(originalRequest.originator):
				result.request.ct = csz[0]

			result.request.rqi = originalRequest.rqi
			result.request.rvi = originalRequest.rvi
			result.request.vsi = originalRequest.vsi
			result.request.ec  = originalRequest.ec
			result.request.rset = originalRequest.rset
		
		#	Transform request to oneM2M request
		outResult = requestFromResult(result, isResponse = True, originalRequest = originalRequest)

		#
		# 	Transform oneM2M request to CoAP message
		#

		# Build the options
		if result.rsc:
			response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RSC.number, f'{int(result.rsc)}'))	# type:ignore[attr-defined]
		if rqi := findXPath(cast(JSON, outResult.data), 'rqi'):
			response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RQI.number, rqi))					# type:ignore[attr-defined]
		else:
			response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RQI.number, result.request.rqi))	# type:ignore[attr-defined]
		if rvi := findXPath(cast(JSON, outResult.data), 'rvi'):
			response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RVI.number, rvi))					# type:ignore[attr-defined]
		if vsi := findXPath(cast(JSON, outResult.data), 'vsi'):
			response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_VSI.number, vsi))					# type:ignore[attr-defined]
		if rset := findXPath(cast(JSON, outResult.data), 'rset'):
			response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RSET.number, rset))					# type:ignore[attr-defined]
		response.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_OT.number, getResourceDate()))			# type:ignore[attr-defined]

		# CoAP status code
		response.code = result.rsc.coapStatusCode().number
		
		# Assign and encode content accordingly
		response.add_option(newCoAPOption(defines.OptionRegistry.CONTENT_TYPE.number, result.request.ct.toCoAPContentType()))

		# From hereon, data is a string or byte string
		origData:JSON = cast(JSON, outResult.data)
		# outResult.data = serializeData(cast(JSON, outResult.data)['pc'], result.request.ct) if 'pc' in cast(JSON, outResult.data) else ''
		match result.request.ct:
			case ContentSerializationType.JSON:
				outResult.data = response.payload = bytes(cast(str, serializeData(origData['pc'], ContentSerializationType.JSON)) if 'pc' in origData else '', 'utf-8')
			case ContentSerializationType.CBOR:
				outResult.data = response.payload = cast(bytes, serializeData(origData['pc'], ContentSerializationType.CBOR) if 'pc' in origData else b'')
			case ContentSerializationType.XML:
				L.logErr('XML serialization not supported')
				raise INTERNAL_SERVER_ERROR('XML serialization not supported')
			case ContentSerializationType.PLAIN:
				outResult.data = response.payload = cast(bytes, origData['pc'] if 'pc' in origData else b'')
		
		#
		#	Add Location-Path header, if this is a response to a CREATE operation, and uri is present
		#
		try:
			if originalRequest and originalRequest.op == Operation.CREATE:
				if  (uri := findXPath(origData, 'pc/m2m:uri')) is not None or \
					(uri := findXPath(origData, 'pc/m2m:rce/uri')):
						response.add_option(newCoAPOption(defines.OptionRegistry.LOCATION_PATH.number, uri))
		except Exception as e:
			raise INTERNAL_SERVER_ERROR(f'Error while processing the response: {L.logErr(str(e))}')

		# Log the response
		# if isinstance(outResult.data, (bytes)):
		if result.request.ct == ContentSerializationType.CBOR:
			L.isDebug and L.logDebug(f'<== CoAP Response ({result.rsc}):\nOptions: {optionsToDict(response.options)}\nBody: \n{toHex(cast(bytes, outResult.data))}\n=>\n{str(result.toData())}')
		elif 'pc' in origData:
			L.isDebug and L.logDebug(f'<== CoAP Response ({result.rsc}):\nOptions: {optionsToDict(response.options)}\nBody: {origData["pc"]}')	# might be different serialization
		else:
			L.isDebug and L.logDebug(f'<== CoAP Response ({result.rsc}):\nOptions: {optionsToDict(response.options)}')

		# Return the response
		return response



class ACMECoAPRequestLayer(CoapthonRequestLayer):
	"""	Implementation of an own request layer handler for the coapthon CoAP framework.

		This implementation replaces the `receive_request` method of the RequestLayer class to handle the requests
		according to the ACME CSE requirements. It doesn't call a resource layer to handle the requests, but an internal
		handler.
	"""

	def __init__(self, server:CoAP, handler:ACMECoAPHandler):
		"""	Initialize the request layer.

			Args:
				server: The CoAP server instance.
				handler: A handler class to handle the requests.
		"""
		super(ACMECoAPRequestLayer, self).__init__(server)
		self._handlers = {
			defines.Codes.GET.number: handler.handleGET,
			defines.Codes.FETCH.number: handler.handleFETCH,
			defines.Codes.POST.number: handler.handlePOST,
			defines.Codes.PUT.number: handler.handlePUT,
			defines.Codes.DELETE.number: handler.handleDELETE,
		}
		"""	The handlers for the different CoAP operations. """


	def receive_request(self, transaction:CoapthonTransaction) -> CoapthonTransaction:
		"""	Handle a CoAP request.

			This method overrides the `receive_request` method of the CoapthonRequestLayer class to handle the requests.
		
			Args:
				transaction: The CoAP transaction.

			Returns:
				The transaction.
		"""

		if transaction.request.block2:
			transaction.response = CoapthonResponse()
			transaction.response.destination = transaction.request.source
			transaction.response.token = transaction.request.token
			return transaction

		# Prevent the server from handling blockwise requests
		options = dissectOptions(transaction.request.options)

		# prepare the response		
		transaction.response = CoapthonResponse()
		transaction.response.destination = transaction.request.source
		transaction.response.token = transaction.request.token

		# handle the request
		if (_handler := self._handlers.get(transaction.request.code)):
			try:
				# transaction.response = _handler(transaction.request, transaction.response, options)
				_handler(transaction.request, transaction.response, options)
			except NO_CONTENT:
				transaction.response = None
		else:
			transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number

		return transaction


class ACMECoAPServer(CoAP):
	"""	ACME CoAP Server. 
		
		It is used to setup the CoAPthon library to handle CoAP requests according to the ACME CSE requirements.
		It also provides functionality to send CoAP requests to other CoAP servers.	
	"""

	__slots__ = (
		'clientCache',
		'_requestHandler',
		'_requestLayer',
		'_eventResponseReceived',
	)
	"""	Slots of the ACME CoAP Server. """

	class CoapLoggingHandler(logging.StreamHandler):
		"""	A logging handler for redirecting the CoAPthon logging to the ACME logging.
		"""

		def emit(self, record: logging.LogRecord) -> None:
			"""	Emit a log record.

				Args:
					record: The log record.
			"""
			if L.enableBindingsLogging:
				L._log(record.levelno, record.msg, 5)


	def __init__(self, host:str, port:int) -> None:
		"""	Initialize the ACME CoAP Server.

			Args:
				host: The host to bind the CoAP server to.
				port: The port to bind the CoAP server to.
		"""

		CoAP.__init__(self, (host, port), cb_ignore_listen_exception = self._handleListenException)

		# Register the oneM2M options, codes etc first
		registerOneM2MOptions()
		registerOneM2MContentTypes()

		self._requestHandler = ACMECoAPHandler(self)
		"""	The request handler to handle requests. """

		# Normally, the coapthon server is initialized with one ore more resources to handle 
		# requests. Here, we are providing our own request layer to handle all the requests and responses.
		self._requestLayer = ACMECoAPRequestLayer(self, self._requestHandler)
		"""	The request layer to handle requests instead of resources. """

		# Install a LRU cache for outgoing client connections
		self.clientCache:ACMELRUCache = ACMELRUCache(maxsize = Configuration.coap_clientConnectionCacheSize, 
											   		 evict = lambda _, val: val.close() if val else None)
		"""	A cache for outgoing client connections. """

		self._eventResponseReceived = CSE.event.responseReceived	# type: ignore [attr-defined]
		"""	The event to trigger when a response is received. """

		# Redirect the CoAPthon logging to the ACME logging
		_logger = logging.getLogger('coapthon')
		if not L.enableBindingsLogging:
			_logger.propagate = False	# Disable logging to the console
			_logger.addHandler(logging.NullHandler())
		else:
			_logger.addHandler(ACMECoAPServer.CoapLoggingHandler())
			_logger.setLevel(L.logLevel)


	def run(self) -> None:
		"""	Run the CoAP Server.
		"""
		self.listen(1)	# run the server, 1 second internal check interval for other events

	
	def stop(self) -> None:
		"""	Stop the CoAP Server.
		"""
		L.isDebug and L.logDebug('Closing all client connections')
		while self.clientCache.currsize > 0:
			_, client = self.clientCache.popitem()
			cast(HelperClient, client).close()
		self.close()


	def _handleListenException(self, e:Exception, coapServer:CoAP) -> bool:
		"""	Handle a listen exception.

			Args:
				e: The exception.
				coapServer: The CoAP server.

			Returns:
				*True* if the exception was handled, *False* otherwise.
		"""
		L.isWarn and L.logWarn(f'CoAP server listen exception: {str(e)}')
		return True


	def sendRequest(self, request:CSERequest, url:str, ignoreResponse:bool = False) -> Result:
		"""	Send a CoAP request to a URL.

			Args:
				request: The request to send.
				url: The URL to send the request to.
				ignoreResponse: Flag whether to ignore the response.

			Returns:
				The result of the request.

		"""
		client:HelperClient = None

		def _closeClient() -> None:
			"""	Close the client connection.
			"""
			if client and Configuration.coap_clientConnectionCacheSize == 0:
				client.close()

		# Check if the CoAP server is running, otherwise return an errors
		if CSE.coapServer.isPaused:
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
						  dbg = 'CoAP client is not running')


		# Parse url and create a first request object
		res, url, urlParsed = createRequestResultFromURI(request, url)
		req = res.request

		# Request timeout
		timeout:float = None

		# Re-use or create a CoAP client
		destination = (urlParsed.hostname, urlParsed.port)
		if (client := self.clientCache.get(destination)) is None or Configuration.coap_clientConnectionCacheSize == 0:
			# Create DTLS socket if security is required
			sock:socket.socket = None
			if urlParsed.scheme == 'coaps':
				return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR,
							  dbg = 'CoAP security is not yet supported')
				# if not Configuration.coap_security_useDTLS:
				# 	return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
				# 				  dbg = 'CoAP security is not enabled')
				# # Create a DTLS socket

				# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				# sock = wrap_client(sock, cert_reqs = ssl.CERT_REQUIRED, 
		       	# 						 keyfile = Configuration.coap_security_caPrivateKeyFile,
				# 						 certfile = Configuration.coap_security_caCertificateFile,
				# 						 # TODO support ca certs ca_certs = ....caCertificateFile
				# 						 do_handshake_on_connect = True, 
				# 						 ssl_version = Configuration.coap_security_dtlsVersion)
				# 						#  ssl_version = CSE.security.getSSLContextCoAP())

			# Create a new client
			client = HelperClient(server=(urlParsed.hostname, urlParsed.port), sock = sock)
			if Configuration.coap_clientConnectionCacheSize > 0:
				self.clientCache[destination] = client
			L.isDebug and L.logDebug('Creating new CoAP client')
		else:
			L.isDebug and L.logDebug('Re-using CoAP client')


		# This try..catch is mainly to catch exceptions and possibly close the client connection in case of
		# an error.
		try:

			#
			#	Prepare the CoAP request
			#

			# create a CoAP request object. destination is filled, token is generated during the request call
			coapRequest = CoaptthonRequest(client)

			# Operation
			coapRequest.code = operationsMethodsMap[req.op]

			# resource id target
			coapRequest.uri_path = toCoAPPath(req.to)
			# Content-type
			ct = request.ct if request.ct else RC.defaultSerialization
			coapRequest.add_option(newCoAPOption(defines.OptionRegistry.CONTENT_TYPE.number, ct.toCoAPContentType()))
			# Resource type
			if request.ty:
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_TY.number, request.ty.value))	# type:ignore[attr-defined]
			# Originator
			coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_FR.number, request.originator))		# type:ignore[attr-defined]
			# Request Identifier
			if not request.rqi:
				request.rqi = uniqueRI()
			coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RQI.number, request.rqi))			# type:ignore[attr-defined]
			# Release version
			if request.rvi != '1':
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RVI.number, request.rvi if request.rvi is not None else RC.releaseVersion))		# type:ignore[attr-defined]
			# Originating Timestamp
			coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_OT.number, request.ot if request.ot else getResourceDate()))			# type:ignore[attr-defined]
			# Event Category
			if request.ec:
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_EC.number, request.ec.value))	# type:ignore[attr-defined]
			# Request Expiration Timestamp. Also sets the timeout
			if request.rqet:
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RQET.number, request.rqet))		# type:ignore[attr-defined]
				timeout = timeUntilAbsRelTimestamp(request.rqet)
			# Result Expiration Timestamp
			if request.rset:
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RSET.number, request.rset))		# type:ignore[attr-defined]
			# Operation Execution Time
			if request.oet:
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_OET.number, request.oet))		# type:ignore[attr-defined]
			# Blocking Request URI
			if request.rt and request.rt != ResponseType.blockingRequest:
				if (nu := request.originalRequest.get('nu')):
					coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_RTURI.number, '&'.join(nu)))	# type:ignore[attr-defined]
			# VSI
			if request.vsi:
				coapRequest.add_option(newCoAPOption(defines.OptionRegistry.oneM2M_VSI.number, request.vsi))		# type:ignore[attr-defined]

			queryArguments = []
			# result content type
			if request.rcn and request.rcn != ResultContentType.default(request.op):
				queryArguments.append(f'rcn={request.rcn.value}')
			# desired identifier result type
			if request.drt and request.drt != DesiredIdentifierResultType.structured:
				queryArguments.append(f'drt={request.drt.value}')
			# Add filterCriteria arguments
			if fc := request.fc:
				fc.mapAttributes(lambda k, v: queryArguments.append(f'{k}={v}'), True)
			# Add further non-filterCriteria arguments
			if request.sqi:
				queryArguments.append(f'sqi={request.sqi}')
			# Add attributeList
			if (atrl := findXPath(request.pc, 'm2m:atrl')) is not None:
				queryArguments.append(f'atrl={"+".join(atrl)}')

			# Add query arguments to the request
			if queryArguments:
				coapRequest.uri_query = '&'.join(queryArguments)
				# TODO patch Coapthon Request . uri_query setter to accept list of values as well

			# Get request timeout
			timeout = Configuration.coap_timeout if timeout is None else timeout

			#
			#	Payload
			#

			# Add payload
			content = request.pc if request.pc else None

			# serialize data (only if dictionary, pass on non-dict data)
			data:Optional[bytes] = None
			# TODO support FETCH requests for R5
			if request.op in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ]:
				data = cast(bytes, serializeData(content, ct))
			# elif content and not raw:
			elif content:
				raise INTERNAL_SERVER_ERROR(L.logErr(f'Operation: {request.op.name} doesn\'t allow content'))
			coapRequest.payload = data

			# Send the 
			try:
				L.isDebug and L.logDebug(f'Sending request: {request.op} {url}{coapRequest.uri_path}')
				if ct == ContentSerializationType.CBOR:
					L.isDebug and L.logDebug(f'CoAP Request ==>{url}{coapRequest.uri_path}:\nOperation: {request.op}\nOptions: {coapRequest.options}\nPayload: \n{contentAsString(data, ct)}\n=>\n{str(data) if data else ""}')
				else:
					L.isDebug and L.logDebug(f'CoAP Request ==>:\nOperation: {request.op}\nOptions: {coapRequest.options}\nPayload: \n{contentAsString(data, ct)}')
				
				# Send the request
				coapResponse = client.send_request(coapRequest, timeout = timeout)
				if coapResponse is None:
					raise REQUEST_TIMEOUT(L.logWarn(f'CoAP request timeout after {timeout}s'))

				# Dissect the response's options
				options = dissectOptions(coapResponse.options)

				# Construct CSERequest response object from the result
				resp = CSERequest(requestType = RequestType.RESPONSE)

				rsc:ResponseStatusCode = None
				for number, option in options.items():
					match number:

						# content type
						case defines.OptionRegistry.CONTENT_TYPE.number:
							resp.ct = ContentSerializationType.fromCoAP(options.getOne(number))
							if resp.ct == ContentSerializationType.UNKNOWN:
								resp.ct = RC.defaultSerialization

						# response status code
						case defines.OptionRegistry.oneM2M_RSC.number:		# type:ignore[attr-defined]
							rsc = options.getOne(number)
							resp.rsc = ResponseStatusCode(int(options.getOne(number)))

						# originator
						case defines.OptionRegistry.oneM2M_FR.number:		# type:ignore[attr-defined]
							resp.originator = options.getOne(number)
						
						# request identifier
						case defines.OptionRegistry.oneM2M_RQI.number:		# type:ignore[attr-defined]
							rqi = options.getOne(number)
							if rqi != request.rqi:
								raise BAD_REQUEST(L.logWarn(f'Received wrong or missing request identifier: {rqi}'))
							resp.rqi = rqi

						# originator timestamp
						case defines.OptionRegistry.oneM2M_OT.number:		# type:ignore[attr-defined]
							ot = options.getOne(number)
							try:
								isodate.parse_datetime(ot) # Check if valid ISO 8601 date, may raise exception
								resp.ot = ot
							except Exception as ee:
								raise BAD_REQUEST(L.logWarn(f'Received wrong format for X-M2M-OT: {ot} - {str(ee)}'))

				# some further checks			
				if resp.rsc is None:
					raise BAD_REQUEST(L.logWarn(f'Received wrong or missing response status code: {resp.rsc}'))

				# Get payload
				resp.pc = deserializeData(coapResponse.payload, resp.ct) if coapResponse.payload is not None else None

				L.isDebug and L.logDebug(f'CoAP Response <== ({str(resp.rsc)}):\nOptions: {str(coapResponse.options)}\nPayload: \n{contentAsString(coapResponse.payload, resp.ct)}\n')

			except ResponseException as e:
				raise e
			except socket.timeout as e:
				raise REQUEST_TIMEOUT(L.logWarn(f'CoAP request timeout after {timeout}s'))
			except Exception as e:
				L.logWarn(f'Failed to send request: {str(e)}')
				raise TARGET_NOT_REACHABLE('target not reachable')

			if ignoreResponse and request.op == Operation.NOTIFY:
				L.isDebug and L.logDebug('HTTP: Ignoring response to notification')
				return createPositiveResponseResult()


			res = Result(rsc = resp.rsc, data = resp.pc, request = resp)
			self._eventResponseReceived(resp)
			return res
	
		# Catch exceptions and close the client connection
		except Exception as e:
			_closeClient()
			raise e
		finally:
			_closeClient()


class CoAPServer(object):
	"""	CoAPServer Server implementation.
	"""

	__slots__ = [ 
		'isPaused', 
		'coapServer', 
		'operationEvents',
		'actor'
	]
	""" Define slots for instance variables. """


	def __init__(self) -> None:
		"""	Initialization of the CoAP Server.
		"""

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self._configUpdate)			# type: ignore

		self.isPaused = False
		"""	Flag whether the server is currently paused. Requests are not handled when the server is paused. """

		self.coapServer:Optional[ACMECoAPServer] = None
		"""	The CoAP server object. """

		self.operationEvents = {
			Operation.CREATE:		[CSE.event.coapCreate, 'CO_C'],		# type: ignore [attr-defined]
			Operation.RETRIEVE: 	[CSE.event.coapRetrieve, 'CO_R'],	# type: ignore [attr-defined]
			Operation.UPDATE:		[CSE.event.coapUpdate, 'CI_U'],		# type: ignore [attr-defined]
			Operation.DELETE:		[CSE.event.coapDelete, 'CI_D'],		# type: ignore [attr-defined]
			Operation.NOTIFY:		[CSE.event.coapNotify, 'CO_M'],		# type: ignore [attr-defined]
			Operation.DISCOVERY:	[CSE.event.coapRetrieve, 'CO_F'],	# type: ignore [attr-defined]
		}
		"""	Events for the different operations. """

		self.actor:Optional[BackgroundWorker] = None
		"""	The actor for running the synchronous CoAP server in the background. """

		L.isInfo and L.log('CoAP server initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the CoAP server.

			Returns:
				True if the server has been shut down successfully.
		"""
		L.isInfo and L.log('CoAP server shut down')
		self._stop()
		return True


	def _configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the *configUpdate* event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'coap.enable', 
						'coap.port',
						'coap.listenIF',
					  ]:
			return

		# Restart the server if the configuration has changed
		self.shutdown()
		self.run()		# Restart the server


	def run(self) -> bool:
		"""	Initialize and run the CoAP server as a BackgroundWorker/Actor.

			Returns:
				True if the server has been started successfully.
		"""
		if not Configuration.coap_enable:	# type:ignore[attr-defined]
			L.isInfo and L.log('CoAP: server NOT enabled')
			return True
		
		# Actually start the actor to run the WebSocket Server as a thread
		self.actor = BackgroundWorkerPool.newActor(self._run, name = 'CoAPServer').start()

		L.isInfo and L.log('Start CoAP server')
		return True


	def _run(self) -> None:
		"""	CoAP server main loop.
		"""
		self.coapServer = ACMECoAPServer(Configuration.coap_listenIF, Configuration.coap_port)	# type:ignore[attr-defined]
		self.coapServer.run()	
		L.isDebug and L.logDebug('CoAP server shut down')
		

	def _stop(self) -> None:
		"""	Stop the CoAP server.
		"""
		if self.coapServer is not None:
			L.isDebug and L.logDebug('Stopping CoAP server')
			self.coapServer.stop()
			self.coapServer = None
		if self.actor is not None:
			self.actor.stop()
			self.actor = None


	def pause(self) -> None:
		"""	Stop handling requests.
		"""
		L.isInfo and L.log('CoAP server paused')
		self.isPaused = True
		
	
	def unpause(self) -> None:
		"""	Continue handling requests.
		"""
		L.isInfo and L.log('CoAP server unpaused')
		self.isPaused = False
	

	def sendCoAPRequest(self, request:CSERequest, url:str, isDirectURL:bool = False) -> Result:
		"""	Send a CoAP request to a URL.

			Args:
				request: The request to send.
				url: The URL to send the request to.
				isDirectURL: Flag whether the URL is a direct URL.

			Returns:
				The result of the request.
		"""
		if self.coapServer is None:
			raise INTERNAL_SERVER_ERROR('CoAP server not running')
		return self.coapServer.sendRequest(request, url, isDirectURL)


##########################################################################
#
#	Helper functions
#

def optionsToDict(options:list[CoapthonOption]) -> MultiDict:
	"""	Convert CoAP options to a dictionary.

		Args:
			options: The options to convert.

		Returns:
			A multi-dictionary with the options. The key is the option number, the value is a set of option values for that number
	"""
	result = MultiDict()
	for o in options:
		result[o.name] = o.value
	return result


def dissectOptions(options:list[CoapthonOption]) -> MultiDict:
	"""	Dissect the options of a CoAP request in a dictionary.

		Args:
			options: The options of a CoAP request.

		Returns:
			A multi-dictionary with the options. The key is the option number, the value is a set of option values for that number.
	"""
	opts = MultiDict()
	for opt in options:
		opts[opt.number] = opt.value
	return opts
