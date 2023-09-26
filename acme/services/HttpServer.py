#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Server to implement the http part of the oneM2M Mcx communication interface.
#

from __future__ import annotations
from typing import Any, Callable, cast, Tuple, Optional

import logging, sys, urllib3, re
from copy import deepcopy

import flask
from flask import Flask, Request, request
from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import MultiDict
from waitress import serve
from flask_cors import CORS
import requests
import isodate

from ..etc.Constants import Constants
from ..etc.Types import ReqResp, RequestType, ResourceTypes, Result, ResponseStatusCode, JSON
from ..etc.Types import Operation, CSERequest, ContentSerializationType, DesiredIdentifierResultType, ResponseType, ResultContentType
from ..etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR, BAD_REQUEST, REQUEST_TIMEOUT, TARGET_NOT_REACHABLE, ResponseException
from ..etc.Utils import exceptionToResult, renameThread, uniqueRI, toSPRelative, removeNoneValuesFromDict,isURL
from ..helpers.TextTools import findXPath
from ..etc.DateUtils import timeUntilAbsRelTimestamp, getResourceDate, rfc1123Date
from ..etc.RequestUtils import toHttpUrl, serializeData, deserializeData, requestFromResult
from ..helpers.NetworkTools import isTCPPortAvailable
from ..services.Configuration import Configuration
from ..services import CSE
from ..webui.webUI import WebUI
from ..helpers import TextTools as TextTools
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers.Interpreter import SType
from ..services.Logging import Logging as L, LogLevel


#
# Types definitions for the http server
#

FlaskHandler = 	Callable[[str], Response]
""" Type definition for flask handler. """


