#
#	HttpWebUI.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Plugin to add the Web UI functionality for the http server. """

from __future__ import annotations

from typing import Optional
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..etc.Constants import Constants
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.PluginManager import pluginClass, start, configure, validate
from ..runtime.Configuration import Configuration
from ..webui.webUI import WebUI


@pluginClass
class HttpWebUI:
	"""	Plugin class to add the Web UI functionality to the HTTP server.
	"""

	webuiDirectory:Optional[str] = None
	""" The directory where the web UI is located. """

	webui:Optional[WebUI] = None
	""" The web UI instance. """


	@start
	def startWebUI(self) -> None:
		L.isDebug and L.logDebug('Starting Web UI plugin')
		# Register the endpoint for the web UI
		# This is done by instancing the otherwise "external" web UI
		self.webui = WebUI(CSE.httpServer.flaskApp, 
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
		parser = config.configParser
		config.webui_root = parser.get('webui', 'root', fallback='/webui')


	@validate
	def validate(self, config: Configuration) -> None:
		self.webuiDirectory = f'{Configuration.moduleDirectory}/webui'
