#
#	TimeSeriesManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Manager for TimeSeries handlings
#
from __future__ import annotations
from Logging import Logging


class TimeSeriesManager(object):

	def __init__(self) -> None:
		Logging.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		Logging.log('TimeSeriesManager shut down')
		return True


	
	def stopMonitoring(self, timeSeries:Resource):
		pass
		# TODO 