class HttpServer(object):

	__close__ = (
		'flaskApp',
		'rootPath',
		'serverAddress',
		'listenIF',
		'port',
		'allowPatchForDelete',
		'requestTimeout',
		'webuiRoot',
		'webuiDirectory',
		'isStopped',
		'corsEnable',
		'corsResources',
		'backgroundActor',
		'serverID',
		'_responseHeaders',
		'webui',
		'mappeings',
		'httpActor',

		'_eventHttpRetrieve',
		'_eventHttpCreate',
		'_eventNotify',
		'_eventHttpUpdate',
		'_eventHttpDelete',
		'_eventResponseReceived',
	)

	def __init__(self) -> None:

		# Initialize the http server
		# Meaning defaults are automatically provided.
		self.flaskApp			= Flask(CSE.cseCsi)
		self.rootPath			= Configuration.get('http.root')
		self.serverAddress		= Configuration.get('http.address')
		self.listenIF			= Configuration.get('http.listenIF')
		self.port 				= Configuration.get('http.port')
		self.allowPatchForDelete= Configuration.get('http.allowPatchForDelete')
		self.requestTimeout 	= Configuration.get('http.timeout')
		self.webuiRoot 			= Configuration.get('webui.root')
		self.webuiDirectory 	= f'{Configuration.get("packageDirectory")}/webui'
		self.isStopped			= False
		self.corsEnable			= Configuration.get('http.cors.enable')
		self.corsResources		= Configuration.get('http.cors.resources')

		self.backgroundActor:BackgroundWorker = None

		self.serverID			= f'ACME {Constants.version}' 	# The server's ID for http response headers
		self._responseHeaders	= {'Server' : self.serverID}	# Additional headers for other requests

		L.isInfo and L.log(f'Registering http server root at: {self.rootPath}')
		if CSE.security.useTLSHttp:
			L.isInfo and L.log('TLS enabled. HTTP server serves via https.')
		
		# Add CORS support for flask
		if self.corsEnable:
			logging.getLogger('flask_cors').level = logging.DEBUG	# switch on flask-cors internal logging
			L.isInfo and L.log('CORS is enabled for the HTTP server.')
			CORS(self.flaskApp, resources = self.corsResources)
		else:
			L.isDebug and L.logDebug('CORS is NOT enabled for the HTTP server.')

		# Add endpoints
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handleGET, methods = ['GET'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handlePOST, methods = ['POST'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handlePUT, methods = ['PUT'])
		self.addEndpoint(self.rootPath + '/<path:path>', handler=self.handleDELETE, methods = ['DELETE'])

		# Register the endpoint for the web UI
		# This is done by instancing the otherwise "external" web UI
		self.webui = WebUI(self.flaskApp, 
						   defaultRI = CSE.cseRi, 
						   defaultOriginator = CSE.cseOriginator, 
						   root = self.webuiRoot,
						   webuiDirectory = self.webuiDirectory,
						   version = Constants.version)

		# Enable the config endpoint
		if Configuration.get('http.enableStructureEndpoint'):
			structureEndpoint = f'{self.rootPath}/__structure__'
			L.isInfo and L.log(f'Registering structure endpoint at: {structureEndpoint}')
			self.addEndpoint(structureEndpoint, handler = self.handleStructure, methods  =['GET'], strictSlashes = False)
			self.addEndpoint(f'{structureEndpoint}/<path:path>', handler = self.handleStructure, methods = ['GET', 'PUT'])

		# Enable the upper tester endpoint
		if Configuration.get('http.enableUpperTesterEndpoint'):
			upperTesterEndpoint = f'{self.rootPath}/__ut__'
			L.isInfo and L.log(f'Registering upper tester endpoint at: {upperTesterEndpoint}')
			self.addEndpoint(upperTesterEndpoint, handler = self.handleUpperTester, methods = ['POST'], strictSlashes=False)

		# Allow to use PATCH as a replacement for the DELETE method
		if Configuration.get('http.allowPatchForDelete'):
			self.addEndpoint(self.rootPath + '/<path:path>', handler = self.handlePATCH, methods = ['PATCH'])

		# Disable most logs from requests and urllib3 library 
		logging.getLogger("requests").setLevel(LogLevel.WARNING)
		logging.getLogger("urllib3").setLevel(LogLevel.WARNING)
		if not CSE.security.verifyCertificateHttp:	# only when we also verify  certificates
			urllib3.disable_warnings()
		L.isInfo and L.log('HTTP Server initialized')

		# Optimize event handling
		self._eventHttpRetrieve =  CSE.event.httpRetrieve			# type: ignore [attr-defined]
		self._eventHttpCreate = CSE.event.httpCreate				# type: ignore [attr-defined]
		self._eventNotify =  CSE.event.httpNotify					# type: ignore [attr-defined]
		self._eventHttpUpdate = CSE.event.httpUpdate				# type: ignore [attr-defined]
		self._eventHttpDelete = CSE.event.httpDelete				# type: ignore [attr-defined]
		self._eventResponseReceived = CSE.event.responseReceived	# type: ignore [attr-defined]


	def run(self) -> bool:
		"""	Run the http server in a separate thread.
		"""
		if isTCPPortAvailable(self.port):
			self.httpActor = BackgroundWorkerPool.newActor(self._run, name='HTTPServer')
			self.httpActor.start()
			return True
		L.logErr(f'Cannot start HTTP server. Port: {self.port} already in use.', showStackTrace = False)
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

				""" TODO
				Do not use run() in a production setting. 
    			It is not intended to meet security and performance requirements for a production server. 
       			Instead, see Deploying to Production for WSGI server recommendations.
				https://flask.palletsprojects.com/en/2.3.x/api/#flask.Flask.run
    			"""
				# self.flaskApp.run(host = self.listenIF, 
				# 				  port = self.port,
				# 				  threaded = True,
				# 				  request_handler = ACMERequestHandler,
				# 				  ssl_context = CSE.security.getSSLContext(),
				# 				  debug = False)
				# Run HTTP server using waitress.serve function
				serve(self.flaskApp, host=self.listenIF, port=self.port, threads=2) # TODO: Adjust threads counts
			except Exception as e:
				# No logging for headless, nevertheless print the reason what happened
				if CSE.isHeadless:
					L.console(str(e), isError=True)
				if type(e) == PermissionError:
					m  = f'{e}.'
					m += f' You may not have enough permission to run a server on this port ({self.port}).'
					if self.port < 1024:
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


	def _handleRequest(self, path:str, operation:Operation) -> Response:
		"""	Get and check all the necessary information from the request and
			build the internal strutures. Then, depending on the operation,
			call the associated request handler.
		"""
		L.isDebug and L.logDebug(f'==> HTTP Request: {path}') 	# path = request.path  w/o the root
		L.isDebug and L.logDebug(f'Operation: {operation.name}')
		L.isDebug and L.logDebug(f'Headers: \n{str(request.headers).rstrip()}')
		try:
			dissectResult = self._dissectHttpRequest(request, operation, path)
		except ResponseException as e:
			dissectResult = Result(rsc = e.rsc, request = e.data, dbg = e.dbg)


		# log Body, if there is one
		if operation in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ] and dissectResult.request.originalData:
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
			CSE.request.recordRequest(dissectResult.request, dissectResult)
			return self._prepareResponse(dissectResult)

		try:
			responseResult = CSE.request.handleRequest(dissectResult.request)
		except Exception as e:
			responseResult = exceptionToResult(e)
		# L.inspect(responseResult)
		return self._prepareResponse(responseResult, dissectResult.request)


	def handleGET(self, path:Optional[str] = None) -> Response:
		renameThread('HTRE')
		self._eventHttpRetrieve()
		return self._handleRequest(path, Operation.RETRIEVE)


	def handlePOST(self, path:Optional[str] = None) -> Response:
		if self._hasContentType():
			renameThread('HTCR')
			self._eventHttpCreate()
			return self._handleRequest(path, Operation.CREATE)
		else:
			renameThread('HTNO')
			self._eventNotify()
			return self._handleRequest(path, Operation.NOTIFY)


	def handlePUT(self, path:Optional[str] = None) -> Response:
		renameThread('HTUP')
		self._eventHttpUpdate()
		return self._handleRequest(path, Operation.UPDATE)


	def handleDELETE(self, path:Optional[str] = None) -> Response:
		renameThread('HTDE')
		self._eventHttpDelete()
		return self._handleRequest(path, Operation.DELETE)


	def handlePATCH(self, path:Optional[str] = None) -> Response:
		"""	Support instead of DELETE for http/1.0.
		"""
		if request.environ.get('SERVER_PROTOCOL') != 'HTTP/1.0':
			return Response(L.logWarn('PATCH method is only allowed for HTTP/1.0. Rejected.'), status = 405)
		renameThread('HTDE')
		self._eventHttpDelete()
		return self._handleRequest(path, Operation.DELETE)


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
		return flask.redirect(self.webuiRoot, code = 302)


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

		renameThread('UT')
		L.isDebug and L.logDebug(f'==> Upper Tester Request:') 
		L.isDebug and L.logDebug(f'Headers: \n{str(request.headers).rstrip()}')
		if request.data:
			L.isDebug and L.logDebug(f'Body: \n{request.json}')

		# Handle special commands
		if (cmd := request.headers.get('X-M2M-UTCMD')) is not None:
			cmd, _, arg = cmd.partition(' ')
			if not (res := CSE.script.run(cmd, arg, metaFilter = [ 'uppertester' ]))[0]:
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

	def _prepContent(self, content:bytes|str|Any, ct:ContentSerializationType) -> str:
		if not content:	return ''
		if isinstance(content, str): return content
		return content.decode('utf-8') if ct == ContentSerializationType.JSON else TextTools.toHex(content)


	def sendHttpRequest(self, request:CSERequest, url:str) -> Result:
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
		ct = request.ct if request.ct else CSE.defaultSerialization

		# Set basic headers
		hty = f';ty={int(request.ty):d}' if request.ty else ''
		hds = {	'Date'			: rfc1123Date(),
				'User-Agent'	: self.serverID,
				'Content-Type' 	: f'{ct.toHeader()}{hty}',
				'cache-control'	: 'no-cache',
		}
		hds[Constants.hfOrigin]	= toSPRelative(request.originator)
		if not request.rqi:
			request.rqi = uniqueRI()
		hds[Constants.hfRI]		= request.rqi
		# hds[Constants.hfRI]		= request.rqi if request.rqi else uniqueRI()
		if request.rvi != '1':
			hds[Constants.hfRVI]= request.rvi if request.rvi is not None else CSE.releaseVersion
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
			hds[Constants.hfRTU] = str(request.rt.value)
		if request.vsi:
			hds[Constants.hfVSI] = request.vsi

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
		timeout = self.requestTimeout if timeout is None else timeout

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
				L.isDebug and L.logDebug(f'HTTP Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(data, ct)}\n=>\n{str(data) if data else ""}\n')
			else:
				L.isDebug and L.logDebug(f'HTTP Request ==>:\nHeaders: {hds}\nBody: \n{self._prepContent(data, ct)}\n')
			
			# Actual sending the request
			r = method(url, 
					   data = data,
					   headers = hds,
					   verify = CSE.security.verifyCertificateHttp,
					   timeout = timeout)

			# Construct CSERequest response object from the result
			resp = CSERequest(requestType = RequestType.RESPONSE)
			resp.ct = ContentSerializationType.getType(r.headers['Content-Type']) if 'Content-Type' in r.headers else ct
			resp.rsc = ResponseStatusCode(int(r.headers[Constants.hfRSC])) if Constants().hfRSC in r.headers else ResponseStatusCode.INTERNAL_SERVER_ERROR
			resp.pc = deserializeData(r.content, resp.ct)
			resp.originator = r.headers.get(Constants.hfOrigin)
			try:
				# Add Originating Timestamp if present in request
				if (ot := r.headers.get(Constants().hfOT)):
					isodate.parse_date(ot) # Check if valid ISO 8601 date, may raise exception
					resp.ot = ot
			except Exception as ee:
				raise BAD_REQUEST(L.logWarn(f'Received wrong format for X-M2M-OT: {ot} - {str(ee)}'))
			if (rqi := r.headers.get(Constants().hfRI)) != hds[Constants().hfRI]:
				raise BAD_REQUEST(L.logWarn(f'Received wrong or missing request identifier: {resp.rqi}'))
			resp.rqi = rqi

			L.isDebug and L.logDebug(f'HTTP Response <== ({str(r.status_code)}):\nHeaders: {str(r.headers)}\nBody: \n{self._prepContent(r.content, resp.ct)}\n')
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

		result.request.ct = CSE.defaultSerialization	# default serialization
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
	
		#
		#	Transform request to oneM2M request
		#
		outResult = requestFromResult(result, isResponse = True)

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
		headers[Constants().hfOT] = getResourceDate()

		# HTTP status code
		statusCode = result.rsc.httpStatusCode()
		
		# Assign and encode content accordingly
		headers['Content-Type'] = (cts := result.request.ct.toHeader())
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

		def extractMultipleArgs(args:MultiDict, argName:str) -> None:
			"""	Get multi-arguments. Remove the found arguments from the original list, but add the new list again with the argument name.
			"""
			lst = [ t for sublist in args.getlist(argName) for t in sublist.split() ]
			args.poplist(argName)	# type: ignore [no-untyped-call] # perhaps even multiple times
			if len(lst) > 0:
				args[argName] = lst



		cseRequest 					= CSERequest()
		req:ReqResp 				= {}
		cseRequest.originalData 	= request.data			# get the data first. This marks the request as consumed, just in case that we have to return early
		cseRequest.op 				= operation
		req['op']   				= operation.value		# Needed later for validation

		# resolve http's /~ and /_ special prefixs
		if path[0] == '~':
			path = path[1:]			# ~/xxx -> /xxx
		elif path[0] == '_':
			path = f'/{path[1:]}'	# _/xxx -> //xxx
		req['to'] 		 			= path


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
			req['rt'] = rt					# req.rt.rtu
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

		cseRequest.mediaType = contentType

		# parse accept header
		cseRequest.httpAccept 	= [ a for a in _headers.getlist('accept') if a != '*/*' ]
		cseRequest.originalHttpArgs	= deepcopy(request.args)	# Keep the original args

		# copy request arguments for greedy attributes checking
		_args = request.args.copy() 	# type: ignore [no-untyped-call]
		
		# Do some special handling for those arguments that could occur multiple
		# times in the args MultiDict. They are collected together in a single list
		# and added again to args.
		extractMultipleArgs(_args, 'ty')	# conversation to int happens later in fillAndValidateCSERequest()
		extractMultipleArgs(_args, 'cty')
		extractMultipleArgs(_args, 'lbl')

		# Handle some parameters differently.
		# They are not filter criteria, but request attributes
		for param in ['rcn', 'rp', 'drt', 'sqi']:
			if p := _args.get(param):	# type: ignore [assignment]
				req[param] = p
				del _args[param]
		if rtv := _args.get('rt'):
			if not (rt := cast(JSON, req.get('rt'))):
				rt = {}
			rt['rtv'] = rtv		# type: ignore [assignment] # req.rt.rtv
			req['rt'] = rt
			del _args['rt']
		
		# Maxage
		if (ma := _args.get('ma')):
			cseRequest.ma = ma

		# Handle attributeList
		attributeList:list[str] = []
		extractMultipleArgs(_args, 'atrl')
		if atrl := _args.get('atrl'):
			if len(atrl) == 1:
				req['to'] = f'{req["to"]}#{atrl[0]}'
			else:
				attributeList = [ a for a in atrl ]
			del _args['atrl']
		
		# Extract further request arguments from the http request
		# add all the args to the filterCriteria
		filterCriteria:ReqResp = { k:v for k,v in _args.items() }
		if len(filterCriteria) > 0:
			req['fc'] = filterCriteria

		if attributeList:
			req['pc'] = { 'm2m:atrl': attributeList }
			cseRequest.ct = CSE.defaultSerialization

		else:

			# De-Serialize the content
			pc, ct = CSE.request.deserializeContent(cseRequest.originalData, cseRequest.mediaType) # may throw an exception
			
			# Remove 'None' fields *before* adding the pc, because the pc may contain 'None' fields that need to be preserved
			req = removeNoneValuesFromDict(req)

			# Add the primitive content and 
			req['pc'] = pc		# The actual content
			cseRequest.ct = ct	# The conten serialization type

		cseRequest.originalRequest	= req	# finally store the oneM2M request object in the cseRequest
		
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
	

