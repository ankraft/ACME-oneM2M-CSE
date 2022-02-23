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
from ..resources.Resource import Resource
from ..services import CSE
from ..etc.Types import BeaconCriteria
from ..etc.Types import ResourceTypes as T
from ..etc import DateUtils



class TimeManager(object):

	def __init__(self) -> None:

		# Read all periofics and add them (again)
		for each in self._getAllPeriodicTimeSyncBeacons():
			self.addPeriodicTimeSyncBeacon(each)
		L.isInfo and L.log('TimeManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeManager.
		
			Return:
				Boolean, always True.
		"""
		L.isInfo and L.log('TimeManager shut down')
		return True
	
	# TODO restart: stop all timers


	# TODO addPeriodic
	# TODO isLossOfSynchronization


	def _getAllPeriodicTimeSyncBeacons(self) -> list[TSB]:
		return cast(List[TSB], CSE.storage.searchByFragment( { 'ty': T.TSB, 'bcnc': BeaconCriteria.PERIODIC} ))

	
	def addPeriodicTimeSyncBeacon(self, tsb:TSB) -> None:
		# TODO start monitor
		pass


	def getCSETimestamp(self) -> str:
		"""	Get the CSE's current date and time (UTC based).
		
			Return:
				ISO time stamp string
		"""
		return DateUtils.getResourceDate()