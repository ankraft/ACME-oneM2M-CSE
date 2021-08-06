#
#	BackgroundWorker.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This class implements a background process.
#

from __future__ import annotations
from .TextTools import simpleMatch
import random, sys, heapq, datetime
from threading import Thread, Timer, Lock
from typing import Callable, List, Dict, Any
import logging


_loggerCB:Callable[[int, str], None] = logging.log


def _utcTime() -> float:
	"""	Return the current time's timestamp, but relative to UTC.
	"""
	return datetime.datetime.utcnow().timestamp()

class BackgroundWorker(object):
	"""	This class provides the functionality for background worker or a single actor instance.
	"""

	def __init__(self, interval:float, callback:Callable, name:str=None, startWithDelay:bool=False, maxCount:int=None, dispose:bool=True, id:int=None, runOnTime:bool=True, runPastEvents:bool=False) -> None:
		self.interval 				= interval
		self.runOnTime				= runOnTime			# Compensate for processing time
		self.runPastEvents			= runPastEvents		# Run events that are in the past
		self.nextRunTime:float		= None				# Timestamp
		self.callback 				= callback			# Actual callback to process
		self.running 				= False				# Indicator that a worker is running or will be stopped
		self.name 					= name
		self.startWithDelay 		= startWithDelay
		self.maxCount 				= maxCount			# max runs
		self.numberOfRuns 			= 0					# Actual runs
		self.dispose 				= dispose			# Only run once, then remove itself from the pool
		self.id 					= id


	def start(self, **args:Any) -> BackgroundWorker:
		"""	Start the background worker in a thread. If the background worker is already
			running then it is stopped and started again.
		"""

		if self.running:
			self.stop()
		if _loggerCB:
				_loggerCB(logging.DEBUG, f'Starting {"worker" if self.interval > 0.0 else "actor"}: {self.name}')
		# L.isDebug and L.logDebug(f'Starting {"worker" if self.interval > 0.0 else "actor"}: {self.name}')
		self.numberOfRuns	= 0
		self.args 			= args
		self.running 		= True
		realInterval 		= self.interval if self.startWithDelay else 0	# first interval
		self.nextRunTime 	= _utcTime() + realInterval			# now + interval (or 0)
		BackgroundWorkerPool._queueWorker(self.nextRunTime, self)
		return self


	def stop(self) -> BackgroundWorker:
		"""	Stop the background worker.
		"""
		self.running = False
		if _loggerCB:
				_loggerCB(logging.DEBUG, f'Stopping {"worker" if self.interval > 0.0 else "actor"}: {self.name}')
		# L.isDebug and L.logDebug(f'Stopping {"worker" if self.interval > 0.0 else "actor"}: {self.name}')
		BackgroundWorkerPool._unqueueWorker(self.id)		# Stop the timer and remove from queue
		self._postCall()									# Note: worker is removed in _postCall()
		return self


	def _work(self) -> None:
		"""	Wrapper around the actual worker function. It deals with terminating,
			process time compensation, etc.
			This wrapper and the callback are executed in a separate Thread.
			At the end, depending on return value and whether the maxCount has been reached, the worker is added to the queue again.
		"""
		if not self.running:
			return
		result = True
		try:
			self.numberOfRuns += 1
			result = self.callback(**self.args)
		except Exception as e:
			if _loggerCB:
				_loggerCB(logging.ERROR, f'Worker "{self.name}" exception during callback {self.callback.__name__}: {str(e)}')
		finally:
			if not result or (self.maxCount and self.numberOfRuns >= self.maxCount):
				# False returned, or the numberOfRuns has reached the maxCount
				self.stop()
				# Not queued anymore after this run, but the Timer is restarted in stop()
			else:
				now = _utcTime()
				while True:
					if self.runOnTime:									# compensate for processing time?
						self.nextRunTime += self.interval				# timestamp for next interval (fixed interval)
					else:
						self.nextRunTime =  now + self.interval			# timestamp for next interval (interval + time from end of processing)
					if now < self.nextRunTime or self.runPastEvents:	# check whether to increment nextRunTime again (and again...)
						break

				BackgroundWorkerPool._queueWorker(self.nextRunTime, self)		# execute at nextRunTime


	def _postCall(self) -> None:
		"""	Internal cleanup after execution finished.
		"""
		if self.dispose:
			BackgroundWorkerPool._removeBackgroundWorkerFromPool(self)


	def __repr__(self) -> str:
		return f'BackgroundWorker(name={self.name}, callback={str(self.callback)}, running={self.running}, interval={self.interval:f}, startWithDelay={self.startWithDelay}, numberOfRuns={self.numberOfRuns:d}, dispose={self.dispose}, id={self.id}, runOnTime={self.runOnTime})'


