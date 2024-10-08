#
#	ACMEIntEnum.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Improved *IntEnum* base class."""

from __future__ import annotations

from typing import List, Tuple, cast, Optional, Any
from enum import IntEnum

class ACMEIntEnum(IntEnum):
	""" A base class for many oneM2M related enum types in ACME. It provides additional halper
		methods to simplify working with *IntEnum* classes.
	"""

	@classmethod
	def has(cls, value:int|str|List[int|str]|Tuple[int|str]) -> bool:
		"""	Check whether the enum type has an entry with
			either the given int value or string name. 

			Args:
				value: *value* can also be a tuple of values to test. 
					In this case, all the values in the tuple must exist.
			Return:
				*True* if the value exists.
		"""

		def _check(value:int|str) -> bool:
			if isinstance(value, int):
				return value in cls.__members__.values()
			else:
				return value in cls.__members__

		if isinstance(value, list):	# Checks if list
			for v in cast(list, value):
				if not _check(v):
					return False
			return True

		if isinstance(value, tuple):	# Checks if tuple
			for v in cast(tuple, value):
				if not _check(v):
					return False
			return True

		return _check(value)


	@classmethod
	def to(cls, name:str|Tuple[str], insensitive:Optional[bool]=False) -> Any:
		"""	Return an enum value by its name.

			Args:
				name: String or a tuple of strings with names.
				insensitive: Optional boolean indicating whether names should be treated case-sensitive or not.
			
			Return:
				A valid enum value, a list of enum values if *name* is a tupple of strings (according to the order in the tuple), or *None* in case of an error.

		"""
		# TODO docu
		
		def _to(name:str) -> Any:
			try:
				if insensitive:
					_n = name.lower()
					return next(v for n,v in cls.__members__.items() if n.lower() == _n)	# type: ignore
				return next(v for n,v in cls.__members__.items() if n == name)	# type: ignore
			except StopIteration:
				return None

		if isinstance(name, tuple):
			result = []
			for n in name:
				if not (t := _to(n)):
					return None			# Early return
				result.append(t)
			return result
			
		return _to(cast(str, name))


	def __str__(self) -> str:
		"""	Stringify an enum.

			Return:
				The name of an enum value.		
		"""
		return self.name
	
	
	def __int__(self) -> int:
		"""	Get the integer value of an enum.

			Return:
				The value of an enum value.		
		"""
		return self.value


	def __repr__(self) -> str:
		"""	Stringify an enum.

			Return:
				The name of an enum value.		
		"""
		return self.__str__()
