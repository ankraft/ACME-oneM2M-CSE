#
#	HttpStructure.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Structure functionality for the http server. """

from __future__ import annotations

from typing import Optional
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..helpers.PluginManager import pluginClass, start, configure
from ..runtime.Configuration import Configuration


@pluginClass('httpStructure')
class HttpStructure:
	"""	Plugin class to add the Structure functionality to the HTTP server.
	"""

	@start
	def startStructure(self) -> None:
		L.isDebug and L.logDebug('Starting Structure plugin')
		# Enable the config endpoint
		if Configuration.http_enableStructureEndpoint:
			path = CSE.httpServer.addEndpoint('__structure__', handler=self.handleStructure, methods=['GET'], strictSlashes=False)
			CSE.httpServer.addEndpoint('__structure__/<path:path>', handler=self.handleStructure, methods=['GET', 'PUT'])
			L.isInfo and L.log(f'Registering structure endpoint at: {path}')


	@configure
	def configure(self, config: Configuration) -> None:
		parser = config.configParser
		config.http_enableStructureEndpoint = parser.getboolean('http', 'enableStructureEndpoint', fallback=False)


	def handleStructure(self, path:Optional[str]='puml') -> Response: # type: ignore
		"""	Handle a structure request. Return a description of the CSE's current resource
			and registrar / registree deployment.
			An optional parameter 'lvl=<int>' can limit the generated resource tree's depth.
		"""
		with CSE.httpServer.flaskApp.app_context():
			from flask import Response, request
			if CSE.httpServer.isStopped:
				return Response('Service not available', status=503)
			lvl = request.args.get('lvl', default=0, type=int)
			if path == 'puml':
				return Response(response=CSE.statistics.getStructurePuml(lvl), headers=CSE.httpServer._responseHeaders)
			if path == 'text':
				return Response(response=CSE.console.getResourceTreeText(lvl), headers=CSE.httpServer._responseHeaders)
			return Response(response='unsupported', status=422, headers=CSE.httpServer._responseHeaders)

