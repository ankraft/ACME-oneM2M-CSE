#
#	ResourceSemaphore.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Helper classes and function to help with critical sections etc.
#

""" Helper classes and function to help with critical sections etc..
"""
from __future__ import annotations

from typing import Any, Dict, Callable, Optional, Type
from types import TracebackType
from functools import wraps
from ..etc.DateUtils import waitFor

#
#	Resource States
#
		
_resourceStates:Dict[str, str]	= {}
"""	Dictionary for store states for ID's. """

def setResourceState(id:str, state:str, timeout:Optional[float] = None) -> None:
	"""	Store the state of a resource.

		This can be used by resources to store individual transient states
		(only in memory).
	
		If *timeout* is provided and a state is already set for the given *id* then the
		function waits for *timeout* seconds that the state is cleared again. It then sets
		the *state* for the *id* as usual. If the *timeout* passes a *TimeoutError*
		exception is raised. 

		If *timeout* is not provided then the state is set immediately and a possible
		existing state for *id* is overwritten.

		Args:
			id: Resource ID
			state: Individual state or marker
			timeout: Optional time to wait if a state is already set for *id*.
		
		Raises:
			TimeoutError: Raised if the *timeout* passes and no new *state* can be set for *id*.
	"""
	if timeout is not None and id in _resourceStates:
		if not waitFor(timeout, lambda: getResourceState(id) == None):
			raise TimeoutError(f'Timeout reached while waiting for setting resource state for id: {id}')

	_resourceStates[id] = state


def getResourceState(id:str) -> str:
	"""	Retrieve the state of a resource.
	
		Args:
			id: Resource ID
		Return:
			The resource state, or None.
	"""
	return _resourceStates.get(id)


def clearResourceState(id:str) -> None:
	"""	Clear the state of a resource.
	
		Args:
			id: Resource ID
	"""
	if id in _resourceStates:
		del _resourceStates[id]


def resourceState(state:str) -> Callable:
	"""	Decorator to set and remove a state when a resource method is called.
	
		Args:
			state: The state to set.
		Return:
			Wrapped decorator.
	"""
	def decorate(func:Callable) -> Callable:
		@wraps(func)
		def wrapper(*args:Any, **kwargs:Any) -> Any:
			setResourceState(args[0].ri, state)
			r = func(*args, **kwargs)
			clearResourceState(args[0].ri)
			return r
		return wrapper
	return decorate


#
#	Context Manager
#
		

class CriticalResourceSectionException(Exception):
	"""	This exception is raised when a resource is alreay in a critical path.
	"""
	...


class CriticalResourceSection(object):
	""" Context manager to guard a critical resource path. """

	def __init__(self, id:str, state:str) -> None:
		"""	Initialization of the context manager.
		
			Args:
				id: Resource ID of the resource to be monitored.
				state: State of the resource.
		"""
		if (_s := getResourceState(id)) and _s == state:
			raise CriticalResourceSectionException(f'Resource {id} already in state {state}')
		self.id = id
		self.state = state


	def __enter__(self) -> None:
		setResourceState(self.id, self.state)

	
	def __exit__(self,	exctype: Optional[Type[BaseException]],
			 			excinst: Optional[BaseException],
						exctb: Optional[TracebackType]) -> Optional[bool]:
		clearResourceState(self.id)
		return None






