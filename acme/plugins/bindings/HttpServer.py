#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This module provides the HTTP server for the CSE. """

from __future__ import annotations
from typing import Any, Callable, cast, Optional, TYPE_CHECKING

import logging, sys, urllib3, re, os

from flask import Flask, Request, request

from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import MultiDict as WerkzeugMultiDict
from waitress import serve
from flask_cors import CORS
import requests
import isodate

from ...etc.Constants import Constants
from ...etc.Types import ReqResp, RequestType, Result, ResponseStatusCode, JSON, LogLevel, RequestCredentials, AuthorizationResult
from ...etc.Types import Operation, CSERequest, ContentSerializationType, DesiredIdentifierResultType, ResponseType, ResultContentType
from ...etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR, BAD_REQUEST, REQUEST_TIMEOUT, TARGET_NOT_REACHABLE, ResponseException
from ...etc.IDUtils import uniqueRI, toSPRelative, isCSERelative
from ...etc.Utils import renameThread, getThreadName, isURL, getBasicAuthFromUrl, normalizeURL
from ...etc.Constants import RuntimeConstants as RC
from ...etc.DateUtils import timeUntilAbsRelTimestamp, getResourceDate, rfc1123Date
from ...etc.RequestUtils import toHttpUrl, serializeData, deserializeData
from ...etc.RequestUtils import createPositiveResponseResult, fromHttpURL, contentAsString, fillRequestWithArguments
from ...helpers.TextTools import findXPath
from ...helpers.MultiDict import MultiDict
from ...helpers.NetworkTools import isTCPPortAvailable, isValidPort, isValidateIpAddress, isValidateHostname
from ...helpers import TextTools as TextTools
from ...helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.Logging import Logging as L
from ...runtime.PluginSupport import *

if TYPE_CHECKING:
	from ...services.SecurityManager import SecurityManager
	from ...services.RequestManager import RequestManager


#
# Types definitions for the http server
#

FlaskHandler = 	Callable[[str], Response]
""" Type definition for flask handler. """


#########################################################################
#
#	HTTP Server
#

