#
#	HttpManagement.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Management functionality for the http server. """

from __future__ import annotations

from typing import Optional
from ....runtime import CSE
from ....runtime.Logging import Logging as L
from ....etc.Types import LogLevel, AuthorizationResult
from ....helpers.PluginManager import pluginClass, start, configure
from ....runtime.Configuration import Configuration
from ....runtime import Management as Mgmt


@pluginClass
class HttpManagement:
	"""	Plugin class to add the Management functionality to the HTTP server.
	"""

	@start
	def startManagement(self) -> None:
		L.isDebug and L.logDebug('Starting Management plugin')
		# Enable the management endpoint
		if Configuration.http_enableManagementEndpoint:
			path = CSE.httpServer.addEndpoint('__mgmt__', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			CSE.httpServer.addEndpoint('__mgmt__/<command>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
			CSE.httpServer.addEndpoint('__mgmt__/<command>/<param>', handler=self.handleManagement, methods=['GET'], strictSlashes=False)
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
		with CSE.httpServer.flaskApp.app_context():
			from flask import Response

			if CSE.httpServer.isStopped:
				return Response('Service not available', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if CSE.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)
			
			try:
				command = command.lower() if command else None
				L.isInfo and L.log(f'Management request: {command}{"(" + param + ")" if param else ""}')
				match command:

					case 'config':
						return Response(response=Mgmt.getConfig(), mimetype='application/json',	headers=CSE.httpServer._responseHeaders)
				
					case 'log':
						return Response(Mgmt.getLogGenerator(), mimetype='text/event-stream')
						
					case 'loglevel':
						if param is None: # No parameter given, return the current log level
							return Response(response=Mgmt.getLoglevel(), headers=CSE.httpServer._responseHeaders)
						else: # A parameter is given, try to set the log level
							match param.lower():
								case 'info' | 'debug' | 'warning' | 'error' | 'off':
									_n = Mgmt.setLogLevel(param)
									return Response(response=f'Log level set to {_n}', headers=CSE.httpServer._responseHeaders)
								case _:
									return Response(response=f'Unknown log level: {param}.\nValid log levels are: {list(LogLevel.__members__.keys())}', 
													status=422, 
													headers=CSE.httpServer._responseHeaders)

					case 'registrations':
						if param is None:
							return Response(response=Mgmt.getRegistrations(), mimetype='application/json', headers=CSE.httpServer._responseHeaders)
						else:
							match param.lower():
								case 'refresh':
									return Response(response=Mgmt.refreshRegistrations(), headers=CSE.httpServer._responseHeaders)
								case 'help':
									return Response(response='''ACME oneM2M CSE Management Registrations Commands
							
(no command)  Get the current registrations
refresh       Refresh the registrations
help          Show this help message
''',
										status=200,
										headers=CSE.httpServer._responseHeaders)
								case _:
									L.isWarn and L.logWarn(f'Unknown management registrations command: {param}')
									return Response(response=f'Unknown management registrations command: {param}.\nUse "registrations/help" for a list of commands.', 
													status=422, 
													headers=CSE.httpServer._responseHeaders)

					case 'requests':
						if param is None:
							return Response(response=Mgmt.getRequests(), mimetype='application/json', headers=CSE.httpServer._responseHeaders)
						else:
							match param.lower():
								case 'enable' | 'on' | 'disable' | 'off' | 'status':
									return Response(response=Mgmt.setRequestRecording(param), headers=CSE.httpServer._responseHeaders)
								case 'puml':
									_, puml = Mgmt.getRequestsRich()
									return Response(response=puml, headers=CSE.httpServer._responseHeaders)
								case 'help':
									return Response(response='''ACME oneM2M CSE Management Requests Commands
							
(no command)  Stream the current requests
enable        Enable request recording
disable       Disable request recording
status        Get the current request recording status
puml		  Get a UML sequence diagram of the recorded requests
help          Show this help message
''',
										status=200,
										headers=CSE.httpServer._responseHeaders)
								case _:
									L.isWarn and L.logWarn(f'Unknown management requests command: {param}')
									return Response(response=f'Unknown management requests command: {param}.\nUse "requests/help" for a list of commands.', 
													status=422, 
													headers=CSE.httpServer._responseHeaders)
							
							
					case 'reset':
						Mgmt.resetCSE()
						return Response(response='CSE resetting', headers=CSE.httpServer._responseHeaders)
					
					case 'restart':
						Mgmt.restartCSE()	# This might not return (e.g. under Windows)
						return Response(response='CSE is shutting down to restart', headers=CSE.httpServer._responseHeaders)

					case 'shutdown':
						Mgmt.shutdownCSE()	# This might not return (e.g. under Windows)
						return Response(response='CSE is shutting down', headers=CSE.httpServer._responseHeaders)

					case 'status':
						return Response(response=Mgmt.getCSEStatus(), mimetype='application/json', headers=CSE.httpServer._responseHeaders)

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
										headers=CSE.httpServer._responseHeaders)

					case _:
						L.isWarn and L.logWarn(f'Unknown management command: {command}')

			except Exception as e:
				return Response(response=L.logWarn(f'Error occurred while processing command: {e}'),
								status=500, 
								headers=CSE.httpServer._responseHeaders)

			return Response(response='Unsupported command.\nUse "help" for a list of commands.', 
							status=422, 
							headers=CSE.httpServer._responseHeaders)

