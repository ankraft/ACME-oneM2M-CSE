#
# PluginManager.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	PluginManager class for managing plugins."""

from __future__ import annotations
from typing import Any, Callable, ClassVar, Optional
from dataclasses import dataclass
import os, importlib, importlib.util, inspect, sys, copy
from types import ModuleType
from enum import IntEnum, auto

from ..helpers.TextTools import simpleMatch

try:
	import Singleton	# type: ignore
except ImportError:
	from . import Singleton


_tagType = '_pm_type'
_tagInstanceName = '_pm_instance_name'
_tagInstancePriority = '_pm_instance_priority'
_tagInstanceTags = '_pm_instance_tags'
_tagNoRestartWhilePaused = '_pm_no_restart_while_paused'


#
#	Exceptions
#
class PluginError(RuntimeError):
	""" Base class for all plugin system errors. """
	pass


class DependencyError(PluginError):
	""" Raised when a dependency resolution fails. """
	pass

class PluginConfigurationError(PluginError):
	""" Raised when a plugin is not configured correctly. """
	pass

class PluginState(IntEnum):
	"""	Plugin states. """
	LOADED		= auto()
	INITIALIZED	= auto()
	RESOLVED	= auto()
	RUNNING		= auto()
	PAUSED		= auto()
	STOPPED		= auto()
	UNRESOLVED	= auto()
	FINALIZED	= auto()
	ERROR		= auto()

@dataclass
class Dependency:
	""" Dataclass to hold information about a dependency. """
	attributeName: str
	pluginName: str
	className: str
	required: bool
	resolved: bool = False
	provided: bool = False

DependencyGraph = dict[type|str, list[Dependency]]
""" Type alias for a dependency graph. The keys are (plugin) classes or names, and the values are lists of dependencies. """

dependencies: DependencyGraph = {}
"""	Dictionary to hold the dependencies of plugin and other classes. """

dependentClasses: dict[type, tuple[str, bool]] = {}
"""	Dictionary to hold the classes that depend on a plugin or other class. 
	These are classes that have a @requires decorator attached. 

	The keys are the classes, the values are tuples containing the names of the plugins they depend
	 on and a boolean indicating whether the dependency is resolved.
"""

providedInstances: dict[str, Any] = {}
""" Dictionary to hold instances that are extra provided class instances. 
	The keys are the names of the instances, ie. the  module name,
	the values are the instances themselves. 	
"""


