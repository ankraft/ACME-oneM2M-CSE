#
#	HttpUpperTester.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Upper Tester functionality for the http server. """

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from flask import Response
from ....runtime.Logging import Logging as L
from ....etc.Utils import renameThread
from ....etc.Types import ResponseStatusCode, ContentSerializationType, AuthorizationResult
from ....helpers.PluginManager import plugin, start, configure, requires
from ....helpers.interpreter.Interpreter import SType
from ....etc.ResponseStatusCodes import ResponseException
from ....runtime.Configuration import Configuration

if TYPE_CHECKING:
	from ....services.RequestManager import RequestManager
	from ....runtime.ScriptManager import ScriptManager
	from ..HttpServer import HttpServer

@plugin(tags=['acme', 'core'])
@requires(httpServer='acme.plugins.bindings.HttpServer')
@requires(requestManager='acme.services.RequestManager')
@requires(script='acme.runtime.ScriptManager')
class HttpUpperTester:
	"""	Plugin class to add the Upper Tester functionality to the HTTP server.

		See TS-0019 for details about the Upper Tester specification.
	"""


	requestManager: RequestManager = None	# type: ignore
	""" RequestManager instance. """

	script: ScriptManager = None	# type: ignore
	""" ScriptManager instance. """

	# "httpServer" is injected by the PluginManager, only if the HttpServer plugin is loaded and the dependency can be resolved.
	httpServer: HttpServer = None	# type: ignore
	"""	The HttpServer plugin instance is injected by the PluginManager based on the declared dependency. The plugin will only be loaded if the HttpServer plugin is loaded. """

	@start
	def startUpperTester(self) -> None:
		L.isDebug and L.logDebug('Starting Upper Tester plugin')
		# Enable the upper tester endpoint
		if Configuration.http_enableUpperTesterEndpoint:
			path = self.httpServer.addEndpoint('__ut__', handler=self.handleUpperTester, methods=['POST'], strictSlashes=False)
			L.isInfo and L.log(f'Registered upper tester endpoint at: {path}')


	@configure
	def configure(self, config: Configuration) -> None:
		parser = config.configParser
		config.http_enableUpperTesterEndpoint = parser.getboolean('http', 'enableUpperTesterEndpoint', fallback=False)


	def handleUpperTester(self, path:Optional[str]=None) -> Response: # type: ignore
		"""	Handle a Upper Tester request. See TS-0019 for details.

			Args:
				path: The path of the request.

			Return:
				A response object.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response, request

			if self.httpServer.isStopped:
				return Response('Service not available', status=503)

			# Check, when authentication is enabled, the user is authorized, else return status 401
			if self.httpServer.handleAuthentication() == AuthorizationResult.UNAUTHORIZED:
				return Response(status=401)


			def prepareUTResponse(rcs: ResponseStatusCode, result: Optional[str] = None, body: Optional[str|bytes] = None) -> Response:
				"""	Prepare the Upper Tester Response.

					Args:
						rcs: The response status code.
						result: The result to be returned.

					Return:
						The response object.
				"""
				headers = {}
				headers['Server'] = self.httpServer.serverID
				headers['X-M2M-RSC'] = str(rcs.value)	# Set the ResponseStatusCode accordingly
				if result:								# Return an optional return value
					headers['X-M2M-UTRSP'] = result
				resp = Response(status=200 if rcs == ResponseStatusCode.OK else 400, headers=headers, response=body)
				L.isDebug and L.logDebug(f'<== Upper Tester Response:') 
				L.isDebug and L.logDebug(f'Headers: \n{str(resp.headers).rstrip()}')
				return resp


			L.enableScreenLogging and renameThread('UT')
			L.isDebug and L.logDebug(f'==> Upper Tester Request:') 
			L.isDebug and L.logDebug(f'Headers: \n{str(request.headers).rstrip()}')

			# Handle special commands
			if (cmd := request.headers.get('X-M2M-UTCMD')) is not None:
				cmd, _, arg = cmd.partition(' ')
				if not (res := self.script.run(cmd, arg, metaFilter=[ 'uppertester' ], ignoreCase=True))[0]:
					return prepareUTResponse(ResponseStatusCode.BAD_REQUEST, str(res[1]))
				
				if res[1].type in [SType.tList, SType.tListQuote]:
					_r = ','.join(res[1].raw())
				else:
					_r = res[1].toString(quoteStrings=False, pythonList=True)
				return prepareUTResponse(ResponseStatusCode.OK, _r)
			
			# Treat the request as a normal UT request
			
			# Extract the request from the body
			L.isDebug and L.logDebug(f'Body: \n{request.data!r}')
			if request.data:
				try:
					# Dissect the request
					dissectResult = self.requestManager.dissectRequestFromBytes(request.data, ContentSerializationType.getType(request.content_type))
					# Directly handle the request
					responseResult = self.requestManager.handleRequest(dissectResult.request)
				except ResponseException as e:
					return prepareUTResponse(ResponseStatusCode.BAD_REQUEST, body=f'{{ "m2m:dbg" : "{e.dbg}" }}')
				
				# Prepare and send the response
				_rs, _b = self.requestManager.prepareResultForSending(responseResult.prepareResultFromRequest(dissectResult.request),
																	  True, 
																	  dissectResult.request)
				return prepareUTResponse(ResponseStatusCode.OK, body=_b)

			# Return an error if no body or command is present
			return prepareUTResponse(ResponseStatusCode.BAD_REQUEST, L.logWarn('UT requires request body or X-M2M-UTCMD.'))