@plugin(property='httpServer', tags=['binding', 'acme'], priority=20, noRestartWhilePaused=True)
@requires(security='acme.services.SecurityManager')
@requires(requestManager='acme.services.RequestManager')
@requires(cseShutdown='acme.runtime.CSE.shutdown')
class HttpServer(object):
	""" The HTTP server for the CSE.
	"""

	security: SecurityManager = None
	""" SecurityManager instance. """

	requestManager: RequestManager = None
	""" RequestManager instance. """

	cseShutdown: Callable[[], None] = None
	""" Function to shut down the CSE. """

	__slots__ = (
		'flaskApp',
		'isStopped',
		'backgroundActor',
		'serverID',
		'_responseHeaders',
		'httpActor',
	)
	""" The slots for the HttpServer class to optimize memory usage. """

	@init
	def init(self) -> None:
		"""	Start the HTTP server.
			This sets up the Flask application, configures CORS, adds endpoints,
			and initializes the web UI.
		"""

		self.isStopped = False
		""" Whether the HTTP server is stopped. """

		self.backgroundActor:BackgroundWorker = None
		""" The background worker for the HTTP server. """

		self.serverID = f'ACME/{Constants.version}' 
		""" The server's ID for HTTP response headers. """

		self._responseHeaders = {'Server' : self.serverID}
		""" Additional headers for HTTP responses. """

		self.httpActor:Optional[BackgroundWorker] = None
		""" The background worker for the HTTP server. """

		# Disable most logs from requests and urllib3 library 
		logging.getLogger("requests").setLevel(LogLevel.WARNING)
		logging.getLogger("urllib3").setLevel(LogLevel.WARNING)


	@start
	def run(self) -> None:
		"""	Run the http server in a separate thread.
		"""

		# Initialize the http server
		# Meaning defaults are automatically provided.
		# Also prevent flask from registering the static endpoint
		self.flaskApp = Flask(RC.cseCsi, static_folder=None)
		""" The Flask application instance. """
		L.isInfo and L.log(f'Registering http server root at: {Configuration.http_root}')
		if Configuration.http_security_useTLS:
			L.isInfo and L.log('TLS enabled. HTTP server serves via https.')
		# Add CORS support for flask
		if Configuration.http_cors_enable:
			logging.getLogger('flask_cors').level = logging.DEBUG	# switch on flask-cors internal logging
			L.isInfo and L.log('CORS is enabled for the HTTP server.')
			CORS(self.flaskApp, resources=Configuration.http_cors_resources)
		else:
			L.isDebug and L.logDebug('CORS is NOT enabled for the HTTP server.')

		# Add endpoints
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handleGET, methods=['GET'])
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handlePOST, methods=['POST'])
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handlePUT, methods=['PUT'])
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handleDELETE, methods=['DELETE'])

		# Allow to use PATCH as a replacement for the DELETE method
		if Configuration.http_allowPatchForDelete:
			self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handlePATCH, methods=['PATCH'])

		if not Configuration.http_security_verifyCertificate:	# only when we also verify  certificates
			urllib3.disable_warnings()
		L.isInfo and L.log('HTTP Server initialized')

		# Start the http server in a separate thread. This is necessary to not block the main thread, which runs the CSE.
		if not isTCPPortAvailable(Configuration.http_port):
			raise RuntimeError(L.logErr(f'Cannot start HTTP server. Port: {Configuration.http_port} already in use.'))
		self.httpActor = BackgroundWorkerPool.newActor(self._run, name='HTTPServer')
		self.httpActor.start()
	

	@stop
	def shutdown(self) -> None:
		"""	Shutting down the http server.
		"""
		L.isInfo and L.log('HttpServer shut down')
		self.isStopped = True
	

	@pause
	def pause(self) -> None:
		"""	Stop handling requests.
		"""
		L.isInfo and L.log('HttpServer paused')
		self.isStopped = True
		
	
	@unpause
	def unpause(self) -> None:
		"""	Continue handling requests.
		"""
		L.isInfo and L.log('HttpServer unpaused')
		self.isStopped = False

	
	def _run(self) -> None:
		"""	Run the http server.
			This method is run in a separate thread.
			It starts the Flask application and serves it.
		"""
		WSGIRequestHandler.protocol_version = "HTTP/1.1"

		# Run the http server. This runs forever.
		# The server can run single-threadedly since some of the underlying
		# components (e.g. TinyDB) may run into problems otherwise.
		if self.flaskApp:
			# Disable the flask banner messages
			cli = sys.modules['flask.cli']
			cli.show_server_banner = lambda *x: None 	# type: ignore
			# Start the server
			try:
				if Configuration.http_wsgi_enable:
					L.isInfo and L.log(f'HTTP server listening on {Configuration.http_listenIF}:{Configuration.http_port} (wsgi)')
					serve(self.flaskApp, 
		   				  host=Configuration.http_listenIF, 
						  port=Configuration.http_port, 
						  threads=Configuration.http_wsgi_threadPoolSize,
						  connection_limit=Configuration.http_wsgi_connectionLimit)
				else:
					L.isInfo and L.log(f'HTTP server listening on {Configuration.http_listenIF}:{Configuration.http_port} (flask http)')
					self.flaskApp.run(host=Configuration.http_listenIF, 
									  port=Configuration.http_port,
									  threaded=True,
									  request_handler=ACMERequestHandler,
									  ssl_context= self.security.getSSLContextHttp(),
									  debug=False)
			except Exception as e:
				# No logging for headless, nevertheless print the reason what happened
				if RC.isHeadless:
					L.console(str(e), isError=True)
				if type(e) == PermissionError:
					m  = f'{e}.'
					m += f' You may not have enough permission to run a server on this port ({Configuration.http_port}).'
					if Configuration.http_port < 1024:
						m += ' Try another, non-privileged port > 1024.'
					L.logErr(m )
				else:
					L.logErr(str(e))
				self.cseShutdown() 


	def addEndpoint(self, endpoint:Optional[str]=None, 
						  endpoint_name:Optional[str]=None, 
						  handler:Optional[FlaskHandler]=None, 
						  methods:Optional[list[str]]=None, 
						  strictSlashes:Optional[bool]=True) -> str:
		"""	Add an endpoint to the Flask application.

			Args:
				endpoint: The endpoint URL.
				endpoint_name: The name of the endpoint.
				handler: The handler function for the endpoint.
				methods: The HTTP methods allowed for this endpoint.
				strictSlashes: Whether to enforce strict slashes in the URL.
			Return:
				The path of the registered endpoint.
		"""
		path = f'{Configuration.http_root}/{endpoint}'
		self.flaskApp.add_url_rule(path, endpoint_name, handler, methods=methods, strict_slashes=strictSlashes)
		return path


	def getEndpoints(self) -> list[dict]:
		"""Get all registered HTTP endpoints.
		
		Return:
			List of dictionaries containing endpoint information.
		"""
		endpoints = []
		for rule in self.flaskApp.url_map.iter_rules():
			endpoints.append({
				'endpoint': rule.endpoint,
				'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'})),
				'url_pattern': str(rule),
				'strict_slashes': rule.strict_slashes
			})
		return endpoints
	

	def _handleRequest(self, path:str, operation:Operation, authResult:AuthorizationResult) -> Response:
		"""	Get and check all the necessary information from the request and
			build the internal strutures. Then, depending on the operation,
			call the associated request handler.
		"""

		def _runRequest(request:CSERequest) -> Result:
			try:
				return self.requestManager.handleRequest(request)	# type: ignore[arg-type]
			except Exception as e:
				return Result.exceptionToResult(e)

		L.isDebug and L.logDebug(f'==> HTTP Request: {path}') 	# path = request.path  w/o the root
		L.isDebug and L.logDebug(f'Operation: {operation.name}')
		L.isDebug and L.logDebug(f'Headers: { { k:v for k,v in request.headers.items()} }')
		try:
			dissectResult = self._dissectHttpRequest(request, operation, path)
		except ResponseException as e:
			dissectResult = Result(rsc = e.rsc, request = e.data, dbg = e.dbg)

		# Set the authorization result
		if dissectResult.request:
			dissectResult.request.rq_authn = authResult == AuthorizationResult.AUTHORIZED

		# log Body, if there is one
		if operation in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ] and dissectResult.request and dissectResult.request.originalData:
			if dissectResult.request.ct == ContentSerializationType.JSON:
				L.isDebug and L.logDebug(f'Body: \n{str(dissectResult.request.originalData)}')
			else:
				L.isDebug and L.logDebug(f'Body: \n{TextTools.toHex(cast(bytes, dissectResult.request.originalData))}\n=>\n{dissectResult.request.pc}')

		# Send and error message when the CSE is shutting down, or the http server is stopped
		if self.isStopped:
			# Return an error if the server is stopped

			return self._prepareResponse(Result(rsc=ResponseStatusCode.INTERNAL_SERVER_ERROR, 
												request=dissectResult.request, 
												dbg='http server not running'))

		if dissectResult.rsc != ResponseStatusCode.UNKNOWN:	# any other value right now indicates an error condition
			# Something went wrong during dissection
			if dissectResult.request:
				self.requestManager.recordRequest(dissectResult.request, dissectResult)
			return self._prepareResponse(dissectResult)

		# Return without a response if the request is a noResponse request
		# This means return a simple "status = 204" response, but execute the request in the background
		if dissectResult.request.rt == ResponseType.noResponse:
			L.isDebug and L.logDebug('No response requested')
			BackgroundWorkerPool.newActor(lambda: _runRequest(dissectResult.request), name=getThreadName()+'_1').start()
			return Response(status = 204)	# No Content

		# Otherwise, handle the request and return the response
		responseResult = _runRequest(dissectResult.request)

		# Return a proper response
		return self._prepareResponse(responseResult, dissectResult.request)


	# @perfTimer('handleGet', L.logDebug)
	def handleGET(self, path:Optional[str]=None) -> Response:
		"""	Handle a GET request.

			Args:
				path: The path of the request.
		"""
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status=401)
		L.enableScreenLogging and renameThread('HT_R')
		eventManager.httpRetrieve()
		return self._handleRequest(path, Operation.RETRIEVE, authResult)


	def handlePOST(self, path:Optional[str]=None) -> Response:
		"""	Handle a POST request.

			Args:
				path: The path of the request.
		"""
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status=401)
		if self._hasContentType():
			L.enableScreenLogging and renameThread('HT_C')
			eventManager.httpCreate()
			return self._handleRequest(path, Operation.CREATE, authResult)
		else:
			L.enableScreenLogging and renameThread('HT_N')
			eventManager.httpNotify()
			return self._handleRequest(path, Operation.NOTIFY, authResult)


	def handlePUT(self, path:Optional[str]=None) -> Response:
		"""	Handle a PUT request.

			Args:
				path: The path of the request.
		"""
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status=401)
		L.enableScreenLogging and renameThread('HT_U')
		eventManager.httpUpdate()
		return self._handleRequest(path, Operation.UPDATE, authResult)


	def handleDELETE(self, path:Optional[str]=None) -> Response:
		"""	Handle a DELETE request.

			Args:
				path: The path of the request.
		"""
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status=401)
		L.enableScreenLogging and renameThread('HT_D')
		eventManager.httpDelete()
		return self._handleRequest(path, Operation.DELETE, authResult)


	def handlePATCH(self, path:Optional[str]=None) -> Response:
		"""	Support PATCH instead of DELETE for http/1.0.

			Args:
				path: The path of the request.
		"""
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status=401)
		if request.environ.get('SERVER_PROTOCOL') != 'HTTP/1.0':
			return Response(L.logWarn('PATCH method is only allowed for HTTP/1.0. Rejected.'), status=405)
		L.enableScreenLogging and renameThread('HT_D')
		eventManager.httpDelete()
		return self._handleRequest(path, Operation.DELETE, authResult)

	#########################################################################

	#
	#	Send HTTP requests
	#

	operation2method = {
		Operation.CREATE	: requests.post,
		Operation.RETRIEVE	: requests.get,
		Operation.UPDATE 	: requests.put,
		Operation.DELETE 	: requests.delete,
		Operation.NOTIFY 	: requests.post,
		Operation.DISCOVERY	: requests.get,
	}
	""" A mapping of operations to the corresponding HTTP methods. """


	def sendHttpRequest(self, request:CSERequest, url:str, ignoreResponse:bool) -> Result:
		"""	Send an http request.
		
			The result is always returned in *Result.data*, even an error/dbg message.
		"""

		# Request timeout
		timeout:float = None

		# Set the request method
		method:Callable = self.operation2method[request.op] 	# type: ignore[assignment]

		# Add the to to the base url
		if request.to:
			if isURL(request.to):
				url = request.to
			else:
				url = url + request.to

		# Make the URL a valid http URL (escape // and ///)
		url = toHttpUrl(url)

		# get the serialization
		ct = request.ct if request.ct else RC.defaultSerialization

		# Set basic headers
		hty = f';ty={int(request.ty):d}' if request.ty else ''
		hds = {	'Date'			: rfc1123Date(),
				'User-Agent'	: self.serverID,
				'Content-Type' 	: f'{ct.toHttpContentType()}{hty}',
				'cache-control'	: 'no-cache',
		}
		hds[Constants.hfOrigin]	= toSPRelative(request.originator) if isCSERelative(request.originator) else request.originator
		if not request.rqi:
			request.rqi = uniqueRI()
		hds[Constants.hfRI]		= request.rqi
		# hds[Constants.hfRI]		= request.rqi if request.rqi else uniqueRI()
		if request.rvi != '1':
			hds[Constants.hfRVI]= request.rvi if request.rvi is not None else RC.releaseVersion
		hds[Constants.hfOT]		= request.ot if request.ot else getResourceDate()
		if request.ec:				# Event Category
			hds[Constants.hfEC] = str(request.ec.value)
		if request.rqet:
			hds[Constants.hfRET] = request.rqet
			timeout = timeUntilAbsRelTimestamp(request.rqet)
		if request.rset:
			hds[Constants.hfRST] = request.rset
		if request.oet:
			hds[Constants.hfOET] = request.oet
		if request.rt and request.rt != ResponseType.blockingRequest:
			if (nu := request.originalRequest.get('nu')):
				hds[Constants.hfRTU] = '&'.join(nu)
		if request.vsi:
			hds[Constants.hfVSI] = request.vsi

		# check for basic authentication in the URL. This overwrites any other credentials!!!
		parsedUrl = getBasicAuthFromUrl(url)
		url = parsedUrl[0] # replace with the URL without credentials
		if parsedUrl[1] and parsedUrl[2]: # credentials are present in the URL
			request.credentials = RequestCredentials(httpUsername=parsedUrl[1], httpPassword=parsedUrl[2])

		# Add authentication headers
		if request.credentials:
			if request.credentials.httpUsername and request.credentials.httpPassword:
				hds['Authorization'] = f'Basic {request.credentials.getHttpBasic()}'
			elif request.credentials.httpToken:
				hds['Authorization'] = f'Bearer {request.credentials.getHttpBearerToken()}'
			else:
				L.isDebug and L.logDebug('No credentials found for HTTP request')


		arguments = []
		if request.rcn and request.rcn != ResultContentType.default(request.op):
			arguments.append(f'rcn={request.rcn.value}')
		if request.drt and request.drt != DesiredIdentifierResultType.structured:
			arguments.append(f'drt={request.drt.value}')

		# Add filterCriteria arguments
		if fc := request.fc:
			fc.mapAttributes(lambda k, v: arguments.append(f'{k}={v}'), True)

		# Add further non-filterCriteria arguments
		if request.sqi:
			arguments.append(f'sqi={request.sqi}')
			
		# Add attributeList
		if (atrl := findXPath(request.pc, 'm2m:atrl')) is not None:
			arguments.append(f'atrl={"+".join(atrl)}')
		
		# Add arguments to URL
		if arguments:
			url += f'?{"&".join(arguments)}'

		# Add content
		content = request.pc if request.pc else None

		
		# Get request timeout
		timeout = Configuration.http_timeout if timeout is None else timeout

		# serialize data (only if dictionary, pass on non-dict data)
		data = None
		if request.op in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ]:
			data = serializeData(content, ct)
		# elif content and not raw:
		elif content:
			raise INTERNAL_SERVER_ERROR(L.logErr(f'Operation: {request.op.name} doesn\'t allow content'))

		# ! Don't forget: requests are done through the request library, not flask.
		# ! The attribute names are different
		try:
			L.isDebug and L.logDebug(f'Sending request: {method.__name__.upper()} {url}')
			if ct == ContentSerializationType.CBOR:
				L.isDebug and L.logDebug(f'HTTP Request ==>:\nHeaders: {hds}\nBody: \n{contentAsString(data, ct)}\n=>\n{str(data) if data else ""}\n')
			else:
				L.isDebug and L.logDebug(f'HTTP Request ==>:\nHeaders: {hds}\nBody: \n{contentAsString(data, ct)}\n')
			
			# Actual sending the request
			r = method(url, 
					   data=data,
					   headers=hds,
					   verify=Configuration.http_security_verifyCertificate,
					   timeout=timeout)

			# Ignore the response to notifications in some cases
			if ignoreResponse and request.op == Operation.NOTIFY:
				L.isDebug and L.logDebug('HTTP: Ignoring response to notification')
				return createPositiveResponseResult()

			# Construct CSERequest response object from the result
			resp = CSERequest(requestType=RequestType.RESPONSE)
			resp.ct = ContentSerializationType.getType(r.headers.get('Content-Type', ct))
			resp.rsc = ResponseStatusCode(int(r.headers.get(Constants.hfRSC, ResponseStatusCode.INTERNAL_SERVER_ERROR)))
			resp.pc = deserializeData(r.content, resp.ct)
			resp.originator = r.headers.get(Constants.hfOrigin)
			try:
				# Add Originating Timestamp if present in request
				if (ot := r.headers.get(Constants().hfOT)):
					isodate.parse_datetime(ot) # Check if valid ISO 8601 date, may raise exception
					resp.ot = ot
			except Exception as ee:
				raise BAD_REQUEST(L.logWarn(f'Received wrong format for X-M2M-OT: {ot} - {str(ee)}'))
			if (rqi := r.headers.get(Constants().hfRI)) != hds[Constants().hfRI]:
				raise BAD_REQUEST(L.logWarn(f'Received wrong or missing request identifier: {resp.rqi}'))
			resp.rqi = rqi

			L.isDebug and L.logDebug(f'HTTP Response <== ({str(r.status_code)}):\nHeaders: {str(r.headers)}\nBody: \n{contentAsString(r.content, resp.ct)}\n')
		except ResponseException as e:
			raise e
		except requests.Timeout as e:
			raise REQUEST_TIMEOUT(L.logWarn(f'http request timeout after {timeout}s'))
		except Exception as e:
			L.logWarn(f'Failed to send request: {str(e)}')
			raise TARGET_NOT_REACHABLE('target not reachable')
		
		res = Result(rsc = resp.rsc, data = resp.pc, request = resp)
		eventManager.responseReceived(EventData(payload=resp))
		return res
		
	#########################################################################

	#
	#	Handle authentication
	#

	def handleAuthentication(self) -> AuthorizationResult:
		"""	Handle the authentication for the current request.

			Return:
				Enum value for the authentication result.

		"""

		def testBasicAuthentication(parameters:dict) -> bool:
			"""	Validate the basic authentication.

				If basic authentication is not enabled, a warning is logged, but the
				authentication is considered valid.

				Args:
					parameters: The parameters for the basic authentication.
			
				Return:
					True if the authentication is valid, False otherwise.
			"""
			if not Configuration.http_security_enableBasicAuth:
				L.isWarn and L.logWarn('Basic authentication is not enabled, but a basic authorization header was found.')
				return True
			if not self.security.validateHttpBasicAuth(parameters['username'], parameters['password']):
				L.isWarn and L.logWarn(f'Invalid username or password for basic authentication: {parameters["username"]}')
				return False
			return True
		

		def testTokenAuthentication(token:str) -> bool:
			"""	Validate the token.

				If token authentication is not enabled, a warning is logged, but the
				authentication is considered valid.

				Args:
					token: The token to validate.
			
				Return:
					True if the token is valid, False otherwise.
			"""
			if not Configuration.http_security_enableTokenAuth:
				L.isWarn and L.logWarn('Token authentication is not enabled, but a bearer authorization header was found.')
				return True
			if not self.security.validateHttpTokenAuth(token):
				L.isWarn and L.logWarn(f'Invalid token for token authentication: {token}')
				return False
			return True

		L.isDebug and L.logDebug('Checking authentication')
		if not (Configuration.http_security_enableBasicAuth or Configuration.http_security_enableTokenAuth):
			if request.authorization:
				L.isWarn and L.logWarn('Basic or token authentication is not enabled, but an authorization header was found.')
			return AuthorizationResult.NOTSET
		
		if (authorization := request.authorization) is None:
			L.isDebug and L.logDebug('No authorization header found.')
			return AuthorizationResult.UNAUTHORIZED
		
		match authorization.type:
			case 'basic':
				return AuthorizationResult.AUTHORIZED if testBasicAuthentication(authorization.parameters) else AuthorizationResult.UNAUTHORIZED
			case 'bearer':
				return AuthorizationResult.AUTHORIZED if testTokenAuthentication(authorization.token) else AuthorizationResult.UNAUTHORIZED
			case _:
				L.isWarn and L.logWarn(f'Unsupported authentication method: {authorization.type}')
				return AuthorizationResult.UNAUTHORIZED
	

	#########################################################################

	def _prepareResponse(self, result: Result, 
							   originalRequest: Optional[CSERequest] = None) -> Response:
		"""	Prepare the response for a request. If `request` is given then
			set it for the response.
		"""
		content: str|bytes|JSON = ''
		if not result.request:
			result.request = CSERequest()

		#
		#  Copy a couple of attributes from the originalRequest to the new request
		#

		result.request.ct = RC.defaultSerialization	# default serialization
		if originalRequest:

			# Determine contentType for the response. Check the 'accept' header first, then take the
			# original request's contentType. If this is not possible, the fallback is still the
			# CSE's default
			result.request.originator = originalRequest.originator
			if originalRequest.httpAccept:																# accept / contentType
				result.request.ct = ContentSerializationType.getType(originalRequest.httpAccept[0])
			elif csz := self.requestManager.getSerializationFromOriginator(originalRequest.originator):
				result.request.ct = csz[0]

			result.request.rqi = originalRequest.rqi
			result.request.rvi = originalRequest.rvi
			result.request.vsi = originalRequest.vsi
			result.request.ec  = originalRequest.ec
			result.request.rset = originalRequest.rset
		
	
		#
		#	Transform request to oneM2M request
		#
		outResult = self.requestManager.requestFromResult(result, isResponse=True, originalRequest=originalRequest)

		#
		#	Transform oneM2M request to http message
		#

		# Build the headers
		headers = {}
		headers['Server'] = self.serverID						# set server field
		if result.rsc:
			headers[Constants().hfRSC] = f'{int(result.rsc)}'				# set the response status code
		if rqi := findXPath(cast(JSON, outResult.data), 'rqi'):
			headers[Constants().hfRI] = rqi
		else:
			headers[Constants().hfRI] = result.request.rqi
		if rvi := findXPath(cast(JSON, outResult.data), 'rvi'):
			headers[Constants().hfRVI] = rvi
		if vsi := findXPath(cast(JSON, outResult.data), 'vsi'):
			headers[Constants().hfVSI] = vsi
		if rset := findXPath(cast(JSON, outResult.data), 'rset'):
			headers[Constants().hfRST] = rset
		headers[Constants().hfOT] = getResourceDate()

		# HTTP status code
		statusCode = result.rsc.httpStatusCode()
		
		# Assign and encode content accordingly
		headers['Content-Type'] = (cts := result.request.ct.toHttpContentType())
		# (re-)add an empty pc if it is missing	


		# From hereon, data is a string or byte string
		origData:JSON = cast(JSON, outResult.data)
		outResult.data = serializeData(cast(JSON, outResult.data)['pc'], result.request.ct) if 'pc' in cast(JSON, outResult.data) else ''
		
		#
		#	Add Content-Location header, if this is a response to a CREATE operation, and uri is present
		#
		try:
			if originalRequest and originalRequest.op == Operation.CREATE:
				if  (uri := findXPath(origData, 'pc/m2m:uri')) is not None or \
					(uri := findXPath(origData, 'pc/m2m:rce/uri')):
						headers['Content-Location'] = uri
		except Exception as e:
			L.logErr(str(e))
			quit()	# TODO

		# Build and return the response
		if isinstance(outResult.data, bytes):
			L.isDebug and L.logDebug(f'<== HTTP Response ({result.rsc}):\nHeaders: {str(headers)}\nBody: \n{TextTools.toHex(outResult.data)}\n=>\n{str(result.toData())}')
		elif 'pc' in origData:
			# L.isDebug and L.logDebug(f'<== HTTP Response (RSC: {int(result.rsc)}):\nHeaders: {str(headers)}\nBody: {str(content)}\n')
			L.isDebug and L.logDebug(f'<== HTTP Response ({result.rsc}):\nHeaders: {str(headers)}\nBody: {origData["pc"]}')	# might be different serialization
		else:
			L.isDebug and L.logDebug(f'<== HTTP Response ({result.rsc}):\nHeaders: {str(headers)}')
		return Response(response=outResult.data, status=statusCode, content_type=cts, headers=headers)


	#########################################################################
	#
	#	HTTP request helper functions
	#

	def _dissectHttpRequest(self, request:Request, operation:Operation, path:str) -> Result:
		"""	Dissect an HTTP request. Combine headers and contents into a single structure. Result is returned in Result.request.
		"""

		def extractMultipleArgs(args:WerkzeugMultiDict, argName:str) -> None:
			"""	Get multi-arguments. Remove the found arguments from the original list, but add the new list again with the argument name.
			"""
			lst = [ t for sublist in args.getlist(argName) for t in sublist.split() ]
			args.poplist(argName)	# type: ignore [no-untyped-call] # perhaps even multiple times
			if len(lst) > 0:
				args[argName] = lst


		# TODO: change the args handling to the MultiDict like in CoAP


		cseRequest = CSERequest()
		req:ReqResp = {}
		cseRequest.originalData = request.data		# get the data first. This marks the request as consumed, just in case that we have to return early
		cseRequest.op = operation
		req['op'] = operation.value					# Needed later for validation

		# resolve http's /~ and /_ special prefixs
		req['to'] = fromHttpURL(path)


		# Copy and parse the original request headers
		_headers = request.headers							# optimize access to headers
		if f := _headers.get(Constants.hfOrigin):
			req['fr'] = f
		if f := _headers.get(Constants.hfRI):
			req['rqi'] = f
		if f := _headers.get(Constants.hfRET):
			req['rqet'] = f
		if f := _headers.get(Constants.hfRST):
			req['rset'] = f
		if f := _headers.get(Constants.hfOET):
			req['oet'] = f
		if f := _headers.get(Constants.hfRVI):
			req['rvi'] = f
		if (rtu := _headers.get(Constants.hfRTU)) is not None:	# handle rtu as a list AND it might be an empty list!
			rt = dict()
			rt['nu'] = rtu.split('&')		
			req['rt'] = rt					# req.rt.rtu Create a new dict for the rt here. Might be used later
		if f := _headers.get(Constants.hfVSI):
			req['vsi'] = f
		if f := _headers.get(Constants.hfOT):
			req['ot'] = f

		cseRequest.originalRequest = req 	# Already store now the incompliete request to save the header data
	
		# parse and extract content-type header
		if contentType := request.content_type:
			if not contentType.startswith(tuple(ContentSerializationType.supportedContentSerializations())):
				contentType = None
			else:
				p  = contentType.partition(';')		# always returns a 3-tuple
				contentType = p[0] 					# only the content-type without the resource type
				t  = p[2].partition('=')[2]
				if len(t) > 0:
					try:
						req['ty'] = int(t)			# Here we found the type for CREATE requests
					except:
						raise BAD_REQUEST(L.logWarn(f'resource type must be an integer: {t}'), data = cseRequest)

		# Get the media type from the content-type header
		cseRequest.ct = ContentSerializationType.getType(contentType, default = RC.defaultSerialization)

		# parse accept header. Ignore */* and variants thereof
		cseRequest.httpAccept = []
		for h in _headers.getlist('accept'):
			cseRequest.httpAccept.extend([ a.strip() for a in h.split(',') if not a.startswith('*/*')])

		# Copy the request arguments into an own multi-dict
		_args = MultiDict()	
		for k,v in request.args.items(multi=True): # multi=True returns a list of values for each key
			_args[k] = v
			# splitting + arguments is in the value

		# Extract the request arguments and copy them into the request, including the PC
		cseRequest = fillRequestWithArguments(_args, req, cseRequest)
		
		# do validation and copying of attributes of the whole request
		try:
			self.requestManager.fillAndValidateCSERequest(cseRequest)
		except REQUEST_TIMEOUT as e:
			raise e
		except ResponseException as e:
			e.dbg = f'invalid arguments/attributes: {e.dbg}'
			raise e

		# Here, if everything went okay so far, we have a request to the CSE
		return Result(request = cseRequest)


	_hdrArgument = re.compile(r'^\s*ty\s*=\s*', re.IGNORECASE)
	"""	Regex to check if the request has a content type that is supported by the CSE."""

	def _hasContentType(self) -> bool:
		"""	Check if the request has a content type that is supported by the CSE.
			This is used to determine if the request can be processed.
			
			Return:
				True if the request has a content type that is supported, False otherwise.
		"""
		return (ct := request.content_type) is not None and any(re.match(self._hdrArgument, s) is not None for s in ct.split(';'))



	@configure
	def configure(self, config: Configuration) -> None:

		parser = config.configParser

		#	HTTP Server
		config.http_enable = parser.getboolean('http', 'enable', fallback=True)
		config.http_address = parser.get('http', 'address', fallback='http://127.0.0.1:8080')
		config.http_allowPatchForDelete = parser.getboolean('http', 'allowPatchForDelete', fallback=False)
		config.http_listenIF = parser.get('http', 'listenIF', fallback='0.0.0.0')
		config.http_port = parser.getint('http', 'port', fallback=8080)
		config.http_root = parser.get('http', 'root', fallback='')
		config.http_externalRoot = parser.get('http', 'externalRoot', fallback=config.http_root)
		config.http_timeout = parser.getfloat('http', 'timeout', fallback=10.0)

		#	HTTP Server CORS
		config.http_cors_enable = parser.getboolean('http.cors', 'enable', fallback=False)
		config.http_cors_resources = parser.getlist('http.cors', 'resources', fallback=[ r'/*' ])	# type: ignore[attr-defined]

		#	HTTP Server Security
		config.http_security_caCertificateFile = parser.get('http.security', 'caCertificateFile', fallback=None)
		config.http_security_caPrivateKeyFile = parser.get('http.security', 'caPrivateKeyFile', fallback=None)
		config.http_security_tlsVersion = parser.get('http.security', 'tlsVersion', fallback='auto')
		config.http_security_useTLS = parser.getboolean('http.security', 'useTLS', fallback=False)
		config.http_security_verifyCertificate = parser.getboolean('http.security', 'verifyCertificate', fallback=False)
		config.http_security_enableBasicAuth = parser.getboolean('http.security', 'enableBasicAuth', fallback=False)
		config.http_security_enableTokenAuth = parser.getboolean('http.security', 'enableTokenAuth', fallback=False)
		config.http_security_basicAuthFile = parser.get('http.security', 'basicAuthFile', fallback='./certs/http_basic_auth.txt')
		config.http_security_tokenAuthFile = parser	.get('http.security', 'tokenAuthFile', fallback='./certs/http_token_auth.txt')

		#	HTTP Server WSGI
		config.http_wsgi_enable = parser.getboolean('http.wsgi', 'enable', fallback=False)
		config.http_wsgi_connectionLimit = parser.getint('http.wsgi', 'connectionLimit', fallback=100)
		config.http_wsgi_threadPoolSize = parser.getint('http.wsgi', 'threadPoolSize', fallback=100)


	@validate
	def validate(self, config: Configuration) -> None:
		# override configuration with command line arguments
		if Configuration._args_httpAddress is not None:
			Configuration.http_address = Configuration._args_httpAddress
		if Configuration._args_httpPort is not None:
			Configuration.http_port = Configuration._args_httpPort
		if Configuration._args_listenIF is not None:
			Configuration.http_listenIF = Configuration._args_listenIF
		if Configuration._args_runAsHttps is not None:
			Configuration.http_security_useTLS = Configuration._args_runAsHttps
		if Configuration._args_runAsHttpWsgi is not None:
			Configuration.http_wsgi_enable = Configuration._args_runAsHttpWsgi

		if not config.http_root.endswith('/'):
			raise ConfigurationError(fr'[i]\[http]:root[/i] must end with a trailing slash (/): {config.http_root}')
		if not config.http_externalRoot.endswith('/'):
			raise ConfigurationError(fr'[i]\[http]:externalRoot[/i] must end with a trailing slash (/): {config.http_externalRoot}')
		
		config.http_address = normalizeURL(config.http_address)
		config.http_root = normalizeURL(config.http_root)
		config.http_externalRoot = normalizeURL(config.http_externalRoot)

		# Raise an error if TLS and the WSGI server are both enabled, as they are incompatible
		if config.http_security_useTLS and config.http_wsgi_enable:
			raise ConfigurationError(r'[i]\[http.security].useTLS[/i] (https) cannot be enabled when [i]\[http.wsgi].enable[/i] is enabled. WSGI does not support TLS.')

		# Just in case: check the URL's (http, ws)
		if config.http_security_useTLS:
			if config.http_address.startswith('http:'):
				Configuration._warning(r'Changing "http" to "https" in [i]\[http]:address[/i]')
				config.http_address = config.http_address.replace('http:', 'https:')
			# registrar might still be accessible via another protocol
		else: 
			if config.http_address.startswith('https:'):
				Configuration._warning(r'Changing "https" to "http" in [i]\[http]:address[/i]')
				config.http_address = config.http_address.replace('https:', 'http:')
			# registrar might still be accessible via another protocol

		# HTTP server
		if not isValidPort(config.http_port):
			raise ConfigurationError(fr'Invalid port number for [i]\[http]:port[/i]: {config.http_port}')
		if not (isValidateHostname(config.http_listenIF) or isValidateIpAddress(config.http_listenIF)):
			raise ConfigurationError(fr'Invalid hostname or IP address for [i]\[http]:listenIF[/i]: {config.http_listenIF}')
		if config.http_timeout < 0.0:
			raise ConfigurationError(fr'Invalid timeout value for [i]\[http]:timeout[/i]: {config.http_timeout}')
		
		# HTTP TLS & certificates
		if not config.http_security_useTLS:	# clear certificates configuration if not in use
			config.http_security_verifyCertificate = False
			config.http_security_tlsVersion = 'auto'
			config.http_security_caCertificateFile = ''
			config.http_security_caPrivateKeyFile = ''
		else:
			if not (val := config.http_security_tlsVersion).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				raise ConfigurationError(fr'Unknown value for [i]\[http.security]:tlsVersion[/i]: {val}')
			if not (val := config.http_security_caCertificateFile):
				raise ConfigurationError(r'[i]\[http.security]:caCertificateFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'[i]\[http.security]:caCertificateFile[/i] does not exists or is not accessible: {val}')
			if not (val := config.http_security_caPrivateKeyFile):
				raise ConfigurationError(r'[i]\[http.security]:caPrivateKeyFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'[i]\[http.security]:caPrivateKeyFile[/i] does not exists or is not accessible: {val}')
		# HTTP Security
		Configuration.http_security_tlsVersion = Configuration.http_security_tlsVersion.lower()

		# HTTP CORS
		if config.http_cors_enable and not config.http_security_useTLS:
			Configuration._warning(r'[i]\[http.security].useTLS[/i] (https) should be enabled when [i]\[http.cors].enable[/i] is enabled.')

		# HTTP authentication
		if config.http_security_enableBasicAuth and not config.http_security_basicAuthFile:
			raise ConfigurationError(r'[i]\[http.security]:basicAuthFile[/i] must be set when HTTP Basic Auth is enabled')
		if config.http_security_enableTokenAuth and not config.http_security_tokenAuthFile:
			raise ConfigurationError(r'[i]\[http.security]:tokenAuthFile[/i] must be set when HTTP Token Auth is enabled')

		# HTTP WSGI
		if config.http_wsgi_enable and config.http_security_useTLS:
			# WSGI and TLS cannot both be enabled
			raise ConfigurationError(r'[i]\[http.security].useTLS[/i] (https) cannot be enabled when [i]\[http.wsgi].enable[/i] is enabled (WSGI and TLS cannot both be enabled).')
		if config.http_wsgi_threadPoolSize < 1:
			raise ConfigurationError(r'[i]\[http.wsgi]:threadPoolSize[/i] must be > 0')
		if config.http_wsgi_connectionLimit < 1:
			raise ConfigurationError(r'[i]\[http.wsgi]:connectionLimit[/i] must be > 0')

		# Add the HTTP server address to the list of CSE POA addresses if the server is enabled
		if Configuration.http_enable:
			RC.csePOA.append(Configuration.http_address)


##########################################################################
#
#	Own request handler.
#	Actually only to redirect some logging of the http server.
#	This handler does NOT handle requests.
#

class ACMERequestHandler(WSGIRequestHandler):
	"""	ACMERequestHandler is a custom request handler for the ACME CSE HTTP server.
		It extends the WSGIRequestHandler to provide custom logging.
	"""

	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type:str, message:str, *args:Any) -> None:
		"""	Log a message with the given type and arguments.
			This is used to log HTTP requests and responses.

			Args:
				type: The type of the log message (e.g. "request", "response").
				message: The log message format string.
				*args: The values to interpolate into the message format string.
		"""
		L.enableBindingsLogging and L.isDebug and L.logDebug(f'HTTP: {message % args}')

	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code:Optional[str|int]='-', size:Optional[str|int]='-') -> None:
		"""	Log an HTTP request with the given code and size.
			This is used to log HTTP requests and responses.

			Args:
				code: The HTTP status code of the response.
				size: The size of the response in bytes.
		"""
		L.enableBindingsLogging and L.isDebug and L.logDebug(f'HTTP: "{self.requestline}" {size} {code}')

	def log_message(self, format:str, *args:Any) -> None:
		"""	Log a message with the given format and arguments.
			This is used to log HTTP requests and responses.

			Args:
				format: The log message format string.
				*args: The values to interpolate into the message format string.
		"""
		L.enableBindingsLogging and L.isDebug and L.logDebug(f'HTTP: {format % args}')
	
