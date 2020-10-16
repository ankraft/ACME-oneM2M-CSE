# From O'Reilly Python Cookbook by David Ascher, Alex Martelli
# With changes to cover the starvation situation where a continuous
#   stream of readers may starve a writer, Lock Promotion and Context Managers

import threading
#import logging


class ReadWriteLock(object):
    """ A lock object that allows many simultaneous "read locks", but
    only one "write lock." """

    def __init__(self, withPromotion=False):
        self._read_ready = threading.Condition(threading.RLock())
        self._readers = 0
        self._writers = 0
        self._promote = withPromotion
        self._readerList = []  # List of Reader thread IDs
        self._writerList = []  # List of Writer thread IDs

    def acquire_read(self):
        #logging.debug("RWL : acquire_read()")
        """ Acquire a read lock. Blocks only if a thread has
	acquired the write lock. """
        self._read_ready.acquire()
        try:
            while self._writers > 0:
                self._read_ready.wait()
            self._readers += 1
        finally:
            self._readerList.append(threading.get_ident())
            self._read_ready.release()

    def release_read(self):
        #logging.debug("RWL : release_read()")
        """ Release a read lock. """
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notifyAll()
        finally:
            self._readerList.remove(threading.get_ident())
            self._read_ready.release()

    def acquire_write(self):
        #logging.debug("RWL : acquire_write()")
        """ Acquire a write lock. Blocks until there are no
	acquired read or write locks. """
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

    def release_write(self):
        #logging.debug("RWL : release_write()")
        """ Release a write lock. """
        self._writers -= 1
        self._writerList.remove(threading.get_ident())
        self._read_ready.notifyAll()
        self._read_ready.release()

##############################################################################


class ReadRWLock(object):
    # Context Manager class for ReadWriteLock

    def __init__(self, rwLock):
        self.rwLock = rwLock

    def __enter__(self):
        self.rwLock.acquire_read()
        return self         # Not mandatory, but returning to be safe

    def __exit__(self, exc_type, exc_value, traceback):
        self.rwLock.release_read()
        return False        # Raise the exception, if exited due to an exception

##############################################################################


class WriteRWLock(object):
    # Context Manager class for ReadWriteLock

    def __init__(self, rwLock):
        self.rwLock = rwLock

    def __enter__(self):
        self.rwLock.acquire_write()
        return self         # Not mandatory, but returning to be safe

    def __exit__(self, exc_type, exc_value, traceback):
        self.rwLock.release_write()
        return False        # Raise the exception, if exited due to an exception


import time


def reads():
    readLock = ReadRWLock(lock)
    while True:
        with readLock as _:
            print("read")
            time.sleep(0.1)


def writes():
    writeLock = WriteRWLock(lock)
    while True:
        with writeLock as _:
            print("***write")
            time.sleep(0.1)
        time.sleep(0.1)


lock = ReadWriteLock()

if __name__ == '__main__':

    threading.Timer(1, reads).start()
    threading.Timer(1, writes).start()
