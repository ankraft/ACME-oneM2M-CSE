#
#	MultiDict.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of a multi-dictionary
#
""" Implementation of a multi-dictionary. """

from __future__ import annotations
from typing import Any
from collections import defaultdict

class MultiDict(defaultdict):
	"""	Implementation of a multi-dictionary. Keys can occur multiple times.

		Internally, the MultiDict is a defaultdict with list for each key that can hold multiple values.
	"""

	def __init__(self, dct:dict = None) -> None:
		""" Initialize the MultiDict. 

			Args:
				dct: A dictionary to initialize the MultiDict with.
		"""
		super(MultiDict, self).__init__(list)
		if dct is not None:
			for key in dct:
				self[key] = dct[key]


	def __setitem__(self, key:Any, value:Any) -> None:
		""" Set an item in the MultiDict. 

			Args:
				key: The key to set.
				value: The value to set.
		"""
		if key not in self.keys():
			super().__setitem__(key, [])
		self[key].append(value)	# append in place


	def getOne(self, key:Any, default:Any = None, greedy:bool = False) -> Any:
		""" Get one value for a key. If the key has multiple values, the first value is returned.

			Args:
				key: The key to get the value for.
				default: The default value to return if the key does not exist.
				greedy: If True, the value is removed from the MultiDict. This is only the value, not the key. The key is only removed if all values are removed.

			Returns:
				The value for the key.
		"""
		result = default
		if key in self:
			result = next(iter(self[key]))
			if greedy:
				self[key].remove(result)
				if not self[key]:
					del self[key]
		return result
	

	def get(self, key:Any, default:Any = None, greedy:bool = False, flatten:bool = False) -> Any:
		""" Get a value for a key. This returns a list of all values for the key.

			Args:
				key: The key to get the value lisz for.
				default: The default value to return if the key does not exist.
				greedy: If True, the value is removed from the MultiDict. This removes the key and all values.
				flatten: If True, and the value is a list with only one element, the element is returned instead of the list.

			Returns:
				The value for the key.
		"""
		result = super().get(key, default)
		if result is not None and greedy:
			del self[key]
		if flatten and isinstance(result, list):
			result = result[0] if len(result) == 1 else result
		return result
	

	def __str__(self) -> str:
		""" Return a string representation of the MultiDict. 
		
			Returns:
				A string representation of the MultiDict.
		"""
		return str( { k: v if len(v)>1 else v[0] for k,v in self.items() } )


	def __repr__(self) -> str:
		""" Return a string representation of the MultiDict. 
		
			Returns:
				A string representation of the MultiDict.
		"""
		return self.__str__()
