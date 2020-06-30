#
#	BackgroundWorker.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This class implements a background process.
#

from Logging import Logging
import time
from threading import Thread
from typing import Callable

class BackgroundWorker(object):

	def __init__(self, updateIntervall: float, workerCallback: Callable, name: str = None) -> None:
		self.workerUpdateIntervall = updateIntervall
		self.workerCallback = workerCallback
		self.doStop = True
		self.workerThread: Thread = None
		self.name = name


	def start(self) -> None:
		Logging.logDebug('Starting worker thread: %s' % self.name)
		self.doStop = False
		self.workerThread = Thread(target=self.work)
		self.workerThread.setDaemon(True)	# Make the thread a daemon of the main thread
		self.workerThread.start()


	def stop(self) -> None:
		Logging.logDebug('Stopping worker thread: %s' % self.name)
		# Stop the thread
		self.doStop = True
		if self.workerThread is not None and self.workerUpdateIntervall is not None:
			self.workerThread.join(self.workerUpdateIntervall + 5) # wait a short time for the thread to terminate
			self.workerThread = None


	def work(self) -> None:
		while not self.doStop:
			if self.workerCallback():
				self.sleep()
			else:
				Logging.logDebug('Stopping worker thread: %s' % self.name)
				self.doStop = True


	# self-made sleep. Helps in speed-up shutdown etc
	divider = 5.0
	def sleep(self) -> None:
		if self.workerUpdateIntervall < 1.0:
			time.sleep(self.workerUpdateIntervall)
		else:
			for i in range(0, int(self.workerUpdateIntervall * self.divider)):
				time.sleep(1.0 / self.divider)
				if self.doStop:
					break
