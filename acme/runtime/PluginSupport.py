#
#	PluginSupport.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Various plugin support functions. """

from ..runtime.PluginManager import PluginManager, pluginManager
from ..helpers.PluginManager import plugin, init, finish, start, stop, restart, pause, unpause, onResolved, onUnresolved
from ..helpers.PluginManager import configure, validate, plugin, requires, provide
from ..helpers.PluginManager import Service as SVC, endpoint, serviceClasses, DependencyError, Dependency
from ..runtime.EventManager import EventHandler, eventManager


@EventHandler
class Service(SVC):
	"""	Service support class. This class provides the base for service classes. 
		It is also an event handler to handle CSE-related events. 
	"""	
	pass