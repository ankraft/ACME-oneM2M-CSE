#
#	ACMELRUCache.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Improved LRUCache with eviction callback."""

from __future__ import annotations
from typing import Callable, Tuple, Optional
import cachetools

class ACMELRUCache(cachetools.LRUCache):
	"""	An improved version of the LRUCache from cachetools with an eviction callback.
	"""

	_evict:Optional[Callable] = None
	"""	The eviction callback function.
	"""

	def __init__(self, maxsize:int, getsizeof:Callable = None, evict:Callable = None) -> None:
		"""	Initialize the LRUCache.

			Args:
				maxsize: The maximum size of the cache.
				getsizeof: Optional function to determine the size of an item.
				evict: Optional callback function that is called when an item is evicted.
		"""
		super().__init__(maxsize, getsizeof)
		self._evict = evict

	def popitem(self) -> Tuple[object, object]:
		"""	Pop an item from the cache and call the (optional) eviction callback.

			Return:
				A tuple with the key and the value of the evicted item.
		"""
		key, val = cachetools.LRUCache.popitem(self)
		if self._evict:
			self._evict(key, val)
		return key, val