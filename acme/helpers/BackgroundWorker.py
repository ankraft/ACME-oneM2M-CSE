#
#	BackgroundWorker.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This class implements a background process.
#

from __future__ import annotations
from Logging import Logging
import time, random, sys
from threading import Thread
from typing import Callable, List, Dict, Any, Protocol


class BackgroundWorker(object):

	def __init__(self, updateInterval:float, callback:Callable, name:str=None, startWithDelay:bool=False, count:int=None, dispose:bool=True, id:int=None) -> None:		# type: ignore[type-arg]
		self.updateInterval = updateInterval
		self.callback = callback
		self.running = False		# Indicator that a worker is running or will be stopped
		self.isStopped = True		# Indicator that a worker has really stopped
		self.workerThread: Thread = None
		self.name = name
		self.startWithDelay = startWithDelay
		self.count = count
		self.numberOfRuns = 0
		self.dispose = dispose	# Only run once, then remove itself from the pool
		self.id = id


	def start(self, **args:Any) -> BackgroundWorker:
		if self.running:
			self.stop()
		Logging.logDebug(f'Starting worker thread: {self.name}')
		self.running = True
		self.isStopped = True
		self.args = args
		self.workerThread = Thread(target=self.work)
		self.workerThread.setDaemon(True)	# Make the thread a daemon of the main thread
		self.workerThread.name = self.name
		self.workerThread.start()
		return self


	def stop(self) -> BackgroundWorker:
		Logging.logDebug(f'Stopping worker thread: {self.name}')
		# Stop the thread
		self.running = False
		if self.workerThread is not None and self.updateInterval is not None:
			self.workerThread.join(self.updateInterval + 5) # wait a short time for the thread to terminate
			self.workerThread = None
		# Note: worker is removed in _postCall()
		return self



	def work(self) -> None:
		self.numberOfRuns = 0
		if self.startWithDelay:	# First execution of the worker after a sleep
			self._sleep()
		while self.running:
			result = True
			try:
				self.numberOfRuns += 1
				result = self.callback(**self.args)
			except Exception as e:
				Logging.logErr(f'Worker "{self.name}" exception during callback {self.callback.__name__}: {str(e)}')
			finally:
				if self.count is not None and self.numberOfRuns >= self.count:
					self.running = False

				if result and self.running:
					self._sleep()
					continue

			# if we reached this we will stop
			Logging.logDebug(f'Stopping worker thread: {self.name}')
			self.running = False
		self._postCall()


	# self-made sleep. Helps in speed-up shutdown etc
	divider = 5.0
	def _sleep(self) -> None:
		if self.updateInterval < 1.0:
			time.sleep(self.updateInterval)
		else:
			for i in range(0, int(self.updateInterval * self.divider)):
				time.sleep(1.0 / self.divider)
				if not self.running:
					break


	def _postCall(self) -> None:
		"""	Called after execution finished.
		"""
		if self.dispose:
			BackgroundWorkerPool._removeBackgroundWorkerFromPool(self)
		self.running = False
		self.isStopped = True


	def __repr__(self) -> str:
		return f'BackgroundWorker(name={self.name}, callback={str(self.callback)}, running={self.running}, updateInterval={self.updateInterval:f}, startWithDelay={self.startWithDelay}, numberOfRuns={self.numberOfRuns:d}, dispose={self.dispose}, id={self.id})'



class BackgroundWorkerPool(object):

	backgroundWorkers:Dict[int, BackgroundWorker] = {}

	def __new__(cls, *args:str, **kwargs:str) -> BackgroundWorkerPool:
		raise TypeError(f'{BackgroundWorkerPool.__name__} must not be instantiated')


	@classmethod
	def newWorker(cls, updateInterval:float, workerCallback:Callable, name:str=None, startWithDelay:bool=False, count:int=None, dispose:bool=True) -> BackgroundWorker:	# type:ignore[type-arg]
		"""	Create a new background worker that periodically executes the callback.
		"""
		# Get a unique ID
		while True:
			if (id := random.randint(1,sys.maxsize)) not in cls.backgroundWorkers:
				break
		worker = BackgroundWorker(updateInterval, workerCallback, name, startWithDelay, count=count, dispose=dispose, id=id)
		cls.backgroundWorkers[id] = worker
		return worker


	@classmethod
	def newActor(cls, delay:float, workerCallback:Callable, name:str=None, dispose:bool=True) -> BackgroundWorker:	#type:ignore[type-arg]
		"""	Create a new background worker that runs only once after a delay (the 'delay' may be 0.0s, though).
		"""
		return cls.newWorker(delay, workerCallback, name=name, startWithDelay=delay>0.0, count=1, dispose=dispose)


	@classmethod
	def findWorkers(cls, name:str=None, running:bool=None) -> List[BackgroundWorker]:
		return [ w for w in cls.backgroundWorkers.values() if (name is None or w.name == name) and (running is None or running == w.running) ]


	@classmethod
	def stopWorkers(cls, name:str, wait:bool=True) -> List[BackgroundWorker]:
		workers = cls.findWorkers(name=name)
		for w in workers:
			w.stop()
			if wait:
				while not w.isStopped:
					time.sleep(0.01)
		return workers


	@classmethod
	def removeWorkers(cls, name:str) -> List[BackgroundWorker]:
		workers = cls.stopWorkers(name)
		# Most workers should be removed when stopped, but remove the rest here
		for w in workers:
			cls._removeBackgroundWorkerFromPool(w)
		return workers


	@classmethod
	def _removeBackgroundWorkerFromPool(cls, worker:BackgroundWorker) -> None:
		if worker is not None and worker.id in cls.backgroundWorkers:
			del cls.backgroundWorkers[worker.id]


