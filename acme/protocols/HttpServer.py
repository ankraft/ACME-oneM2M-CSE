#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This module provides the HTTP server for the CSE. """

from __future__ import annotations
from typing import Any, Callable, cast, Optional

import logging, sys, urllib3, re

import flask
from flask import Flask, Request, request

from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import MultiDict as WerkzeugMultiDict
from waitress import serve
from flask_cors import CORS
import requests
import isodate

from ..etc.Constants import Constants
from ..etc.Types import ReqResp, RequestType, Result, ResponseStatusCode, JSON, LogLevel, RequestCredentials, AuthorizationResult
from ..etc.Types import Operation, CSERequest, ContentSerializationType, DesiredIdentifierResultType, ResponseType, ResultContentType
from ..etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR, BAD_REQUEST, REQUEST_TIMEOUT, TARGET_NOT_REACHABLE, ResponseException
from ..etc.IDUtils import uniqueRI, toSPRelative
from ..etc.Utils import renameThread, getThreadName, isURL, getBasicAuthFromUrl
from ..helpers.TextTools import findXPath
from ..helpers.MultiDict import MultiDict
from ..etc.DateUtils import timeUntilAbsRelTimestamp, getResourceDate, rfc1123Date
from ..etc.RequestUtils import toHttpUrl, serializeData, deserializeData, requestFromResult
from ..etc.RequestUtils import createPositiveResponseResult, fromHttpURL, contentAsString, fillRequestWithArguments
from ..helpers.NetworkTools import isTCPPortAvailable
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..webui.webUI import WebUI
from ..helpers import TextTools as TextTools
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers.Interpreter import SType
from ..helpers.PerfTimer import perfTimer
from ..runtime.Logging import Logging as L
from ..etc.Constants import RuntimeConstants as RC


#
# Types definitions for the http server
#

FlaskHandler = 	Callable[[str], Response]
""" Type definition for flask handler. """



#########################################################################
#
#	HTTP Server
#

