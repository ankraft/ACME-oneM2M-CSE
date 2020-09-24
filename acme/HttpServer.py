#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Server to implement the http part of the oneM2M Mcx communication interface.
#	This manager is the main run-loop for the CSE (when using http).
#

import json, requests, logging, os, sys, traceback
from typing import Any, Callable, List, Tuple, Union
import flask
from flask import Flask, Request, make_response, request
from werkzeug.wrappers import Response
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC
import CSE, Utils
from Logging import Logging
from resources.Resource import Resource
from werkzeug.serving import WSGIRequestHandler
import ssl


class HttpServer(object):

	def __init__(self) -> None:

		# Initialize the http server
		# Meaning defaults are automatically provided.
		self.flaskApp			= Flask(Configuration.get('cse.csi'))
		self.rootPath			= Configuration.get('http.root')
		self.useTLS 			= Configuration.get('cse.security.useTLS')
		self.verifyCert			= Configuration.get('cse.security.verifyCert')
		self.tlsVersion			= Configuration.get('cse.security.tlsVersion').lower()
		self.caCertificateFile	= Configuration.get('cse.security.caCertificateFile')
		self.caPrivateKeyFile	= Configuration.get('cse.security.caPrivateKeyFile')

		self.serverID	= 'ACME %s' % C.version 	# The server's ID for http response headers

		Logging.log('Registering http server root at: %s' % self.rootPath)
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
		if Configuration.get('cse.webui.enable'):
			self.webuiRoot = Configuration.get('cse.webui.root')
			self.webuiDirectory = '%s/webui' % CSE.rootDirectory
			Logging.log('Registering web ui at: %s, serving from %s' % (self.webuiRoot, self.webuiDirectory))
			self.addEndpoint(self.webuiRoot, handler=self.handleWebUIGET, methods=['GET'])
			self.addEndpoint(self.webuiRoot + '/<path:path>', handler=self.handleWebUIGET, methods=['GET'])
			self.addEndpoint('/', handler=self.redirectRoot, methods=['GET'])
			self.addEndpoint('/__version__', handler=self.getVersion, methods=['GET'])

		# Enable the config endpoint
		if Configuration.get('http.enableRemoteConfiguration'):
			configEndpoint = '%s/__config__' % self.rootPath
			Logging.log('Registering configuration endpoint at: %s' % configEndpoint)
			self.addEndpoint(configEndpoint, handler=self.handleConfig, methods=['GET'], strictSlashes=False)
			self.addEndpoint('%s/<path:path>' % configEndpoint, handler=self.handleConfig, methods=['GET', 'PUT'])


		# Add mapping / macro endpoints
		self.mappings = {}
		if (mappings := Configuration.get('server.http.mappings')) is not None:
			# mappings is a list of tuples
			for (k, v) in mappings:
				Logging.log('Registering mapping: %s%s -> %s%s' % (self.rootPath, k, self.rootPath, v))
				self.addEndpoint(self.rootPath + k, handler=self.requestRedirect, methods=['GET', 'POST', 'PUT', 'DELETE'])
			self.mappings = dict(mappings)


		# Disable most logs from requests library 
		logging.getLogger("requests").setLevel(logging.WARNING)
		logging.getLogger("urllib3").setLevel(logging.WARNING)

		# Keep some values for optimization
		self.csern	= Configuration.get('cse.rn') 
		self.cseri	= Configuration.get('cse.ri')



	def run(self) -> None:
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
					Logging.logDebug('Setup SSL context. Certfile: %s, KeyFile:%s' % (self.caCertificateFile, self.caPrivateKeyFile))
					context = ssl.SSLContext(
									{ 	'tls1.1' : ssl.PROTOCOL_TLSv1_1,
										'tls1.2' : ssl.PROTOCOL_TLSv1_2,
										'auto'   : ssl.PROTOCOL_TLS,			# since Python 3.6. Automatically choose the highest protocol version between client & server
									}[self.tlsVersion.lower()]
								)
					context.load_cert_chain(self.caCertificateFile, self.caPrivateKeyFile)
				self.flaskApp.run(host=Configuration.get('http.listenIF'), 
								  port=Configuration.get('http.port'),
								  threaded=Configuration.get('http.multiThread'),
								  request_handler=ACMERequestHandler,
								  ssl_context=context,
								  debug=False)
			except Exception as e:
				Logging.logErr(str(e))



	def addEndpoint(self, endpoint:str=None, endpoint_name:str=None, handler:Callable=None, methods:List[str]=None, strictSlashes:bool=True) -> None:
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods=methods, strict_slashes=strictSlashes)


	def handleGET(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Retrieve: /%s' % path) # path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		CSE.event.httpRetrieve() # type: ignore
		try:
			result = CSE.dispatcher.retrieveRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		except Exception as e:
			result = self._prepareException(e)
		finally:
			return self._prepareResponse(request, result)


	def handlePOST(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Create: /%s' % path)	# path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		Logging.logDebug('Body: \n' + request.data.decode("utf-8"))
		CSE.event.httpCreate()	# type: ignore
		try:
			result = CSE.dispatcher.createRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		except Exception as e:
			result = self._prepareException(e)
		finally:
			return self._prepareResponse(request, result)


	def handlePUT(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Update: /%s' % path)	# path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		Logging.logDebug('Body: \n' + request.data.decode("utf-8"))
		CSE.event.httpUpdate()	# type: ignore
		try:
			result = CSE.dispatcher.updateRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		except Exception as e:
			result = self._prepareException(e)
		finally:
			return self._prepareResponse(request, result)


	def handleDELETE(self, path:str=None) -> Response:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Delete: /%s' % path)	# path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		CSE.event.httpDelete()	# type: ignore
		try:
			result = CSE.dispatcher.deleteRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		except Exception as e:
			result = self._prepareException(e)
		finally:
			return self._prepareResponse(request, result)


	#########################################################################


	# Handle requests to mapped paths
	def requestRedirect(self) -> Union[Response, Tuple[str, int]]:
		path = request.path[len(self.rootPath):] if request.path.startswith(self.rootPath) else request.path
		if path in self.mappings:
			Logging.logDebug('==> Redirecting to: /%s' % path)
			CSE.event.httpRedirect()	# type: ignore
			return flask.redirect(self.mappings[path], code=307)
		return '', 404


	#########################################################################
	#
	#	Various handlers
	#


	# Redirect request to / to webui
	def redirectRoot(self) -> Response:
		return flask.redirect(Configuration.get('cse.webui.root'), code=302)


	def getVersion(self) -> str:
		return C.version


	def handleConfig(self, path:str=None) -> str:
		if request.method == 'GET':
			if path == None or len(path) == 0:
				return Configuration.print()
			if Configuration.has(path):
				return str(Configuration.get(path))
			return ''
		elif request.method =='PUT':
			data = request.data.decode('utf-8').rstrip()
			try:
				if path == 'cse.checkExpirationsInterval':
					Logging.logDebug('New remote configuration: %s = %s' % (path, data))
					if (d := int(data)) < 1:
						return 'nak'
					Configuration.set(path, d)
					CSE.registration.stopExpirationWorker()
					CSE.registration.startExpirationWorker()
					return 'ack'
			except:
				return 'nak'
			return 'nak'
		return 'unsupported'




	def handleWebUIGET(self, path:str=None) -> Union[Response, Any, Tuple[str, int]]:
		""" Handle a GET request for the web GUI. """

		# security check whether the path will under the web root
		if not (CSE.rootDirectory + request.path).startswith(CSE.rootDirectory):
			return None, 404

		# Redirect to index file. Also include base / cse RI
		if path == None or len(path) == 0 or (path.endswith('index.html') and len(request.args) != 2):
			return flask.redirect('%s/index.html?ri=/%s&or=%s' % (self.webuiRoot, Configuration.get('cse.ri'), Configuration.get('cse.originator')), code=302)
			# return flask.redirect('%s/index.html?ri=/%s' % (self.webuiRoot, Configuration.get('cse.ri')), code=302)
		else:
			filename = '%s/%s' % (self.webuiDirectory, path)	# return any file in the web directory
		try:
			return flask.send_file(filename)
		except Exception as e:
			Logging.logWarn(str(e))
			return flask.abort(404)


	#########################################################################

	#
	#	Send various types of HTTP requests
	#

	def sendRetrieveRequest(self, url:str, originator:str) -> Result:
		return self.sendRequest(requests.get, url, originator)


	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None) -> Result:
		return self.sendRequest(requests.post, url, originator, ty, data)


	def sendUpdateRequest(self, url:str, originator:str, data:Any) -> Result:
		return self.sendRequest(requests.put, url, originator, data=data)


	def sendDeleteRequest(self, url:str, originator:str) -> Result:
		return self.sendRequest(requests.delete, url, originator)


	def sendRequest(self, method:Callable , url:str, originator:str, ty:T=None, data:Any=None, ct:str='application/json') -> Result:	# TODO Constants
		headers = {	'User-Agent'	: self.serverID,
					'Content-Type' 	: '%s%s' % (ct, ';ty=%d' % int(ty) if ty is not None else ''), 
					C.hfOrigin	 	: originator,
					C.hfRI 			: Utils.uniqueRI(),
					C.hfRVI			: C.hfvRVI,			# TODO this actually depends in the originator
				   }
		try:
			Logging.logDebug('Sending request: %s %s' % (method.__name__.upper(), url))
			Logging.logDebug('Request ==>:\n%s\n' % (str(data) if data is not None else ''))
			r = method(url, data=data, headers=headers, verify=self.verifyCert)
			Logging.logDebug('Response <== (%s):\n%s' % (str(r.status_code), str(r.content.decode("utf-8"))))
		except Exception as e:
			Logging.logWarn('Failed to send request: %s' % str(e))
			return Result(rsc=RC.targetNotReachable, dbg='target not reachable')
		rc = RC(int(r.headers['X-M2M-RSC'])) if 'X-M2M-RSC' in r.headers else RC.internalServerError
		return Result(jsn=r.json() if len(r.content) > 0 else None, rsc=rc)

	#########################################################################

	def _prepareResponse(self, request:Request, result:Result) -> Response:
		if isinstance(result.resource, Resource):
			r = json.dumps(result.resource.asJSON())
		elif result.dbg is not None:
			r = '{ "m2m:dbg" : "%s" }' % result.dbg.replace('"', '\\"')
		elif result.resource is None:
			r = ''
		elif isinstance(result.resource, dict):
			r = json.dumps(result.resource)
		elif isinstance(result.resource, str):
			r = result.resource
		else:
			r = ''
			result.rsc = RC.notFound
		Logging.logDebug('<== Response (RSC: %d):\n%s\n' % (result.rsc, str(r)))
		resp = make_response(r)

		# headers
		resp.headers['Server'] = self.serverID	# set server field

		resp.headers['X-M2M-RSC'] = '%d' % result.rsc
		if 'X-M2M-RI' in request.headers:
			resp.headers['X-M2M-RI'] = request.headers['X-M2M-RI']
		if 'X-M2M-RVI' in request.headers:
			resp.headers['X-M2M-RVI'] = request.headers['X-M2M-RVI']

		resp.status_code = result.rsc.httpStatusCode()
		resp.content_type = C.hfvContentType
		self.flaskApp.process_response(resp)
		return resp


	def _prepareException(self, e: Exception) -> Result:
		Logging.logErr(traceback.format_exc())
		return Result(rsc=RC.internalServerError, dbg='encountered exception: %s' % traceback.format_exc().replace('"', '\\"').replace('\n', '\\n'))


##########################################################################
#
#	Own request handler.
#	Actually only to redirect logging.
#

class ACMERequestHandler(WSGIRequestHandler):
	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type, message, *args): # type: ignore
		Logging.logDebug(message % args)
		return
		# Logging.log('%s %s\n' % (self.address_string(),
		# 								 message % args))

	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code='-', size='-'): 	# type: ignore
		Logging.logDebug('"%s" %s %d' % (self.requestline, size, code))

	def log_message(self, format, *args): 	# type: ignore
		Logging.logDebug(format % args)
		return
