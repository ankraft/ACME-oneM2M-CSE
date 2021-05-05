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
import Utils
import time, random, sys
from threading import Thread
from typing import Callable, List, Dict, Any, Protocol

# TODO what happens when interval is continuously to short? Error message?

class BackgroundWorker(object):
	"""	This class provides the functionality for background worker or a single actor instance.
	"""

	def __init__(self, interval:float, callback:Callable, name:str=None, startWithDelay:bool=False, count:int=None, dispose:bool=True, id:int=None, compensateProcessTime:bool=False) -> None:		# type: ignore[type-arg]
		self.interval 				= interval
		self.realInterval 			= interval					# this takes processing time into account and may be calculated for every run. Default = interval
		self.compensateProcessTime	= compensateProcessTime
		self.nextRunTime:float		= None
		self.callback 				= callback
		self.running 				= False						# Indicator that a worker is running or will be stopped
		self.isStopped 				= True						# Indicator that a worker has really stopped
		self.workerThread: Thread 	= None
		self.name 					= name
		self.startWithDelay 		= startWithDelay
		self.count 					= count
		self.numberOfRuns 			= 0
		self.dispose 				= dispose					# Only run once, then remove itself from the pool
		self.id 					= id


	def start(self, **args:Any) -> BackgroundWorker:
		"""	Start the background worker in a thread. If the background worker is already
			running then it is stopped and started again.
		"""
		if self.running:
			self.stop()
		Logging.logDebug(f'Starting worker thread: {self.name}')
		self.running = True
		self.isStopped = True
		self.args = args
		self.workerThread = Thread(target=self.work)
		self.workerThread.setDaemon(True)	# Make the thread a daemon of the main thread
		self.workerThread.name = self.name
		self.nextRunTime = Utils.utcTime()		# initialize
		self.workerThread.start()
		return self


	def stop(self) -> BackgroundWorker:
		"""	Stop the background worker.
		"""
		Logging.logDebug(f'Stopping worker thread: {self.name}')
		# Stop the thread
		self.running = False
		if self.workerThread is not None and self.interval is not None:
			self.workerThread.join(self.interval + 5) # wait a short time for the thread to terminate
			self.workerThread = None
		# Note: worker is removed in _postCall()
		return self



	def work(self) -> None:
		"""	Wrapper around the actual worker function. It deals with terminating,
			process time compensation, etc.
		"""
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
	minSleep = 1.0 / divider
	def _sleep(self) -> None:

		# If compensating for the runtime then re-calculate the next real sleep time necessary to match the next runTime
		if self.compensateProcessTime:
			self.nextRunTime += self.interval						# next interval
			self.realInterval = self.nextRunTime - Utils.utcTime()	# nextRunTime points already to the next run time
			if self.realInterval <= 0.0:							# Running the task might have taken longer than the interval. Then don't sleep.
				return												# no sleep

		if self.realInterval < self.minSleep:
			time.sleep(self.realInterval)
		else:
			for i in range(0, int(self.realInterval * self.divider)):
				time.sleep(self.minSleep)
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
		return f'BackgroundWorker(name={self.name}, callback={str(self.callback)}, running={self.running}, interval={self.interval:f}, startWithDelay={self.startWithDelay}, numberOfRuns={self.numberOfRuns:d}, dispose={self.dispose}, id={self.id}, compensateProcessTime={self.compensateProcessTime})'



class BackgroundWorkerPool(object):
	"""	Pool and factory for background workers and actors.
	"""

	backgroundWorkers:Dict[int, BackgroundWorker] = {}

	def __new__(cls, *args:str, **kwargs:str) -> BackgroundWorkerPool:
		raise TypeError(f'{BackgroundWorkerPool.__name__} must not be instantiated')


	@classmethod
	def newWorker(cls, interval:float, workerCallback:Callable, name:str=None, startWithDelay:bool=False, count:int=None, dispose:bool=True, compensateProcessTime:bool=False) -> BackgroundWorker:	# type:ignore[type-arg]
		"""	Create a new background worker that periodically executes the callback.
		"""
		# Get a unique ID
		while True:
			if (id := random.randint(1,sys.maxsize)) not in cls.backgroundWorkers:
				break
		worker = BackgroundWorker(interval, workerCallback, name, startWithDelay, count=count, dispose=dispose, id=id, compensateProcessTime=compensateProcessTime)
		cls.backgroundWorkers[id] = worker
		return worker


	@classmethod
	def newActor(cls, delay:float, workerCallback:Callable, name:str=None, dispose:bool=True) -> BackgroundWorker:	#type:ignore[type-arg]
		"""	Create a new background worker that runs only once after a delay (the 'delay' may be 0.0s, though).
		"""
		return cls.newWorker(delay, workerCallback, name=name, startWithDelay=delay>0.0, count=1, dispose=dispose)


	@classmethod
	def findWorkers(cls, name:str=None, running:bool=None) -> List[BackgroundWorker]:
		"""	Find and return a list of worker(s) that match the search criteria:

			- `name` - Name of the worker
			- `running` - The running status of the worker
		"""
		return [ w for w in cls.backgroundWorkers.values() if (name is None or w.name == name) and (running is None or running == w.running) ]


	@classmethod
	def stopWorkers(cls, name:str, wait:bool=True) -> List[BackgroundWorker]:
		"""	Stop the worker(s) that match the `name` parameter. Is `wait` is True then this
			function will wait for each worker to stop. It returns a list of the stopped
			workers.
		"""
		workers = cls.findWorkers(name=name)
		for w in workers:
			w.stop()
			if wait:
				while not w.isStopped:
					time.sleep(0.01)
		return workers


	@classmethod
	def removeWorkers(cls, name:str) -> List[BackgroundWorker]:
		"""	Remove workers from the pool. Before removal they will be stopped first.
			Only workers that match the `name` are removed.
		"""
		workers = cls.stopWorkers(name)
		# Most workers should be removed when stopped, but remove the rest here
		for w in workers:
			cls._removeBackgroundWorkerFromPool(w)
		return workers


	@classmethod
	def _removeBackgroundWorkerFromPool(cls, worker:BackgroundWorker) -> None:
		if worker is not None and worker.id in cls.backgroundWorkers:
			del cls.backgroundWorkers[worker.id]


