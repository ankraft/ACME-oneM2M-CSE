	#
#	HttpManagement.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Management functionality for the http server. """

from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING
import sys, json
from unittest import case

from acmecse.runtime.Logging import Logging as L
from acmecse.etc.Types import LogLevel, AuthorizationResult, BindingType
from acmecse.helpers.PluginManager import plugin, start, configure, requires
from acmecse.runtime.Configuration import Configuration

if TYPE_CHECKING:
	from acmecse.runtime.Management import ManagementSupport
	from acmecse.plugins.bindings.HttpServer import HttpServer
	from flask import Response

	
@plugin(tags=['acme', 'core'])
@requires(httpServer='acmecse.plugins.bindings.HttpServer')
@requires(managementSupport='acmecse.runtime.Management') 
class HttpManagement:
	"""	Plugin class to add the Management functionality to the HTTP server.

		The management endpoint is registered at "__mgmt__".

		The plugin depends on the `HttpServer.HttpServer` plugin, which is injected into this plugin by the `acmecse.runtime.PluginManager.PluginManager`. 
		The management endpoint will only be registered if the `HttpServer.HttpServer` plugin is loaded and the dependency can be resolved. 
	"""

	# "httpServer" is injected by the PluginManager, only if the HttpServer plugin is loaded and the dependency can be resolved.
	httpServer: HttpServer = None	# type: ignore
	"""	The injected `HttpServer.HttpServer` plugin instance is injected by the `acmecse.runtime.PluginManager.PluginManager` based on the declared dependency. The plugin will only be loaded if the `HttpServer.HttpServer` plugin is loaded. """

	managementSupport: ManagementSupport = None
	""" Injected `ManagementSupport` instance. """

	@start
	def startManagement(self) -> None:
		""" Start the management plugin. 
		"""
		L.isDebug and L.logDebug('Starting Management plugin')

		# Enable the management endpoint
		if Configuration.http_enableManagementEndpoint:
			path = self.httpServer.addEndpoint('__mgmt__', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>/<subparam>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)

			self.httpServer.addEndpoint('__mgmt__', handler=self.handleManagementPost, methods=['POST'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>', handler=self.handleManagementPost, methods=['POST'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>', handler=self.handleManagementPost, methods=['POST'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>/<subparam>', handler=self.handleManagementPost, methods=['POST'], strictSlashes=False)

			self.httpServer.addEndpoint('__mgmt__', handler=self.handleManagementPut, methods=['PUT'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>', handler=self.handleManagementPut, methods=['PUT'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>', handler=self.handleManagementPut, methods=['PUT'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>/<subparam>', handler=self.handleManagementPut, methods=['PUT'], strictSlashes=False)


			self.httpServer.addEndpoint('__mgmt__', handler=self.handleManagementDelete, methods=['DELETE'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>', handler=self.handleManagementDelete, methods=['DELETE'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>', handler=self.handleManagementDelete, methods=['DELETE'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>/<subparam>', handler=self.handleManagementDelete, methods=['DELETE'], strictSlashes=False)

			L.isInfo and L.log(f'Registered management endpoint at: {path}')


	@configure
	def configure(self, config: Configuration) -> None:
		""" Configure the plugin based on the configuration settings.
			
			Args:
				config: The configuration object.
		"""
		parser = config.configParser
		config.http_enableManagementEndpoint = parser.getboolean('http', 'enableManagementEndpoint', fallback=False)


	def _response(self, response: Any, status: int = 200, mimetype: str = 'application/json') -> Response:
		""" Create a Flask Response object with the given response data, status code, and mimetype.

			Args:
				response: The response data to include in the response.
				status: The HTTP status code for the response. Default is 200 (OK).
				mimetype: The MIME type of the response. Default is 'application/json'.

			Return:
				A Flask Response object.
		"""
		from flask import Response
		return Response(response=response, status=status, mimetype=mimetype, headers=self.httpServer._responseHeaders)
	

	def handleManagement(self, command: Optional[str] = None, param: Optional[str] = None, subparam: Optional[str] = None) -> Response: # type: ignore
		"""	Handle a management request. This is used to control the CSE.

			Args:
				command: The management command to execute. If None, the request is rejected.
				param: An optional parameter for the management command.
				subparam: An optional sub-parameter for the management command.
			

			Return:
				A response object.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response

			if self.httpServer.isStopped:
				return self._response('{ "error" : "Service not available" }', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if self.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)
			
			try:
				command = command.lower() if command else None
				L.isInfo and L.log(f'Management request: {command}{"(" + param + ")" if param else ""}')
				match command:
					case 'config':
						return self._getConfig()
					case 'creds':
						return self._getCreds(param, subparam)
					case 'log':
						return self._response(self.managementSupport.getLogGenerator(), mimetype='text/event-stream')
					case 'loglevel':
						if param is None: # No parameter given, return the current log level
							return self._response(self.managementSupport.getLoglevel())
						else: # A parameter is given, try to set the log level
							match param.lower():
								case 'info' | 'debug' | 'warning' | 'error' | 'off':
									_n = self.managementSupport.setLogLevel(param)
									return self._response(f'{{ "message": "Log level set to {_n}" }}')
								case 'help':
									return self._response('''ACME oneM2M CSE Management Log Commands
							
(no parameter)  Return the current log level
debug           Set log level to DEBUG
info            Set log level to INFO
warning         Set log level to WARNING
error           Set log level to ERROR
off             Set log level to OFF
help            Show this help message
''')
								case _:
									return self._response(f'{{ "error" : "Unknown log level: {param}. Valid log levels: {list(LogLevel.__members__.keys())}" }}')

					case 'policies':
						if param is None:
							return self._response('Use "policies/help" for a list of policy management commands.', status=422, mimetype='text/plain')
						match param.lower():
							case 'attributes':
								return self._response(self.managementSupport.getAttributePolicies(subparam))
							case 'flexcontainers':
								return self._response(self.managementSupport.getFlexContainerPolicies(subparam))
							case 'resourcetypes':
								return self._response(self.managementSupport.getResourceTypePolicies(subparam))
							case 'help':
								return self._response('''ACME oneM2M CSE Management Policy Commands
attributes      Get attribute policies (filter: .../attributes{/<attribute>})
flexcontainers  Get flexcontainer policies (filter: .../flexcontainers{/<type or name>})
resourcetypes   Get resource type policies (filter: .../resourcetypes{/<type or name>})
help            Show this help message
''')
							case _:
								return self._response(f'Unknown policy management command: {param}. Use "policies/help" for a list of commands.', status=422, mimetype='text/plain')
					case 'registrations':
						if param is None:
							return self._response(self.managementSupport.getRegistrations())
						else:
							match param.lower():
								case 'refresh':
									return self._response(self.managementSupport.refreshRegistrations())
								case 'help':
									return self._response('''ACME oneM2M CSE Management Registrations Commands
							
(no command)    Get current registrations
refresh         Refresh registrations
help            Show this help message
''')
								case _:
									L.isWarn and L.logWarn(f'Unknown management registrations command: {param}')
									return self._response(f'Unknown management registrations command: {param}. Use "registrations/help" for a list of commands.', status=422, mimetype='text/plain')

					case 'requests':
						if param is None:
							return self._response(self.managementSupport.getRequests())
						else:
							match param.lower():
								case 'enable' | 'on' | 'disable' | 'off' | 'status':
									return self._response(self.managementSupport.setRequestRecording(param))
								case 'puml':
									_, puml = self.managementSupport.getRequestsRich()
									return self._response(puml, mimetype='text/plain')
								case 'help':
									return self._response('''ACME oneM2M CSE Management Requests Commands
							
(no command)    Stream the current requests
enable          Enable request recording
disable         Disable request recording
status          Get current request recording status
puml            Get a UML sequence diagram of the recorded requests
help            Show this help message
''', mimetype='text/plain')
								case _:
									L.isWarn and L.logWarn(f'Unknown management requests command: {param}')
									return self._response(f'Unknown management requests command: {param}. Use "requests/help" for a list of commands.', status=422, mimetype='text/plain')
							
					case 'reset':
						self.managementSupport.resetCSE()
						return self._response('{ "message": "CSE resetting" }')

					case 'restart':
						self.managementSupport.restartCSE()	# This might not return (e.g. under Windows)
						return self._response('{ "message": "CSE is shutting down to restart" }')

					case 'shutdown':
						self.managementSupport.shutdownCSE()	# This might not return (e.g. under Windows)
						return self._response('{ "message": "CSE is shutting down" }')

					case 'status':
						if param is None:
							return self._response(self.managementSupport.getCSEStatus())
						match param.lower():
							case 'interceptors':
								return self._response(self.managementSupport.getInterceptors())
							case 'modules':
								return self._response(json.dumps(sorted([ { 'name': k, 'file': getattr(m, '__file__', 'built-in') } for k, m in sys.modules.items() ], 
																		   key=lambda d: d['name']), 
																 indent=4))
							case 'plugins':
								return self._response(response=self.managementSupport.getPlugins())
							case 'services':
								return self._response(self.managementSupport.getServices())
							case 'help':
								return self._response('''ACME oneM2M CSE Management Status Commands
						
(no command)    General status information about the CSE
interceptors    Information about the registered interceptors
modules         Information about the loaded Python modules
plugins         Information about the loaded plugins
services        Information about the registered services and endpoints
help            Show this help message
''', mimetype='text/plain')

					case 'help':
							return self._getHelp()
					case _:
						L.isWarn and L.logWarn(f'Unknown management command: {param}')
						return self._response(f'Unknown management command: {param}. Use "help" for a list of commands.', status=422, mimetype='text/plain')

			except Exception as e:
				return self._response(f'{{ "error" : "Error occurred while processing command: {e}" }}', status=500)

			return self._response('Unsupported command. Use "help" for a list of commands.', status=422)


	def _getHelp(self) -> Response: # type: ignore
		"""	Handle the help command. This is used to provide a list of available management commands.

			Return:
				A response object with the help message.
		"""
		return self._response('''ACME oneM2M CSE Management Commands

config          Get the current configuration
creds           Credential management (s. .../creds/help)
log             Stream the live log output
loglevel        Get or set the log level (s. .../loglevel/help)
policies        Get the current policies (s. .../policies/help)
registrations   Get or refresh the registrations (s. .../registrations/help)
requests        Get or set the request recording (s. .../requests/help)
reset           Reset the CSE
restart         Shutdown the CSE with exit code 82 (indicating a restart)
shutdown        Shutdown the CSE normally (with exit code 0)
status          Get the current CSE status (s. .../status/help)
help            Show this help message
				  
For example, to get the current log level, use the following URL: 
http(s)://<host>:<port>/__mgmt__/loglevel
				  
More management commands are available for POST, PUT and DELETE requests.
Use the management endpoint with the appropriate HTTP method to access them.
''', mimetype='text/plain')


	def _getConfig(self) -> Response: # type: ignore
		""" Handle the config command. This is used to provide the current configuration of the CSE.

			Return:
				A response object with the current configuration.
		"""
		return self._response(self.managementSupport.getConfig())


	def _getCreds(self, param: Optional[str] = None, subparam: Optional[str] = None) -> Response: # type: ignore
		""" Handle the creds command. This is used to provide the current credentials of the CSE.

			Args:
				param: An optional parameter for the management command.
				subparam: An optional sub-parameter for the management command.

			Return:
				A response object with the current credentials.
		"""
		if param is None:
			return self._response(f'Use "creds/help" for a list of credential management commands.', status=422, mimetype='text/plain')

		match param.lower():
			case 'httpbasic':
				return self._response(self.managementSupport.getBasicCredentials(BindingType.HTTP))
			case 'httptoken':
				return self._response(self.managementSupport.getTokenCredentials(BindingType.HTTP))
			case 'wsbasic':
				return self._response(self.managementSupport.getBasicCredentials(BindingType.WS))
			case 'wstoken':
				return self._response(self.managementSupport.getTokenCredentials(BindingType.WS))
			case 'reload':
				return self._response(self.managementSupport.reloadCredentials())
			case 'help':
				return self._response('''ACME oneM2M CSE Management Credential Commands
		
httpbasic       Get HTTP basic authentication credentials
httptoken       Get HTTP token authentication credentials
wsbasic         Get WebSocket basic authentication credentials
wstoken         Get WebSocket token authentication credentials
reload          Reload HTTP and WebSocket credentials
help            Show this help message
'''
				, mimetype='text/plain')
			case _:
				return self._response(f'Unknown credential management command: {param}. Use "creds/help" for a list of commands.', status=422, mimetype='text/plain')


	#########################################################################
	#
	#	Setting management commands (POST)
	#

	def handleManagementPost(self, command: Optional[str] = None, param: Optional[str] = None, subparam: Optional[str] = None) -> Response: # type: ignore
		"""	Handle a management request. This is used to control the CSE.

			Args:
				command: The management command to execute. If None, the request is rejected.
				param: An optional parameter for the management command.
				subparam: An optional sub-parameter for the management command.
			

			Return:
				A response object.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response, request

			if self.httpServer.isStopped:
				return self._response('{ "error": "Service not available" }', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if self.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)

			# Get the json with a meanuningful error message if the json is invalid
			try:
				jsn = json.loads(request.data)
			except json.JSONDecodeError as e:
				return self._response(f'{{ "error": "Invalid JSON", "detail": "{str(e)}" }}', status=400)

			mtype = 'application/json'
			match command:
				case 'creds':
					if param is None:
						return self._response('Use "creds/help" for a list of credential management POST commands.', status=422, mimetype='text/plain')

					match param.lower():
						case 'httpbasic':
							return self._response(self.managementSupport.addBasicCredentials(jsn, BindingType.HTTP))
						case 'httptoken':
							return self._response(self.managementSupport.addTokenCredentials(jsn, BindingType.HTTP))
						case 'wsbasic':
							return self._response(self.managementSupport.addBasicCredentials(jsn, BindingType.WS))
						case 'wstoken':
							return self._response(self.managementSupport.addTokenCredentials(jsn, BindingType.WS))
						case 'help':
							return self._response('''ACME oneM2M CSE Management Credential POST Commands
					   
httpbasic       Add HTTP basic authentication credentials (JSON: "username", "password")
httptoken       Add HTTP token authentication credentials (JSON: "token")
wsbasic         Add WebSocket basic authentication credentials (JSON: "username", "password")
wstoken         Add WebSocket token authentication credentials (JSON: "token")
help            Show this help message
''', mimetype='text/plain')
						case _:
							return self._response(f'Unknown credential management command: {param}. Use "creds/help" for a list of commands.', status=422, mimetype='text/plain')

				case 'help':
					return self._response('''ACME oneM2M CSE Management POST Commands
					 
creds           Add credentials for the given type
help            Show this help message
''', mimetype='text/plain')
				case _:
					return self._response(f'Unknown management command: {command}. Use "help" for a list of POST commands.', status=422, mimetype='text/plain')


	#########################################################################
	#
	#	Setting management commands (PUT)
	#

	def handleManagementPut(self, command: Optional[str] = None, param: Optional[str] = None, subparam: Optional[str] = None) -> Response: # type: ignore
		"""	Handle a management request. This is used to update internal management data in the CSE.

			Args:
				command: The management command to execute. If None, the request is rejected.
				param: An optional parameter for the management command.
				subparam: An optional sub-parameter for the management command.

			Return:
				A response object.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response, request

			if self.httpServer.isStopped:
				return self._response('{ "error": "Service not available" }', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if self.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)

			# Get the json with a meanuningful error message if the json is invalid
			try:
				if command and command.lower() not in ['help'] and param and param.lower() not in ['help']:
					jsn = json.loads(request.data)
			except json.JSONDecodeError as e:
				return self._response(f'{{ "error": "Invalid JSON", "detail": "{str(e)}" }}', status=400)
			
			match command:
				case 'creds':
					if param is None:
						return self._response('Use "creds/help" for a list of credential management PUT commands.', status=422, mimetype='text/plain')

					match param.lower():
						case 'httpbasic':
							return self._response(self.managementSupport.updateBasicCredentials(jsn, BindingType.HTTP))
						case 'httptoken':
							return self._response(self.managementSupport.updateTokenCredentials(jsn, BindingType.HTTP))
						case 'wsbasic':
							return self._response(self.managementSupport.updateBasicCredentials(jsn, BindingType.WS))
						case 'wstoken':
							return self._response(self.managementSupport.updateTokenCredentials(jsn, BindingType.WS))

						case 'help':
							return self._response('''ACME oneM2M CSE Management Credential PUT Commands
					   
httpbasic       Update HTTP basic authentication credentials (JSON: "username", "password")
httptoken       Update HTTP token authentication credentials (JSON: "token", "new")
wsbasic         Update WebSocket basic authentication credentials (JSON: "username", "password")
wstoken         Update WebSocket token authentication credentials (JSON: "token", "new")
help            Show this help message
''', mimetype='text/plain')
						
				case 'help':
					return self._response('''ACME oneM2M CSE Management PUT Commands
					 
creds           Update credentials for the given type and username
help            Show this help message
''', mimetype='text/plain')


			return self._response('Unsupported command. Use "help" for a list of PUT commands.', status=402, mimetype='text/plain')
		   			
			

	#########################################################################
	#
	#	Setting management commands (DELETE)
	#

	def handleManagementDelete(self, command: Optional[str] = None, param: Optional[str] = None, subparam: Optional[str] = None) -> Response: # type: ignore
		"""	Handle a management request. This is used to delete internal management data in the CSE.

			Args:
				command: The management command to execute. If None, the request is rejected.
				param: An optional parameter for the management command.
				subparam: An optional sub-parameter for the management command.

			Return:
				A response object.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response, request

			if self.httpServer.isStopped:
				return self._response('{ "error": "Service not available" }', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if self.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)

			match command:
				case 'creds':
					if param is None:
						return self._response(f'"Use "creds/help" for a list of credential management DELETE commands."', status=422, mimetype='text/plain')

					match param.lower():
						case 'httpbasic':
							return self._response(self.managementSupport.deleteBasicCredentials(subparam, BindingType.HTTP))
						case 'httptoken':
							return self._response(self.managementSupport.deleteTokenCredentials(subparam, BindingType.HTTP))
						case 'wsbasic':
							return self._response(self.managementSupport.deleteBasicCredentials(subparam, BindingType.WS))
						case 'wstoken':
							return self._response(self.managementSupport.deleteTokenCredentials(subparam, BindingType.WS))
						case 'help':
							return self._response('''ACME oneM2M CSE Management Credential DELETE Commands

httpbasic/<username>       Delete HTTP basic authentication credentials for the given username
httptoken/<token>          Delete HTTP token authentication credentials for the given token
wsbasic/<username>         Delete WebSocket basic authentication credentials for the given username
wstoken/<token>            Delete WebSocket token authentication credentials for the given token
help                       Show this help message
''', mimetype='text/plain')
				case 'help':
					return self._response('''ACME oneM2M CSE Management DELETE Commands

creds                      Delete credentials for the given type and username
help                       Show this help message
''', mimetype='text/plain')

			return self._response('Unsupported command. Use "help" for a list of DELETE commands."', status=422, mimetype='text/plain')