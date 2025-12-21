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
import os, importlib, importlib.util, inspect, sys
from types import ModuleType
from enum import IntEnum
from .TextTools import simpleMatch

try:
	import Singleton	# type: ignore
except ImportError:
	from . import Singleton


# TODO add disabled plugins configuration

tag = '_pm_state'


class PluginState(IntEnum):
	"""	Plugin states. """
	LOADED		= 0
	INITIALIZED	= 1
	RUNNING		= 2
	STOPPED		= 3
	ERROR		= 4


@dataclass
class PluginInfo:
	name: str
	state: PluginState = PluginState.LOADED
	fileName: str = ''
	module: ModuleType | None = None
	pluginClass: Any | None = None
	instance: Any | None = None
	initMethod: Callable | None = None
	finishMethod: Callable | None = None
	startMethod: Callable | None = None
	restartMethod: Callable | None = None
	stopMethod: Callable | None = None
	configureMethod: Callable | None = None
	validateMethod: Callable | None = None


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
		
		# load all files in the plugin directory as plugins
		for file in sorted(os.listdir(directory), key=str.lower):
			if file.endswith('.py') and not file.startswith('_'):
				pluginName = file[:-3]

				# check for existing plugin
				if pluginName in self.plugins:
					if replace:
						self.unloadPlugins(pluginName)
					else:
						raise KeyError(f'Plugin "{pluginName}" is already loaded.')
				
				# check disabled plugins
				skipModule = False
				for pattern in disabledPlugins:
					# print(f"Checking if plugin '{pluginName}' matches disabled pattern '{pattern}'")
					if simpleMatch(pluginName, pattern):
						skipModule = True
						break
				if skipModule:
					continue

				try:
					fileName = os.path.join(directory, file)
					spec = importlib.util.spec_from_file_location(f'{packagePath}.{pluginName}', fileName)
					module = importlib.util.module_from_spec(spec)
					spec.loader.exec_module(module)
					self.plugins[pluginName] = PluginInfo(name=pluginName, module=module, fileName=fileName)
					#print(f"Loaded plugin: {pluginName}")
				except Exception as e:
					# print(f"Failed to load plugin {pluginName}: {e}")
					raise e

		# Sort plugins by name.
		self.plugins = dict(sorted(self.plugins.items(), key=lambda item: item[0].lower()))

		# After loading all plugins, gather plugin classes and plugin methods
		for plugin in self.plugins.values():
			if plugin.state != PluginState.LOADED:	# Skip already processed plugins
				continue
			for _, obj in inspect.getmembers(plugin.module):
				match getattr(obj, tag, None):

					case 'pluginClass' if not plugin.pluginClass:
						plugin.pluginClass = obj
						for _, method in inspect.getmembers(obj):
							match getattr(method, tag, None):
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

		# Instantiate class and execute init methods of now registered plugins
		for plugin in self.plugins.values():
			if plugin.pluginClass is None:
				raise ValueError(f'Plugin "{plugin.name}" has no plugin class.')
			plugin.instance = plugin.pluginClass()
			if plugin.initMethod:
				plugin.initMethod(plugin.instance, *args, **kwargs)
			plugin.state = PluginState.INITIALIZED


	def unloadPlugins(self, pluginNames: Optional[list[str]|str] = None) -> None:
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

		for pluginName in pluginNames:
			if pluginName in self.plugins:
				plugin = self.plugins[pluginName]
				plugin.finalize()
				del self.plugins[pluginName]
			else:
				raise KeyError(f'Plugin "{pluginName}" not found.')


	def _action(self, 
				pluginNames: str|list[str]|None, 
				action: Callable[[PluginInfo], None]) -> None:
		""" Transition the state of a plugin.

			Args:
				pluginName: The name of the plugin to transition.
				action: The action to perform during the state transition.
		"""
		match pluginNames:
			case None:
				pluginNames = list(self.plugins.keys())
			case str():
				pluginNames = [pluginNames]
		
		for name in pluginNames:
			if (plugin := self.plugins.get(name, None)):
				action(plugin)
			else:
				raise KeyError(f"Plugin '{name}' not found.")
			

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
		self._action(pluginNames, lambda plugin: plugin.stop())

	
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

	setattr(wrapper, tag, tagValue)
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


def pluginClass(cls: ClassVar) -> ClassVar: # type: ignore
	""" Decorator to mark plugin classes in plugins. """
	setattr(cls, tag, 'pluginClass')
	return cls


# → Experimental late loading
#
# import importlib
# mod = importlib.import_module('acme.services.ActionManager')
# action = mod.ActionManager()	

# mod = importlib.import_module('acme.runtime.ScriptManager')			# Initialize the action manager
# # script = mod.ScriptManager()				# Initialize the script manager
# thismodule = sys.modules[__name__]
# setattr(thismodule, 'script', mod.ScriptManager())