@dataclass
class PluginInfo:
	"""	Dataclass to hold runtime information, metadata about a plugin, and state management.
	"""

	name: str
	""" Name of the plugin. """

	priority: int = 50
	""" Priority of the plugin. The priority determines the order in which plugins are started, etc. Lower values mean higher priority, but stopping and finalizing happen in reverse order. """

	tags: list[str] = None
	""" Optional list of tags to attach to the plugin for easier identification and filtering. """

	noRestartWhilePaused: bool = False
	""" Flag to indicate whether the plugin should not restart requests while paused. """

	state: PluginState = PluginState.LOADED
	""" Internal state of the plugin. """

	fileName: str = ''
	""" File name of the plugin module. """

	module: ModuleType | None = None
	""" The loaded plugin module. """

	doc:str = ''
	""" The docstring of the plugin module. """

	pluginClass: Any | None = None
	""" A reference to the plugin class. """

	instance: Any | None = None
	""" The instantiated plugin class. """

	instanceAttributeName: str | None = None
	""" If this is set, the plugin instance is accessible as attribute of the PluginManager under this name. """

	initMethod: Callable | None = None
	""" The initialization method of the plugin. This method, if set, is called during the plugin initialization phase. """

	finishMethod: Callable | None = None
	""" The finalization method of the plugin. This method, if set, is called during the plugin finalization phase. """

	startMethod: Callable | None = None
	""" The start method of the plugin. This method, if set, is called when the plugin is started. """

	restartMethod: Callable | None = None
	""" The restart method of the plugin. This method, if set, is called when the plugin is restarted. """
	
	stopMethod: Callable | None = None
	""" The stop method of the plugin. This method, if set, is called when the plugin is stopped. """

	pauseMethod: Callable | None = None
	""" The pause method of the plugin. This method, if set, is called when the plugin is paused. """

	unpauseMethod: Callable | None = None
	""" The unpause method of the plugin. This method, if set, is called when the plugin is unpaused. """

	configureMethod: Callable | None = None
	""" The configure method of the plugin. This method, if set, is called during the plugin configuration phase. """
	
	validateMethod: Callable | None = None
	""" The validate method of the plugin. This method, if set, is called during the plugin validation phase, after the configuration phase. """

	onResolvedMethod: Callable | None = None
	""" The onResolved method of the plugin. This method, if set, is called when the plugin is resolved. """

	onUnresolvedMethod: Callable | None = None
	""" The onUnresolved method of the plugin. This method, if set, is called when the plugin is unresolved. """


	def resolve(self) -> None:
		""" Set the state of the plugin to resolved.
		"""
		if self.state in (PluginState.INITIALIZED, ):
			self.state = PluginState.RESOLVED
			if self.onResolvedMethod:
				self.onResolvedMethod(self.instance, copy.deepcopy(dependencies.get(self.pluginClass, [])))

	def start(self) -> None:
		""" Start the plugin. """
		if self.state in (PluginState.RESOLVED, PluginState.STOPPED):
			# Start the plugin normally					
			if self.startMethod:
				self.startMethod(self.instance)
			self.state = PluginState.RUNNING
	

	def stop(self) -> None:
		""" Stop the plugin. """
		if self.state in (PluginState.RUNNING, PluginState.PAUSED):
			if self.stopMethod:
				self.stopMethod(self.instance)
			self.state = PluginState.STOPPED


	def restart(self) -> None:
		""" Restart the plugin. """
		match self.state:
			case PluginState.PAUSED if self.noRestartWhilePaused:
				return
			case PluginState.RUNNING | PluginState.PAUSED:
				if self.restartMethod:
					self.restartMethod(self.instance)
				self.state = PluginState.RUNNING


	def pause(self) -> None:
		""" Pause the plugin. """
		if self.state in (PluginState.RUNNING,):
			if self.pauseMethod:
				self.pauseMethod(self.instance)
			self.state = PluginState.PAUSED


	def unpause(self) -> None:
		""" Unpause the plugin. """
		if self.state in (PluginState.PAUSED,):
			if self.unpauseMethod:
				self.unpauseMethod(self.instance)
			self.state = PluginState.RUNNING


	def configure(self, *args: Any, **kwargs: Any) -> None:
		""" Configure the plugin. """
		if self.state in (PluginState.INITIALIZED,):
			if self.configureMethod:
				self.configureMethod(self.instance, *args, **kwargs)


	def validate(self, *args: Any, **kwargs: Any) -> None:
		""" Validate the plugin configuration. """
		if self.state in (PluginState.INITIALIZED,):
			if self.validateMethod:
				self.validateMethod(self.instance, *args, **kwargs)


	def unresolve(self) -> None:
		""" Set the state of the plugin to unresolved.
		"""
		if self.state in (PluginState.STOPPED, ):
			self.state = PluginState.UNRESOLVED
			if self.onUnresolvedMethod:
				self.onUnresolvedMethod(self.instance, copy.deepcopy(dependencies.get(self.pluginClass, [])))


	def finalize(self) -> None:
		""" Finalize the plugin. """
		self.stop()
		self.unresolve()
		if self.state in (PluginState.INITIALIZED, PluginState.UNRESOLVED):
			if self.finishMethod:
				self.finishMethod(self.instance)


