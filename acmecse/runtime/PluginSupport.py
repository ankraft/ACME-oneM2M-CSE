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
from ..helpers.PluginManager import Service, endpoint, serviceClasses, DependencyError, Dependency
from ..runtime.EventManager import eventHandler, eventManager
