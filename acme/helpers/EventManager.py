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

	payload: Any | tuple = None
	"""	The event payload. This may be any data that should be passed to the event handlers. 
		It can be a single value or a tuple of values. 
	"""


	def __getitem__(self, key: int) -> Any:
		"""	Get an item from the payload if it is a tuple.
			Args:
				key: The index of the item to get from the payload.
			Return:
				The item at the specified index in the payload.
			Raises:
				TypeError: If the payload is not a tuple.
		"""
		if isinstance(self.payload, tuple):
			return self.payload[key]
		raise TypeError(f'EventData payload is not a tuple')


	def __len__(self) -> int:
		"""	Get the length of the payload if it is a tuple.
			Return:
				The length of the payload if it is a tuple.
			Raises:
				TypeError: If the payload is not a tuple."""
		if isinstance(self.payload, tuple):
			return len(self.payload)
		raise TypeError(f'EventData payload is not a tuple')



#########################################################################
#
#	Event class.
#

_F = TypeVar("_F", bound=Callable)
""" The F TypeVar on the decorator overload is important — it tells the type
	checker that whatever callable goes in comes back out unchanged, so the handler's own
	signature is preserved after decoration.
"""


class Event(list):	# type:ignore[type-arg]
	"""	This class represents an event. It is actially a list of callable functions, 
		which are the event handlers for this event. Calling an instance of this class will
		call all the registered event handlers for this event. 

		The calls supports all methods from its base class (list), so use append() and remove()
		to add and remove functions.

		An event is raised by calling the event: "anEvent(anArgument)". It may have an
		arbitrary number of arguments which are passed to the functions.

		The functions may be called in a separate thread in order to prevent waiting
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
	def __call__(self, func: _F) -> _F: ...          # decorator path
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
					args: Unnamed function arguments. This should only contain a single argument of type `EventData`.
					kwargs: Keyword function arguments.
			"""
			for function in self:
				# if self.runInBackground:
				# 	x = BackgroundWorkerPool.runJob(lambda name = name, args = args, kwargs = kwargs: function(name, *args, **kwargs))
				# else:
				# 	function(name, *args, **kwargs)

				function(name, *args, **kwargs)

				# if hasattr(function, '_onEvents'):
				# 	function(args[0])
				# else:
				# 	function(name, *args, **kwargs)

		# If the first argument is a callable function and not an EventData, then we are in the decorator path, 
		# so we just add the function to the list of handlers.
		if len(args) == 1 and callable(args[0]) and not isinstance(args[0], EventData):
			self.append(args[0])
			return args[0]

		# Add event name to the event data if not already set
		# We leave kwargs as they are
		if args:
			if isinstance(args[0], EventData):
				if len(args) > 1:
					raise RuntimeError(f'When passing an EventData as argument, it must be the only argument, but got {len(args)} arguments')
				if args[0].name == self.name:
					# If the first argument is an EventData and has the same name as the event, we can use it directly.
					pass
				elif not args[0].name:
					# If the first argument is an EventData but does not have a name, we set the name to the event name.
					args[0].name = self.name
				else:
					# If the first argument is an EventData but has a different name, we raise an error.
					raise RuntimeError(f'EventData name {args[0].name} does not match event name {self.name}')
			else:
				# If the first argument is not an EventData, we create an EventData with the event name and the data
				# If the len is 1, we pass the single argument as payload, otherwise we pass all arguments as
				# a tuple as payload
				args = (EventData(name=self.name, payload=tuple(args) if len(args) > 1 else args[0]),)	# type: ignore[attr-defined]
		else:
			# If no arguments are passed, we create an EventData with the event name and no payload
			args = (EventData(name=self.name),)
		
		if self.runInBackground:
			# Call the handlers in a thread so that we don't block everything
			BackgroundWorkerPool.runJob(lambda args=args, kwargs=kwargs: _runner(*args, **kwargs), name=self.name)
		else:
			_runner(*args, **kwargs)

			

		# 	if isinstance(args[0], EventData):
		# 		if len(args) > 1:
		# 			raise RuntimeError('When passing an EventData as argument, it must be the only argument.')
		# 		if not args[0].name:
		# 			args[0].name = self.name
		# else:
		# 	# If no arguments are passed, create an EventData with the event name as payload
		# 	args = (EventData(name=self.name),)

		# if self.runInBackground:
		# 	# Call the handlers in a thread so that we don't block everything
		# 	BackgroundWorkerPool.runJob(lambda args=args, kwargs=kwargs: _runner(self.name, *args, **kwargs), name=self.name)
		# else:
		# 	_runner(self.name, *args, **kwargs)
		# _runner(self.name, *args, **kwargs)


	def __repr__(self) -> str:
		"""	Event reprsentation.
		
			Return:
				String representation of the event.
		"""
		return f'Event(name={self.name}, handlers={list.__repr__(self)})' 



class EventManager(metaclass=Singleton):
	"""	Base class for an event manager. This class manages events and event handlers. 
		It is implememted as a `Singleton`, so there is only one instance of the event
		manager in the whole application.
	
		Event topics are added as new methods to an *EventManager* instance. 
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
		"""	Dynamically create and return an `Event` instance when accessing an attribute that does not exist.
			Args:
				name: The name of the attribute to access, which will be used as the name of the `Event` instance.
			Return:
				The created `Event` instance.
			Raises:
				AttributeError: If the attribute name starts with an underscore (to prevent access to private attributes).
		"""
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


def onEvent(event: Event) -> Callable[[_F], _F]:
	"""Marks a method for event registration — deferred until instantiation.
	"""
	def decorator(func: _F) -> _F:
		if not hasattr(func, '_onEvents'):
			func._onEvents = []		# type: ignore[attr-defined]
		func._onEvents.append(event)	# type: ignore[attr-defined]
		return func
	return decorator

