#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Server to implement the http part of the oneM2M Mcx communication interface.
#

from __future__ import annotations
import logging, sys, urllib3
from copy import deepcopy
from typing import Any, Callable, cast

import flask
from flask import Flask, Request, make_response, request
from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import MultiDict

from etc.Constants import Constants as C
from etc.Types import ReqResp, ResourceTypes as T, Result, ResponseCode as RC, JSON
from etc.Types import Operation, CSERequest, ContentSerializationType, Parameters
from services.Configuration import Configuration
from resources.Resource import Resource
import services.CSE as CSE, etc.Utils as Utils, etc.RequestUtils as RequestUtils
from services.Logging import Logging as L, LogLevel
from webui.webUI import WebUI
import helpers.TextTools
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
		self.webuiDirectory 	= f'{CSE.rootDirectory}/acme/webui'
		self.hfvRVI				= Configuration.get('cse.releaseVersion')
		self.isStopped			= False


		self.backgroundActor:BackgroundWorker = None

		self.serverID			= f'ACME {C.version}' 			# The server's ID for http response headers
		self._responseHeaders	= {'Server' : self.serverID}	# Additional headers for other requests

		L.isInfo and L.log(f'Registering http server root at: {self.rootPath}')
		if CSE.security.useTLSHttp:
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
		if mappings := Configuration.get('server.http.mappings'):
			# mappings is a list of tuples
			for (k, v) in mappings:
				L.isInfo and L.log(f'Registering mapping: {self.rootPath}{k} -> {self.rootPath}{v}')
				self.addEndpoint(self.rootPath + k, handler=self.requestRedirect, methods=['GET', 'POST', 'PUT', 'DELETE'])
			self.mappings = dict(mappings)


		# Disable most logs from requests and urllib3 library 
		logging.getLogger("requests").setLevel(LogLevel.WARNING)
		logging.getLogger("urllib3").setLevel(LogLevel.WARNING)
		if not CSE.security.verifyCertificateHttp:	# only when we also verify  certificates
			urllib3.disable_warnings()
		L.isInfo and L.log('HTTP Server initialized')



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
		if self.flaskApp:
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
				L.logErr(str(e))
				CSE.shutdown() # exit the CSE. Cleanup happens in the CSE atexit() handler


	def addEndpoint(self, endpoint:str=None, endpoint_name:str=None, handler:FlaskHandler=None, methods:list[str]=None, strictSlashes:bool=True) -> None:
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods=methods, strict_slashes=strictSlashes)


	def _handleRequest(self, path:str, operation:Operation) -> Response:
		"""	Get and check all the necessary information from the request and
			build the internal strutures. Then, depending on the operation,
			call the associated request handler.
		"""
		L.isDebug and L.logDebug(f'==> HTTP-REQUEST: /{path}') 	# path = request.path  w/o the root
		L.isDebug and L.logDebug(f'Operation: {operation.name}')
		L.isDebug and L.logDebug(f'Headers: \n{str(request.headers).rstrip()}')
		dissectResult = self._dissectHttpRequest(request, operation, path)

		# log Body, if there is one
		if operation in [ Operation.CREATE, Operation.UPDATE ]:
			if dissectResult.request.ct == ContentSerializationType.JSON:
				L.isDebug and L.logDebug(f'Body: \n{str(dissectResult.request.data)}')
			else:
				L.isDebug and L.logDebug(f'Body: \n{helpers.TextTools.toHex(cast(bytes, dissectResult.request.data))}\n=>\n{dissectResult.request.dict}')

		if self.isStopped:
			# Return an error if the server is stopped
			return self._prepareResponse(Result(rsc=RC.internalServerError, request=dissectResult.request, dbg='http server not running', status=False))
		if not dissectResult.status:
			# Something went wrong during dissection
			return self._prepareResponse(dissectResult)

		try:
			responseResult = CSE.request.handleRequest(dissectResult.request)
		except Exception as e:
			responseResult = Utils.exceptionToResult(e)
		return self._prepareResponse(responseResult, dissectResult.request)


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
		if not content:	return ''
		if isinstance(content, str): return content
		return content.decode('utf-8') if ct == ContentSerializationType.JSON else helpers.TextTools.toHex(content)


	def sendHttpRequest(self, method:Callable, url:str, originator:str, ty:T=None, data:Any=None, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None) -> Result:	 # type: ignore[type-arg]
		ct = CSE.defaultSerialization if not ct else ct

		# Set basic headers
		hty = f';ty={int(ty):d}' if ty else ''
		hds = {	'User-Agent'	: self.serverID,
				'Content-Type' 	: f'{ct.toHeader()}{hty}',
				'Accept'		: ct.toHeader(),
				C.hfOrigin	 	: originator,
				C.hfRI 			: Utils.uniqueRI(),
				C.hfRVI			: self.hfvRVI,			# TODO this actually depends in the originator
			   }

		# Add additional headers
		if parameters:
			if C.hfcEC in parameters:				# Event Category
				hds[C.hfEC] = parameters[C.hfcEC]

		# serialize data (only if dictionary, pass on non-dict data)
		content = RequestUtils.serializeData(data, ct) if isinstance(data, dict) else data

		# ! Don't forget: requests are done through the request library, not flask.
		# ! The attribute names are different
		try:
			L.isDebug and L.logDebug(f'Sending request: {method.__name__.upper()} {url}')
			if ct == ContentSerializationType.CBOR:
				L.isDebug and L.logDebug(f'HTTP-Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(content, ct)}\n=>\n{str(data) if data else ""}\n')
			else:
				L.isDebug and L.logDebug(f'HTTP-Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(content, ct)}\n')
			
			# Actual sending the request
			r = method(url, data=content, headers=hds, verify=CSE.security.verifyCertificateHttp)

			responseCt = ContentSerializationType.getType(r.headers['Content-Type']) if 'Content-Type' in r.headers else ct
			rc = RC(int(r.headers['X-M2M-RSC'])) if 'X-M2M-RSC' in r.headers else RC.internalServerError
			L.isDebug and L.logDebug(f'HTTP-Response <== ({str(r.status_code)}):\nHeaders: {str(r.headers)}\nBody: \n{self._prepContent(r.content, responseCt)}\n')
		except Exception as e:
			L.isDebug and L.logWarn(f'Failed to send request: {str(e)}')
			return Result(rsc=RC.targetNotReachable, dbg='target not reachable')
		return Result(dict=RequestUtils.deserializeData(r.content, responseCt), rsc=rc)
		

	#########################################################################

	def _prepareResponse(self, result:Result, request:CSERequest=None) -> Response:
		"""	Prepare the response for a request. If `request` is given then
			set it for the response.
		"""
		content:str|bytes|JSON = ''

		if request:
			result.request = request

		# Build the headers
		headers = {}
		headers['Server'] = self.serverID						# set server field
		headers['X-M2M-RSC'] = f'{result.rsc}'					# set the response status code
		if result.request.headers.requestIdentifier:
			headers['X-M2M-RI'] = result.request.headers.requestIdentifier
		if result.request.headers.releaseVersionIndicator:
			headers['X-M2M-RVI'] = result.request.headers.releaseVersionIndicator
		if result.request.headers.vendorInformation:
			headers['X-M2M-VSI'] = result.request.headers.vendorInformation

		# HTTP status code
		statusCode = result.rsc.httpStatusCode()

		#
		# Determine the accept type and encode the content accordinly
		#
		# Look whether there is a accept header in the original request
		if result.request.headers.accept:
			ct = ContentSerializationType.getType(result.request.headers.accept[0])
		
		# No accept, check originator
		elif len(csz := CSE.request.getSerializationFromOriginator(result.request.headers.originator)) > 0:
			ct = csz[0]

		# Default: configured CSE's default
		else:
			ct = CSE.defaultSerialization
		
		# Assign and encode content accordingly
		headers['Content-Type'] = (cts := ct.toHeader())
		content = result.toData(ct)
		
		# Build and return the response
		if isinstance(content, bytes):
			L.isDebug and L.logDebug(f'<== HTTP-Response (RSC: {result.rsc:d}):\nHeaders: {str(headers)}\nBody: \n{helpers.TextTools.toHex(content)}\n=>\n{str(result.toData())}')
		else:
			L.isDebug and L.logDebug(f'<== HTTP-Response (RSC: {result.rsc:d}):\nHeaders: {str(headers)}\nBody: {str(content)}\n')
		return Response(response=content, status=statusCode, content_type=cts, headers=headers)


	#########################################################################
	#
	#	HTTP request helper functions
	#

	#def _dissectHttpRequest(self, request:Request, operation:Operation, _id:Tuple[str, str, str]) -> Result:
	def _dissectHttpRequest(self, request:Request, operation:Operation, to:str) -> Result:
		"""	Dissect an HTTP request. Combine headers and contents into a single structure. Result is returned in Result.request.
		"""

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


		cseRequest 			= CSERequest()
		req:ReqResp 		= {}
		cseRequest.data 	= request.data			# get the data first. This marks the request as consumed, just in case that we have to return early
		cseRequest.op 		= operation
		req['op']   		= operation.value		# Needed later for validation
		req['to'] 		 	= to

		# Copy and parse the original request headers
		if f := requestHeaderField(request, C.hfOrigin):
			req['fr'] = f
		if f := requestHeaderField(request, C.hfRI):
			req['rqi'] = f
		if f := requestHeaderField(request, C.hfRET):
			req['rqet'] = f
		if f := requestHeaderField(request, C.hfRST):
			req['rset'] = f
		if f := requestHeaderField(request, C.hfOET):
			req['oet'] = f
		if f := requestHeaderField(request, C.hfRVI):
			req['rvi'] = f
		if (rtu := requestHeaderField(request, C.hfRTU)) is not None:	# handle rtu as a list AND it may be an empty list!
			rt = dict()
			rt['nu'] = rtu.split('&')		
			req['rt'] = rt					# req.rt.rtu
		if f := requestHeaderField(request, C.hfVSI):
			req['vsi'] = f

		# parse and extract content-type header
		# cseRequest.headers.contentType	= request.content_type
		if ct := request.content_type:
			if not ct.startswith(tuple(C.supportedContentHeaderFormat)):
				ct = None
			else:
				p  = ct.partition(';')		# always returns a 3-tuple
				ct = p[0] 					# only the content-type without the resource type
				t  = p[2].partition('=')[2]
				if len(t) > 0:
					req['ty'] = t			# Here we found the type for CREATE requests
		cseRequest.headers.contentType = ct

		# parse accept header
		cseRequest.headers.accept = request.headers.getlist('accept')
		cseRequest.headers.accept = [ a for a in cseRequest.headers.accept if a != '*/*' ]
		cseRequest.originalArgs	  = deepcopy(request.args)	# Keep the original args

		# copy request arguments for greedy attributes checking
		args = request.args.copy() 	# type: ignore [no-untyped-call]
		
		# Do some special handling for those arguments that could occur multiple
		# times in the args MultiDict. They are collected together in a single list
		# and added again to args.
		extractMultipleArgs(args, 'ty')	# conversation to int happens later in fillAndValidateCSERequest()
		extractMultipleArgs(args, 'cty')
		extractMultipleArgs(args, 'lbl')

		# Handle some parameters differently.
		# They are not filter cirteria, but request attributes
		for param in ['rcn', 'rp']:
			if p := args.get(param):	# type: ignore [assignment]
				req[param] = p
				del args[param]
		if rtv := args.get('rt'):
			if not (rt := cast(JSON, req.get('rt'))):
				rt = {}
			rt['rtv'] = rtv		# type: ignore [assignment] # req.rt.rtv
			req['rt'] = rt
			del args['rt']


		# Extract further request arguments from the http request
		# add all the args to the filterCriteria
		filterCriteria:ReqResp = {}
		for k,v in args.items():
			filterCriteria[k] = v
		req['fc'] = filterCriteria

		# De-Serialize the content
		if not (contentResult := CSE.request.deserializeContent(cseRequest.data, cseRequest.headers.contentType)).status:
			return Result(rsc=contentResult.rsc, request=cseRequest, dbg=contentResult.dbg, status=False)
		
		# Remove 'None' fields *before* adding the pc, because the pc may contain 'None' fields that need to be preserved
		req = Utils.removeNoneValuesFromDict(req)

		# Add the primitive content and 
		req['pc'] 	 	= contentResult.data[0]	# The actual content
		cseRequest.ct	= contentResult.data[1]	# The conten serialization type
		cseRequest.req	= req					# finally store the oneM2M request object in the cseRequest
		
		# do validation and copying of attributes of the whole request
		try:
			# L.logWarn(str(cseRequest))
			if not (res := CSE.request.fillAndValidateCSERequest(cseRequest)).status:
				return res
		except Exception as e:
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'invalid arguments/attributes ({str(e)})', status=False)

		# Here, if everything went okay so far, we have a request to the CSE
		return Result(request=cseRequest, status=True)



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
	

