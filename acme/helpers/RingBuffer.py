#
#	RingBuffer.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Helper classes and function to help with ring buffer operations.
"""

from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')
""" Type variable for the items stored in the ring buffer. """

class RingBuffer(Generic[T]):
	""" A simple ring buffer implementation that allows for fixed-size storage of items.
		It overwrites the oldest item when the buffer is full.

		Calling functions need to maintain their own index to track the current position in the buffer.
		This is useful where an arbitrary number of functions need to access the buffer concurrently,
		and each function needs to maintain its own position without interfering with others.
	"""
	
	def __init__(self, size:int):
		""" Initialize a ring buffer with a fixed size.
		
		Args:
			size: The maximum number of items the buffer can hold.
		"""

		self.capacity = size
		""" The maximum number of items the buffer can hold. """
		
		self.buffer:List[T] = [None] * self.capacity
		""" The internal storage for the ring buffer, initialized with None values. """

		self.head = -1
		""" The current head index of the ring buffer, initialized to -1 indicating an empty buffer. """



	def append(self, item:T) -> None:
		""" Add an item to the ring buffer. If the buffer is full, the oldest item is removed.
		
		Args:
			item: The item to add to the buffer.
		"""
		self.buffer[self.incrementHead()] = item
	

	def incrementHead(self) -> int:
		"""	Increment the head in a circular manner.
		
			Return:
				The new head value.
		"""
		self.head = self.nextIndex(self.head)
		return self.head
	

	def nextIndex(self, index:int) -> int:
		""" Increment an index in a circular manner without modifying the current index.
		
			Args:
				index: The index to increment.

			Return:
				The new index value.
		"""
		return (index + 1) % self.capacity
	

	def __getitem__(self, index:int) -> Optional[T]:
		""" Get an item from the buffer by index.
		
			Args:
				index: The index of the item to retrieve.
			Return:
				The item at the specified index, or None if the index is out of bounds.
		"""
		if 0 <= index < self.capacity:
			return self.buffer[index]
		return None
