#
#	PluginManager.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Plugin manager to manage plugins.
"""	Plugin manager to manage plugins. """

from __future__ import annotations
from typing import Callable
from ..helpers.PluginManager import PluginManager as PM
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..helpers.TextTools import simpleMatch


class PluginManager(PM):

	_pluginChecks:dict[str, Callable] = {
		'acme.plugins.bindings.http.HttpManagement':	lambda : Configuration._cse_operation_plugins_enabledComponents.get('http_enableManagementEndpoint', False),
		'acme.plugins.bindings.http.HttpStructure':		lambda : Configuration._cse_operation_plugins_enabledComponents.get('http_enableStructureEndpoint', False),
		'acme.plugins.bindings.http.HttpUpperTester':	lambda : Configuration._cse_operation_plugins_enabledComponents.get('http_enableUpperTesterEndpoint', False),
		'acme.plugins.bindings.http.HttpWebUI':			lambda : Configuration._cse_operation_plugins_enabledComponents.get('webui_enable', False),
		'acme.plugins.runtime.Console':					lambda : Configuration.console_type == 'rich',
		'acme.plugins.runtime.MinimalConsole':			lambda : Configuration.console_type == 'simple',
		'acme.plugins.runtime.Statistics':				lambda : Configuration._cse_operation_plugins_enabledComponents.get('statistics_enable', False),
	}
	"""	Dictionary of plugin checks. The keys are the plugin names, the values are callables that take the plugin name as an argument and return a boolean indicating whether the plugin should be loaded. This is used to determine which plugins to load based on the configuration. """

	def __init__(self) -> None:
		"""	Runtime instance of the `PluginManager`. """
		super().__init__()

		# Add handler for restart event
		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore

		L.isDebug and L.logDebug('Initializing PluginManager')


		def _allowPlugin(pluginName: str) -> bool:
			"""	Check if a plugin is allowed to be loaded according to the configuration. 
			
				Args:
					pluginName (str): The name of the plugin to check.
				Return:
					True if the plugin is allowed to be loaded, False otherwise.
			"""
			if pluginName in self._pluginChecks:
				allowed = self._pluginChecks[pluginName]()
				L.isDebug and L.logDebug(f'Plugin {pluginName} is {"enabled" if allowed else "not enabled"}')
				return allowed
			
			# Check every pattern in the disabled plugins list, if any matches, the plugin is not allowed
			if Configuration.cse_operation_plugins_disabledPlugins:
				for pattern in Configuration.cse_operation_plugins_disabledPlugins:
					if simpleMatch(pluginName, pattern):
						L.isDebug and L.logDebug(f'Plugin {pluginName} is disabled by pattern: {pattern}')
						return False
			L.isDebug and L.logDebug(f'Plugin {pluginName} is enabled by default')
			return True


		def _loadPluginsFromDirectory(directory: str, packagePath: str) -> None:
			"""	Load plugins from a specific directory. Ignore if the directory does not exist. 
			
				Args:
					directory (str): The directory to load plugins from.
					packagePath (str): The package path for the plugins.
			"""
			try:
				self.loadPlugins(directory=directory, 
								 packagePath=packagePath, 
								 pluginFilter=_allowPlugin,
								 replace=Configuration.cse_operation_plugins_replace)
			except NotADirectoryError:
				# Ignore if the directory does not exist
				L.isDebug and L.logDebug(f'Plugin directory not found: {directory}')
				pass


		# Load system plugins
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/plugins/runtime', 'acme.plugins.runtime')
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/plugins/services', 'acme.plugins.services')
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/plugins/bindings', 'acme.plugins.bindings')
		_loadPluginsFromDirectory(f'{Configuration.moduleDirectory}/plugins/bindings/http', 'acme.plugins.bindings.http')

		# Load user plugins from the plugins directory. This is done after loading the system plugins.
		# The list of disabled plugins is also applied to the user plugins. 
		_loadPluginsFromDirectory(f'{Configuration.baseDirectory}/plugins', 'plugins')		# Load user plugins

		L.isInfo and L.log(f'Loaded plugins: {", ".join(self.plugins.keys())}')

		# Configure, validate and start plugins
		self.configurePlugins(None, None, Configuration)
		self.validatePlugins(None, None, Configuration)
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
