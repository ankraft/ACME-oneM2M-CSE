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
from ....runtime.Logging import Logging as L
from ....etc.Types import LogLevel, AuthorizationResult
from ....helpers.PluginManager import plugin, start, configure, requires
from ....runtime.Configuration import Configuration

if TYPE_CHECKING:
	from ....runtime.Management import ManagementSupport
	
@plugin(tags=['acme', 'core'])
@requires(httpServer='acme.plugins.bindings.HttpServer')
@requires(managementSupport='acme.runtime.Management') 
class HttpManagement:
	"""	Plugin class to add the Management functionality to the HTTP server.

		The management endpoint is registered at `__mgmt__`.

		The plugin depends on the `HttpServer` plugin, which is injected into this plugin by the `PluginManager`. 
		The management endpoint will only be registered if the `HttpServer` plugin is loaded and the dependency can be resolved. 
	"""

	# "httpServer" is injected by the PluginManager, only if the HttpServer plugin is loaded and the dependency can be resolved.
	httpServer: Any = None	# type: ignore
	"""	The HttpServer plugin instance is injected by the PluginManager based on the declared dependency. The plugin will only be loaded if the HttpServer plugin is loaded. """


	managementSupport: ManagementSupport = None
	""" ManagementSupport instance. """

	@start
	def startManagement(self) -> None:
		L.isDebug and L.logDebug('Starting Management plugin')

		# Enable the management endpoint
		if Configuration.http_enableManagementEndpoint:
			path = self.httpServer.addEndpoint('__mgmt__', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			self.httpServer.addEndpoint('__mgmt__/<command>/<param>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			L.isInfo and L.log(f'Registered management endpoint at: {path}')


	@configure
	def configure(self, config: Configuration) -> None:
		parser = config.configParser
		config.http_enableManagementEndpoint = parser.getboolean('http', 'enableManagementEndpoint', fallback=False)


	def handleManagement(self, command:Optional[str]=None, param:Optional[str]=None) -> Response: # type: ignore
		"""	Handle a management request. This is used to control the CSE.

			Args:
				command: The management command to execute. If None, the request is rejected.
			
			Return:
				A response object.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response

			if self.httpServer.isStopped:
				return Response('Service not available', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if self.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)
			
			try:
				command = command.lower() if command else None
				L.isInfo and L.log(f'Management request: {command}{"(" + param + ")" if param else ""}')
				match command:

					case 'config':
						return Response(response=self.managementSupport.getConfig(), mimetype='application/json',	headers=self.httpServer._responseHeaders)
				
					case 'log':
						return Response(self.managementSupport.getLogGenerator(), mimetype='text/event-stream')

					case 'loglevel':
						if param is None: # No parameter given, return the current log level
							return Response(response=self.managementSupport.getLoglevel(), headers=self.httpServer._responseHeaders)
						else: # A parameter is given, try to set the log level
							match param.lower():
								case 'info' | 'debug' | 'warning' | 'error' | 'off':
									_n = self.managementSupport.setLogLevel(param)
									return Response(response=f'Log level set to {_n}', headers=self.httpServer._responseHeaders)
								case 'help':
									return Response(response='''ACME oneM2M CSE Management Log Commands
							
(no parameter)  Stream the live log output
debug           Set log level to DEBUG
info            Set log level to INFO
warning         Set log level to WARNING
error           Set log level to ERROR
off             Set log level to OFF
help            Show this help message
''',
											status=200,
											headers=self.httpServer._responseHeaders)
								case _:
									return Response(response=f'Unknown log level: {param}.\nValid log levels are: {list(LogLevel.__members__.keys())}', 
													status=422, 
													headers=self.httpServer._responseHeaders)

					case 'registrations':
						if param is None:
							return Response(response=self.managementSupport.getRegistrations(), 
					   						mimetype='application/json', 
											headers=self.httpServer._responseHeaders)
						else:
							match param.lower():
								case 'refresh':
									return Response(response=self.managementSupport.refreshRegistrations(), 
						 							headers=self.httpServer._responseHeaders)
								case 'help':
									return Response(response='''ACME oneM2M CSE Management Registrations Commands
							
(no command)  Get the current registrations
refresh       Refresh the registrations
help          Show this help message
''',
										status=200,
										headers=self.httpServer._responseHeaders)
								case _:
									L.isWarn and L.logWarn(f'Unknown management registrations command: {param}')
									return Response(response=f'Unknown management registrations command: {param}.\nUse "registrations/help" for a list of commands.', 
													status=422, 
													headers=self.httpServer._responseHeaders)

					case 'requests':
						if param is None:
							return Response(response=self.managementSupport.getRequests(), 
					   						mimetype='application/json', 
											headers=self.httpServer._responseHeaders)
						else:
							match param.lower():
								case 'enable' | 'on' | 'disable' | 'off' | 'status':
									return Response(response=self.managementSupport.setRequestRecording(param), 
						 							headers=self.httpServer._responseHeaders)
								case 'puml':
									_, puml = self.managementSupport.getRequestsRich()
									return Response(response=puml, 
						 							headers=self.httpServer._responseHeaders)
								case 'help':
									return Response(response='''ACME oneM2M CSE Management Requests Commands
							
(no command)  Stream the current requests
enable        Enable request recording
disable       Disable request recording
status        Get the current request recording status
puml          Get a UML sequence diagram of the recorded requests
help          Show this help message
''',
										status=200,
										headers=self.httpServer._responseHeaders)
								case _:
									L.isWarn and L.logWarn(f'Unknown management requests command: {param}')
									return Response(response=f'Unknown management requests command: {param}.\nUse "requests/help" for a list of commands.', 
													status=422, 
													headers=self.httpServer._responseHeaders)
							
							
					case 'reset':
						self.managementSupport.resetCSE()
						return Response(response='CSE resetting', headers=self.httpServer._responseHeaders)
					
					case 'restart':
						self.managementSupport.restartCSE()	# This might not return (e.g. under Windows)
						return Response(response='CSE is shutting down to restart', headers=self.httpServer._responseHeaders)

					case 'shutdown':
						self.managementSupport.shutdownCSE()	# This might not return (e.g. under Windows)
						return Response(response='CSE is shutting down', headers=self.httpServer._responseHeaders)

					case 'status':
						if param is None:
							return Response(response=self.managementSupport.getCSEStatus(), 
					   mimetype='application/json', headers=self.httpServer._responseHeaders)
						match param.lower():
							case 'modules':
								return Response(response=json.dumps(sorted([ { 'name': k, 'file': getattr(m, '__file__', 'built-in') } for k, m in sys.modules.items() ], 
																		   key=lambda d: d['name']), 
																	indent=4), 
												mimetype='application/json', 
												headers=self.httpServer._responseHeaders)
							case 'plugins':
								return Response(response=self.managementSupport.getPlugins(), 
												mimetype='application/json', 
												headers=self.httpServer._responseHeaders)
							case 'services':
								return Response(response=self.managementSupport.getServices(), 
												mimetype='application/json', 
												headers=self.httpServer._responseHeaders)
							case 'help':
								return Response(response='''ACME oneM2M CSE Management Status Commands
						
(no command)  Generale status information about the CSE
modules       Information about the loaded Python modules
plugins       Information about the loaded plugins
services      Information about the registered services and endpoints
help          Show this help message
''',
									status=200,
									headers=self.httpServer._responseHeaders)

					case 'help':
						return Response(response='''ACME oneM2M CSE Management Commands

config         Get the current configuration
log            Stream the live log output
loglevel       Get or set the log level (.../{info|debug|warning|error|off})
registrations  Get or refresh the registrations (.../refresh)
requests       Get or set the request recording (.../{on|off|status})
reset          Reset the CSE
restart        Shutdown the CSE with exit code 82 (indicating a restart)
shutdown       Shutdown the CSE normally (with exit code 0)
status         Get the current CSE status
help           Show this help message
''',
										status=200,
										headers=self.httpServer._responseHeaders)

					case _:
						L.isWarn and L.logWarn(f'Unknown management command: {command}')

			except Exception as e:
				return Response(response=L.logWarn(f'Error occurred while processing command: {e}'),
								status=500, 
								headers=self.httpServer._responseHeaders)

			return Response(response='Unsupported command.\nUse "help" for a list of commands.', 
							status=422, 
							headers=self.httpServer._responseHeaders)
