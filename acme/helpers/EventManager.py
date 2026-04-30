#
#	EventManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing event handlers and events
#

"""	Generic event and event handling classes and functions. 
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar, cast, overload
from dataclasses import dataclass
import inspect
from unicodedata import name

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..helpers.Singleton import Singleton

# TODO: create/delete each resource to count! resourceCreate(ty)

# TODO move event creations from here to the resp modules.


#########################################################################
#
#	Event Data class.
#

@dataclass
class EventData():
	"""	Event data class. This class is used to pass data to event handlers.
	"""

	name: Optional[str] = None
	"""	The event name. """

	payload: Any | list[Any] = None
	"""	The event payload. """



#########################################################################
#
#	Event class.
#

# The F TypeVar on the decorator overload (see below) is important — it tells the type
# checker that whatever callable goes in comes back out unchanged, so the handler's own
# signature is preserved after decoration.
F = TypeVar("F", bound=Callable)


class Event(list):	# type:ignore[type-arg]
	"""Event subscription.

	A list of callable methods. Calling an instance of Event will cause a
	call to each function in the list in ascending order by index. 
	It supports all methods from its base class (list), so use append() and remove()
	to add and remove functions.

	An event is raised by calling the event: anEvent(anArgument). It may have an
	arbitrary number of arguments which are passed to the functions.

	The function will be called in a separate thread in order to prevent waiting
	for the returns. This might lead to some race conditions, so the synchronizations
	must be done inside the functions.

	Attention: 
		Since the parent class is a *list* calling *isInstance(obj, list)* will return True.
	"""

	__slots__ = (
		'runInBackground',
		'manager',
		'name',
	)
	"""	Slots of the Event class. """

	def __init__(self,  name: Optional[str] = None,
			  			runInBackground: Optional[bool] = True) -> None:
		"""	Event initialization.

			Args:
				runInBackground: Indicator whether an event should be handled in a separate thread.
				name: The event name.
		"""
		self.name = name
		"""	The event name. """
		self.runInBackground = runInBackground
		"""	Indicator whether an event should be handled in a separate thread. """


	@overload
	def __call__(self, func: F) -> F: ...          # decorator path
	@overload
	def __call__(self, *args:Any, **kwargs:Any) -> None: ... # emit path

	def __call__(self, *args:Any, **kwargs:Any) -> None:
		"""	Handle calling an event instance. This call is forwarded to **all** of the registered
			callback functions for this event. 
			
			If the event was created with `runInBackground` as True,
			then the callbacks are called sequentially (not individually!) as a thread.

			This method is used in two ways: 1) as a decorator to register an event handler, 
			and 2) to raise an event by calling the event instance. The method distinguishes between
			the two cases by checking whether the first argument is a callable function and whether 
			it is an instance of `EventData` (in which case it

			Args:
				args: Unnamed function arguments.
				kwargs: Keyword function arguments.
		"""

		def _runner(name: str, *args: Any, **kwargs: Any) -> None:
			"""	Call all registered function for this event object. Pass on any argument.
				The callbacks are called sequentially (not in parallel!).

				Args:
					args: Unnamed function arguments.
					kwargs: Keyword function arguments.
			"""
			for function in self:
				# if self.runInBackground:
				# 	x = BackgroundWorkerPool.runJob(lambda name = name, args = args, kwargs = kwargs: function(name, *args, **kwargs))
				# else:
				# 	function(name, *args, **kwargs)
				if hasattr(function, '_onEvents'):
					if args and isinstance(args[0], EventData):
						function(args[0])
					else:
						function(EventData(name=name, payload=list(args)))	# type: ignore[attr-defined]
				else:
					function(name, *args, **kwargs)

		# If the first argument is a callable function and not an EventData, then we are in the decorator path, 
		# so we just add the function to the list of handlers.
		if len(args) == 1 and callable(args[0]) and not isinstance(args[0], EventData):
			self.append(args[0])
			return args[0]

		# Add event name to the event data if not already set
		if args and isinstance(args[0], EventData):
			if len(args) > 1:
				raise RuntimeError('When passing an EventData as argument, it must be the only argument.')
			if not args[0].name:
				args[0].name = self.name

		if self.runInBackground:
			# Call the handlers in a thread so that we don't block everything
			BackgroundWorkerPool.runJob(lambda args=args, kwargs=kwargs: _runner(self.name, *args, **kwargs), name=self.name)
		else:
			_runner(self.name, *args, **kwargs)
		# _runner(self.name, *args, **kwargs)


	def __repr__(self) -> str:
		"""	Event reprsentation.
		
			Return:
				String representation of the event.
		"""
		return f'Event(name={self.name}, handlers={list.__repr__(self)})' 



class EventManager(metaclass=Singleton):
	"""	Event topics are added as new methods to an *EventManager* instance. 
		Events can be raised by calling those new methods.

		Example:
			manager.addEvent("anEvent")
				Add new `Event` topic *anEvent* to *manager*.

			manager.addHandler(manager.anEvent, handlerFunction)
				Add an event handler for the *anEvent* `Event`.

			manager.anEvent(anArg)
				Raise the *anEvent* `Event` with an *anArg* argument.
	"""

	def addEvent(self, name: str, runInBackground: Optional[bool] = True) -> Event:
		"""	Create and add a new `Event`.

			Args:
				name: Name of the `Event`.
				runInBackground: (optional, default = True) Execute the callbacks in a thread.
			
			Return:
				The created `Event`.
		"""
		if not hasattr(self, name):
			setattr(self, name, Event(name=name, runInBackground=runInBackground))
		return cast(Event, getattr(self, name))


	def removeEvent(self, name: str) -> None:
		"""	Remove an `Event` instance by its name.

			Args:
				name: The name of the `Event` instance to remove.
		"""
		if hasattr(self, name):
			delattr(self, name)
	
	
	def removeAllEvents(self) -> None:
		"""	Remove all registered `Event` instances.
		"""
		for n in list(vars(self)):
			if isinstance(self.__dict__[n], Event):
				self.removeEvent(n)


	def hasEvent(self, name: str) -> bool:
		"""	Check whether an `Event` instance exists.

			Args:
				name: Name of the `Event` instance to check.
			Return:
				*True* if an `Event` instance with *name* exists.
		"""
		return name in self.__dict__


	def addHandler(self, event: Event|list[Event], func: Callable) -> None:		# type:ignore[type-arg]
		"""	Add a new event handler to an `Event` or to a list of `Event` instance.

			Args:
				event: Either a single `Event` instance or a list of `Event` instances.
				func: The function callback to call when the event is raised.
		"""
		if func is None or not callable(func):
			raise RuntimeError('Event handler must be a callable function, but got: ' + str(func))
		list(map(lambda e: e.append(func), [event] if isinstance(event, Event) else event))
	

	def hasHandler(self, event: Event|list[Event], func: Callable) -> bool:
		"""	Test whether one or more events have a specific handler assigned.

			Args:
				event: Either a single `Event` or a list of `Event` instances.
				func: The function callback to call when the event is raised.
			Return:
				*True* if *func* is a registered event handler.
		"""
		l = [ event ] if isinstance(event, Event) else event
		return any([ e for e in l if func in e ])


	def removeHandler(self, event: Event|list[Event], func: Callable) -> None:	# type:ignore[type-arg]
		"""	Remove an event handler from an `Event` instance or a list of `Event` instances.

			Args:
				event: Either a single `Event` or a list of `Event` instances.
				func: The function callback to remove from the `Event` instance(s).
		"""
		list(map(lambda e: e.remove(func), [event] if isinstance(event, Event) else event))


	def __getattr__(self, name: str) -> Event:
		if name.startswith('_'):
			raise AttributeError(name)
		# Add event dynamically if it does not exist yet
		event = Event(name)
		setattr(self, name, event)
		return event


def EventHandler(cls: type) -> type:
	"""	Class decorator to automatically register event handlers. 
		Any method of the decorated class that is decorated with an `Event` 
		decorator will be automatically registered as an event handler for that event.

		It is necessary to use this decorator for any class that has methods decorated with `onEvent`, 
		otherwise the event handlers will not be registered and the decorated methods will not be
		correctly called when the event is raised.
	"""
	originalInit = cls.__init__	# type: ignore[misc]

	def __init__(self, *args: Any, **kwargs: Any) -> None:	# type: ignore[no-untyped-def]
		originalInit(self, *args, **kwargs)
		for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
			for event in getattr(method.__func__, '_onEvents', []):
				event.append(method)


	cls.__init__ = __init__ 	# type: ignore[misc]
	return cls


def onEvent(event: Event) -> Callable[[F], F]:
	"""Marks a method for event registration — deferred until instantiation.
	"""
	def decorator(func: F) -> F:
		if not hasattr(func, '_onEvents'):
			func._onEvents = []		# type: ignore[attr-defined]
		func._onEvents.append(event)	# type: ignore[attr-defined]
		return func
	return decorator

