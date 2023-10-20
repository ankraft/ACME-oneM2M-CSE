#
#	OrderedSet.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Simple implementation of an ordered set."""

from typing import Any

class OrderedSet(list):
	"""	Simple implementation of an ordered set.
	
		Items are ordered in the set by their order of adding them to the set.
		Uniqueness is assurd.
	"""
	
	def add(self, obj:Any) -> None:
		"""	Add an item to the set.

			Only unique items are added.

			Args:
				obj: Object to add.
		"""

		if obj in self:
			return
		self.append(obj)

		
