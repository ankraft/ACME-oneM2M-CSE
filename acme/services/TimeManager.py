#
#	TimeManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing time related CSE functions
#

from __future__ import annotations
from typing import cast, List, Tuple
from ..services.Logging import Logging as L
from ..resources.TSB import TSB
from ..services import CSE
from ..etc.Types import BeaconCriteria, CSERequest, Result, ResourceTypes as T, ResponseStatusCode as RC
from ..etc import DateUtils
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool

# TODO add check to http request handling
# TODO add check to http response handling
# TODO add check to mqtt request handling
# TODO add check to mqtt response handling

class TimeManager(object):

	def __init__(self) -> None:

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		# Read all periofics and add them (again)
		for each in self._getAllPeriodicTimeSyncBeacons():
			self.addPeriodicTimeSyncBeacon(each)
		
		# Register to receive events
		CSE.event.addHandler(CSE.event.requestReceived, self.requestReveivedHandler)			# type: ignore
		CSE.event.addHandler(CSE.event.responseReceived, self.responseReveivedHandler)			# type: ignore
		
		# Table for periodic timeSyncBeacons
		self.periodicTimeSyncBeacons:dict[str, BackgroundWorker] = {}

		# Table for Loss of sync timeSyncBeacons
		self.losTimeSyncBeacons:dict[str, Tuple[float, str]] = {}	# dict bcnr -> (threshold, tsb.ri)

		L.isInfo and L.log('TimeManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeManager.
		
			Return:
				Boolean, always True.
		"""
		self._stopPeriodicBeacons()
		L.isInfo and L.log('TimeManager shut down')
		return True


	def restart(self) -> None:
		"""	Restart the time manager services.
		"""
		self._stopPeriodicBeacons()
		self.losTimeSyncBeacons.clear()
		L.isDebug and L.logDebug('TimeManager restarted')

	
	def _stopPeriodicBeacons(self) -> None:
		"""	Stop all the running periodic timers. """
		for each in self.periodicTimeSyncBeacons.values():
			each.stop()
		self.periodicTimeSyncBeacons.clear()


	def requestReveivedHandler(self, req:CSERequest) -> None:
		# L.logErr(f'Received {req}')
		...

	def responseReveivedHandler(self, resp:CSERequest) -> None:
		# L.logErr(f'Received {resp}')
		#L.logWarn(self.isLossOfSynchronization(resp))
		...

	

	# TODO  removeLoS
	# TODO isLossOfSynchronization


	def _getAllPeriodicTimeSyncBeacons(self) -> list[TSB]:
		return cast(List[TSB], CSE.storage.searchByFragment( { 'ty': T.TSB, 'bcnc': BeaconCriteria.PERIODIC} ))


	def addTimeSyncBeacon(self, tsb:TSB) -> Result:
		# TODO doc
		if tsb.bcnc == BeaconCriteria.PERIODIC:
			return self.addPeriodicTimeSyncBeacon(tsb)
		else:	# Loss of sync
			return self.addLoSTimeSyncBeacon(tsb)


	def addPeriodicTimeSyncBeacon(self, tsb:TSB) -> Result:
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
			notification = {
				'm2m:tsbn' : {	# TODO proposed short name. Check with TS-0004 later
					'tbr' : tsb.ri,
					'ctm' : self.getCSETimestamp()
				}
			}
			CSE.notification.sendNotificationWithDict(notification, tsb.bcnu)
			return True

		
		if (ri := tsb.ri) in self.periodicTimeSyncBeacons:
			self.removePeriodicTimeSyncBeacon(tsb)
		worker = BackgroundWorkerPool.newWorker(tsb.getInterval(), 
												periodicWorker, 
												f'tsbPeriodic_{ri}', 
												startWithDelay = True).start()
		self.periodicTimeSyncBeacons[ri] = worker
		return Result.successResult()


	def addLoSTimeSyncBeacon(self, tsb:TSB) -> Result:
		# TODO doc
		if not (bcnr := tsb.bcnr):
			L.isWarn and L.logWarn(dbg := f'bcnr missing in TSB: {tsb.ri}')
			return Result.errorResult(dbg = dbg)
		if bcnr in self.losTimeSyncBeacons: 
			L.isDebug and L.logDebug(dbg := f'TimeSyncBeacon already defined for requester: {bcnr}')	# TODO wait for discussion whether multiple bcnr are allowed
			return Result.errorResult(dbg = dbg)
		self.losTimeSyncBeacons[bcnr] = (tsb.bcnt, tsb.ri)
		return Result.successResult()

	
	def updateTimeSyncBeacon(self, tsb:TSB, originalBcnc:BeaconCriteria) -> Result:
		# TODO
		...
	

	def removeTimeSyncBeacon(self, tsb:TSB) -> None:
		# TODO doc
		if tsb.bcnc == BeaconCriteria.PERIODIC:
			self.removePeriodicTimeSyncBeacon(tsb)
		else:	# Loss of sync
			self.removeLosTimeSyncBeacon(tsb)


	def removePeriodicTimeSyncBeacon(self, tsb:TSB) -> None:
		"""	Remove a periodic timeSyncBeacon resource. A running worker is stopped.
		
			Args:
				tsb: The timeSyncBeacon resource.
		"""
		if (ri := tsb.ri) in self.periodicTimeSyncBeacons:
			self.periodicTimeSyncBeacons[ri].stop()
			del self.periodicTimeSyncBeacons[tsb.ri]
	

	def removeLosTimeSyncBeacon(self, tsb:TSB) -> None:
		# TODO doc
		if not (bcnr := tsb.bcnr):
			L.isWarn and L.logWarn(f'bcnr missing in TSB: {tsb.ri}')
			return
		if bcnr in self.losTimeSyncBeacons:
			del self.losTimeSyncBeacons[bcnr]


	def isLossOfSynchronization(self, req:CSERequest) -> str:
		if (tup := self.losTimeSyncBeacons.get(req.headers.originator)) and (ot := req.headers.originatingTimestamp):
			tsd = abs(DateUtils.isodateDelta(ot))
			L.logWarn(tsd)
			if tsd is not None and tup[0] > tsd:
				return DateUtils.toDuration(tsd)
			return None

		#L.logWarn(req.headers.originatingTimestamp)
		if (tsd := DateUtils.isodateDelta(req.headers.originatingTimestamp)) is not None:
			#L.logWarn(DateUtils.toDuration(tsd))
			return str(abs(tsd))	# EXPERIMENTAL

		return None


	def getCSETimestamp(self) -> str:
		"""	Get the CSE's current date and time (UTC based).
		
			Return:
				ISO timestamp string
		"""
		return DateUtils.getResourceDate()

	