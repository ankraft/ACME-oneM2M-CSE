#
#	Singleton.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Singleton helper class."""

from typing import Any

class Singleton(type):
	"""	Singleton metaclass.

		This class implements the Singleton design pattern as a metaclass. 

		Attention:
			Classes using this metaclass will never be able to have more than one instance.

			Also, instances will not be garbage collected until the program ends.

		Example:
			class MyClass(metaclass=Singleton):
				pass
	"""

	_instances: dict[type, object] = {} 
	""" Dictionary to hold the single instances of the classes using this metaclass. """

	def __call__(cls, *args: Any, **kwargs: Any) -> object: 
		""" Override the __call__ method to control the instantiation of classes using this metaclass.

			Args:
				*args: Positional arguments to pass to the class constructor.
				**kwargs: Keyword arguments to pass to the class constructor.

			Returns:
				The single instance of the class.
		"""
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


