#
#	ThreadSafeCounter.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module provides a thread-safe counter class.
"""

from threading import Lock

class ThreadSafeCounter():
	""" A thread-safe counter.
	"""

	def __init__(self, initial:int = 0) -> None:
		""" Initialize the counter with an initial value.

			Args:
				initial: The initial counter value.
		"""
		self.counter:int = initial
		""" The counter value. """

		self.lock = Lock()
		""" The lock object. """
 

	def increment(self, value:int = 1) -> int:
		""" Increment the counter.

			Args:
				value: The value to increment the counter by.

			Returns:
				The new counter value.

		"""
		with self.lock:
			self.counter += value
			return self.counter


	def decrement(self, value:int = 1) -> int:
		""" Decrement the counter.

			Args:
				value: The value to decrement the counter by.

			Returns:
				The new counter value.
		"""
		with self.lock:
			self.counter -= 1
			return self.counter
 

	def value(self) -> int:
		""" Get the counter value.

			Returns:
				The current counter value.
		"""
		with self.lock:
			return self.counter