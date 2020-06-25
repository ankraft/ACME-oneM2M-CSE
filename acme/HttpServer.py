#
#	HttpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Server to implement the http part of the oneM2M Mcx communication interface.
#	This manager is the main run-loop for the CSE (when using http).
#

import json, requests, logging, os, sys
import flask
from flask import Flask, request, make_response
from typing import Any, Callable
from Configuration import Configuration, version
from Constants import Constants as C
import CSE, Utils
from Logging import Logging, RedirectHandler
from resources.Resource import Resource
from werkzeug.serving import WSGIRequestHandler



class HttpServer(object):

	def __init__(self):

		# Initialize the http server
		# Meaning defaults are automatically provided.
		self.flaskApp = Flask(Configuration.get('cse.csi'))
		self.rootPath = Configuration.get('http.root')

		Logging.log('Registering http server root at: %s' % self.rootPath)

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



	def run(self):
		# Redirect the http server (Flask) log output to the CSE logs
		#werkzeugLog = logging.getLogger('werkzeug')
		#werkzeugLog.addHandler(RedirectHandler("httpServer"))

		WSGIRequestHandler.protocol_version = "HTTP/1.1"


		# Run the http server. This runs forever.
		# The server can run single-threadedly since some of the underlying
		# components (e.g. TinyDB) may run into problems otherwise.
		if self.flaskApp is not None:
			# Disable the flask banner messages
			cli = sys.modules['flask.cli']
			cli.show_server_banner = lambda *x: None
			# Start the server
			try:
				self.flaskApp.run(host=Configuration.get('http.listenIF'), 
								  port=Configuration.get('http.port'),
								  threaded=Configuration.get('http.multiThread'),
								  request_handler=ACMERequestHandler,
								  debug=False)
			except Exception as e:
				Logging.logErr(e)



	def addEndpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=None):
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods=methods)


	def handleGET(self, path : str = None):
		Logging.logDebug('==> Retrieve: /%s' % path) # path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		CSE.event.httpRetrieve()
		resource, rc = CSE.dispatcher.retrieveRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		return self._prepareResponse(request, resource, rc)


	def handlePOST(self, path : str = None):
		Logging.logDebug('==> Create: /%s' % path)	# path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		Logging.logDebug('Body: \n' + request.data.decode("utf-8"))
		CSE.event.httpCreate()
		resource, rc = CSE.dispatcher.createRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		return self._prepareResponse(request, resource, rc)


	def handlePUT(self, path : str = None):
		Logging.logDebug('==> Update: /%s' % path)	# path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		Logging.logDebug('Body: \n' + request.data.decode("utf-8"))
		CSE.event.httpUpdate()
		resource, rc = CSE.dispatcher.updateRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		return self._prepareResponse(request, resource, rc)


	def handleDELETE(self, path : str = None):
		Logging.logDebug('==> Delete: /%s' % path)	# path = request.path  w/o the root
		Logging.logDebug('Headers: \n' + str(request.headers))
		CSE.event.httpDelete()
		resource, rc = CSE.dispatcher.deleteRequest(request, Utils.retrieveIDFromPath(path, self.csern, self.cseri))
		return self._prepareResponse(request, resource, rc)


	#########################################################################


	# Handle requests to mapped paths
	def requestRedirect(self):
		path = request.path[len(self.rootPath):] if request.path.startswith(self.rootPath) else request.path
		if path in self.mappings:
			Logging.logDebug('==> Redirecting to: /%s' % path)
			CSE.event.httpRedirect()
			return flask.redirect(self.mappings[path], code=307)
		return '', 404


	#########################################################################
	#
	#	Various handlers
	#


	# Redirect request to / to webui
	def redirectRoot(self):
		return flask.redirect(Configuration.get('cse.webui.root'), code=302)

	def getVersion(self) -> str:
		return version

	def handleWebUIGET(self, path : str = None):
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
			flask.abort(404)


	#########################################################################

	#
	#	Send various types of HTTP requests
	#

	def sendRetrieveRequest(self, url : str, originator : str) -> (dict, int):
		return self.sendRequest(requests.get, url, originator)


	def sendCreateRequest(self, url : str, originator : str, ty : int = None, data : Any = None) -> (dict, int):
		return self.sendRequest(requests.post, url, originator, ty, data)


	def sendUpdateRequest(self, url : str, originator : str, data : Any) -> (dict, int):
		return self.sendRequest(requests.put, url, originator, data=data)


	def sendDeleteRequest(self, url : str, originator : str) -> (dict, int):
		return self.sendRequest(requests.delete, url, originator)


	def sendRequest(self, method : Callable , url : str, originator : str, ty : int = None, data : Any = None, ct : str = 'application/json') -> (dict, int):	# TODO Constants
		headers = { 'Content-Type' 	: '%s%s' % (ct, ';ty=%d' % ty if ty is not None else ''), 
					C.hfOrigin	 	: originator,
					C.hfRI 			: Utils.uniqueRI(),
					C.hfRVI			: C.hfvRVI,			# TODO this actually depends in the originator
				   }
		try:
			Logging.logDebug('Sending request: %s %s' % (method.__name__.upper(), url))
			r = method(url, data=data, headers=headers)
		except Exception as e:
			Logging.logWarn('Failed to send request: %s' % str(e))
			return None, C.rcTargetNotReachable
		rc = int(r.headers['X-M2M-RSC']) if 'X-M2M-RSC' in r.headers else C.rcInternalServerError
		return r.json() if len(r.content) > 0 else None, rc

	#########################################################################

	def _prepareResponse(self, request, resource, returnCode):
		if resource is None:
			r = ''
		elif isinstance(resource, dict):
			r = json.dumps(resource)
		else:
			if (r := resource.asJSON() if isinstance(resource, Resource) else resource) is None:
				r = ''
				returnCode = C.rcNotFound
		Logging.logDebug('<== Response (RSC: %d):\n%s\n' % (returnCode, str(r)))
		resp = make_response(r)

		# headers
		resp.headers['X-M2M-RSC'] = str(returnCode)
		if 'X-M2M-RI' in request.headers:
			resp.headers['X-M2M-RI'] = request.headers['X-M2M-RI']
		if 'X-M2M-RVI' in request.headers:
			resp.headers['X-M2M-RVI'] = request.headers['X-M2M-RVI']

		resp.status_code = self._statusCode(returnCode)
		resp.content_type = C.hfvContentType
		return resp


	#
	#	Mapping of oneM2M return codes to http status codes
	#

	_codes = {
		C.rcOK 											: 200,		# OK
		C.rcDeleted 									: 200,		# DELETED
		C.rcUpdated 									: 200,		# UPDATED
		C.rcCreated										: 201,		# CREATED
		C.rcBadRequest									: 400,		# BAD REQUEST
		C.rcContentsUnacceptable						: 400,		# NOT ACCEPTABLE
		C.rcInsufficientArguments 						: 400,		# INSUFFICIENT ARGUMENTS
		C.rcInvalidArguments							: 400,		# INVALID ARGUMENTS
		C.rcMaxNumberOfMemberExceeded					: 400, 		# MAX NUMBER OF MEMBER EXCEEDED
		C.rcGroupMemberTypeInconsistent					: 400,		# GROUP MEMBER TYPE INCONSISTENT
		C.rcOriginatorHasNoPrivilege					: 403,		# ORIGINATOR HAS NO PRIVILEGE
		C.rcInvalidChildResourceType					: 403,		# INVALID CHILD RESOURCE TYPE
		C.rcTargetNotReachable							: 403,		# TARGET NOT REACHABLE
		C.rcAlreadyExists								: 403,		# ALREAD EXISTS
		C.rcTargetNotSubscribable						: 403,		# TARGET NOT SUBSCRIBABLE
		C.rcReceiverHasNoPrivileges						: 403,		# RECEIVER HAS NO PRIVILEGE
		C.rcSecurityAssociationRequired					: 403,		# SECURITY ASSOCIATION REQUIRED
		C.rcNotFound									: 404,		# NOT FOUND
		C.rcOperationNotAllowed							: 405,		# OPERATION NOT ALLOWED
		C.rcNotAcceptable 								: 406,		# NOT ACCEPTABLE
		C.rcConflict									: 409,		# CONFLICT
		C.rcInternalServerError 						: 500,		# INTERNAL SERVER ERROR
		C.rcSubscriptionVerificationInitiationFailed	: 500,		# SUBSCRIPTION_VERIFICATION_INITIATION_FAILED
		C.rcNotImplemented								: 501,		# NOT IMPLEMENTED
	}


	def _statusCode(self, sc):
		""" Map the oneM2M RSC to an http status code. """
		return self._codes[sc]


#	#########################################################################

#	Own request handler.
#	Actually only to redirect logging.
#

class ACMERequestHandler(WSGIRequestHandler):
	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type, message, *args):
		return
		# Logging.log('%s %s\n' % (self.address_string(),
		# 								 message % args))

	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code='-', size='-'):
		Logging.logDebug('"%s" %s %d' % (self.requestline, size, code))

	def log_message(self, format, *args):
		return

