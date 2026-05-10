#
#	HttpStructure.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Structure functionality for the http server. """

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from acme.runtime.Logging import Logging as L
from acme.helpers.PluginManager import plugin, start, configure, requires
from acme.runtime.Configuration import Configuration

if TYPE_CHECKING:
	from acme.runtime.Management import ManagementSupport
	from acme.plugins.bindings.HttpServer import HttpServer


@plugin(tags=['acme', 'core'])
@requires(httpServer='acme.plugins.bindings.HttpServer')
@requires(managementSupport='acme.runtime.Management')
class HttpStructure:
	"""	Plugin class to add the Structure functionality to the HTTP server.
	"""

	managementSupport: ManagementSupport = None
	""" Injected ManagementSupport instance. """

	# "httpServer" is injected by the PluginManager, only if the HttpServer plugin is loaded and the dependency can be resolved.
	httpServer: HttpServer = None	# type: ignore
	"""	The injected HttpServer plugin instance is injected by the PluginManager based on the declared dependency. The plugin will only be loaded if the HttpServer plugin is loaded. """

	@start
	def startStructure(self) -> None:
		L.isDebug and L.logDebug('Starting Structure plugin')
		# Enable the config endpoint
		if Configuration.http_enableStructureEndpoint:
			path = self.httpServer.addEndpoint('__structure__', handler=self.handleStructure, methods=['GET'], strictSlashes=False)
			self.httpServer.addEndpoint('__structure__/<path:path>', handler=self.handleStructure, methods=['GET', 'PUT'])
			L.isInfo and L.log(f'Registering structure endpoint at: {path}')


	@configure
	def configure(self, config: Configuration) -> None:
		parser = config.configParser
		config.http_enableStructureEndpoint = parser.getboolean('http', 'enableStructureEndpoint', fallback=False)


	def handleStructure(self, path: Optional[str] = 'puml') -> Response: # type: ignore
		"""	Handle a structure request. Return a description of the CSE's current resource
			and registrar / registree deployment.
			An optional parameter 'lvl=<int>' can limit the generated resource tree's depth.
		"""
		with self.httpServer.flaskApp.app_context():
			from flask import Response, request
			if self.httpServer.isStopped:
				return Response('Service not available', status=503)
			lvl = request.args.get('lvl', default=0, type=int)
			match path:
				case 'puml':
					return Response(response=self.managementSupport.getStructurePuml(lvl), headers=self.httpServer._responseHeaders)
				case 'text':
					return Response(response=self.managementSupport.getResourceTreeText(lvl), headers=self.httpServer._responseHeaders)
				case 'help':
					return Response(response='''ACME oneM2M CSE Structure Commands
							
(no command)  Same as "puml"
puml          Resource and deployment structure in PlantUML format
text          Resource and deployment structure in text format
help          Show this help message
					 
Arguments:
lvl=<int>    Limit the depth of the generated resource tree (default: 0, no limit)
''',
									headers=self.httpServer._responseHeaders)

				case _:
					return Response(response='unsupported', status=422, headers=self.httpServer._responseHeaders)

