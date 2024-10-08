#
#	TinyDBBetterTable.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module provides an optimized Table class for TinyDB that optimizes the document index handling.
"""

from typing import Dict, Callable, Mapping
from tinydb.table import Table

class TinyDBBetterTable(Table):
	"""	This class is an add-on to TinyDB's *Table* class. It removes some computations that are not
		necessary in ACME.
	
		- Document ID's are always strings.
		- Since document ID's are strings, the conversion during each update is not necessary anymore.
	"""

	@classmethod
	def assign(self, table:Table) -> None:
		"""	Class method to assign this class to an existing *Table* instance.

			Args:
				table: A TinyDB *Table* instance.
		"""
		if not isinstance(table, Table):
			raise TypeError(f'object must be of class Table, is: {type(table)}')
		table.__class__ = TinyDBBetterTable
		table.document_id_class = str				# type:ignore[assignment]


	# Overload
	def _get_next_id(self) -> str:
		"""	Return the ID for a newly inserted document. This method overloads the original method
			to return the ID as a string.

			Returns:
				The ID for the new document.
		"""
		return str(super()._get_next_id()) # type:ignore[no-untyped-call]


	# Overload
	def _update_table(self, updater: Callable[[Dict[int, Mapping]], None]) -> None:
		"""
		Perform a table update operation.

		The storage interface used by TinyDB only allows to read/write the
		complete database data, but not modifying only portions of it. Thus,
		to only update portions of the table data, we first perform a read
		operation, perform the update on the table data and then write
		the updated data back to the storage.

		As a further optimization, we don't convert the documents into the
		document class, as the table data will *not* be returned to the user.
		"""

		tables = self._storage.read()

		if tables is None:
			# The database is empty
			tables = {}

		try:
			table = tables[self.name]
		except KeyError:
			# The table does not exist yet, so it is empty
			table = {}

		# Perform the table update operation
		updater(table) # type:ignore[arg-type]

		tables[self.name] = table

		# Write the newly updated data back to the storage
		self._storage.write(tables)

		# Clear the query cache, as the table contents have changed
		self.clear_cache()
