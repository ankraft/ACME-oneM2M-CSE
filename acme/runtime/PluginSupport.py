#
#	PluginSupport.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Various plugin support functions . """

from ..runtime.PluginManager import PluginManager
from ..helpers.PluginManager import plugin, init, finish, start, stop, restart, pause, unpause, configure, validate, plugin, requires
from ..helpers.PluginManager import ServicePlugin as SP, endpoint
from acme.runtime.EventManager import EventManager, EventHandler, onEvent, EventData

# Get a pluginManager Singleton instance.
pluginManager:PluginManager = PluginManager()	# type: ignore

# Get the event manager instance from the runtime.
eventManager:EventManager = EventManager()	# type: ignore

@EventHandler
class ServicePlugin(SP):
	"""	Plugin support class. This class provides the base for service plugins. 
		It is also an event handler to handle plugin-related events. 
	"""	
	...