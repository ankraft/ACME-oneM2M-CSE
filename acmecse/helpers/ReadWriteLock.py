#
#	ReadWriteLock.py
#
#
#	This is a simple implementation of a ReadWriteLock.
#	From O'Reilly Python Cookbook by David Ascher, Alex Martelli
#	With changes to cover the starvation situation where a continuous
#	stream of readers may starve a writer, Lock Promotion and Context Managers
"""	This is a simple implementation of a ReadWriteLock.
"""

from __future__ import annotations
from typing import Optional
import threading


class ReadWriteLock(object):
	""" A lock object that allows many simultaneous "read locks", but
	only one "write lock." """

	def __init__(self, withPromotion:Optional[bool] = False) -> None:
		""" Initialize the ReadWriteLock object.
		
			Args:
				withPromotion: If True, then a reader thread can promote itself to a writer thread.
		"""
		self._read_ready = threading.Condition(threading.RLock())
		""" Condition object to synchronize the read and write locks."""
		
		self._readers = 0
		""" Number of readers."""
		
		self._writers = 0
		""" Number of writers."""
		
		self._promote = withPromotion
		""" If True, then a reader thread can promote itself to a writer thread."""
		
		self._readerList:list[int] = []  # List of Reader thread IDs
		""" List of Reader thread IDs."""
		
		self._writerList:list[int] = []  # List of Writer thread IDs
		""" List of Writer thread IDs."""


	def acquire_read(self) -> None:
		""" Acquire a read lock. Blocks only if a thread has
			acquired the write lock. 
		"""
		self._read_ready.acquire()
		try:
			while self._writers > 0:
				self._read_ready.wait()
			self._readers += 1
		finally:
			self._readerList.append(threading.get_ident())
			self._read_ready.release()


	def release_read(self) -> None:
		""" Release a read lock. 
		"""
		self._read_ready.acquire()
		try:
			self._readers -= 1
			if not self._readers:
				self._read_ready.notifyAll()
		finally:
			self._readerList.remove(threading.get_ident())
			self._read_ready.release()


	def acquire_write(self) -> None:
		""" Acquire a write lock. Blocks until there are no
			acquired read or write locks. 
		"""
		self._read_ready.acquire()   # A re-entrant lock lets a thread re-acquire the lock
		self._writers += 1
		self._writerList.append(threading.get_ident())
		while self._readers > 0:
			# promote to write lock, only if all the readers are trying to promote to writer
			# If there are other reader threads, then wait till they complete
			# reading
			if self._promote and threading.get_ident() in self._readerList and set(self._readerList).issubset(set(self._writerList)):
				break
			else:
				self._read_ready.wait()


	def release_write(self) -> None:
		""" Release a write lock. 
		"""
		self._writers -= 1
		self._writerList.remove(threading.get_ident())
		self._read_ready.notifyAll()
		self._read_ready.release()

##############################################################################


class ReadRWLock(object):
	""" Context Manager class for ReadWriteLock.
	"""

	def __init__(self, rwLock:ReadWriteLock) -> None:
		""" Initialize the ReadRWLock object."""
		
		self.rwLock = rwLock
		""" ReadWriteLock object."""

	def __enter__(self) -> ReadRWLock:
		""" Context Manager method to enter the block.
		
			This acquires a read lock. Blocks only if a thread has
			acquired the **write** lock.
			
			Returns:
				A ReadRWLock context manager object.
		"""
		self.rwLock.acquire_read()
		return self         # Not mandatory, but returning to be safe


	def __exit__(self, exc_type, exc_value, traceback) -> bool:	# type: ignore[no-untyped-def]
		""" Context Manager method to exit the block.
		
			This releases a read lock.
			
			Returns:
				False if exited due to an exception.
		"""
		self.rwLock.release_read()
		return True

##############################################################################


class WriteRWLock(object):
	"""  Context Manager class for ReadWriteLock.
	"""

	def __init__(self, rwLock:ReadWriteLock) -> None:
		""" Initialize the WriteRWLock object."""
		
		self.rwLock = rwLock
		""" ReadWriteLock object."""

	def __enter__(self) -> WriteRWLock:
		""" Context Manager method to enter the block.
		
			This acquires a write lock. Blocks until there are no
			acquired read or write locks.
			
			Returns:
				A WriteRWLock context manager object.
		"""
		self.rwLock.acquire_write()
		return self         # Not mandatory, but returning to be safe

	def __exit__(self, exc_type, exc_value, traceback) -> bool:		# type:ignore[no-untyped-def, exit-return]
		""" Context Manager method to exit the block.
		
			This releases a write lock.
			
			Returns:
				Always False.
		"""
		self.rwLock.release_write()
		return False        # Surpress any exceptions


##############################################################################
#
#	Tests
#
	
import time

def _reads() -> None:
	""" Test ReadRWLock.
	"""
	readLock = ReadRWLock(_lock)
	while True:
		with readLock as _:
			print("read")
			time.sleep(0.2)


def _writes() -> None:
	""" Test WriteRWLock.
	"""
	writeLock = WriteRWLock(_lock)
	while True:
		with writeLock as _:
			print("***write")
			time.sleep(0.1)
		time.sleep(1.0)


_lock = ReadWriteLock(withPromotion=False)
""" Test ReadWriteLock object."""

if __name__ == '__main__':

	threading.Timer(1, _reads).start()
	threading.Timer(1, _writes).start()
