#
#	TimeManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing time related CSE functions
#

from __future__ import annotations
from typing import cast, List
from ..services.Logging import Logging as L
from ..resources.TSB import TSB
from ..services import CSE
from ..etc.Types import BeaconCriteria
from ..etc.Types import ResourceTypes as T
from ..etc import DateUtils
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool


class TimeManager(object):

	def __init__(self) -> None:

		# Read all periofics and add them (again)
		for each in self._getAllPeriodicTimeSyncBeacons():
			self.addPeriodicTimeSyncBeacon(each)
		
		# Table for periodic timeSyncBeacons
		self.periodicTimeSyncBeacons:dict[str, BackgroundWorker] = {}

		L.isInfo and L.log('TimeManager initialized')


# LoS table
#dict[bcnr, (threshold, tsb.ri)]

	def shutdown(self) -> bool:
		"""	Shutdown the TimeManager.
		
			Return:
				Boolean, always True.
		"""
		L.isInfo and L.log('TimeManager shut down')
		return True
	
	# TODO restart: stop all timers


	# TODO addLoS, removeLoS
	# TODO isLossOfSynchronization


	def _getAllPeriodicTimeSyncBeacons(self) -> list[TSB]:
		return cast(List[TSB], CSE.storage.searchByFragment( { 'ty': T.TSB, 'bcnc': BeaconCriteria.PERIODIC} ))


	def addTimeSyncBeacon(self, tsb:TSB) -> None:
		# TODO
		if tsb.bcnc == BeaconCriteria.PERIODIC:
			self.addPeriodicTimeSyncBeacon(tsb)
		else:	# Loss of sync
			self.addLoSTimeSyncBeacon(tsb)


	def addPeriodicTimeSyncBeacon(self, tsb:TSB) -> None:
		"""	Add a worker for a periodic timeSyncBeacon resource.
		
			Args:
				tsb: timeSyncBeacon resource
		"""

		def periodicWorker() -> bool:
			"""	Worker to send a time sync notification.

				Return:
					Bool to indicate the continous run of the worker.
			"""
			L.isDebug and L.logDebug(f'Sending beacon notification for {tsb.ri}')
			return True

		
		# TODO send real notification

		if (ri := tsb.ri) in self.periodicTimeSyncBeacons:
			self.removePeriodicTimeSyncBeacon(tsb)
		worker = BackgroundWorkerPool.newWorker(tsb.getInterval(), 
												periodicWorker, 
												f'tsbPeriodic_{ri}', 
												startWithDelay = True).start()
		self.periodicTimeSyncBeacons[ri] = worker


	def addLoSTimeSyncBeacon(self, tsb:TSB) -> None:
		# TODO add to a table
		...

	
	def updateTimeSyncBeacon(self, tsb:TSB, originalBcnc:BeaconCriteria) -> None:
		# TODO
		...
	

	def removeTimeSyncBeacon(self, tsb:TSB) -> None:
		# TODO
		if tsb.bcnc == BeaconCriteria.PERIODIC:
			self.removePeriodicTimeSyncBeacon(tsb)
		else:	# Loss of sync
			# TODO
			...


	def removePeriodicTimeSyncBeacon(self, tsb:TSB) -> None:
		"""	Remove a periodic timeSyncBeacon resource. A running worker is stopped.
		
			Args:
				tsb: The timeSyncBeacon resource.
		"""
		if (ri := tsb.ri) in self.periodicTimeSyncBeacons:
			self.periodicTimeSyncBeacons[ri].stop()
			del self.periodicTimeSyncBeacons[tsb.ri]


	def getCSETimestamp(self) -> str:
		"""	Get the CSE's current date and time (UTC based).
		
			Return:
				ISO timestamp string
		"""
		return DateUtils.getResourceDate()