class HttpServer(object):
	""" The HTTP server for the CSE.
	"""

	__slots__ = (
		'webuiDirectory',
		
		'flaskApp',
		'isStopped',
		'backgroundActor',
		'serverID',
		'_responseHeaders',
		'webui',
		'httpActor',

		'_eventHttpRetrieve',
		'_eventHttpCreate',
		'_eventHttpNotify',
		'_eventHttpUpdate',
		'_eventHttpDelete',
		'_eventResponseReceived',
	)

	def __init__(self) -> None:

		# Initialize the http server
		# Meaning defaults are automatically provided.
		self.flaskApp = Flask(RC.cseCsi)

		# Get the configuration settings
		self._assignConfig()

		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)				# type: ignore

		self.isStopped = False
		self.backgroundActor:BackgroundWorker = None

		self.serverID = f'ACME {Constants.version}' 	# The server's ID for http response headers
		self._responseHeaders = {'Server' : self.serverID}	# Additional headers for other requests

		L.isInfo and L.log(f'Registering http server root at: {Configuration.http_root}')
		if Configuration.http_security_useTLS:
			L.isInfo and L.log('TLS enabled. HTTP server serves via https.')
		
		# Add CORS support for flask
		if Configuration.http_cors_enable:
			logging.getLogger('flask_cors').level = logging.DEBUG	# switch on flask-cors internal logging
			L.isInfo and L.log('CORS is enabled for the HTTP server.')
			CORS(self.flaskApp, resources = Configuration.http_cors_resources)
		else:
			L.isDebug and L.logDebug('CORS is NOT enabled for the HTTP server.')

		# Add endpoints
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handleGET, methods = ['GET'])
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handlePOST, methods = ['POST'])
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handlePUT, methods = ['PUT'])
		self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler=self.handleDELETE, methods = ['DELETE'])

		# Register the endpoint for the web UI
		# This is done by instancing the otherwise "external" web UI
		self.webui = WebUI(self.flaskApp, 
						   defaultRI = RC.cseRi, 
						   defaultOriginator = RC.cseOriginator, 
						   root = Configuration.webui_root,
						   webuiDirectory = self.webuiDirectory,
						   redirectURL= f'{Configuration.http_address}{Configuration.http_root}' if Configuration.http_root else None,
						   version = Constants.version,
						   httpRoot = Configuration.http_root)

		# Enable the config endpoint
		if Configuration.http_enableStructureEndpoint:
			structureEndpoint = f'{Configuration.http_root}/__structure__'
			L.isInfo and L.log(f'Registering structure endpoint at: {structureEndpoint}')
			self.addEndpoint(structureEndpoint, handler = self.handleStructure, methods  =['GET'], strictSlashes = False)
			self.addEndpoint(f'{structureEndpoint}/<path:path>', handler = self.handleStructure, methods = ['GET', 'PUT'])

		# Enable the upper tester endpoint
		if Configuration.http_enableUpperTesterEndpoint:
			upperTesterEndpoint = f'{Configuration.http_root}/__ut__'
			L.isInfo and L.log(f'Registering upper tester endpoint at: {upperTesterEndpoint}')
			self.addEndpoint(upperTesterEndpoint, handler = self.handleUpperTester, methods = ['POST'], strictSlashes=False)

		# Allow to use PATCH as a replacement for the DELETE method
		if Configuration.http_allowPatchForDelete:
			self.addEndpoint(f'{Configuration.http_root}/<path:path>', handler = self.handlePATCH, methods = ['PATCH'])

		# Disable most logs from requests and urllib3 library 
		logging.getLogger("requests").setLevel(LogLevel.WARNING)
		logging.getLogger("urllib3").setLevel(LogLevel.WARNING)
		if not Configuration.http_security_verifyCertificate:	# only when we also verify  certificates
			urllib3.disable_warnings()
		L.isInfo and L.log('HTTP Server initialized')

		# Optimize event handling
		self._eventHttpRetrieve =  CSE.event.httpRetrieve			# type: ignore [attr-defined]
		self._eventHttpCreate = CSE.event.httpCreate				# type: ignore [attr-defined]
		self._eventHttpNotify =  CSE.event.httpNotify				# type: ignore [attr-defined]
		self._eventHttpUpdate = CSE.event.httpUpdate				# type: ignore [attr-defined]
		self._eventHttpDelete = CSE.event.httpDelete				# type: ignore [attr-defined]
		self._eventResponseReceived = CSE.event.responseReceived	# type: ignore [attr-defined]


	def _assignConfig(self) -> None:
		"""	Assign the configuration values to the http server.
		"""
		self.webuiDirectory 	= f'{Configuration.moduleDirectory}/webui'


	def configUpdate(self, name:str, 
						   key:Optional[str] = None,
						   value:Any = None) -> None:
		"""	Handle configuration updates.

			Args:
				name: The name of the configuration section.
				key: The key of the configuration value.
				value: The new value.
		"""
		if key not in ( 'http.root', 
						'http.address',
						'http.listenIF',
						'http.port',
						'http.allowPatchForDelete',
						'http.timeout',
						'webui.root',
						'http.cors.enable',
						'http.cors.resources',
						'http.wsgi.enable',
						'http.wsgi.threadPoolSize',
						'http.wsgi.connectionLimit',
						'http.security.enableBasicAuth',
						'http.security.enableTokenAuth'
					  ):
			return
		self._assignConfig()
		# TODO remove _assignConfig
		# TODO restart with delay


	def run(self) -> bool:
		"""	Run the http server in a separate thread.
		"""
		if isTCPPortAvailable(Configuration.http_port):
			self.httpActor = BackgroundWorkerPool.newActor(self._run, name='HTTPServer')
			self.httpActor.start()
			return True
		L.logErr(f'Cannot start HTTP server. Port: {Configuration.http_port} already in use.', showStackTrace = False)
		return False
	

	def shutdown(self) -> bool:
		"""	Shutting down the http server.
		"""
		L.isInfo and L.log('HttpServer shut down')
		self.isStopped = True
		return True
	

	def pause(self) -> None:
		"""	Stop handling requests.
		"""
		L.isInfo and L.log('HttpServer paused')
		self.isStopped = True
		
	
	def unpause(self) -> None:
		"""	Continue handling requests.
		"""
		L.isInfo and L.log('HttpServer unpaused')
		self.isStopped = False

	
	def _run(self) -> None:
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
		   				  host = Configuration.http_listenIF, 
						  port = Configuration.http_port, 
						  threads = Configuration.http_wsgi_threadPoolSize,
						  connection_limit = Configuration.http_wsgi_connectionLimit)
				else:
					L.isInfo and L.log(f'HTTP server listening on {Configuration.http_listenIF}:{Configuration.http_port} (flask http)')
					self.flaskApp.run(host = Configuration.http_listenIF, 
									  port = Configuration.http_port,
									  threaded = True,
									  request_handler = ACMERequestHandler,
									  ssl_context = CSE.security.getSSLContextHttp(),
									  debug = False)
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
				CSE.shutdown() # exit the CSE. Cleanup happens in the CSE atexit() handler


	def addEndpoint(self, endpoint:Optional[str] = None, 
						  endpoint_name:Optional[str] = None, 
						  handler:Optional[FlaskHandler] = None, 
						  methods:Optional[list[str]] = None, 
						  strictSlashes:Optional[bool] = True) -> None:
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods = methods, strict_slashes = strictSlashes)


	def _handleRequest(self, path:str, operation:Operation, authResult:AuthorizationResult) -> Response:
		"""	Get and check all the necessary information from the request and
			build the internal strutures. Then, depending on the operation,
			call the associated request handler.
		"""

		def _runRequest(request:CSERequest) -> Result:
			try:
				return CSE.request.handleRequest(request)	# type: ignore[arg-type]
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

			return self._prepareResponse(Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
												request = dissectResult.request, 
												dbg = 'http server not running'))

		if dissectResult.rsc != ResponseStatusCode.UNKNOWN:	# any other value right now indicates an error condition
			# Something went wrong during dissection
			if dissectResult.request:
				CSE.request.recordRequest(dissectResult.request, dissectResult)
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
	def handleGET(self, path:Optional[str] = None) -> Response:
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status = 401)
		L.enableScreenLogging and renameThread('HT_R')
		self._eventHttpRetrieve()
		return self._handleRequest(path, Operation.RETRIEVE, authResult)


	def handlePOST(self, path:Optional[str] = None) -> Response:
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status = 401)
		if self._hasContentType():
			L.enableScreenLogging and renameThread('HT_C')
			self._eventHttpCreate()
			return self._handleRequest(path, Operation.CREATE, authResult)
		else:
			L.enableScreenLogging and renameThread('HT_N')
			self._eventHttpNotify()
			return self._handleRequest(path, Operation.NOTIFY, authResult)


	def handlePUT(self, path:Optional[str] = None) -> Response:
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status = 401)
		L.enableScreenLogging and renameThread('HT_U')
		self._eventHttpUpdate()
		return self._handleRequest(path, Operation.UPDATE, authResult)


	def handleDELETE(self, path:Optional[str] = None) -> Response:
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status = 401)
		L.enableScreenLogging and renameThread('HT_D')
		self._eventHttpDelete()
		return self._handleRequest(path, Operation.DELETE, authResult)


	def handlePATCH(self, path:Optional[str] = None) -> Response:
		"""	Support instead of DELETE for http/1.0.
		"""
		if (authResult := self.handleAuthentication()) == AuthorizationResult.UNAUTHORIZED:
			return Response(status = 401)
		if request.environ.get('SERVER_PROTOCOL') != 'HTTP/1.0':
			return Response(L.logWarn('PATCH method is only allowed for HTTP/1.0. Rejected.'), status = 405)
		L.enableScreenLogging and renameThread('HT_D')
		self._eventHttpDelete()
		return self._handleRequest(path, Operation.DELETE, authResult)


	#########################################################################
	#
	#	Various handlers
	#

	# Redirect request to / to webui
	def redirectRoot(self) -> Response:
		"""	Redirect a request to the webroot to the web UI.
		"""
		if self.isStopped:
			return Response('Service not available', status = 503)
		return flask.redirect(Configuration.webui_root, code = 302)


	def handleStructure(self, path:Optional[str] = 'puml') -> Response:
		"""	Handle a structure request. Return a description of the CSE's current resource
			and registrar / registree deployment.
			An optional parameter 'lvl=<int>' can limit the generated resource tree's depth.
		"""
		if self.isStopped:
			return Response('Service not available', status = 503)
		lvl = request.args.get('lvl', default = 0, type = int)
		if path == 'puml':
			return Response(response = CSE.statistics.getStructurePuml(lvl), headers = self._responseHeaders)
		if path == 'text':
			return Response(response = CSE.console.getResourceTreeText(lvl), headers = self._responseHeaders)
		return Response(response = 'unsupported', status = 422, headers = self._responseHeaders)


	def handleUpperTester(self, path:Optional[str] = None) -> Response:
		"""	Handle a Upper Tester request. See TS-0019 for details.
		"""
		if self.isStopped:
			return Response('Service not available', status = 503)

		# Check, when authentication is enabled, the user is authorized, else return status 401
		if not self.handleAuthentication():
			return Response(status = 401)


		def prepareUTResponse(rcs:ResponseStatusCode, result:str) -> Response:
			"""	Prepare the Upper Tester Response.
			"""
			headers = {}
			headers['Server'] = self.serverID
			headers['X-M2M-RSC'] = str(rcs.value)	# Set the ResponseStatusCode accordingly
			if result:								# Return an optional return value
				headers['X-M2M-UTRSP'] = result
			resp = Response(status = 200 if rcs == ResponseStatusCode.OK else 400, headers = headers)
			L.isDebug and L.logDebug(f'<== Upper Tester Response:') 
			L.isDebug and L.logDebug(f'Headers: \n{str(resp.headers).rstrip()}')
			return resp

		L.enableScreenLogging and renameThread('UT')
		L.isDebug and L.logDebug(f'==> Upper Tester Request:') 
		L.isDebug and L.logDebug(f'Headers: \n{str(request.headers).rstrip()}')
		if request.data:
			L.isDebug and L.logDebug(f'Body: \n{request.json}')

		# Handle special commands
		if (cmd := request.headers.get('X-M2M-UTCMD')) is not None:
			cmd, _, arg = cmd.partition(' ')
			if not (res := CSE.script.run(cmd, arg, metaFilter = [ 'uppertester' ], ignoreCase = True))[0]:
				return prepareUTResponse(ResponseStatusCode.BAD_REQUEST, str(res[1]))
			
			if res[1].type in [SType.tList, SType.tListQuote]:
				_r = ','.join(res[1].raw())
			else:
				_r = res[1].toString(quoteStrings = False, pythonList = True)
			return prepareUTResponse(ResponseStatusCode.OK, _r)

		L.logWarn('UT functionality is not fully supported.')
		return prepareUTResponse(ResponseStatusCode.BAD_REQUEST, None)


	#########################################################################

	#
	#	Send HTTP requests
	#

	operation2method = {
		Operation.CREATE	: requests.post,
		Operation.RETRIEVE	: requests.get,
		Operation.UPDATE 	: requests.put,
		Operation.DELETE 	: requests.delete,
		Operation.NOTIFY 	: requests.post
	}


	def sendHttpRequest(self, request:CSERequest, url:str, ignoreResponse:bool) -> Result:
		"""	Send an http request.
		
			The result is returned in *Result.data*.
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
		hds[Constants.hfOrigin]	= toSPRelative(request.originator)
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
				L.logWarn('No credentials found for HTTP request found')


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
					   data = data,
					   headers = hds,
					   verify = Configuration.http_security_verifyCertificate,
					   timeout = timeout)
		
			# Ignore the response to notifications in some cases
			if ignoreResponse and request.op == Operation.NOTIFY:
				L.isDebug and L.logDebug('HTTP: Ignoring response to notification')
				return createPositiveResponseResult()

			# Construct CSERequest response object from the result
			resp = CSERequest(requestType = RequestType.RESPONSE)
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
		self._eventResponseReceived(resp)
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
			if not CSE.security.validateHttpBasicAuth(parameters['username'], parameters['password']):
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
			if not CSE.security.validateHttpTokenAuth(token):
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

	def _prepareResponse(self, result:Result, 
							   originalRequest:Optional[CSERequest] = None) -> Response:
		"""	Prepare the response for a request. If `request` is given then
			set it for the response.
		"""
		content:str|bytes|JSON = ''
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
			elif csz := CSE.request.getSerializationFromOriginator(originalRequest.originator):
				result.request.ct = csz[0]

			result.request.rqi = originalRequest.rqi
			result.request.rvi = originalRequest.rvi
			result.request.vsi = originalRequest.vsi
			result.request.ec  = originalRequest.ec
			result.request.rset = originalRequest.rset
		
	
		#
		#	Transform request to oneM2M request
		#
		outResult = requestFromResult(result, isResponse = True, originalRequest = originalRequest)

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
		return Response(response = outResult.data, status = statusCode, content_type = cts, headers = headers)


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


		cseRequest 					= CSERequest()
		req:ReqResp 				= {}
		cseRequest.originalData 	= request.data			# get the data first. This marks the request as consumed, just in case that we have to return early
		cseRequest.op 				= operation
		req['op']   				= operation.value		# Needed later for validation

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
			CSE.request.fillAndValidateCSERequest(cseRequest)
		except REQUEST_TIMEOUT as e:
			raise e
		except ResponseException as e:
			e.dbg = f'invalid arguments/attributes: {e.dbg}'
			raise e

		# Here, if everything went okay so far, we have a request to the CSE
		return Result(request = cseRequest)


	_hdrArgument = re.compile(r'^\s*ty\s*=\s*', re.IGNORECASE)
	def _hasContentType(self) -> bool:
		return (ct := request.content_type) is not None and any(re.match(self._hdrArgument, s) is not None for s in ct.split(';'))


##########################################################################
#
#	Own request handler.
#	Actually only to redirect some logging of the http server.
#	This handler does NOT handle requests.
#

class ACMERequestHandler(WSGIRequestHandler):
	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type, message, *args): # type: ignore
		L.enableBindingsLogging and L.isDebug and L.logDebug(f'HTTP: {message % args}')

	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code='-', size='-'): 	# type: ignore
		L.enableBindingsLogging and L.isDebug and L.logDebug(f'HTTP: "{self.requestline}" {size} {code}')

	def log_message(self, format, *args): 	# type: ignore
		L.enableBindingsLogging and L.isDebug and L.logDebug(f'HTTP: {format % args}')
	
