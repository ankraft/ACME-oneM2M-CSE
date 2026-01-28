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
import os, importlib, importlib.util, inspect
from types import ModuleType
from enum import IntEnum
from .TextTools import simpleMatch

try:
	import Singleton	# type: ignore
except ImportError:
	from . import Singleton


_tagType = '_pm_type'
_tagInstanceName = '_pm_instance_name'
_tagInstancePriority = '_pm_instance_priority'


class PluginState(IntEnum):
	"""	Plugin states. """
	LOADED		= 0
	INITIALIZED	= 1
	RUNNING		= 2
	STOPPED		= 3
	ERROR		= 4


@dataclass
class PluginInfo:
	"""	Dataclass to hold runtime information, metadata about a plugin, and state management.
	"""

	name: str
	""" Name of the plugin. """

	priority: int = 50
	""" Priority of the plugin. The priority determines the order in which plugins are started, etc. Lower values mean higher priority, but stopping and finalizing happen in reverse order. """

	state: PluginState = PluginState.LOADED
	""" Internal state of the plugin. """

	fileName: str = ''
	""" File name of the plugin module. """

	module: ModuleType | None = None
	""" The loaded plugin module. """

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

	configureMethod: Callable | None = None
	""" The configure method of the plugin. This method, if set, is called during the plugin configuration phase. """
	
	validateMethod: Callable | None = None
	""" The validate method of the plugin. This method, if set, is called during the plugin validation phase, after the configuration phase. """


	def start(self) -> None:
		""" Start the plugin. """
		if self.state in (PluginState.INITIALIZED, PluginState.STOPPED) and self.startMethod:
			self.startMethod(self.instance)
			self.state = PluginState.RUNNING
	
	def stop(self) -> None:
		""" Stop the plugin. """
		if self.state == PluginState.RUNNING:
			if self.stopMethod:
				self.stopMethod(self.instance)
			self.state = PluginState.STOPPED

	def restart(self) -> None:
		""" Restart the plugin. """
		if self.state == PluginState.RUNNING:
			if self.restartMethod:
				self.restartMethod(self.instance)
			self.state = PluginState.RUNNING

	def configure(self, *args: Any, **kwargs: Any) -> None:
		""" Configure the plugin. """
		if self.state in (PluginState.INITIALIZED, PluginState.RUNNING, PluginState.STOPPED):
			if self.configureMethod:
				self.configureMethod(self.instance, *args, **kwargs)

	def validate(self, *args: Any, **kwargs: Any) -> None:
		""" Validate the plugin configuration. """
		if self.state in (PluginState.INITIALIZED, PluginState.RUNNING, PluginState.STOPPED):
			if self.validateMethod:
				self.validateMethod(self.instance, *args, **kwargs)

	def finalize(self) -> None:
		""" Finalize the plugin. """
		self.stop()
		if self.state in (PluginState.INITIALIZED, PluginState.STOPPED):
			if self.finishMethod:
				self.finishMethod(self.instance)

