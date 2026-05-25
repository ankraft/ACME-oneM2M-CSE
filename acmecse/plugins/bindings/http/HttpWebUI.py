#
#	HttpWebUI.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Web UI functionality for the http server. """

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from acmecse.runtime.Logging import Logging as L
from acmecse.etc.Constants import Constants
from acmecse.etc.Constants import RuntimeConstants as RC
from acmecse.helpers.PluginManager import plugin, start, configure, validate, requires
from acmecse.runtime.Configuration import Configuration
from acmecse.webui.webUI import WebUI

if TYPE_CHECKING:
	from acmecse.plugins.bindings.HttpServer import HttpServer

@plugin(tags=['acme', 'core', 'ui'])
@requires(httpServer='acmecse.plugins.bindings.HttpServer')
class HttpWebUI:
	"""	Plugin class to add the Web UI functionality to the HTTP server.

		The web UI is registered at the root of the HTTP server or at the path specified in the configuration under the endpoint "webui".
	"""

	# "httpServer" is injected by the PluginManager, only if the HttpServer plugin is loaded and the dependency can be resolved.
	httpServer: HttpServer = None	# type: ignore
	"""	The injected HttpServer plugin instance is injected by the PluginManager based on the declared dependency. The plugin will only be loaded if the HttpServer plugin is loaded. """

	webuiDirectory:Optional[str] = None
	""" The directory where the web UI is located. """

	webui:Optional[WebUI] = None
	""" The web UI instance. """


	@start
	def startWebUI(self) -> None:
		""" Start the web UI plugin. 
		"""
		L.isDebug and L.logDebug('Starting Web UI plugin')
		# Register the endpoint for the web UI
		# This is done by instancing the otherwise "external" web UI
		self.webui = WebUI(self.httpServer.flaskApp, 
						   defaultRI=RC.cseRi, 
						   defaultOriginator=RC.cseOriginator, 
						   root=Configuration.webui_root,
						   webuiDirectory=self.webuiDirectory,
						   redirectURL=f'{Configuration.http_address}' if Configuration.http_root else None,
						   version=Constants.version,
						   httpRoot=Configuration.http_root,
						   externalRoot=Configuration.http_externalRoot)


	@configure
	def configure(self, config: Configuration) -> None:
		""" Configure the plugin based on the configuration settings.
			
			Args:
				config: The configuration object.
		"""
		parser = config.configParser
		config.webui_root = parser.get('webui', 'root', fallback='/webui')
		config.webui_enable = parser.getboolean('webui', 'enable', fallback=True)


	@validate
	def validate(self, config: Configuration) -> None:
		""" Validate the plugin configuration.
			
			Args:
				config: The configuration object.
		"""
		self.webuiDirectory = f'{Configuration.moduleDirectory}/webui'
