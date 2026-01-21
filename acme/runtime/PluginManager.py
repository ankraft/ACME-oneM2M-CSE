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

		# Load plugins, configure, validate and start them
		self.loadPlugins(directory=f'{Configuration.moduleDirectory}/plugins', 
						 packagePath='acme.plugins', 
						 disabledPlugins=Configuration.cse_operation_plugins_disabledPlugins, 
						 replace=Configuration.cse_operation_plugins_replace)	# Load system plugins
		self.loadPlugins(directory=f'{Configuration.moduleDirectory}/runtime/plugins', 
						 packagePath='acme.runtime', 
						 disabledPlugins=Configuration.cse_operation_plugins_disabledPlugins, 
						 replace=Configuration.cse_operation_plugins_replace)	# Load system runtime plugins
		self.loadPlugins(directory=f'{Configuration.moduleDirectory}/services/plugins', 
						 packagePath='acme.services', 
						 disabledPlugins=Configuration.cse_operation_plugins_disabledPlugins, 
						 replace=Configuration.cse_operation_plugins_replace)	# Load system servicesplugins

		try:
			# Load plugins from working directory's plugins directory, if it exists
			self.loadPlugins(directory=f'{Configuration.baseDirectory}/plugins', 
							 packagePath='acme.plugins', 
							 disabledPlugins=Configuration.cse_operation_plugins_disabledPlugins, 
							 replace=Configuration.cse_operation_plugins_replace)		# Load working directory plugins
		except NotADirectoryError:
			# Ignore if the directory does not exist
			pass

		L.isInfo and L.log(f'Loaded plugins: {", ".join(self.plugins.keys())}')
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
