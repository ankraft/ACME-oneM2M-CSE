#
#	TimeManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing time related CSE functions
#
""" Managing time related CSE functions.
"""

from __future__ import annotations
from typing import cast, List, Tuple, Optional

from ..resources.TSB import TSB
from ..runtime import CSE
from ..etc.Types import BeaconCriteria, CSERequest, ResourceTypes
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.DateUtils import isodateDelta, toDuration, getResourceDate
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..runtime.Logging import Logging as L

# TODO add check to http request handling
# TODO add check to http response handling
# TODO add check to mqtt request handling
# TODO add check to mqtt response handling
# TODO add check to ws request handling
# TODO add check to ws response handling

class TimeManager(object):
	"""	Managing time related CSE functions.
	"""

	__slots__ = (
		'periodicTimeSyncBeacons',
		'losTimeSyncBeacons',
		'cseActiveSchedule'
	)
	""" Define slots for instance variables. """

	def __init__(self) -> None:
		"""	Initialize the TimeManager.
		"""

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		# Read all periofics and add them (again)
		for each in self._getAllPeriodicTimeSyncBeacons():
			self.addPeriodicTimeSyncBeacon(each)
		
		# Register to receive events
		CSE.event.addHandler(CSE.event.requestReceived, self.requestReveivedHandler)			# type: ignore
		CSE.event.addHandler(CSE.event.responseReceived, self.responseReveivedHandler)			# type: ignore
		
		self.periodicTimeSyncBeacons:dict[str, BackgroundWorker] = {}
		"""	Table for periodic timeSyncBeacons."""

		self.losTimeSyncBeacons:dict[str, Tuple[float, str]] = {}	# dict bcnr -> (threshold, tsb.ri)
		"""	Table for Loss-of-sync timeSyncBeacons."""

		self.cseActiveSchedule:list[str] = []
		""" List of active schedules when the CSE is active and will process requests. """

		L.isInfo and L.log('TimeManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeManager.
		
			Return:
				Boolean, always True.
		"""
		self._stopPeriodicBeacons()
		L.isInfo and L.log('TimeManager shut down')
		return True


	def restart(self, name:str) -> None:
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


	def requestReveivedHandler(self, name:str, req:CSERequest) -> None:
		"""	Handle a received request.
		
			Args:
				req: The received request
		"""
		# L.logErr(f'Received {req}')
		...

	def responseReveivedHandler(self, name:str, resp:CSERequest) -> None:
		"""	Handle a received response.
		
			Args:
				resp: The received response
		"""
		# L.logErr(f'Received {resp}')
		#L.logWarn(self.isLossOfSynchronization(resp))
		...

	

	# TODO  removeLoS
	# TODO isLossOfSynchronization


	def _getAllPeriodicTimeSyncBeacons(self) -> list[TSB]:
		"""	Get all periodic timeSyncBeacons from the storage.
		
			Return:
				List of periodic timeSyncBeacons
		"""
		return cast(List[TSB], CSE.storage.searchByFragment( { 'ty': ResourceTypes.TSB, 'bcnc': BeaconCriteria.PERIODIC} ))


	def addTimeSyncBeacon(self, tsb:TSB) -> None:
		"""	Add a timeSyncBeacon resource.
		
			Args:
				tsb: timeSyncBeacon resource
		"""
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
			notification = {
				'm2m:tsbn' : {	# TODO proposed short name. Check with TS-0004 later
					'tbr' : tsb.ri,
					'ctm' : self.getCSETimestamp()
				}
			}
			CSE.notification.sendNotificationWithDict(notification, tsb.bcnu, originator = RC.cseCsi)
			return True

		
		if (ri := tsb.ri) in self.periodicTimeSyncBeacons:
			self.removePeriodicTimeSyncBeacon(tsb)
		worker = BackgroundWorkerPool.newWorker(tsb.getInterval(), 
												periodicWorker, 
												f'tsbPeriodic_{ri}', 
												startWithDelay = True).start()
		self.periodicTimeSyncBeacons[ri] = worker


	def addLoSTimeSyncBeacon(self, tsb:TSB) -> None:
		"""	Add a Loss-of-sync timeSyncBeacon resource.
		
			Args:
				tsb: timeSyncBeacon resource
		"""
		# TODO doc
		if not (bcnr := tsb.bcnr):
			raise BAD_REQUEST(f'bcnr missing in TSB: {tsb.ri}')
		if bcnr in self.losTimeSyncBeacons: 
			raise BAD_REQUEST(f'TimeSyncBeacon already defined for requester: {bcnr}')	# TODO wait for discussion whether multiple bcnr are allowed
		self.losTimeSyncBeacons[bcnr] = (tsb.bcnt, tsb.ri)

	
	def updateTimeSyncBeacon(self, tsb:TSB, originalBcnc:BeaconCriteria) -> None:
		"""	Update a timeSyncBeacon resource.
		
			Args:
				tsb: The timeSyncBeacon resource
				originalBcnc: The original beacon criteria
		"""
		...
	

	def removeTimeSyncBeacon(self, tsb:TSB) -> None:
		"""	Remove a timeSyncBeacon resource.
		
			Args:
				tsb: The timeSyncBeacon resource
		"""
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
		"""	Remove a Loss-of-sync timeSyncBeacon resource.
		
			Args:
				tsb: The timeSyncBeacon resource.
		"""
		if not (bcnr := tsb.bcnr):
			L.isWarn and L.logWarn(f'bcnr missing in TSB: {tsb.ri}')
			return
		if bcnr in self.losTimeSyncBeacons:
			del self.losTimeSyncBeacons[bcnr]


	def isLossOfSynchronization(self, req:CSERequest) -> Optional[str]:
		"""	Check if a request is a loss-of-synchronization request.
		
			Args:
				req: The request.
			
			Return:
				The duration of the loss-of-synchronization or None.
		"""
		if (tup := self.losTimeSyncBeacons.get(req.originator)) and (ot := req.ot):
			tsd = abs(isodateDelta(ot))
			L.logWarn(tsd)
			if tsd is not None and tup[0] > tsd:
				return toDuration(tsd)
			return None

		#L.logWarn(req.originatingTimestamp)
		if (tsd := isodateDelta(req.ot)) is not None:
			#L.logWarn(toDuration(tsd))
			return str(abs(tsd))	# EXPERIMENTAL

		return None


	def getCSETimestamp(self) -> str:
		"""	Get the CSE's current date and time (UTC based).
		
			Return:
				ISO timestamp string
		"""
		return getResourceDate()

	