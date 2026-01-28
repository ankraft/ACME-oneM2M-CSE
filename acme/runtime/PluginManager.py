#
#	PluginManager.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Plugin manager to manage plugins.
"""	Plugin manager to manage plugins. """

from __future__ import annotations
from ..helpers.PluginManager import PluginManager as PM
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..runtime.Logging import Logging as L


class PluginManager(PM):

	def __init__(self) -> None:
		"""	Runtime instance of the `PluginManager`. """
		super().__init__()

		# Add handler for restart event
		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore

		L.isDebug and L.logDebug('Initializing PluginManager')


		def _loadPluginsFromDirectory(directory:str, packagePath:str) -> None:
			"""	Load plugins from a specific directory. Ignore if the directory does not exist. 
			
				Args:
					directory (str): The directory to load plugins from.
					packagePath (str): The package path for the plugins.
			"""
			try:
				self.loadPlugins(directory=directory, 
								 packagePath=packagePath, 
								 disabledPlugins=Configuration.cse_operation_plugins_disabledPlugins, 
								 replace=Configuration.cse_operation_plugins_replace)
			except NotADirectoryError:
				# Ignore if the directory does not exist
				L.isDebug and L.logDebug(f'Plugin directory not found: {directory}')
				pass

		# Load plugins, configure, validate and start them
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/plugins', 'acme.plugins')			# Load system plugins
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/services/plugins', 'acme.services')	# Load system services plugins
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/runtime/plugins', 'acme.runtime')	# Load system runtime plugins
		_loadPluginsFromDirectory(f'{Configuration.baseDirectory}/plugins', 'acme.plugins')				# Load user plugins

		L.isInfo and L.log(f'Loaded plugins: {", ".join(self.plugins.keys())}')

		# Configure, validate and start plugins
		self.configurePlugins(None, Configuration)
		self.validatePlugins(None, Configuration)
		self.startPlugins()
		L.isInfo and L.log('Plugins configured and started')


	def restart(self, _: str) -> None:
		"""	Restart the PluginManager service.
		"""
		self.restartPlugins()
		L.isDebug and L.logDebug('Plugins restarted')

		
	def shutdown(self) -> bool:
		"""	Shutdown the PluginManager service and plugins.
		"""
		# Shutdown plugins
		L.isInfo and L.log('Shutting down and unloading plugins')
		self.unloadPlugins()	# This implicitly stops the plugins as well
		L.isInfo and L.log('Plugins stopped and unloaded')
		return True
