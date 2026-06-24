#
# 	InterceptorManager.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	InterceptorManager class for managing interceptors."""

from __future__ import annotations
from typing import Callable, Optional, Tuple
from dataclasses import dataclass

from ..helpers.Singleton import Singleton
from ..helpers.ACMEIntEnum import ACMEIntEnum
from ..etc.Types import CSERequest, Result, Operation, ResourceTypes


class Phase(ACMEIntEnum):
	""" Enumeration of interception phases. 
	"""

	ALL = 0
	""" Intercept all phases. This is a special value that can be used to indicate that the interceptor should be applied to all phases. """
	REQUEST_PRE_PROCESSING = 1
	""" Intercept the request pre-processing phase. """
	REQUEST_POST_PROCESSING = 2
	""" Intercept the request post-processing phase. """
	REQUEST_PRE_SENDING = 3
	""" Intercept the request pre-sending phase. This intercepts a request from the CSE before it is sent to another entity. """
	REQUEST_POST_SENDING = 4
	""" Intercept the request post-sending phase. This intercepts the response to a request from another entity after it has been sent by the CSE. """
	REQUEST_ERROR_RESPONSE = 5
	""" Intercept the request error response phase. """


@dataclass
class InterceptorHandlerInfo:
	""" Data class to hold information about an interceptor handler method.
	"""

	func: Callable
	""" The interceptor handler function (bound method). """

	phase: frozenset[Phase]
	""" The phases this interceptor handler is interested in. """

	operation: frozenset[Operation]
	""" The operations this interceptor handler is interested in. """

	resource: frozenset[ResourceTypes]
	""" The resource types this interceptor handler is interested in. """

	priority: int
	""" The priority of this interceptor handler. Handlers with lower priority are executed first. """


InterceptorFilter = Tuple[Optional[Phase], Optional[Operation], Optional[ResourceTypes]]
""" A tuple of (phase, operation, resource) to filter interceptor handlers. Each
	element can be a specific value or None to match all. This is used as a key for caching 
	interceptor handler lookups in the InterceptorManager. 
"""

interceptorPluginMapping: dict[Callable, str] = {}	
""" Maps interceptor handler functions to their plugin names for management purposes. """


class InterceptorManager(metaclass=Singleton):
	"""	Manager for interceptors. This class is responsible for registering interceptors and calling the
	 	appropriate interceptor handlers when a request is processed by the CSE. 
		It maintains a registry of all interceptor handlers and their metadata, and uses this registry to
		find and call the appropriate handlers for each request.
	"""

	
	def __init__(self) -> None:
		"""	Initialize the InterceptorManager with an empty registry and cache.
		"""

		self._registry: list[InterceptorHandlerInfo] = []
		""" The registry of interceptor handlers. This is a list of InterceptorHandlerInfo objects that 
			contain the handler function and its metadata (phase, operation, resource, priority). 
			This registry is populated when interceptors are registered with the InterceptorManager. 
		"""

		self._cache: dict[InterceptorFilter, list[InterceptorHandlerInfo]] = {} 
		""" Cache for interceptor handler lookups. 
			The keys are InterceptorFilter tuples and the values are lists of InterceptorHandlerInfo objects
			that match the filter. This cache is used to speed up the lookup of interceptor handlers for each request.
			The cache is invalidated whenever a new interceptor is registered.
		"""

	
	def register(self, interceptor: Interceptor, pluginName: str) -> None:
		"""	Register an interceptor with the InterceptorManager. This method is called when
		 	an interceptor plugin is loaded and instantiated.
			  
			Args:
				interceptor: The interceptor instance to register. This instance should have its handler methods 
					decorated with @intercept.
			pluginName: The name of the plugin that the interceptor belongs to.
		"""
		for handler in interceptor._handlers:
			self._registry.append(handler)
			interceptorPluginMapping[handler.func] = pluginName
		self._cache.clear()  # invalidate cache on registration

	
	def interceptRequestPreProcessing(self, request: CSERequest) -> None:
		"""	Call the interceptor handlers for the REQUEST_PRE_PROCESSING phase.

			Args:
				request: The incoming CSERequest object that is being processed.
		"""
		for handler in self._findHandlers( (Phase.REQUEST_PRE_PROCESSING, request.op, request.ty) ):
			handler.func(request)


	def interceptRequestPostProcessing(self, request: CSERequest, result: Result) -> None:
		"""	Call the interceptor handlers for the REQUEST_POST_PROCESSING phase.

			Args:
				request: The incoming CSERequest object that is being processed.
				result: The Result object that is the response to the request, which can be modified by the interceptor handlers.
		"""
		for handler in self._findHandlers( (Phase.REQUEST_POST_PROCESSING, request.op, request.ty) ):
			handler.func(request, result)


	def interceptRequestPreSending(self, request: CSERequest) -> None:
		"""	Call the interceptor handlers for the REQUEST_PRE_SENDING phase.

			Args:
				request: The outgoing CSERequest object that is being sent to another entity.
		"""
		for handler in self._findHandlers( (Phase.REQUEST_PRE_SENDING, request.op, request.ty) ):
			handler.func(request)


	def interceptRequestPostSending(self, request: CSERequest, result: Result) -> None:
		"""	Call the interceptor handlers for the REQUEST_POST_SENDING phase.

			Args:
				request: The outgoing CSERequest object that is being sent to another entity.
				result: The Result object that is the response to the request, which can be modified by the interceptor handlers.
		"""
		for handler in self._findHandlers( (Phase.REQUEST_POST_SENDING, request.op, request.ty) ):
			handler.func(request, result)


	def interceptErrorResponse(self, request: CSERequest, result: Result) -> None:
		"""	Call the interceptor handlers for the REQUEST_ERROR_RESPONSE phase.

			Args:
				request: The incoming CSERequest object that is being processed.
				result: The Result object that is the response to the request, which can be modified by the interceptor handlers.
		"""
		for handler in self._findHandlers( (Phase.REQUEST_ERROR_RESPONSE, request.op, request.ty) ):
			handler.func(request, result)
	

	def _findHandlers(self, filter: InterceptorFilter) -> list:
		"""	Find and return the list of interceptor handlers for the given phase, operation, and resource type.

			This method uses caching to improve performance. The cache is invalidated whenever a new interceptor
			is registered.

			Args:
				filter: A tuple of (phase, operation, resource) to find handlers for. Each element can be a specific value or None to match all.

			Returns:
				A list of interceptor handlers sorted by priority, or an empty list if no handlers are found.
		"""
		if filter not in self._cache:
			self._cache[filter] = sorted([
				h for h in self._registry
				if (Phase.ALL in h.phase or filter[0] in h.phase)
					and (Operation.ALL in h.operation or filter[1] in h.operation)
					and (ResourceTypes.ALL in h.resource or filter[2] in h.resource)
			], key=lambda h: h.priority)
		return self._cache[filter]


