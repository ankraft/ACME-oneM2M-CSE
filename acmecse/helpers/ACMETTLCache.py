#
#	ACMETTLCache.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Improved TTLCache with eviction callback."""

from __future__ import annotations
from typing import Callable, Tuple, Optional, Any
from cachetools import TTLCache
import time

class ACMETTLCache(TTLCache):
	"""	An improved TTLCache that supports an eviction callback function. 
	
		This callback is called whenever an item is evicted from the cache, 
		either due to expiration or because the cache has reached its maximum size.
	"""
	
	_evict:Optional[Callable] = None
	"""	The eviction callback function.
	"""

	def __init__(self, maxsize: int, 
			  		   ttl: Any, 
					   timer: Callable=time.monotonic, 
					   getsizeof: Optional[Callable]=None, 
					   evict: Optional[Callable]=None) -> None:
		"""	Initialize the LRUCache.

			Args:
				maxsize: The maximum size of the cache.
				ttl: The time-to-live for cache entries.
				getsizeof: Optional function to determine the size of an item.
				evict: Optional callback function that is called when an item is evicted.
		"""
		super().__init__(maxsize, ttl, timer, getsizeof)
		self._evict = evict


	def expire(self, time: Optional[float]=None) -> list[Tuple[Any, Any]]:
		"""	Expire items from the cache and call the (optional) eviction callback for each expired item.
		
			Args:
				time: Optional time to check for expiration. If None, the current time is used.
			Return: 
				A list of tuples containing the expired key-value pairs.
		"""
		for e in (expired := super().expire(time)):
			if self._evict:
				print(e)
				self._evict(e[0], e[1])
		return expired