class PluginManager(metaclass=Singleton.Singleton):
	"""	PluginManager class.

		This class manages the loading and registration of plugins.
	"""

	plugins: dict[str, PluginInfo] = {}
	unloadedPlugins: list[str] = []
	_pluginInstances: dict[str, Any] = {}
	_tagsPluginMap: dict[str, list[tuple[str, Any]]] = {}


	def loadPlugins(self, directory: str, 
				 		  packagePath: str, 
						  pluginFilter: Optional[Callable[[str], bool]]=None,
						  replace: bool=False, 
						  *args: Any, **kwargs: Any) -> None:
		""" Load plugins from the specified directory. 

			Plugins are initialized after loading according to their priority.

			Args:
				directory: The directory from which to load plugins.
				packagePath: The package path to use for the plugins.
				pluginFilter: A callback function to filter plugins. The function should take a plugin name as input and return True if the plugin should be loaded, False otherwise.
				replace: Whether to replace already loaded plugins.
				*args: Positional arguments to pass to the plugin init methods.
				**kwargs: Keyword arguments to pass to the plugin init methods.
			Raises:
				NotADirectoryError: If the directory does not exist.
				KeyError: If a plugin is already loaded.
				PluginConfigurationError: If the plugin is not valid.
		"""
		# Check that the directory exists and is a directory
		if not os.path.isdir(directory):
			raise NotADirectoryError(f'Plugin directory "{directory}" does not exist or is not a directory.')
		
		newPlugins: dict[str, PluginInfo] = {}

		# load all files in the plugin directory as plugins in alphabetical order
		for file in sorted(os.listdir(directory), key=str.lower):
			if file.endswith('.py') and not file.startswith('_'):

				try:
					fileName = os.path.join(directory, file)
					pluginName = file[:-3]
					fullModuleName = f'{packagePath}.{pluginName}'
					spec = importlib.util.spec_from_file_location(fullModuleName, fileName)
					module = importlib.util.module_from_spec(spec)

					# change the simple pluginName to the full module name
					pluginName = module.__name__

					# check for existing plugin. If already loaded, either replace or raise error
					if pluginName in self.plugins:
						if replace:
							# Unload existing plugin first if replace is True
							self.unloadPlugins(pluginName)
						else:
							raise KeyError(f'Plugin "{pluginName}" is already loaded.')
					
					# check disabled plugins
					if pluginFilter and not pluginFilter(pluginName):
						self.unloadedPlugins.append(pluginName)
						continue

					# If the plugin was previously unloaded or filtered out, remove 
					# it from the unloaded plugins list, since it is now being loaded. 
					if pluginName in self.unloadedPlugins:
						del self.unloadedPlugins[self.unloadedPlugins.index(pluginName)]

					# The module must be added to sys.modules before executing it
					# This is needed for some Python 3.13 checks that require the module to 
					# be present in sys.modules before accessing its attributes.
					sys.modules[fullModuleName] = module 

					# Load the module into the interpreter
					spec.loader.exec_module(module)

					newPlugins[pluginName] = PluginInfo(name=pluginName, 
										 				module=module, 
														doc=module.__doc__.strip() if module.__doc__ else '',
														fileName=fileName)

				except Exception as e:
					raise e

		# After loading all plugins, gather plugin classes and plugin methods
		for plugin in newPlugins.values():
			for _, obj in inspect.getmembers(plugin.module):
				try:
					match getattr(obj, _tagType, None):

						case 'pluginClass' if not plugin.pluginClass:
							plugin.pluginClass = obj
							for _, method in inspect.getmembers(obj):
								match getattr(method, _tagType, None):
									case 'init':
										plugin.initMethod = method
									case 'finish':
										plugin.finishMethod = method
									case 'start':
										plugin.startMethod = method
									case 'restart':
										plugin.restartMethod = method
									case 'stop':
										plugin.stopMethod = method
									case 'pause':
										plugin.pauseMethod = method
									case 'unpause':
										plugin.unpauseMethod = method
									case 'configure':
										plugin.configureMethod = method
									case 'validate':
										plugin.validateMethod = method
									case 'onResolved':
										plugin.onResolvedMethod = method
									case 'onUnresolved':
										plugin.onUnresolvedMethod = method

						case 'pluginClass' if plugin.pluginClass:
							raise PluginConfigurationError(f'Plugin "{plugin.name}" has multiple plugin classes.')
						
				except RuntimeError as e:
					# Catch runtime errors that can occur when accessing attributes of modules that 
					# want to protect against access before initialization. We can ignore these errors for now.
					continue

			if not plugin.pluginClass:
				raise PluginConfigurationError(f'Plugin "{plugin.name}" has no plugin class.')
			
			# Store instance attribute name
			if (n := getattr(plugin.pluginClass, _tagInstanceName, None)):
				plugin.instanceAttributeName = n

			# Store priority
			if (p := getattr(plugin.pluginClass, _tagInstancePriority, None)) is not None:
				plugin.priority = p
			
			# Store tags
			if (t := getattr(plugin.pluginClass, _tagInstanceTags, None)) is not None:
				plugin.tags = t

			# Store noRestartWhilePaused flag
			if (i := getattr(plugin.pluginClass, _tagNoRestartWhilePaused, None)) is not None:
				plugin.noRestartWhilePaused = i

		# Instantiate class and execute init methods of now registered plugins
		# Sorted by priority
		for plugin in sorted(newPlugins.values(), key=lambda p: p.priority):

			# Instantiate plugin class
			plugin.instance = plugin.pluginClass()

			# Add plugin as attribute of the plugin manager
			if plugin.instanceAttributeName:
				self._pluginInstances[plugin.instanceAttributeName] = plugin.instance

			# Call init method if it exists
			if plugin.initMethod:
				plugin.initMethod(plugin.instance, *args, **kwargs)

			plugin.state = PluginState.INITIALIZED
		
		# Map tags to plugin names for easier lookup by tag
		for plugin in newPlugins.values():
			if plugin.tags:
				for tag in plugin.tags:
					if tag not in self._tagsPluginMap:
						self._tagsPluginMap[tag] = []
					self._tagsPluginMap[tag].append((plugin.name, plugin.instance))

		# Add new plugins to the main plugin list
		self.plugins.update(newPlugins)


	def unloadPlugins(self, pluginNames: Optional[list[str]|str]=None) -> None:
		""" Unload a plugin by name. If running, stop it first.

			Args:
				pluginNames: The name(s) of the plugin(s) to remove.
			Raises:
				KeyError: If the plugin is not found.
		"""

		match pluginNames:
			case None:
				pluginNames = list(self.plugins.keys())
			case str():
				pluginNames = [pluginNames]
			case _:
				pass # already a list

		# Stop plugins first to ensure proper shutdown and cleanup of resources. This includes
		# unresolving dependencies to clean up injected dependencies.
		self.stopPlugins(pluginNames)

		# Sort the plugin names by priority to unload in correct reverse order, then iterate
		for pluginName in sorted(pluginNames, key=lambda name: self.plugins[name].priority, reverse=True):
			plugin = self.plugins[pluginName]

			# Finalize plugin (which also stops it if running)
			plugin.finalize()

			# Remove instance attribute from PluginManager
			if plugin.instanceAttributeName:	
				delattr(self, plugin.instanceAttributeName)
			plugin.instance = None	# release instance reference
			del self.plugins[pluginName]

			# unload module from interpreter
			if pluginName in sys.modules.keys():
				del sys.modules[pluginName]

		# Remove plugin names from tag map
		for tag, pluginList in self._tagsPluginMap.items():
			self._tagsPluginMap[tag] = [name for name in pluginList if name not in pluginNames]


	def _transition(self, 
					pluginNames: str|list[str]|None, 
					action: Callable[[PluginInfo], None],
					tags: Optional[str|list[str]] = None,
					excludedTags: Optional[str|list[str]] = None,
					reverse: bool = False) -> None:
		""" Transition the state of a plugin. This will happen in the order of the plugin priority, 
			but can be reversed if necessary (e.g. for stopping plugins, which should happen in reverse order of starting).

			Plugins can be filtered by name, pattern and/or tags. If no filters are provided, the action will be applied to all plugins.

			Args:
				pluginName: The name of the plugin to transition. If None, all plugins are transitioned. If a string is provided, it is treated as a pattern to match plugin names.
				tags: The tags to match for the plugins to transition. If None, all plugins are transitioned.
				excludedTags: The tags to exclude from the plugins to transition. If None, no plugins are excluded.
				action: The action to perform during the state transition.
				reverse: Whether to process the plugins in reverse order.
		"""
		match pluginNames:
			case None:
				pluginNames = list(self.plugins.keys())
			case str():
				# Treat pluginNames as a pattern to match plugin names
				pluginNames = [ name for name in self.plugins.keys() if simpleMatch(name, pluginNames)] # filter out non-matching plugins
			case _:
				pass # already a list

		# Make a list from a single tag string if necessary
		if isinstance(tags, str):
			tags = [tags]
		
		for name in sorted(pluginNames, key=lambda name: self.plugins[name].priority, reverse=reverse):
			plugin = self.plugins[name]

			if tags:
				if not plugin.tags:	# Plugin must have tags to match, if it has no tags, it does not match
					continue
				# Check if the plugin has any of the specified tags
				if not any(tag in self.plugins[name].tags for tag in tags):
					continue
				# fall through if tags match

			if excludedTags:
				if not plugin.tags:	# Plugin must have tags to match, if it has no tags, it does not match, so it does not get excluded
					pass
				# Check if the plugin has any of the specified excludedTags, if it does, skip it
				elif any(tag in self.plugins[name].tags for tag in excludedTags):
					continue
				# fall through if excludedTags do not match

			action(plugin)
			

	def startPlugins(self, pluginNames: Optional[str|list[str]] = None, 
				  		   tags: Optional[str|list[str]] = None,
						   excludedTags: Optional[str|list[str]] = None) -> None:
		""" Start the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to start. Start all if None.
				tags: The tags of the plugins to match. Match all if None.
				excludedTags: The tags of the plugins to exclude. Exclude none if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.start(), tags=tags, excludedTags=excludedTags)


	def stopPlugins(self, pluginNames: Optional[str|list[str]] = None, 
				 		  tags: Optional[str|list[str]] = None,
						  excludedTags: Optional[str|list[str]] = None) -> None:
		""" Shutdown the specified plugins. Plugins are stopped in reverse order of their priority.

			Args:
				pluginNames: The name(s) of the plugin(s) to shutdown. Shutdown all if None.
				tags: The tags of the plugins to match. Match all if None.
				excludedTags: The tags of the plugins to exclude. Exclude none if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.stop(), tags=tags, excludedTags=excludedTags, reverse=True)


	def restartPlugins(self, pluginNames: Optional[str|list[str]] = None, 
							 tags: Optional[str|list[str]] = None,
							 excludedTags: Optional[str|list[str]] = None) -> None:
		""" Restart the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to restart. Restart all if None.
				tags: The tags of the plugins to match. Match all if None.
				excludedTags: The tags of the plugins to exclude. Exclude none if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.restart(), tags=tags, excludedTags=excludedTags)


	def pausePlugins(self, pluginNames: Optional[str|list[str]] = None, 
				  		   tags: Optional[str|list[str]] = None,
						   excludedTags: Optional[str|list[str]] = None) -> None:
		""" Pause the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to pause. Pause all if None.
				tags: The tags of the plugins to match. Match all if None. 
				excludedTags: The tags of the plugins to exclude. Exclude none if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.pause(), tags=tags, excludedTags=excludedTags)


	def unpausePlugins(self, pluginNames: Optional[str|list[str]] = None, 
							 tags: Optional[str|list[str]] = None, 
							 excludedTags: Optional[str|list[str]] = None) -> None:
		""" Unpause the specified plugins. Plugins are unpaused in reverse order of their priority.

			Args:
				pluginNames: The name(s) of the plugin(s) to unpause. Unpause all if None.
				tags: The tags of the plugins to match. Match all if None.
				excludedTags: The tags of the plugins to exclude. Exclude none if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.unpause(), tags=tags, excludedTags=excludedTags, reverse=True)


	def configurePlugins(self, pluginNames: Optional[str|list[str]] = None, 
					  		   tags: Optional[str|list[str]] = None, 
							   excludedTags: Optional[str|list[str]] = None,
							   *args: Any, **kwargs: Any) -> None:
		""" Configure the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to configure. Configure all if None.
				tags: The tags of the plugins to match. Match all if None.
				excludedTags: The tags of the plugins to exclude. Exclude none if None.
				*args: Positional arguments to pass to the configure method.
				**kwargs: Keyword arguments to pass to the configure method.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.configure(*args, **kwargs), tags=tags, excludedTags=excludedTags)


	def validatePlugins(self, pluginNames: Optional[str|list[str]] = None, 
					 		  tags: Optional[str|list[str]] = None, 
							  excludedTags: Optional[str|list[str]] = None, 
							  *args: Any, **kwargs: Any) -> None:
		""" Validate the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to validate.
				tags: The tags of the plugins to match. Match all if None.
				excludedTags: The tags of the plugins to exclude. Exclude none if None.
				*args: Positional arguments to pass to the validate method.
				**kwargs: Keyword arguments to pass to the validate method.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._transition(pluginNames, lambda plugin: plugin.validate(*args, **kwargs), tags=tags, excludedTags=excludedTags)
	
	def _checkPluginTags(self, pluginName: str, 
					  		   tags: Optional[str|list[str]] = None, 
							   excludedTags: Optional[str|list[str]] = None) -> bool:
		if pluginName not in self.plugins:
			return False
		if tags and not any(tag in self.plugins[pluginName].tags for tag in tags):
			return False
		if excludedTags and any(tag in self.plugins[pluginName].tags for tag in excludedTags):
			return False
		return True
	

	def resolvePlugins(self, tags: Optional[str|list[str]] = None,
					   		 excludedTags: Optional[str|list[str]] = None) -> None:
		""" Resolve the dependencies of all plugins and other classes.
			This is called before starting the plugins to ensure that all dependencies are resolved 
			and the plugin instances have all the required attributes injected.

			Args:
				tags: The tags of the plugins to match for dependency resolution. Match all if None.
				excludedTags: The tags of the plugins to exclude from dependency resolution. Exclude none
			Raises:
				DependencyError: If a required dependency cannot be resolved.
		"""

		for cls, deps in dependencies.items():
			# Resolve all dependency for all registered dependents.
			# This includes plugins and other clases that have dependencies injected via the @requires decorator. 

			for dep in deps:
				if not self._checkPluginTags(dep.pluginName, tags, excludedTags):
					continue
				if dep.pluginName in self.plugins and self.plugins[dep.pluginName].instance:
					setattr(cls, dep.attributeName, self.plugins[dep.pluginName].instance)
					deps[deps.index(dep)] = Dependency(attributeName=dep.attributeName, 
													   pluginName=dep.pluginName, 
													   className=cls.__name__ if isinstance(cls, type) else str(cls),
													   required=dep.required, 
													   resolved=True)
				elif dep.required:
					raise DependencyError(f'Class "{cls}" requires the plugin "{dep.pluginName}" which could not be resolved. Is it disabled?')
				# Otherwise, the dependency is not resolved, but it is not required, so we can ignore it for now. 

		# Set all plugins (not other classes) to "resolved" state even if they have no dependencies.
		for plugin in self.plugins.values():
			if self._checkPluginTags(plugin.name, tags, excludedTags):
				plugin.resolve()

		
		# Do we have any fullfilled classes (not plugins)? If so, we should call the fulfilled callbacks on them.
		for cls, (moduleName, resolved) in dependentClasses.items():
			if moduleName not in self.plugins and not resolved:
				# find the callback method in the class. Not ideal, but we have to do it this way because the class
				# itself does not have any tag to identify the callback method, so we have to look for it here.
				for _, method in inspect.getmembers(cls):
					if getattr(method, _tagType, None) == 'onResolved':
						resolvedCallback = method
						break
				else:
					continue
				resolvedCallback(cls, copy.deepcopy(dependencies.get(cls, [])))
				dependentClasses[cls] = (moduleName, True)	# Mark as resolved	
		
		# Now, resolve the provided instances as well, since they are not plugins and therefore not resolved in the previous steps.
		for moduleName, instance in providedInstances.items():
			for cls, deps in dependencies.items():
				for dep in deps:
					if dep.pluginName == moduleName and not dep.resolved:
						setattr(cls, dep.attributeName, instance)
						deps[deps.index(dep)] = Dependency(attributeName=dep.attributeName, 
														   pluginName=dep.pluginName, 
														   className=cls.__name__ if isinstance(cls, type) else str(cls),
														   required=dep.required, 
														   resolved=True,
														   provided=True)


	def unresolvePlugins(self) -> None:
		""" Unresolve the plugins. This is called when plugins are unloaded to clean up the injected dependencies 
			and set the plugin instances to None.
		"""

		for cls, deps in dependencies.items():
			# Unresolve all dependency for all registered dependents. This means
			# to set all attributes that were injected to None and set the resolved flag to False. 
			for dep in deps:
				if dep.pluginName in self.plugins and dep.resolved and hasattr(cls, dep.attributeName):
					setattr(cls, dep.attributeName, None)
					deps[deps.index(dep)] = Dependency(attributeName=dep.attributeName, 
													   pluginName=dep.pluginName, 
													   className=cls.__name__ if isinstance(cls, type) else str(cls),
													   required=dep.required, 
													   resolved=False)

		# Set all plugins (not other classes) to "unresolved" state even if they have no dependencies.
		for plugin in self.plugins.values():
			plugin.unresolve()
		
		# Do we have any fullfilled classes (not plugins)? If so, we should call the fulfilled callbacks on them.
		for cls, (moduleName, resolved) in dependentClasses.items():
			if moduleName not in self.plugins:
				# find the callback method in the class. Not ideal, but we have to do it this way because the class
				# itself does not have any tag to identify the callback method, so we have to look for it here.
				for _, method in inspect.getmembers(cls):
					if getattr(method, _tagType, None) == 'onUnresolved':
						resolvedCallback = method
						break
				else:
					continue
				resolvedCallback(cls, copy.deepcopy(dependencies.get(cls, [])))
				dependentClasses[cls] = (moduleName, False)	# Mark as resolved	

	def setupFinished(self) -> None:
		""" Check if all required dependencies are resolved. This can be called after the resolvePlugins method to check if there are any unresolved dependencies that are required and not provided.
			This is a separate step because sometimes, we might want to resolve the plugins first and then check for missing dependencies, so that we can provide the missing dependencies before starting the plugins. 
			For example, we might want to provide some extra instances that are not plugins, but are required by some plugins or other classes. 
			In this case, we can call resolvePlugins first, then setupFinished to see if there are any missing dependencies, then provide the missing instances, and then start the plugins.
		"""
		for cls, deps in dependencies.items():
			for dep in deps:
				# plugin = self.plugins.get(dep.pluginName)
			
				if dep.required and not dep.provided and not dep.resolved and dep.pluginName not in providedInstances:
					raise DependencyError(f'Class "{cls}" requires the provided instance "{dep.pluginName}" which could not be resolved. Is it missing?')

	
	


	def __getattr__(self, name:str) -> Any:
		""" Get the instance or plugin by name.

			Args:
				name: The name of the instance orplugin.
			Returns:
				The instance or plugin module, or None if not found.
		"""
		if name in self._pluginInstances:
			return self._pluginInstances[name]
		if name in self.plugins:
			return self.plugins[name]
		return None
	

	def __delattr__(self, name:str) -> None:
		""" Delete the plugin by name.
		"""
		if name in self._pluginInstances:
			del self._pluginInstances[name]
			return
		elif name in self.plugins:
			self.unloadPlugins(name)
		else:
			raise AttributeError(f'"PluginManager" object has no attribute "{name}"')
		
	
	def has(self, instanceName: str) -> bool:
		""" Check if a plugin instance with the given name exists.

			Args:
				instanceName: The name of the plugin instance to check.
			Returns:
				True if a plugin instance with the given name exists, False otherwise.
		"""
		return hasattr(self, instanceName)
	

	def provide(self, moduleName: str, instance: Any) -> None:
		""" Provide a instance of any non-plugin class to be injected as a dependency.
			This can be used to provide instances of classes that are not plugins, 
			but are required as dependencies by plugins or other classes. 

			The provided instances are injected into the dependent classes during the dependency 
			resolution phase, just like plugin instances. 

			The provided instances are not managed by the plugin manager, so they are not started, 
			stopped, etc. They are simply injected as attributes into the dependent classes.
	
			Args:
				moduleName: The name of the module that provides the instance. This is used to identify the instance in the dependency graph and to inject it into the dependent classes.
				instance: The instance to provide. This can be any instance of any class, as long as it is not a plugin class (i.e. it does not have the @pluginClass decorator).
				
			
		"""
		if moduleName in self.plugins:
			raise ValueError(f'Cannot provide instance for module "{moduleName}" because it is already registered as a plugin. Please choose a different name for the provided instance.')
		providedInstances[moduleName] = instance
		


	def dependencyGraph(self, name: Optional[str] = None) -> dict[str, list[Dependency]]:
		""" Get the dependency graph of the plugins and other classes.

			Args:
				name: Optional name of the plugin to get the dependency graph for. If None, returns the entire graph.
			Returns:
				The dependency graph as a dictionary where the keys are the class names and the values are lists of dependencies (module name, optional instance name).
		"""
		graph: dict[str, list[Dependency]] = {}
		for cls, deps in dependencies.items():
			for pluginName, plugin in self.plugins.items():
				if plugin.pluginClass == cls:
					graph[pluginName] = copy.deepcopy(deps)
					break
			else:
				graph[cls.__module__] = copy.deepcopy(deps)
		if name:
			return {name: graph[name] if name in graph else []}
		return graph
	

	def getPluginsByTag(self, tag: str, byPriority: bool = False) -> list[tuple[str, Any]]:
		""" Get the names of the plugins that have the given tag.

			Args:
				tag: The tag to search for.
				byPriority: Whether to sort the plugins by their priority. If True, the plugins are returned sorted by their priority, with the highest priority first (0 = highest priority).
			Returns:
				A list of plugin names that have the given tag.
		"""
		plugins = self._tagsPluginMap.get(tag, [])
		if byPriority:
			# Sort plugins by priority, with the highest priority first
			plugins.sort(key=lambda p: self.plugins[p[0]].priority)
		return plugins
	

	def callService(self, tag: str, endpoint: str, *args: Any, **kwargs: Any) -> Any:
		"""	Call a service plugin endpoint. 

			Args:
				tag: The tag of the plugin to call. This is used to identify the plugin to call. If multiple plugins with the same tag are found, the one with the highest priority is called.
				endpoint: The endpoint of the plugin to call. This is used to identify the method to call on the plugin instance. The endpoint must be defined in the plugin class using the `@endpoint` decorator.
				*args: Positional arguments to pass to the endpoint method.
				**kwargs: Keyword arguments to pass to the endpoint method.

			Return:
				The result of the endpoint method call.

			Raises:
				ValueError: If no plugin with the given tag and endpoint is found, or if multiple plugins with the same tag and endpoint are found.
		"""

		# Get the plugin instance for the given tag and endpoint
		plugins = self.getPluginsByTag(tag)
		plugins = [ (p, i) for p, i in plugins if hasattr(i, '_endpointMap') and endpoint in i._endpointMap ]
		if not plugins:
			raise ValueError(f'No plugin found with tag: {tag}')
		if len(plugins) > 1:
			raise ValueError(f'Multiple plugins found with tag: {tag}: {[p[0] for p in plugins]}')
		
		# Call the endpoint method on the plugin instance
		# The actual endpoint method name is looked up in the plugin's endpoint map internally
		# (see the @endpoint decorator and the ServicePlugin class) 
		return getattr(plugins[0][1], endpoint)(*args, **kwargs)


#
#	Decorators for plugin methods and classes
#

def _wrap(func: Callable, tagValue: str) -> Callable:
	""" Helper function to wrap a function and set a tag attribute to the wrapper function.

		Args:
			func: The function to wrap.
			tagValue: The tag value to set to the wrapper function.
		Returns:
			The wrapped function.
	"""

	def wrapper(self :Any, *args :Any, **kwargs: Any) -> Callable:
		return func(self, *args, **kwargs)

	setattr(wrapper, _tagType, tagValue)
	return wrapper


def init(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark initialization functions in plugins. """
	return _wrap(func, 'init')


