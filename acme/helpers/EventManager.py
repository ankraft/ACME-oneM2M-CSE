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

from typing import Any, Callable, Optional, cast

from ..helpers.BackgroundWorker import BackgroundWorkerPool

# TODO: create/delete each resource to count! resourceCreate(ty)

# TODO move event creations from here to the resp modules.


#########################################################################
#
#	Event class.
#


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

	def __init__(self,  runInBackground:Optional[bool] = True, 
						manager:Optional[EventManager] = None,
						name:Optional[str] = None):
		"""	Event initialization.

			Args:
				runInBackground: Indicator whether an event should be handled in a separate thread.
				manager: The responsible `EventManager` to handle an event.
				name: The event name.
		"""
		self.runInBackground = runInBackground
		"""	Indicator whether an event should be handled in a separate thread. """
		self.manager = manager
		"""	The responsible `EventManager` to handle an event. """
		self.name = name
		"""	The event name. """


	def __call__(self, *args:Any, **kwargs:Any) -> None:
		"""	Handle calling an event instance. This call is forwarded to **all** of the registered
			callback functions for this event. 
			
			If the event was created with `runInBackground` as True,
			then the callbacks are called sequentially (not individually!) as a thread.

			Args:
				args: Unnamed function arguments.
				kwargs: Keyword function arguments.
		"""

		def _runner(name:str, *args:Any, **kwargs:Any) -> None:
			"""	Call all registered function for this event object. Pass on any argument.
	
				Args:
					args: Unnamed function arguments.
					kwargs: Keyword function arguments.
			"""
			for function in self:
				# if self.runInBackground:
				# 	x = BackgroundWorkerPool.runJob(lambda name = name, args = args, kwargs = kwargs: function(name, *args, **kwargs))
				# else:
				# 	function(name, *args, **kwargs)
				function(name, *args, **kwargs)

		if not self.manager._running:
			return
		if self.runInBackground:
			# Call the handlers in a thread so that we don't block everything
			BackgroundWorkerPool.runJob(lambda args = args, kwargs = kwargs: _runner(self.name, *args, **kwargs), name = self.name)
		else:
			_runner(self.name, *args, **kwargs)
		# _runner(self.name, *args, **kwargs)


	def __repr__(self) -> str:
		"""	Event reprsentation.
		
			Return:
				String representation of the event.
		"""
		return f'Event({list.__repr__(self)})' 



class EventManager(object):
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

	__slots__ = (
		'_running',
	)
	"""	Slots of the EventManager class. """


	def __init__(self) -> None:
		"""	EventManager initialization.
		"""
		self._running = True
		"""	Internal Running indicator for the manager instance. """


	def shutdown(self) -> bool:
		"""	Shutdown the Event Manager.
		
			Return:
				*True* when shutdown is complete.
		"""
		self._running = False
		return True

	#########################################################################

	def addEvent(self, name:str, runInBackground:Optional[bool] = True) -> Event:
		"""	Create and add a new `Event`.

			Args:
				name: Name of the `Event`.
				runInBackground: (optional, default = True) Execute the callbacks in a thread.
			
			Return:
				The created `Event`.
		"""
		if not hasattr(self, name):
			setattr(self, name, Event(runInBackground = runInBackground, manager = self, name = name))
		return cast(Event, getattr(self, name))


	def removeEvent(self, name:str) -> None:
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


	def hasEvent(self, name:str) -> bool:
		"""	Check whether an `Event` instance exists.

			Args:
				name: Name of the `Event` instance to check.
			Return:
				*True* if an `Event` instance with *name* exists.
		"""
		return name in self.__dict__


	def addHandler(self, event:Event|list[Event], func:Callable) -> None:		# type:ignore[type-arg]
		"""	Add a new event handler to an `Event` or to a list of `Event` instance.

			Args:
				event: Either a single `Event` instance or a list of `Event` instances.
				func: The function callback to call when the event is raised.
		"""
		list(map(lambda e: e.append(func), [event] if isinstance(event, Event) else event))
	

	def hasHandler(self, event:Event|list[Event], func:Callable) -> bool:
		"""	Test whether one or more events have a specific handler assigned.

			Args:
				event: Either a single `Event` or a list of `Event` instances.
				func: The function callback to call when the event is raised.
			Return:
				*True* if *func* is a registered event handler.
		"""
		l = [ event ] if isinstance(event, Event) else event
		return any([ e for e in l if func in e ])


	def removeHandler(self, event:Event|list[Event], func:Callable) -> None:	# type:ignore[type-arg]
		"""	Remove an event handler from an `Event` instance or a list of `Event` instances.

			Args:
				event: Either a single `Event` or a list of `Event` instances.
				func: The function callback to remove from the `Event` instance(s).
		"""
		list(map(lambda e: e.remove(func), [event] if isinstance(event, Event) else event))