class BackgroundWorkerPool(object):
	"""	Pool and factory for background workers and actors.
	"""
	backgroundWorkers:Dict[int, BackgroundWorker]	= {}
	workerQueue:List 								= []
	""" Priority queue. Contains tuples (nextExecution timestamp, workerID). """
	workerTimer:Timer								= None
	queueLock:Lock					 				= Lock()


	def __new__(cls, *args:str, **kwargs:str) -> BackgroundWorkerPool:
		raise TypeError(f'{BackgroundWorkerPool.__name__} must not be instantiated')
	

	@classmethod
	def setLogger(cls, loggerCB:Callable) -> None:
		"""	Assign a callback for logging
		"""
		global _loggerCB
		_loggerCB = loggerCB


	@classmethod
	def newWorker(cls, interval:float, workerCallback:Callable, name:str=None, startWithDelay:bool=False, maxCount:int=None, dispose:bool=True, runOnTime:bool=True, runPastEvents:bool=False) -> BackgroundWorker:	# typxe:ignore[type-arg]
		"""	Create a new background worker that periodically executes the callback.
		"""
		# Get a unique worker ID
		while True:
			if (id := random.randint(1,sys.maxsize)) not in cls.backgroundWorkers:
				break
		worker = BackgroundWorker(interval, workerCallback, name, startWithDelay, maxCount=maxCount, dispose=dispose, id=id, runOnTime=runOnTime, runPastEvents=runPastEvents)
		cls.backgroundWorkers[id] = worker
		return worker


	@classmethod
	def newActor(cls, workerCallback:Callable, delay:float=0.0, at:float=None, name:str=None, dispose:bool=True) -> BackgroundWorker:
		"""	Create a new background worker that runs only once after a `delay`
			(the 'delay' may be 0.0s, though), or `at` a sepcific time (UTC timestamp).
			The `at` argument provide convenience to calculate the delay to wait before the
			worker runs.
			The "actor" is only a BackgroundWorker object and needs to be started manually
			with the `start()` method.
		"""
		if at:
			if delay != 0.0:
				raise ValueError('Cannot set both "delay" and "at" arguments')
			delay = at - _utcTime()
		return cls.newWorker(delay, workerCallback, name=name, startWithDelay=delay>0.0, maxCount=1, dispose=dispose)


	@classmethod
	def findWorkers(cls, name:str=None, running:bool=None) -> List[BackgroundWorker]:
		"""	Find and return a list of worker(s) that match the search criteria:

			- `name` - Name of the worker. The `name` may contain simple wildcards (* and ?)
			- `running` - The running status of the worker


		"""
		return [ w for w in cls.backgroundWorkers.values() if (name is None or simpleMatch(w.name, name)) and (running is None or running == w.running) ]


	@classmethod
	def stopWorkers(cls, name:str=None) -> List[BackgroundWorker]:
		"""	Stop the worker(s) that match the optional `name` parameter. If `name` is not given then stop all workers.
			It returns a list of the stopped workers.
		"""
		workers = cls.findWorkers(name=name)
		for w in workers:
			w.stop()
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


	@classmethod
	def _queueWorker(cls, delay:float, worker:BackgroundWorker) -> None:
		"""	Queue a `worker` for execution after `delay` seconds.
		"""
		top = cls.workerQueue[0] if cls.workerQueue else None
		with cls.queueLock:
			heapq.heappush(cls.workerQueue, (delay, worker.id, worker.name	))
			cls._stopTimer()
		cls._startTimer()


	@classmethod
	def _unqueueWorker(cls, id:int) -> None:
		"""	Remove the Backgroundworker for `id` from the queue.
		"""
		with cls.queueLock:
			cls._stopTimer()
			for h in cls.workerQueue:
				if h[1] == id:
					cls.workerQueue.remove(h)
					heapq.heapify(cls.workerQueue)
					break	# Only 1 worker
			cls._startTimer()


	@classmethod
	def _startTimer(cls) -> None:
		""" Start the workers queue timer.
		"""
		if cls.workerQueue:
			cls.workerTimer = Timer(cls.workerQueue[0][0] - _utcTime(), cls._execQueue)
			cls.workerTimer.setDaemon(True)	# Make the Timer thread a daemon of the main thread
			cls.workerTimer.start()
	

	@classmethod
	def _stopTimer(cls) -> None:
		"""	Cancel/interrupt the workers queue timer.
		"""
		if cls.workerTimer is not None:
			cls.workerTimer.cancel()


	@classmethod
	def _execQueue(cls) -> None:
		"""	Execute the actual BackgroundWorker's callback in a thread.
		"""
		with cls.queueLock:
			if cls.workerQueue:
				_, workerID, name = heapq.heappop(cls.workerQueue)
				if (worker := cls.backgroundWorkers.get(workerID)) is not None:
					thread = Thread(target=worker._work)
					thread.setDaemon(True)
					thread.setName(name)
					thread.start()
			cls._startTimer()	# start timer again

