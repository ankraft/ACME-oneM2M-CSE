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
from ..helpers.PluginManager import Service, endpoint, serviceClasses, Dependency
from ..helpers.PluginManager import PluginConfigurationError, DependencyError, PluginNotFoundError, EndpointNotFoundError, PluginTimeoutError
from ..runtime.EventManager import eventHandler, eventManager
from ..runtime.InterceptorManager import Interceptor, InterceptorManager, Phase, intercept, interceptorManager
from ..etc.Types import CSERequest, Result, Operation, ResourceTypes