def finish(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark finalization functions in plugins. """
	return _wrap(func, 'finish')


def start(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark start functions in plugins. """
	return _wrap(func, 'start')


def stop(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark stop functions in plugins. """
	return _wrap(func, 'stop')


def restart(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark restart functions in plugins. """
	return _wrap(func, 'restart')


def pause(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark pause functions in plugins. """
	return _wrap(func, 'pause')


def unpause(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark unpause functions in plugins. """
	return _wrap(func, 'unpause')


def configure(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark configuration functions in plugins. """
	return _wrap(func, 'configure')


def validate(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark validation functions in plugins. """
	return _wrap(func, 'validate')


def onResolved(func: Callable) -> Callable:
	""" Decorator to mark a method as a callback to be called when the plugin or class becomes resolved. """
	return _wrap(func, 'onResolved')


def onUnresolved(func: Callable) -> Callable:
	""" Decorator to mark a method as a callback to be called when the plugin or class becomes unresolved. """
	return _wrap(func, 'onUnresolved')


def plugin(property: str|ClassVar = None,						 # type: ignore
		   priority: int = 50, 
		   tags: list[str] = [], 
		   noRestartWhilePaused: bool = False) -> ClassVar: # type: ignore
	""" Decorator to mark plugin classes in plugins.

		Args:
			property: Optional name for the plugin instance. If a class is given here, it is treated directly as the class to decorate.
			priority: The priority of the plugin. It determines the order in which plugins are started, stopped, etc. Lower values mean higher priority.
			tags: Optional list of tags to attach to the plugin for easier identification and filtering.
			noRestartWhilePaused: Flag to indicate whether the plugin should not restart while paused.

		Returns:
			The class with the plugin class tag set.
	"""

	# Check types of the parameters
	if not isinstance(property, (str, type, type(None))):
		raise ValueError(f'Invalid value for "property" parameter in "plugin" decorator. Expected a string or a class, got {type(property)}')
	if not isinstance(priority, int):
		raise ValueError(f'Invalid value for "priority" parameter in "plugin" decorator. Expected an integer, got {type(priority)}')
	if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
		raise ValueError(f'Invalid value for "tags" parameter in "plugin" decorator. Expected a list of strings, got {type(tags)} with elements of types {[type(tag) for tag in tags]}')
	if not isinstance(noRestartWhilePaused, bool):
		raise ValueError(f'Invalid value for "noRestartWhilePaused" parameter in "plugin" decorator. Expected a boolean, got {type(noRestartWhilePaused)}')

	# if property is a class, set the tagType in the class and return it immediately.
	if inspect.isclass(property):
		setattr(property, _tagType, 'pluginClass')
		setattr(property, _tagInstanceTags, tags)
		setattr(property, _tagNoRestartWhilePaused, noRestartWhilePaused)
		setattr(property, _tagInstancePriority, priority)
		return property

	# else treat name as extra parameter for an instance name
	# Here we return the actual decorator.
	def decorator(cls: type) -> type:
		""" Decorator to mark plugin classes in plugins. 

			Args:
				cls: The class to mark as plugin class.
			Returns:
				The class with the plugin class tag set.
		"""
			
		setattr(cls, _tagType, 'pluginClass')
		if property: # If name is given, set it as instance name
			setattr(cls, _tagInstanceName, property)
		setattr(cls, _tagInstanceTags, tags)
		setattr(cls, _tagNoRestartWhilePaused, noRestartWhilePaused)
		setattr(cls, _tagInstancePriority, priority)
		return cls
	
	return decorator


def requires(*args:Any, **kwargs:Any) -> Callable:
	""" Class decorator to mark plugin and other classes with dependencies. 

		Args:
			*args: Positional arguments to pass to the plugin decorator.
			**kwargs: Keyword arguments to pass to the plugin decorator.
		Returns:
			The class.
	"""
		
	def decorator(cls: type) -> type:
		""" Decorator to get the dependencies of plugin classes and other classes.
			The dependencies are stores and injected later.

			Args:
				cls: The class to mark with dependencies.
			Returns:
				The class.
			Raises:
				ValueError: If the required flag is not a boolean, or if the keys or values
		"""

		# Get dependencies
		isRequired = kwargs.get('required', True)
		if not isinstance(isRequired, bool):
			raise ValueError(f'Invalid value for "required" flag in "requires" decorator. Expected a boolean.')

		# Add to depdencies dictionary and tag it
		# These classes may be plugins, but they can also be other classes that want
		# to have dependencies injected.
		if cls not in dependentClasses:
			dependentClasses[cls] = (cls.__module__, False)
			if not hasattr(cls, _tagType): # Don't override. But may be overridden later when analyzing plugins, but this is intentional
				setattr(cls, _tagType, 'dependentClass')

		for attributeName, pluginName in kwargs.items():
			if attributeName == 'required':
				continue
			if not isinstance(attributeName, str):
				raise ValueError(f'Invalid key for "requires" decorator. Expected a string, got {type(attributeName)}')
			if not isinstance(pluginName, str):
				raise ValueError(f'Invalid value for "requires" decorator "{attributeName}". Expected a string, got {type(pluginName)}')

			# Add the dependency to the dependencies dictionary for that class
			if cls not in dependencies:
				dependencies[cls] = []
			dependencies[cls].append(Dependency(attributeName=attributeName, 
												pluginName=pluginName, 
												className=cls.__name__,
												required=isRequired, 
												resolved=False))

		return cls
	return decorator


# #############################################################################
# #
# #	Create the plugin manager singleton instance. 
# #

# pluginManager = PluginManager()	


#############################################################################
#
#	Service Plugin Support
#

class ServicePlugin:
	"""	Base class for service plugins. """

	_endpointMap: dict[str, str]	# mapping of endpoint names to method names

	def __init_subclass__(cls, **kwargs: Any) -> None:
		"""	Initialize the plugin class, creating the service endpoint map by checking
			the methods marked by the @endpoint decorator. 
		"""
		super().__init_subclass__(**kwargs)
		cls._endpointMap = {}
		for attrName, method in inspect.getmembers(cls, predicate=inspect.isfunction):
			for endPointname in getattr(method, '_endpoints', []):
				cls._endpointMap[endPointname] = attrName


	def __getattribute__(self, name: str) -> Any:
		"""	Override __getattribute__ to allow access to service endpoints by their
			endpoint name instead of the method name. 
			
			Args:
				name: The name of the attribute to access. This can be either the real method name or the endpoint name defined by the @endpoint decorator.

			Return:
				The attribute value. If the name is an endpoint name, the corresponding method is returned.
		"""
		endpointMap = object.__getattribute__(self, '_endpointMap')
		if name in endpointMap:
			name = endpointMap[name]
		return object.__getattribute__(self, name)
	

#############################################################################
#
#	Functions for Services Support
#

# TODO move to -> pluginManager? 

	

#############################################################################
#
#	Decorators for Service Plugins
#

def endpoint(name: str) -> Callable:
	"""	Decorator to mark a method as an endpoint for a Serviceplugin. 
		The name of the endpoint is given as an argument.
	"""

	def decorator(func: type) -> type:
		if not hasattr(func, '_endpoints'):
			func._endpoints = []		# type: ignore[attr-defined]
		func._endpoints.append(name)	# type: ignore[attr-defined]
		return func
	
	return decorator


