#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Server to implement the http part of the oneM2M Mcx communication interface.
#

from __future__ import annotations
import logging, sys, traceback, urllib3
from copy import deepcopy
from typing import Any, Callable, Tuple, cast
import flask
from flask import Flask, Request, make_response, request
from urllib3.exceptions import RequestError
from Configuration import Configuration
from Constants import Constants as C
from Types import ReqResp, ResourceTypes as T, Result, ResponseCode as RC, JSON, Conditions
from Types import Operation, CSERequest, RequestHeaders, ContentSerializationType, RequestHandler, Parameters, RequestArguments, FilterUsage, FilterOperation, DesiredIdentifierResultType, ResultContentType, ResponseType
import CSE, Utils
from Logging import Logging as L, LogLevel
from resources.Resource import Resource
from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import MultiDict
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
		self.webuiRoot 			= Configuration.get('cse.webui.root')
		self.webuiDirectory 	= f'{CSE.rootDirectory}/webui'
		self.hfvRVI				= Configuration.get('cse.releaseVersion')
		self.isStopped			= False


		self.backgroundActor:BackgroundWorker = None

		self.serverID			= f'ACME {C.version}' 			# The server's ID for http response headers
		self._responseHeaders	= {'Server' : self.serverID}	# Additional headers for other requests

		L.isInfo and L.log(f'Registering http server root at: {self.rootPath}')
		if CSE.security.useTLS:
			L.isInfo and L.log('TLS enabled. HTTP server serves via https.')


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
			L.isInfo and L.log(f'Registering configuration endpoint at: {configEndpoint}')
			self.addEndpoint(configEndpoint, handler=self.handleConfig, methods=['GET'], strictSlashes=False)
			self.addEndpoint(f'{configEndpoint}/<path:path>', handler=self.handleConfig, methods=['GET', 'PUT'])

		# Enable the config endpoint
		if Configuration.get('http.enableStructureEndpoint'):
			structureEndpoint = f'{self.rootPath}/__structure__'
			L.isInfo and L.log(f'Registering structure endpoint at: {structureEndpoint}')
			self.addEndpoint(structureEndpoint, handler=self.handleStructure, methods=['GET'], strictSlashes=False)
			self.addEndpoint(f'{structureEndpoint}/<path:path>', handler=self.handleStructure, methods=['GET', 'PUT'])

		# Enable the reset endpoint
		if Configuration.get('http.enableResetEndpoint'):
			resetEndPoint = f'{self.rootPath}/__reset__'
			L.isInfo and L.log(f'Registering reset endpoint at: {resetEndPoint}')
			self.addEndpoint(resetEndPoint, handler=self.handleReset, methods=['GET'], strictSlashes=False)



		# Add mapping / macro endpoints
		self.mappings = {}
		if (mappings := Configuration.get('server.http.mappings')) is not None:
			# mappings is a list of tuples
			for (k, v) in mappings:
				L.isInfo and L.log(f'Registering mapping: {self.rootPath}{k} -> {self.rootPath}{v}')
				self.addEndpoint(self.rootPath + k, handler=self.requestRedirect, methods=['GET', 'POST', 'PUT', 'DELETE'])
			self.mappings = dict(mappings)


		# Disable most logs from requests and urllib3 library 
		logging.getLogger("requests").setLevel(LogLevel.WARNING)
		logging.getLogger("urllib3").setLevel(LogLevel.WARNING)
		if not CSE.security.verifyCertificate:	# only when we also verify  certificates
			urllib3.disable_warnings()
		if L.isInfo: L.log('HTTP Server initialized')



	def run(self) -> None:
		"""	Run the http server in a separate thread.
		"""
		self.httpActor = BackgroundWorkerPool.newActor(self._run, name='HTTPServer')
		self.httpActor.start()
	

	def shutdown(self) -> bool:
		"""	Shutting down the http server.
		"""
		L.isInfo and L.log('HttpServer shut down')
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
				self.flaskApp.run(host=self.listenIF, 
								  port=self.port,
								  threaded=Configuration.get('http.multiThread'),
								  request_handler=ACMERequestHandler,
								  ssl_context=CSE.security.getSSLContext(),
								  debug=False)
			except Exception as e:
				# No logging for headless, nevertheless print the reason what happened
				if CSE.isHeadless:
					L.console(str(e), isError=True)
					#print(str(e))
				L.logErr(str(e))
				CSE.shutdown() # exit the CSE. Cleanup happens in the CSE atexit() handler


	def addEndpoint(self, endpoint:str=None, endpoint_name:str=None, handler:FlaskHandler=None, methods:list[str]=None, strictSlashes:bool=True) -> None:
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods=methods, strict_slashes=strictSlashes)


	def _handleRequest(self, path:str, operation:Operation) -> Response:
		"""	Get and check all the necessary information from the request and
			build the internal strutures. Then, depending on the operation,
			call the associated request handler.
		"""
		L.isDebug and L.logDebug(f'==> {operation.name}: /{path}') 	# path = request.path  w/o the root
		L.isDebug and L.logDebug(f'Headers: \n{str(request.headers)}')
		httpRequestResult = self._dissectHttpRequest(request, operation, Utils.retrieveIDFromPath(path, CSE.cseRn, CSE.cseCsi))

		if self.isStopped:
			responseResult = Result(rsc=RC.internalServerError, dbg='http server not running', status=False)
		else:
			try:
				if httpRequestResult.status:
					if operation in [ Operation.CREATE, Operation.UPDATE ]:
						if httpRequestResult.request.ct == ContentSerializationType.CBOR:
							L.isDebug and L.logDebug(f'Body: \n{Utils.toHex(cast(bytes, httpRequestResult.request.data))}\n=>\n{httpRequestResult.request.dict}')
						else:
							L.isDebug and L.logDebug(f'Body: \n{str(httpRequestResult.request.data)}')
					responseResult = CSE.request.handleRequest(operation, httpRequestResult.request)
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
			L.isDebug and L.logDebug(f'==> Redirecting to: /{path}')
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
				L.isDebug and L.logDebug(f'New remote configuration: {path} = {data}')
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
			L.isDebug and L.logDebug(f'Sending request: {method.__name__.upper()} {url}')
			if ct == ContentSerializationType.CBOR:
				L.isDebug and L.logDebug(f'Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(content, ct)}\n=>\n{str(data) if data is not None else ""}\n')
			else:
				L.isDebug and L.logDebug(f'Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(content, ct)}\n')
			
			# Actual sending the request
			r = method(url, data=content, headers=hds, verify=CSE.security.verifyCertificate)

			responseCt = ContentSerializationType.getType(r.headers['Content-Type']) if 'Content-Type' in r.headers else ct
			rc = RC(int(r.headers['X-M2M-RSC'])) if 'X-M2M-RSC' in r.headers else RC.internalServerError
			L.isDebug and L.logDebug(f'Response <== ({str(r.status_code)}):\nHeaders: {str(r.headers)}\nBody: \n{self._prepContent(r.content, responseCt)}\n')
		except Exception as e:
			L.isDebug and L.logWarn(f'Failed to send request: {str(e)}')
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
			L.isDebug and L.logDebug(f'<== Response (RSC: {result.rsc:d}):\nHeaders: {str(headers)}\nBody: \n{Utils.toHex(content)}\n=>\n{str(result.toData())}')
		else:
			L.isDebug and L.logDebug(f'<== Response (RSC: {result.rsc:d}):\nHeaders: {str(headers)}\nBody: {str(content)}\n')
		return Response(response=content, status=statusCode, content_type=cts, headers=headers)


	def _prepareException(self, e:Exception) -> Result:
		tb = traceback.format_exc()
		L.logErr(tb, exc=e)
		tbs = tb.replace('"', '\\"').replace('\n', '\\n')
		return Result(rsc=RC.internalServerError, dbg=f'encountered exception: {tbs}')


	#########################################################################
	#
	#	HTTP request helper functions
	#

	def _dissectHttpRequest(self, request:Request, operation:Operation, _id:Tuple[str, str, str]) -> Result:
		"""	Dissect an HTTP request. Combine headers and contents into a single structure. Result is returned in Result.request.
		"""

		# def extractMultipleArgs(args:MultiDict, argName:str, validate:bool=True) -> Tuple[bool, str]:
		# 	"""	Get multi-arguments. Remove the found arguments from the original list, but add the new list again with the argument name.
		# 	"""
		# 	lst = []
		# 	for e in args.getlist(argName):
		# 		for es in (t := e.split()):	# check for number
		# 			if validate:
		# 				if not CSE.validator.validateRequestArgument(argName, es).status:
		# 					return False, f'error validating "{argName}" argument(s)'
		# 		lst.extend(t)
		# 	args.poplist(argName)	# type: ignore [no-untyped-call] # perhaps even multiple times
		# 	if len(lst) > 0:
		# 		args[argName] = lst
		# 	return True, None

		def extractMultipleArgs(args:MultiDict, argName:str) -> None:
			"""	Get multi-arguments. Remove the found arguments from the original list, but add the new list again with the argument name.
			"""
			lst = [ t for sublist in args.getlist(argName) for t in sublist.split() ]
			args.poplist(argName)	# type: ignore [no-untyped-call] # perhaps even multiple times
			if len(lst) > 0:
				args[argName] = lst


		def requestHeaderField(request:Request, field:str) -> str:
			"""	Return the value of a specific Request header, or `None` if not found.
			""" 
			if not request.headers.has_key(field):
				return None
			return request.headers.get(field)


		cseRequest = CSERequest()
		cseRequest.headers = RequestHeaders()
		req:ReqResp = {}


		# get the data first. This marks the request as consumed, just in case that we have to return early
		cseRequest.data = request.data

		# handle ID's 
		cseRequest.id, cseRequest.csi, cseRequest.srn = _id

		# operator and target
		req['op']   = operation.value
		req['to']   = cseRequest.id

		# Copy and parse the original request headers
		if (f := requestHeaderField(request, C.hfOrigin)) is not None:
			req['fr'] = f
		if (f := requestHeaderField(request, C.hfRI)) is not None:
			req['rqi'] = f
		if (f := requestHeaderField(request, C.hfRET)) is not None:
			req['rqet'] = f
		if (f := requestHeaderField(request, C.hfRST)) is not None:
			req['rset'] = f
		if (f := requestHeaderField(request, C.hfOET)) is not None:
			req['oet'] = f
		if (f := requestHeaderField(request, C.hfRVI)) is not None:
			req['rvi'] = f
		if (rtu := requestHeaderField(request, C.hfRTU)) is not None:			# handle rtu as a list
			req['rtu'] = rtu.split('&')
		
		# parse and extract content-type header
		cseRequest.headers.contentType	= request.content_type
		L.isDebug and L.logDebug(str(cseRequest.headers))
		if cseRequest.headers.contentType is not None:
			if not cseRequest.headers.contentType.startswith(tuple(C.supportedContentHeaderFormat)):
				cseRequest.headers.contentType 	= None
			else:
				p = cseRequest.headers.contentType.partition(';')	# always returns a 3-tuple
				cseRequest.headers.contentType = p[0] 				# content-type
				t = p[2].partition('=')[2]
				if len(t) > 0:
					req['ty'] = t

				# if len(t) > 0:										# check only if there is a resource type
				# 	if t.isdigit() and (_t := int(t)):
				# 		req['ty'] = _t
		
		# parse accept header
		cseRequest.headers.accept = request.headers.getlist('accept')
		cseRequest.headers.accept = [ a for a in cseRequest.headers.accept if a != '*/*' ]

		# Extract further request arguments from the http request
		filterCriteria:ReqResp = {}

		# copy request arguments for greedy attributes checking
		args = request.args.copy() 	# type: ignore [no-untyped-call]
		
		# Do some special handling for those arguments that could occur multiple
		# times in the args MultiDict. They are collected together in a single list
		# and added again to args.

		# TODO validation!!!
		extractMultipleArgs(args, 'ty')
		if 'ty' in args:	# make ints out of the strings
			args['ty'] = [ int(t) for t in args['ty'] ]	# This should work since the validation already happened in the extract method
		extractMultipleArgs(args, 'cty')
		extractMultipleArgs(args, 'lbl')
		
		# Now, handle the rest of the arguments
		cseRequest.args, cseRequest.op, dbg = self.getRequestArguments(args, operation)
		if cseRequest.args is None:
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=dbg, status=False)
		
		cseRequest.originalArgs	= deepcopy(request.args)
		# add all the args to the request
		filterCriteria['fu']    = cseRequest.args.fu
		filterCriteria['drt']   = cseRequest.args.drt
		filterCriteria['fo']    = cseRequest.args.fo
		filterCriteria['rcn']   = cseRequest.args.rcn
		filterCriteria['rt']    = cseRequest.args.rt
		filterCriteria['rp']    = cseRequest.args.rp
		filterCriteria['rpts']  = cseRequest.args.rpts
		filterCriteria['rp']    = cseRequest.args.rp

		for k,v in cseRequest.args.handling.items():
			filterCriteria[k]   = v
		for k,v in cseRequest.args.conditions.items():
			filterCriteria[k]   = v
		for k,v in cseRequest.args.attributes.items():
			filterCriteria[k]   = v
		
		if len(filterCriteria) > 0:
			req['fc'] = filterCriteria

		# De-Serialize the content
		if not (res := CSE.request.deserializeContent(cseRequest.data, cseRequest.headers.contentType, operation)).status:
			return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
		
		# Remove 'None' fields *before* adding the pc, because the pc may contain 'None' fields that need to be preserved
		req = Utils.removeNoneValuesFromDict(req)

		# Add the primitive contant
		req['pc'] = res.data[0]
		cseRequest.ct = res.data[1]

		# finally store the oneM2M request object to the cseRequest
		cseRequest.req = req
				
		L.logWarn(str(cseRequest))
		try:
			if not (res := CSE.request.fillAndValidateCSERequest(cseRequest)).status:
				return res
		except Exception as e:
			return Result(rsc=RC.invalidArguments, request=cseRequest, dbg=f'invalid arguments ({str(e)})', status=False)
		L.logWarn(str(cseRequest))

		return Result(request=cseRequest, status=True)



	def getRequestArguments(self, args:dict, operation:Operation=Operation.RETRIEVE) -> Tuple[RequestArguments, Operation, str]:
		"""	Get the request arguments, or meaningful defaults.
			Only a subset is supported yet.

			The `operation` might have been updated and is therefore returned as well.
		"""
		result = RequestArguments()

		# FU - Filter Usage
		result.fu  = args.get('fu')
		result.drt = args.get('drt')
		result.fo  = args.get('fo')
		result.rcn = args.get('rcn')






		# RT - Response Type
		if (rt := args.get('rt')) is not None: 
			if not (res := CSE.validator.validateRequestArgument('rt', rt)).status:
				return None, Operation.NA, f'error validating "rt" argument ({res.dbg})'
			try:
				rt = ResponseType(int(rt))
			except ValueError as exc:
				return None, Operation.NA, f'"{rt}" is not a valid value for rt'
			del args['rt']
		else:
			rt = ResponseType.blockingRequest
		result.rt = rt

		# RP - Result Persistence
		if (rp := args.get('rp')) is not None: 
			if not (res := CSE.validator.validateRequestArgument('rp', rp)).status:
				return None, Operation.NA, f'error validating "rp" argument ({res.dbg})'
			if (rpts := Utils.toISO8601Date(Utils.fromAbsRelTimestamp(rp))) == 0.0:
				return None, Operation.NA, f'"{rp}" is not a valid value for rp'
			del args['rp']
		else:
			rp = None
			rpts = None
		result.rp = rp
		result.rpts = rpts

		# handling conditions
		handling:Conditions = { }
		for c in ['lim', 'lvl', 'ofst']:	# integer parameters
			if c in args:
				v = args[c]
				if not CSE.validator.validateRequestArgument(c, v).status:
					return None, Operation.NA, f'error validating "{c}" argument'
				handling[c] = int(v)
				del args[c]
		for c in ['arp']:					# string parameters
			if c in args:
				v = args[c]
				if not CSE.validator.validateRequestArgument(c, v).status:
					return None, Operation.NA, f'error validating "{c}" argument'
				handling[c] = v # string
				del args[c]
		result.handling = handling

		# conditions
		conditions:Conditions = {}

		# Extract and store other arguments
		for c in ['crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr']:
			if (v := args.get(c)) is not None:
				if not CSE.validator.validateRequestArgument(c, v).status:
					return None, Operation.NA, f'error validating "{c}" argument'
				conditions[c] = v
				del args[c]
		
		# Copy multipe arguments. They have been aggregated into single lists before.
		for c in [ 'ty', 'cty', 'lbl' ]:
			if (v := args.get(c)) is not None:
				conditions[c] = v if isinstance(v, list) else [v]	#hack to add a single value as a list
				del args[c]

		result.conditions = conditions

		# all remaining arguments are treated as matching attributes
		for arg, val in args.items():
			if not CSE.validator.validateRequestArgument(arg, val).status:
				return None, Operation.NA, f'error validating (unknown?) "{arg}" argument)'
		
		# all arguments have passed, so add the remaining 
		# TODO exclude a couple of them
		for k,v in args.items():
			result.attributes[k] = v

		# Finally return the collected arguments
		return result, operation, None
	


	# def getRequestArguments(self, args:dict, operation:Operation=Operation.RETRIEVE) -> Tuple[RequestArguments, Operation, str]:
	# 	"""	Get the request arguments, or meaningful defaults.
	# 		Only a subset is supported yet.

	# 		The `operation` might have been updated and is therefore returned as well.
	# 	"""
	# 	result = RequestArguments()

	# 	# FU - Filter Usage
	# 	if (fu := args.get('fu')) is not None:
	# 		if not CSE.validator.validateRequestArgument('fu', fu).status:
	# 			return None, Operation.NA, 'error validating "fu" argument'
	# 		try:
	# 			fu = FilterUsage(int(fu))
	# 		except ValueError as exc:
	# 			return None, Operation.NA, f'"{fu}" is not a valid value for fu'
	# 		del args['fu']
	# 	else:
	# 		fu = FilterUsage.conditionalRetrieval
	# 	if fu == FilterUsage.discoveryCriteria and operation == Operation.RETRIEVE:
	# 		operation = Operation.DISCOVERY
	# 	result.fu = fu

	# 	# DRT - Desired Identifier Result Type
	# 	if (drt := args.get('drt')) is not None: # 1=strucured, 2=unstructured
	# 		if not CSE.validator.validateRequestArgument('drt', drt).status:
	# 			return None, Operation.NA, 'error validating "drt" argument'
	# 		try:
	# 			drt = DesiredIdentifierResultType(int(drt))
	# 		except ValueError as exc:
	# 			return None, Operation.NA, f'"{drt}" is not a valid value for drt'
	# 		del args['drt']
	# 	else:
	# 		drt = DesiredIdentifierResultType.structured
	# 	result.drt = drt

	# 	# FO - Filter Operation
	# 	if (fo := args.get('fo')) is not None: # 1=AND, 2=OR
	# 		if not CSE.validator.validateRequestArgument('fo', fo).status:
	# 			return None, Operation.NA, 'error validating "fo" argument'
	# 		try:
	# 			fo = FilterOperation(int(fo))
	# 		except ValueError as exc:
	# 			return None, Operation.NA, f'"{fo}" is not a valid value for fo'
	# 		del args['fo']
	# 	else:
	# 		fo = FilterOperation.AND # default
	# 	result.fo = fo

	# 	# RCN Result Content Type
	# 	if (rcn := args.get('rcn')) is not None: 
	# 		if not CSE.validator.validateRequestArgument('rcn', rcn).status:
	# 			return None, Operation.NA, 'error validating "rcn" argument'
	# 		rcn = int(rcn)
	# 		del args['rcn']
	# 	else:
	# 		if fu != FilterUsage.discoveryCriteria:
	# 			# Different defaults for each operation
	# 			if operation in [ Operation.RETRIEVE, Operation.CREATE, Operation.UPDATE ]:
	# 				rcn = ResultContentType.attributes
	# 			elif operation == Operation.DELETE:
	# 				rcn = ResultContentType.nothing
	# 		else:
	# 			# discovery-result-references as default for Discovery operation
	# 			rcn = ResultContentType.discoveryResultReferences

	# 	# Check value of rcn depending on operation
	# 	if operation == Operation.RETRIEVE and rcn not in [ ResultContentType.attributes,
	# 														ResultContentType.attributesAndChildResources,
	# 														ResultContentType.attributesAndChildResourceReferences,
	# 														ResultContentType.childResourceReferences,
	# 														ResultContentType.childResources,
	# 														ResultContentType.originalResource ]:
	# 		return None, Operation.NA, f'rcn: {rcn:d} not allowed in RETRIEVE operation'
	# 	elif operation == Operation.DISCOVERY and rcn not in [ ResultContentType.childResourceReferences,
	# 														ResultContentType.discoveryResultReferences ]:
	# 		return None, Operation.NA, f'rcn: {rcn:d} not allowed in DISCOVERY operation'
	# 	elif operation == Operation.CREATE and rcn not in [ ResultContentType.attributes,
	# 														ResultContentType.modifiedAttributes,
	# 														ResultContentType.hierarchicalAddress,
	# 														ResultContentType.hierarchicalAddressAttributes,
	# 														ResultContentType.nothing ]:
	# 		return None, Operation.NA, f'rcn: {rcn:d} not allowed in CREATE operation'
	# 	elif operation == Operation.UPDATE and rcn not in [ ResultContentType.attributes,
	# 														ResultContentType.modifiedAttributes,
	# 														ResultContentType.nothing ]:
	# 		return None, Operation.NA, f'rcn: {rcn:d} not allowed in UPDATE operation'
	# 	elif operation == Operation.DELETE and rcn not in [ ResultContentType.attributes,
	# 														ResultContentType.nothing,
	# 														ResultContentType.attributesAndChildResources,
	# 														ResultContentType.childResources,
	# 														ResultContentType.attributesAndChildResourceReferences,
	# 														ResultContentType.childResourceReferences ]:
	# 		return None, Operation.NA, f'rcn:  not allowed DELETE operation'

	# 	result.rcn = ResultContentType(rcn)

	# 	# RT - Response Type
	# 	if (rt := args.get('rt')) is not None: 
	# 		if not (res := CSE.validator.validateRequestArgument('rt', rt)).status:
	# 			return None, Operation.NA, f'error validating "rt" argument ({res.dbg})'
	# 		try:
	# 			rt = ResponseType(int(rt))
	# 		except ValueError as exc:
	# 			return None, Operation.NA, f'"{rt}" is not a valid value for rt'
	# 		del args['rt']
	# 	else:
	# 		rt = ResponseType.blockingRequest
	# 	result.rt = rt

	# 	# RP - Result Persistence
	# 	if (rp := args.get('rp')) is not None: 
	# 		if not (res := CSE.validator.validateRequestArgument('rp', rp)).status:
	# 			return None, Operation.NA, f'error validating "rp" argument ({res.dbg})'
	# 		if (rpts := Utils.toISO8601Date(Utils.fromAbsRelTimestamp(rp))) == 0.0:
	# 			return None, Operation.NA, f'"{rp}" is not a valid value for rp'
	# 		del args['rp']
	# 	else:
	# 		rp = None
	# 		rpts = None
	# 	result.rp = rp
	# 	result.rpts = rpts

	# 	# handling conditions
	# 	handling:Conditions = { }
	# 	for c in ['lim', 'lvl', 'ofst']:	# integer parameters
	# 		if c in args:
	# 			v = args[c]
	# 			if not CSE.validator.validateRequestArgument(c, v).status:
	# 				return None, Operation.NA, f'error validating "{c}" argument'
	# 			handling[c] = int(v)
	# 			del args[c]
	# 	for c in ['arp']:					# string parameters
	# 		if c in args:
	# 			v = args[c]
	# 			if not CSE.validator.validateRequestArgument(c, v).status:
	# 				return None, Operation.NA, f'error validating "{c}" argument'
	# 			handling[c] = v # string
	# 			del args[c]
	# 	result.handling = handling

	# 	# conditions
	# 	conditions:Conditions = {}

	# 	# Extract and store other arguments
	# 	for c in ['crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr']:
	# 		if (v := args.get(c)) is not None:
	# 			if not CSE.validator.validateRequestArgument(c, v).status:
	# 				return None, Operation.NA, f'error validating "{c}" argument'
	# 			conditions[c] = v
	# 			del args[c]
		
	# 	# Copy multipe arguments. They have been aggregated into single lists before.
	# 	for c in [ 'ty', 'cty', 'lbl' ]:
	# 		if (v := args.get(c)) is not None:
	# 			conditions[c] = v if isinstance(v, list) else [v]	#hack to add a single value as a list
	# 			del args[c]

	# 	result.conditions = conditions

	# 	# all remaining arguments are treated as matching attributes
	# 	for arg, val in args.items():
	# 		if not CSE.validator.validateRequestArgument(arg, val).status:
	# 			return None, Operation.NA, f'error validating (unknown?) "{arg}" argument)'
		
	# 	# all arguments have passed, so add the remaining 
	# 	# TODO exclude a couple of them
	# 	for k,v in args.items():
	# 		result.attributes[k] = v

	# 	# Finally return the collected arguments
	# 	return result, operation, None
	


##########################################################################
#
#	Own request handler.
#	Actually only to redirect some logging of the http server.
#	This handler does NOT handle requests.
#

class ACMERequestHandler(WSGIRequestHandler):
	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type, message, *args): # type: ignore
		L.isDebug and L.logDebug(message % args)
		return
		# L.isDebug and L.log(f'{self.address_string()} {message % args}\n')

	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code='-', size='-'): 	# type: ignore
		L.isDebug and L.logDebug(f'"{self.requestline}" {size} {code}')
		return

	def log_message(self, format, *args): 	# type: ignore
		L.isDebug and L.logDebug(format % args)
		return
	

