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

from typing import Any, Dict, Callable, Optional, Type, Tuple
from types import TracebackType
from functools import wraps
from threading import Semaphore

#
#	Resource States
#
		
_semaphores:Dict[Tuple[str, str], Semaphore]	= {}
"""	Dictionary for store semaphores states for (ID, state) tuples. """

def  enterCriticalSection(id:str, 
		     			  state:str, 
		     			  timeout:Optional[float] = None) -> None:
	"""	Store the state of a resource, and enter or wait for entering a critical section.

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
	
	if not (semaphore := _semaphores.get((id, state))):
		semaphore = Semaphore()
		semaphore.acquire(timeout = timeout)
		_semaphores[(id, state)] = semaphore
	else:
		if not semaphore.acquire(timeout = timeout):
			raise TimeoutError(f'Timeout reached while waiting for semaphore state for: ({id}, {state})')


def inCriticalSection(id:str, state:str) -> bool:
	"""	Check if a resource and state are in a critical section or waiting to enter.
	
		Args:
			id: Resource ID
			state: The state to check.

		Return:
			True if a resource and state are set, False otherwise.
	"""
	return (id, state) in _semaphores


def leaveCriticalSection(id:str, state:str) -> None:
	"""	Clear the state of a resource.
	
		Args:
			id: Resource ID
			state: The state to clear.
	"""

	if semaphore := _semaphores.get((id, state)):
		# if no one else is waiting, remove the semaphore
		if not semaphore._cond._waiters:	# type: ignore[attr-defined]
			del _semaphores[(id, state)]
		semaphore.release()


def criticalResourceSection(id:str = '', state:str = '') -> Callable:
	"""	Decorator to set and remove a state when a resource method is called.
	
		Args:
			state: The state to set.
		Return:
			Wrapped decorator.
	"""
	def decorate(func:Callable) -> Callable:
		@wraps(func)
		def wrapper(*args:Any, **kwargs:Any) -> Any:
			try:
				_id = args[0].ri	# ACME Resource type
			except:
				_id = id 
			enterCriticalSection(_id, state)
			r = func(*args, **kwargs)
			leaveCriticalSection(_id, state)
			return r
		return wrapper
	return decorate


#
#	Context Manager
# 


class CriticalSection(object):
	""" Context manager to guard a critical resource path. """

	def __init__(self, id:str, state:Optional[str] = '', timeout:Optional[float] = None) -> None:
		"""	Initialization of the context manager.
		
			Args:
				id: Resource ID of the resource to be monitored. This may also be any other ID in cases where the critical section is not a resource.
				state: State of the resource.
		"""
		self.id = id
		self.state = state
		self.timeout = timeout


	def __enter__(self) -> None:
		enterCriticalSection(self.id, self.state, self.timeout)

	
	def __exit__(self,	exctype: Optional[Type[BaseException]],
			 			excinst: Optional[BaseException],
						exctb: Optional[TracebackType]) -> Optional[bool]:
		leaveCriticalSection(self.id, self.state)
		return None