class Interceptor:
	"""	Base class for interceptors. Interceptors are classes that can define methods decorated with @intercept 
		to intercept requests at different phases (e.g. pre-processing, post-processing) and for different 
		operations and resource types.

		They hold the interceptor handler methods and their metadata, which are registered with the 
		InterceptorManager when the interceptor is instantiated.
	"""

	def __init__(self) -> None:
		"""	Initialize the interceptor and extract its handlers and metadata.
		"""

		self._handlers: list[InterceptorHandlerInfo] = []
		""" The list of interceptor handlers defined in this interceptor. 
			This is populated by scanning the class for methods decorated with @intercept and extracting
			their metadata. 
		"""

		# Scan the class for methods decorated with @intercept and register them as handlers
		for name in dir(self.__class__):
			method = getattr(self.__class__, name)
			if callable(method) and hasattr(method, '_interceptor'):
				self._handlers.append(
					InterceptorHandlerInfo(
						func=getattr(self, name),  # bound method
						phase=method._phase,
						operation=method._operation,
						resource=method._resource,
						priority=method._priority,
					)
				)	


def intercept(phase: Optional[Phase | list[Phase]] = Phase.ALL, 
			  operation: Optional[Operation | list[Operation]] = Operation.ALL, 
			  resource: Optional[ResourceTypes | list[ResourceTypes]] = ResourceTypes.ALL, 
			  priority: Optional[int] = 50) -> Callable:
	"""	Decorator to mark a method as an interceptor handler. The decorated method will be registered with the InterceptorManager
	when the interceptor class is instantiated.

	Args:
		phase: The phase at which to intercept (pre, post, or all).
		operation: The operation to intercept (create, retrieve, update, delete, notify, discovery, or all).
		resource: The resource type to intercept (e.g. container, contentInstance, etc. or all).
		priority: The priority of the interceptor handler (lower numbers are executed first). Default is 50.
	
	Returns:
		A decorator function that marks the method as an interceptor handler with the specified metadata.
	"""

	# normalize to frozensets for consistent cache keys
	_phase     = frozenset(phase     if isinstance(phase,     list) else [phase])
	_operation = frozenset(operation if isinstance(operation, list) else [operation])
	_resource  = frozenset(resource  if isinstance(resource,  list) else [resource])


	def decorator(func: Callable) -> Callable:
		"""	Decorator function that marks the method as an interceptor handler with the specified metadata.

			Args:
				func: The method to decorate as an interceptor handler.

			Returns:
				The original method, now marked with interceptor metadata.
		"""
		func._interceptor = True		# type: ignore[attr-defined]
		func._phase = _phase				# type: ignore[attr-defined]
		func._operation = _operation		# type: ignore[attr-defined]
		func._resource = _resource		# type: ignore[attr-defined]
		func._priority = priority		# type: ignore[attr-defined]
		return func
	
	return decorator


interceptorManager: InterceptorManager = InterceptorManager()	# type: ignore
""" The global interceptor manager instance. This is a singleton instance. """

