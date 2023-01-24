#
#	TinyDBBufferedStorage.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module provides a storage driver class for TinyDB that implements a buffered disk write.
"""

import _thread as Thread
from threading import Event
from time import sleep
from typing import Optional, Dict, Any
from tinydb.storages import JSONStorage


class TinyDBBufferedStorage(JSONStorage):
	"""	Storage driver class for TinyDB that implements a buffered disk write.

		Attributes:
			__slots__: Define slots for instance variables.
			_writeEvent: Event instance to notify when a write happened.
			_writeDelay: Delay before writing the data to disk.
			_shutdownLock: Internal lock when shutting down the database.
			_running: Indicating that the database is open and in use.
			_shutting_down: Indicator that the database is closing. This is different from `_running`.
			_changed: Indicator that the write buffer is *dirty* and needs to be written.
			_data: The actual database data, which is also strored in memory as a buffer.
	"""

	__slots__ = (
		'_writeEvent',
		'_writeDelay',
		'_shutdownLock',
		'_running',
		'_shutting_down',
		'_changed',
		'_data',
	)

	def __init__(self, path:str, create_dirs:bool = False, encoding:str = None, access_mode:str = 'r+', write_delay:int = 1, **kwargs:Any) -> None:
		"""	Initialization of the storage driver.

			This initializer adds a new parameter *write_delay* to the initialization of TinyDB's *JSONStorage* base class.

			Args:
				path: Where to store the JSON data.
				access_mode: Mode in which the file is opened.
				encoding: The encoding character set for the database file
				create_dirs: Whether the directory structure to the database file should be created or not.
				write_delay: Time to wait before writing a changed database buffer, in seconds.
				kwargs: Any other argument.
		"""
		super().__init__(path, create_dirs, encoding, access_mode, **kwargs)

		self._shutdownLock = Thread.allocate_lock()
		self._writeEvent = Event()
		self._running = True
		self._shutting_down = False
		self._changed = False
		self._writeDelay:int = write_delay
		self._data:Dict[str, Dict[str, Any]] = {}

		# finishing init. Read the data for the first time
		self._data = super().read()

		# only start the file write thread at all if the access mode is not read only
		if self._mode == 'r+':
			Thread.start_new_thread(self._fileWriter, ())


	def write(self, data:Dict[str, Dict[str, Any]]) -> None:
		"""	Write the current state of the database to the storage.

			This is not done directly, but it is indicated that the data has changed and should be written during
			the next phase of the buffered write.
		
			Args:
				data: The current state of the database.
		"""
		if not self._mode == "r+":
			raise PermissionError('DB Storage is openend as read-only')
		self._data = data
		self._changed = True
		self._writeEvent.set()


	def _fileWriter(self) -> None:
		"""	Worker for the file writer thread.
		"""
		self._shutdownLock.acquire()
		self._writeEvent.clear()
		while self._running:

			if self._writeEvent.wait() and self._changed:
				# Instead of busy waiting in the loop the following line waits
				# for the occurance of a write event. 
				# After a dirty buffer (ie. when the event occurs) there will be
				# a short delay, to prevent trashing.
				for _ in range(int(self._writeDelay)):
					if self._shutting_down:
						break
					sleep(1)
						
				self._changed = False
				super().write(self._data)
				self._writeEvent.clear()

		self._shutdownLock.release()


	def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
		"""	Read the current state.

			This just returns the in-memory representation of the database.

			Return:
				Return the current state.
		"""

		return self._data


	def close(self) -> None:
		"""	Write any dirty database files and close all handles.
		"""
		# Wait for last change
		self._shutting_down = True
		while self._changed:
			...
		self._running = False			# terminate _fileWriter loop
		self._writeEvent.set()			# send event
		self._shutdownLock.acquire()	# Wait for the _fileWriter loop to finish
		if self._handle != None:
			self._handle.flush()
			self._handle.close()

