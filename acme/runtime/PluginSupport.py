#
#	PluginSupport.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Various plugin support functions . """

from ..runtime.PluginManager import PluginManager
from ..helpers.PluginManager import plugin, init, finish, start, stop, restart, pause, unpause, onResolved, onUnresolved
from ..helpers.PluginManager import configure, validate, plugin, requires, provide
from ..helpers.PluginManager import ServicePlugin as _SP_, endpoint, serviceClasses, DependencyError, Dependency
from ..runtime.EventManager import EventHandler

# Get a pluginManager Singleton instance.
pluginManager:PluginManager = PluginManager()	# type: ignore
@EventHandler
class ServicePlugin(_SP_):
	"""	Plugin support class. This class provides the base for service plugins. 
		It is also an event handler to handle plugin-related events. 
	"""	
	pass