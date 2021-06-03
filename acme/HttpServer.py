#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Server to implement the http part of the oneM2M Mcx communication interface.
#	This manager is the main run-loop for the CSE (when using http).
#

from __future__ import annotations
import json, requests, logging, os, sys, traceback, urllib3
from copy import deepcopy
from typing import Any, Callable, Tuple, Union, Protocol
import flask
from flask import Flask, Request, make_response, request
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON, Conditions
from Types import Operation, CSERequest, RequestHeaders, ContentSerializationType, RequestHandler, Parameters
import CSE, Utils
from Logging import Logging
from resources.Resource import Resource
from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import MultiDict
import ssl
from webUI import WebUI
from helpers.BackgroundWorker import *


#
# Types definitions for the http server
#

FlaskHandler = 	Callable[[str], Response]
""" Type definition for flask handler. """


class HttpServer(object):

	def __init__(self) -> None:

		# Initialize the http server
		# Meaning defaults are automatically provided.
		self.flaskApp			= Flask(CSE.cseCsi)
		self.rootPath			= Configuration.get('http.root')
		self.serverAddress		= Configuration.get('http.address')
		self.listenIF			= Configuration.get('http.listenIF')
		self.port 				= Configuration.get('http.port')
		self.useTLS 			= Configuration.get('cse.security.useTLS')
		self.verifyCertificate	= Configuration.get('cse.security.verifyCertificate')
		self.tlsVersion			= Configuration.get('cse.security.tlsVersion').lower()
		self.caCertificateFile	= Configuration.get('cse.security.caCertificateFile')
		self.caPrivateKeyFile	= Configuration.get('cse.security.caPrivateKeyFile')
		self.webuiRoot 			= Configuration.get('cse.webui.root')
		self.webuiDirectory 	= f'{CSE.rootDirectory}/webui'
		self.hfvRVI				= Configuration.get('cse.releaseVersion')
		self.isStopped			= False

		# request handlers for operations
		self._requestHandlers:RequestHandler = {
			Operation.RETRIEVE	: CSE.request.retrieveRequest,
			Operation.CREATE	: CSE.request.createRequest,
			Operation.UPDATE	: CSE.request.updateRequest,
			Operation.DELETE	: CSE.request.deleteRequest
		}

		self.backgroundActor:BackgroundWorker = None

		self.serverID			= f'ACME {C.version}' 			# The server's ID for http response headers
		self._responseHeaders	= {'Server' : self.serverID}	# Additional headers for other requests

		Logging.log(f'Registering http server root at: {self.rootPath}')
		if self.useTLS:
			Logging.log('TLS enabled. HTTP server serves via https.')


		# Add endpoints

		# self.addEndpoint(self.rootPath + '/', handler=self.handleGET, methods=['GET'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handleGET, methods=['GET'])

		# self.addEndpoint(self.rootPath + '/', handler=self.handlePOST, methods=['POST'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handlePOST, methods=['POST'])

		# self.addEndpoint(self.rootPath + '/', handler=self.handlePUT, methods=['PUT'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handlePUT, methods=['PUT'])

		# self.addEndpoint(self.rootPath + '/', handler=self.handleDELETE, methods=['DELETE'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handleDELETE, methods=['DELETE'])

		# Register the endpoint for the web UI
		# This is done by instancing the otherwise "external" web UI
		self.webui = WebUI(self.flaskApp, 
						   defaultRI=CSE.cseRi, 
						   defaultOriginator=CSE.cseOriginator, 
						   root=self.webuiRoot,
						   webuiDirectory=self.webuiDirectory,
						   version=C.version)

		# Enable the config endpoint
		if Configuration.get('http.enableRemoteConfiguration'):
			configEndpoint = f'{self.rootPath}/__config__'
			Logging.log(f'Registering configuration endpoint at: {configEndpoint}')
			self.addEndpoint(configEndpoint, handler=self.handleConfig, methods=['GET'], strictSlashes=False)
			self.addEndpoint(f'{configEndpoint}/<path:path>', handler=self.handleConfig, methods=['GET', 'PUT'])

		# Enable the config endpoint
		if Configuration.get('http.enableStructureEndpoint'):
			structureEndpoint = f'{self.rootPath}/__structure__'
			Logging.log(f'Registering structure endpoint at: {structureEndpoint}')
			self.addEndpoint(structureEndpoint, handler=self.handleStructure, methods=['GET'], strictSlashes=False)
			self.addEndpoint(f'{structureEndpoint}/<path:path>', handler=self.handleStructure, methods=['GET', 'PUT'])

		# Enable the reset endpoint
		if Configuration.get('http.enableResetEndpoint'):
			resetEndPoint = f'{self.rootPath}/__reset__'
			Logging.log(f'Registering reset endpoint at: {resetEndPoint}')
			self.addEndpoint(resetEndPoint, handler=self.handleReset, methods=['GET'], strictSlashes=False)



		# Add mapping / macro endpoints
		self.mappings = {}
		if (mappings := Configuration.get('server.http.mappings')) is not None:
			# mappings is a list of tuples
			for (k, v) in mappings:
				Logging.log(f'Registering mapping: {self.rootPath}{k} -> {self.rootPath}{v}')
				self.addEndpoint(self.rootPath + k, handler=self.requestRedirect, methods=['GET', 'POST', 'PUT', 'DELETE'])
			self.mappings = dict(mappings)


		# Disable most logs from requests and urllib3 library 
		logging.getLogger("requests").setLevel(logging.WARNING)
		logging.getLogger("urllib3").setLevel(logging.WARNING)
		if not self.verifyCertificate:	# only when we also verify  certificates
			urllib3.disable_warnings()



	def run(self) -> None:
		"""	Run the http server in a separate thread.
		"""
		self.httpActor = BackgroundWorkerPool.newActor(self._run, name='HTTP Server')
		self.httpActor.start()
	

	def shutdown(self) -> bool:
		"""	Shutting down the http server.
		"""
		Logging.log('HttpServer shut down')
		self.isStopped = True
		return True
		
	
	def _run(self) -> None:
		WSGIRequestHandler.protocol_version = "HTTP/1.1"

		# Run the http server. This runs forever.
		# The server can run single-threadedly since some of the underlying
		# components (e.g. TinyDB) may run into problems otherwise.
		if self.flaskApp is not None:
			# Disable the flask banner messages
			cli = sys.modules['flask.cli']
			cli.show_server_banner = lambda *x: None 	# type: ignore
			# Start the server
			try:
				context = None
				if self.useTLS:
					Logging.logDebug(f'Setup SSL context. Certfile: {self.caCertificateFile}, KeyFile:{self.caPrivateKeyFile}, TLS version: {self.tlsVersion}')
					context = ssl.SSLContext(
									{ 	'tls1.1' : ssl.PROTOCOL_TLSv1_1,
										'tls1.2' : ssl.PROTOCOL_TLSv1_2,
										'auto'   : ssl.PROTOCOL_TLS,			# since Python 3.6. Automatically choose the highest protocol version between client & server
									}[self.tlsVersion.lower()]
								)
					context.load_cert_chain(self.caCertificateFile, self.caPrivateKeyFile)
				self.flaskApp.run(host=self.listenIF, 
								  port=self.port,
								  threaded=Configuration.get('http.multiThread'),
								  request_handler=ACMERequestHandler,
								  ssl_context=context,
								  debug=False)
			except Exception as e:
				# No logging for headless, nevertheless print the reason what happened
				if CSE.isHeadless:
					Logging.console(str(e), isError=True)
					#print(str(e))
				Logging.logErr(str(e))
				CSE.shutdown() # exit the CSE. Cleanup happens in the CSE atexit() handler


	def addEndpoint(self, endpoint:str=None, endpoint_name:str=None, handler:FlaskHandler=None, methods:list[str]=None, strictSlashes:bool=True) -> None:
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods=methods, strict_slashes=strictSlashes)


	def _handleRequest(self, path:str, operation:Operation) -> Response:
		"""	Get and check all the necessary information from the request and
			build the internal strutures. Then, depending on the operation,
			call the associated request handler.
		"""
		Logging.logDebug(f'==> {operation.name}: /{path}') 	# path = request.path  w/o the root
		Logging.logDebug(f'Headers: \n{str(request.headers)}')
		httpRequestResult = self._dissectHttpRequest(request, operation, Utils.retrieveIDFromPath(path, CSE.cseRn, CSE.cseCsi))

		if self.isStopped:
			responseResult = Result(rsc=RC.internalServerError, dbg='http server not running	', status=False)
		else:
			try:
				if httpRequestResult.status:
					if operation in [ Operation.CREATE, Operation.UPDATE ]:
						if httpRequestResult.request.ct == ContentSerializationType.CBOR:
							Logging.logDebug(f'Body: \n{Utils.toHex(httpRequestResult.request.data)}\n=>\n{httpRequestResult.request.dict}')
						else:
							Logging.logDebug(f'Body: \n{str(httpRequestResult.request.data)}')
					responseResult = self._requestHandlers[operation](httpRequestResult.request)
				else:
					responseResult = httpRequestResult
			except Exception as e:
				responseResult = self._prepareException(e)
		responseResult.request = httpRequestResult.request

		return self._prepareResponse(responseResult)


	def handleGET(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		CSE.event.httpRetrieve() # type: ignore
		return self._handleRequest(path, Operation.RETRIEVE)


	def handlePOST(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		CSE.event.httpCreate()	# type: ignore
		return self._handleRequest(path, Operation.CREATE)


	def handlePUT(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		CSE.event.httpUpdate()	# type: ignore
		return self._handleRequest(path, Operation.UPDATE)


	def handleDELETE(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		CSE.event.httpDelete()	# type: ignore
		return self._handleRequest(path, Operation.DELETE)


	#########################################################################


	# Handle requests to mapped paths
	def requestRedirect(self, path:str=None) -> Response:
		path = request.path[len(self.rootPath):] if request.path.startswith(self.rootPath) else request.path
		if path in self.mappings:
			Logging.logDebug(f'==> Redirecting to: /{path}')
			CSE.event.httpRedirect()	# type: ignore
			return flask.redirect(self.mappings[path], code=307)
		return Response('', status=404)


	#########################################################################
	#
	#	Various handlers
	#


	# Redirect request to / to webui
	def redirectRoot(self) -> Response:
		"""	Redirect a request to the webroot to the web UI.
		"""
		return flask.redirect(self.webuiRoot, code=302)


	def getVersion(self) -> Response:
		"""	Handle a GET request to return the CSE version.
		"""
		return Response(C.version, headers=self._responseHeaders)


	def handleConfig(self, path:str=None) -> Response:
		"""	Handle a configuration request. This can either be e GET request to query a 
			configuration value, or a PUT request to set a new value to a configuration setting.
			Note, that only a few of configuration settings are supported.
		"""

		def _r(r:str) -> Response:	# just construct a response. Trying to reduce the clutter here
			return Response(r, headers=self._responseHeaders)

		if request.method == 'GET':
			if path == None or len(path) == 0:
				return _r(Configuration.print())
			if Configuration.has(path):
				return _r(str(Configuration.get(path)))
			return _r('')
		elif request.method =='PUT':
			data = request.data.decode('utf-8').rstrip()
			try:
				Logging.logDebug(f'New remote configuration: {path} = {data}')
				if path == 'cse.checkExpirationsInterval':
					if (d := int(data)) < 1:
						return _r('nak')
					Configuration.set(path, d)
					CSE.registration.stopExpirationMonitor()
					CSE.registration.startExpirationMonitor()
					return _r('ack')
				elif path in [ 'cse.req.minet', 'cse.req.maxnet' ]:
					if (d := int(data)) < 1:
							return _r('nak')
					Configuration.set(path, d)
					return _r('ack')

			except:
				return _r('nak')
			return _r('nak')
		return _r('unsupported')


	def handleStructure(self, path:str='puml') -> Response:
		"""	Handle a structure request. Return a description of the CSE's current resource
			and registrar / registree deployment.
			An optional parameter 'lvl=<int>' can limit the generated resource tree's depth.
		"""
		lvl = request.args.get('lvl', default=0, type=int)
		if path == 'puml':
			return Response(response=CSE.statistics.getStructurePuml(lvl), headers=self._responseHeaders)
		if path == 'text':
			return Response(response=CSE.console.getResourceTreeText(lvl), headers=self._responseHeaders)
		return Response(response='unsupported', status=422, headers=self._responseHeaders)


	def handleReset(self, path:str=None) -> Response:
		"""	Handle a CSE reset request.
		"""
		CSE.resetCSE()
		return Response(response='', status=200)


	#########################################################################

	#
	#	Send HTTP requests
	#

	def _prepContent(self, content:bytes|str|Any, ct:ContentSerializationType) -> str:
		if content is None:	return ''
		if isinstance(content, str): return content
		return content.decode('utf-8') if ct == ContentSerializationType.JSON else Utils.toHex(content)


	def sendHttpRequest(self, method:Callable, url:str, originator:str, ty:T=None, data:Any=None, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:	 # type: ignore[type-arg]
		ct = CSE.defaultSerialization if ct is None else ct

		# Set basic headers
		hty = f';ty={int(ty):d}' if ty is not None else ''
		hds = {	'User-Agent'	: self.serverID,
				'Content-Type' 	: f'{ct.toHeader()}{hty}',
				'Accept'		: ct.toHeader(),
				C.hfOrigin	 	: originator,
				C.hfRI 			: Utils.uniqueRI(),
				C.hfRVI			: self.hfvRVI,			# TODO this actually depends in the originator
			   }

		# Add additional headers
		if parameters is not None:
			if C.hfcEC in parameters:				# Event Category
				hds[C.hfEC] = parameters[C.hfcEC]

		# serialize data (only if dictionary, pass on non-dict data)
		content = Utils.serializeData(data, ct) if isinstance(data, dict) else data

		# ! Don't forget: requests are done through the request library, not flask.
		# ! The attribute names are different
		try:
			Logging.logDebug(f'Sending request: {method.__name__.upper()} {url}')
			if ct == ContentSerializationType.CBOR:
				Logging.logDebug(f'Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(content, ct)}\n=>\n{str(data) if data is not None else ""}\n')
			else:
				Logging.logDebug(f'Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(content, ct)}\n')
			
			# Actual sending the request
			r = method(url, data=content, headers=hds, verify=self.verifyCertificate)

			responseCt = ContentSerializationType.getType(r.headers['Content-Type']) if 'Content-Type' in r.headers else ct
			rc = RC(int(r.headers['X-M2M-RSC'])) if 'X-M2M-RSC' in r.headers else RC.internalServerError
			Logging.logDebug(f'Response <== ({str(r.status_code)}):\nHeaders: {str(r.headers)}\nBody: \n{self._prepContent(r.content, responseCt)}\n')
		except Exception as e:
			Logging.logWarn(f'Failed to send request: {str(e)}')
			return Result(rsc=RC.targetNotReachable, dbg='target not reachable')
		return Result(dict=Utils.deserializeData(r.content, responseCt), rsc=rc)
		

	#########################################################################

	def _prepareResponse(self, result:Result) -> Response:
		content:str|bytes = ''

		# Build the headers
		headers = {}
		headers['Server'] = self.serverID						# set server field
		headers['X-M2M-RSC'] = f'{result.rsc}'					# set the response status code
		if result.request.headers.requestIdentifier is not None:
			headers['X-M2M-RI'] = result.request.headers.requestIdentifier
		if result.request.headers.releaseVersionIndicator is not None:
			headers['X-M2M-RVI'] = result.request.headers.releaseVersionIndicator

		# HTTP status code
		statusCode = result.rsc.httpStatusCode()

		#
		# Determine the accept type and encode the content accordinly
		#
		# Look whether there is a accept header in the original request
		if result.request.headers.accept is not None and len(result.request.headers.accept) > 0:
			ct = ContentSerializationType.getType(result.request.headers.accept[0])
		
		# No accept, check originator
		elif len(csz := Utils.getSerializationFromOriginator(result.request.headers.originator)) > 0:
			ct = csz[0]
		
		# Default: configured CSE's default
		else:
			ct = CSE.defaultSerialization
		
		# Assign and encode content accordingly
		headers['Content-Type'] = (cts := ct.toHeader())
		content = result.toData(ct)
				
		# Build and return the response
		if isinstance(content, bytes):
			Logging.logDebug(f'<== Response (RSC: {result.rsc:d}):\nHeaders: {str(headers)}\nBody: \n{Utils.toHex(content)}\n=>\n{str(result.toData())}')
		else:
			Logging.logDebug(f'<== Response (RSC: {result.rsc:d}):\nHeaders: {str(headers)}\nBody: {str(content)}\n')
		return Response(response=content, status=statusCode, content_type=cts, headers=headers)


	def _prepareException(self, e:Exception) -> Result:
		tb = traceback.format_exc()
		Logging.logErr(tb)
		tbs = tb.replace('"', '\\"').replace('\n', '\\n')
		return Result(rsc=RC.internalServerError, dbg=f'encountered exception: {tbs}')


	#########################################################################
	#
	#	HTTP request helper functions
	#


	def _dissectHttpRequest(self, request:Request, operation:Operation, _id:Tuple[str, str, str]) -> Result:
		cseRequest = CSERequest()

		# get the data first. This marks the request as consumed 
		#cseRequest.data = request.get_data(as_text=True)	# alternative: request.data.decode("utf-8")
		#cseRequest.data = request.data.decode("utf-8")		# alternative: request.get_data(as_text=True)
		cseRequest.data = request.data

		# handle ID's 
		cseRequest.id, cseRequest.csi, cseRequest.srn = _id

		# Copy the original request headers
		res = self._getRequestHeaders(request)
		cseRequest.headers = res.data	# copy the headers
		if res.rsc != RC.OK:			# but still, something might be wrong
			return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)

		# No ID, return immediately 
		if cseRequest.id is None and cseRequest.srn is None:
			return Result(rsc=RC.notFound, request=cseRequest, dbg='missing identifier', status=False)
		
		# Extract request arguments
		try:
			# copy request arguments for greedy attributes checking
			args = request.args.copy() 	# type: ignore [no-untyped-call]
			
			# Do some special handling for those arguments that could occur multiple
			# times in the args MultiDict. They are collected together in a single list
			# and added again to args.
			if not (resm := self._extractMultipleArgs(args, 'ty'))[0]:
				Result(rsc=RC.badRequest, request=cseRequest, dbg=resm[1], status=False)
			if not (resm := self._extractMultipleArgs(args, 'cty'))[0]:
				Result(rsc=RC.badRequest, request=cseRequest, dbg=resm[1], status=False)
			if not (resm := self._extractMultipleArgs(args, 'lbl', validate=False))[0]:
				Result(rsc=RC.badRequest, request=cseRequest, dbg=resm[1], status=False)
			
			cseRequest.args, msg = Utils.getRequestArguments(args, operation)
			if cseRequest.args is None:
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=msg, status=False)
		except Exception as e:
			return Result(rsc=RC.invalidArguments, request=cseRequest, dbg=f'invalid arguments ({str(e)})', status=False)
		cseRequest.originalArgs	= deepcopy(request.args)

		# De-Serialize the content
		if cseRequest.data is not None and len(cseRequest.data) > 0:
			try:
				cseRequest.ct = ContentSerializationType.getType(cseRequest.headers.contentType, default=CSE.defaultSerialization)
				if (_d := Utils.deserializeData(cseRequest.data, cseRequest.ct)) is None:
					return Result(rsc=RC.unsupportedMediaType, request=cseRequest, dbg=f'Unsupported media type for content-type: {cseRequest.headers.contentType}', status=False)
				cseRequest.dict = _d
			except Exception as e:
				Logging.logWarn('Bad request (malformed content?)')
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'Malformed content? {str(e)}', status=False)
		
		# Check whether content is empty for UPDATE or CREATE -> Error
		elif operation in [ Operation.CREATE, Operation.UPDATE ]:
			Logging.logWarn(dbg := f'Missing content for operation: {operation.name}')
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=dbg, status=False)
				
		return Result(request=cseRequest, status=True)


	def _extractMultipleArgs(self, args:MultiDict, argName:str, validate:bool=True) -> Tuple[bool, str]:
		"""	Get multi-arguments. Remove the found arguments from the original list, but add the new list again with the argument name.
		"""
		lst = []
		for e in args.getlist(argName):
			for es in (t := e.split()):	# check for number
				if validate:
					if not CSE.validator.validateRequestArgument(argName, es).status:
						return False, f'error validating "{argName}" argument(s)'
			lst.extend(t)
		args.poplist(argName)	# type: ignore [no-untyped-call] # perhaps even multiple times
		if len(lst) > 0:
			args[argName] = lst
		return True, None

		
	def _getRequestHeaders(self, request:Request) -> Result:
		"""	Extract the Request's header and put them into a CSERequest object.
		"""
		# TODO move a couple of check to general request check functions. Also for MQTT etc

		rh 								= RequestHeaders()
		rh.originator 					= self._requestHeaderField(request, C.hfOrigin)
		rh.requestIdentifier			= self._requestHeaderField(request, C.hfRI)
		rh.requestExpirationTimestamp 	= self._requestHeaderField(request, C.hfRET)
		rh.responseExpirationTimestamp 	= self._requestHeaderField(request, C.hfRST)
		rh.operationExecutionTime 		= self._requestHeaderField(request, C.hfOET)
		rh.releaseVersionIndicator 		= self._requestHeaderField(request, C.hfRVI)

		if (rtu := self._requestHeaderField(request, C.hfRTU)) is not None:			# handle rtu list
			rh.responseTypeNUs = rtu.split('&')

		# Check Release Version
		if rh.releaseVersionIndicator is None:
			return Result(rsc=RC.badRequest, data=rh, dbg=f'Release Version Indicator parameter is mandatory in request')
		if rh.releaseVersionIndicator not in C.supportedReleaseVersions:
			return Result(rsc=RC.releaseVersionNotSupported, data=rh, dbg=f'Release version not supported: {rh.releaseVersionIndicator}')


		# content-type and accept
		rh.contentType 	= request.content_type
		rh.accept		= [ mt for mt, _ in request.accept_mimetypes ]	# get (multiple) accept headers from MIMEType[(x,nr)]

		if rh.contentType is not None:
			if not rh.contentType.startswith(tuple(C.supportedContentHeaderFormat)):
				rh.contentType 	= None
			else:
				p 				= rh.contentType.partition(';')	# always returns a 3-tuple
				rh.contentType 	= p[0] # content-type
				t  				= p[2].partition('=')[2]
				if len(t) > 0:	# check only if there is a resource type
					if t.isdigit() and (_t := int(t)) and T.has(_t):
						rh.resourceType = T(_t)
					else:
						return Result(rsc=RC.badRequest, data=rh, dbg=f'Unknown resource type: {t}')
		
		# accept
		rh.accept = request.headers.getlist('accept')
		rh.accept = [ a for a in rh.accept if a != '*/*' ]
		# if ((l := len(rh.accept)) == 1 and '*/*' in rh.accept) or l == 0:
		# 	rh.accept = [ CSE.defaultSerialization.toHeader() ]

		# perform some validitions

		if rh.releaseVersionIndicator is None:
			Logging.logDebug(dbg := 'Release Version Indicator paraneter is mandatory in request')
			return Result(data=rh, rsc=RC.badRequest, dbg=dbg)

		if rh.requestIdentifier is None:
			Logging.logDebug(dbg := 'Request Identifier parameter is mandatory in request')
			return Result(data=rh, rsc=RC.badRequest, dbg=dbg)

		# Test whether originator is present
		if rh.originator is None and not (rh.resourceType == T.AE and request.method == 'POST'):
			Logging.logDebug(dbg := 'From/Originator parameter is mandatory in request')
			return Result(data=rh, rsc=RC.badRequest, dbg=dbg)		
		
		# Test for request expiration
		if rh.requestExpirationTimestamp is not None:
			if (ts := Utils.fromAbsRelTimestamp(rh.requestExpirationTimestamp)) == 0.0:
				Logging.logDebug(dbg := 'Error in provided Request Expiration Timestamp')
				return Result(data=rh, rsc=RC.badRequest, dbg=dbg)
			if ts < Utils.utcTime():
				Logging.logDebug(dbg := 'Request timeout')
				return Result(data=rh, rsc=RC.requestTimeout, dbg=dbg)
			rh.requestExpirationTimestamp = Utils.toISO8601Date(ts)	# Re-assign "real" ISO8601 timestamp

		return Result(data=rh, rsc=RC.OK)


	def _requestHeaderField(self, request:Request, field:str) -> str:
		"""	Return the value of a specific Request header, or `None` if not found.
		""" 
		if not request.headers.has_key(field):
			return None
		return request.headers.get(field)

##########################################################################
#
#	Own request handler.
#	Actually only to redirect some logging of the http server.
#	This handler does NOT handle requests.
#

class ACMERequestHandler(WSGIRequestHandler):
	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type, message, *args): # type: ignore
		Logging.logDebug(message % args)
		return
		# Logging.log(f'{self.address_string()} {message % args}\n')

	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code='-', size='-'): 	# type: ignore
		Logging.logDebug(f'"{self.requestline}" {size} {code}')
		return

	def log_message(self, format, *args): 	# type: ignore
		Logging.logDebug(format % args)
		return
	

