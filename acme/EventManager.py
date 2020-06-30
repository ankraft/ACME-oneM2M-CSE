#
#	EventManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing event handlers and events
#

import threading
from typing import Callable, Any
from Logging import Logging
from Constants import Constants as C
import CSE

# TODO: create/delete each resource to count! resourceCreate(ty)

# TODO move event creations from here to the resp modules.




	#########################################################################

	#
	#	Event class.
	#


class Event(list):
	"""Event subscription.

	A list of callable methods. Calling an instance of Event will cause a
	call to each function in the list in ascending order by index. 
	It supports all methods from its base class (list), so use append() and remove()
	to add and remove functions.

	An event is raised by calling the event: anEvent(anArgument). It may have an
	arbitrary number of arguments which are passed to the functions.

	The function will be called in a separate thread in order to prevent waiting
	for the returns. This might lead to some race conditions, so the synchronizations
	must be done insode the functions.
	"""
	def __call__(self, *args: Any, **kwargs: Any) -> None:
		# Call the handlers in a thread so that we don't block everything
		thrd = threading.Thread(target=self._callThread, args=args, kwargs=kwargs)
		thrd.setDaemon(True)		# Make the thread a daemon of the main thread
		thrd.start()

	def _callThread(self, *args: Any, **kwargs: Any) -> None:
		for function in self:
			function(*args, **kwargs)


	def __repr__(self) -> str:
		return "Event(%s)" % list.__repr__(self)



class EventManager(object):

	def __init__(self) -> None:
		self.addEvent('httpRetrieve')
		self.addEvent('httpCreate')
		self.addEvent('httpDelete')
		self.addEvent('httpUpdate')
		self.addEvent('httpRedirect')
		self.addEvent('createResource')
		self.addEvent('updateResource')
		self.addEvent('deleteResource')
		self.addEvent('cseStartup')
		self.addEvent('logError')
		self.addEvent('logWarning')
		Logging.log('EventManager initialized')


	def shutdown(self) -> None:
		Logging.log('EventManager shut down')


	#########################################################################


	#	Event topics are added as new methods of the handler class with the 
	#	given name and can be raised by calling those new methods, e.g.
	#
	#		manager.addEvent("someName")							# add new event topic
	#		manager.addHandler(manager.someName, handlerFunction)	# add an event handler
	#		handler.someName()										# raises the event


	def addEvent(self, name: str) -> Event:
		if not hasattr(self, name):
			setattr(self, name, Event())
		return getattr(self, name)


	def removeEvent(self, name: str) -> None:
		if hasattr(self, name):
			delattr(self, name)


	def hasEvent(self, name: str) -> bool:
		return name in self.__dict__


	def addHandler(self, event: Event, func: Callable) -> None:
		event.append(func)


	def removeHandler(self, event: Event, func: Callable) -> None:
		try:
			event.remove(func)
		except Exception as e:
			pass
