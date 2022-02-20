#
#	TimeManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing time related CSE functions
#


from __future__ import annotations
from ..services.Logging import Logging as L

class TimeManager(object):

	def __init__(self) -> None:
		# TODO configurable
		self.defaultBeaconInterval = 60 # s
		self.defaultBeaconThreshold = 60 # s

		L.isInfo and L.log('TimeManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeManager.
		
			Return:
				Boolean, always True.
		"""
		L.isInfo and L.log('TimeManager shut down')
		return True
	