class PluginManager(metaclass=Singleton.Singleton):
	"""	PluginManager class.

		This class manages the loading and registration of plugins.
	"""

	plugins: dict[str, PluginInfo] = {}


	def loadPlugins(self, directory: str, 
				 		  packagePath: str, 
						  disabledPlugins: list[str]=[], 
						  replace: bool=False, 
						  *args: Any, **kwargs: Any) -> None:
		""" Load plugins from the specified directory. 

			Plugins are initialized after loading according to their priority.

			Args:
				directory: The directory from which to load plugins.
				packagePath: The package path to use for the plugins.
				disabledPlugins: A list of plugin name patterns to disable. A pattern may include simple wildcards.
				replace: Whether to replace already loaded plugins.
				*args: Positional arguments to pass to the plugin init methods.
				**kwargs: Keyword arguments to pass to the plugin init methods.
			Raises:
				NotADirectoryError: If the directory does not exist.
				KeyError: If a plugin is already loaded.
				ValueError: If the plugin is not valid.
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
					spec = importlib.util.spec_from_file_location(f'{packagePath}.{pluginName}', fileName)
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
					if any(pattern for pattern in disabledPlugins if simpleMatch(pluginName, pattern)):
						continue

					# Load the module into the interpreter
					spec.loader.exec_module(module)

					# self.plugins[pluginName] = PluginInfo(name=pluginName, module=module, fileName=fileName)
					newPlugins[pluginName] = PluginInfo(name=pluginName, module=module, fileName=fileName)

				except Exception as e:
					# print(f"Failed to load plugin {pluginName}: {e}")
					raise e

		# After loading all plugins, gather plugin classes and plugin methods
		for plugin in newPlugins.values():
			for _, obj in inspect.getmembers(plugin.module):
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
								case 'configure':
									plugin.configureMethod = method
								case 'validate':
									plugin.validateMethod = method

					case 'pluginClass' if plugin.pluginClass:
						raise ValueError(f'Plugin "{plugin.name}" has multiple plugin classes.')

			if not plugin.pluginClass:
				raise ValueError(f'Plugin "{plugin.name}" has no plugin class.')
			
			# Store instance attribute name
			if (n := getattr(plugin.pluginClass, _tagInstanceName, None)):
				plugin.instanceAttributeName = n

			# Store priority
			if (p := getattr(plugin.pluginClass, _tagInstancePriority, None)) is not None:
				plugin.priority = p


		# Instantiate class and execute init methods of now registered plugins
		# Sorted by priority
		for plugin in sorted(newPlugins.values(), key=lambda p: p.priority):

			# Instantiate plugin class
			plugin.instance = plugin.pluginClass()
			if plugin.initMethod:
				plugin.initMethod(plugin.instance, *args, **kwargs)

			# Add plugin as attribute of the plugin manager
			if plugin.instanceAttributeName:
				setattr(self, plugin.instanceAttributeName, plugin.instance)
			plugin.state = PluginState.INITIALIZED
	
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

		# Sort the plugin names by priority to unload in correct reverse order, then iterate
		for pluginName in sorted(pluginNames, key=lambda name: self.plugins[name].priority, reverse=True):
			plugin = self.plugins[pluginName]

			# Remove instance attribute from PluginManager
			if plugin.instanceAttributeName:	
				delattr(self, plugin.instanceAttributeName)

			plugin.instance = None	# release instance reference
			plugin.finalize()
			del self.plugins[pluginName]

			# TODO unload module from interpreter
			# import sys
			# if pluginName in sys.modules.keys():
			# 	del sys.modules[pluginName]



	def _action(self, 
				pluginNames: str|list[str]|None, 
				action: Callable[[PluginInfo], None],
				reverse: bool=False) -> None:
		""" Transition the state of a plugin.

			Args:
				pluginName: The name of the plugin to transition.
				action: The action to perform during the state transition.
				reverse: Whether to process the plugins in reverse order.
		"""
		match pluginNames:
			case None:
				pluginNames = list(self.plugins.keys())
			case str():
				pluginNames = [pluginNames]
			case _:
				pass # already a list
		
		for name in sorted(pluginNames, key=lambda name: self.plugins[name].priority, reverse=reverse):
			action(self.plugins[name])
			

	def startPlugins(self, pluginNames: Optional[str|list[str]]=None) -> None:
		""" Start the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to start. Start all if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._action(pluginNames, lambda plugin: plugin.start())


	def stopPlugins(self, pluginNames: Optional[str|list[str]]=None) -> None:
		""" Shutdown the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to shutdown. Shutdown all if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._action(pluginNames, lambda plugin: plugin.stop(), reverse=True)

	
	def restartPlugins(self, pluginNames: Optional[str|list[str]]=None) -> None:
		""" Restart the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to restart. Restart all if None.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._action(pluginNames, lambda plugin: plugin.restart())


	def configurePlugins(self, pluginNames: Optional[str|list[str]]=None, *args: Any, **kwargs: Any) -> None:
		""" Configure the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to configure. Configure all if None.
				*args: Positional arguments to pass to the configure method.
				**kwargs: Keyword arguments to pass to the configure method.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._action(pluginNames, lambda plugin: plugin.configure(*args, **kwargs))


	def validatePlugins(self, pluginNames: Optional[str|list[str]]=None, *args: Any, **kwargs: Any) -> None:
		""" Validate the specified plugins.

			Args:
				pluginNames: The name(s) of the plugin(s) to validate.
				*args: Positional arguments to pass to the validate method.
				**kwargs: Keyword arguments to pass to the validate method.

			Raises:
				KeyError: If a specified plugin is not found.
		"""
		self._action(pluginNames, lambda plugin: plugin.validate(*args, **kwargs))
	

	def __getattr__(self, name:str) -> Any:
		""" Get the plugin by name.

			Args:
				name: The name of the plugin.
			Returns:
				The plugin module.
			Raises:
				AttributeError: If the plugin is not found.
		"""
		if name in self.plugins:
			return self.plugins[name]
		raise AttributeError(f"'PluginManager' object has no attribute '{name}'")
	

	def __delattr__(self, name:str) -> None:
		""" Delete the plugin by name.
		"""
		if name in self.plugins:
			self.unloadPlugins(name)
		elif hasattr(self, name):
			super().__delattr__(name)
		else:
			raise AttributeError(f'"PluginManager" object has no attribute "{name}"')

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


def configure(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark configuration functions in plugins. """
	return _wrap(func, 'configure')


def validate(func: Callable) -> Callable: # type: ignore
	""" Decorator to mark validation functions in plugins. """
	return _wrap(func, 'validate')


def pluginClass(property: str|ClassVar=None, priority: int=50) -> ClassVar: # type: ignore
	""" Decorator to mark plugin classes in plugins.

		Args:
			property: Optional name for the plugin instance. If a class is given here, it is treated directly as the class to decorate.
			priority: The priority of the plugin. It determines the order in which plugins are started, stopped, etc. Lower values mean higher priority.

		Returns:
			The class with the plugin class tag set.
	"""

	# if property is a class, set the tagType in the class and return it immediately.
	if inspect.isclass(property):
		setattr(property, _tagType, 'pluginClass')
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
		setattr(cls, _tagInstancePriority, priority)
		return cls
	
	return decorator

