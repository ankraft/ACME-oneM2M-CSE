#
#	RequestPreProcessingInterceptor.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Interceptor for incoming requests. Requests are intercepted before they are processed by the CSE. 
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from acmecse.runtime.PluginSupport import *
from acmecse.runtime.Logging import Logging as L
from acmecse.etc.DateUtils import timeUntilAbsRelTimestamp, waitFor, timeUntilTimestamp, cronMatchesTimestamp
from acmecse.etc.ResponseStatusCodes import REQUEST_TIMEOUT, TARGET_NOT_REACHABLE, BAD_REQUEST

if TYPE_CHECKING:
	from acmecse.plugins.services.TimeManager import TimeManager


@requires(timeManager='acmecse.plugins.services.TimeManager', required=False)
@plugin(tags=['acme', 'interceptor'])
class RequestInterceptor(Interceptor):
	"""	Interceptor for incoming requests. Requests are intercepted before they are processed by the CSE.

		This interceptor checks for delayed execution, active CSE schedule, request expiration and 
		result expiration before the request is processed by the CSE. 
		If any of these checks fail, an appropriate error response is raised and the request processing is aborted.
	"""

	timeManager: Optional[TimeManager] = None		# type: ignore
	""" Injected TimeManager instance. """

	@intercept(Phase.REQUEST_PRE_PROCESSING, Operation.ALL, ResourceTypes.ALL, priority=10)
	def preRequestInterceptor(self, request:CSERequest) -> None:
		"""	Pre-processing interceptor for incoming requests. 
		
			This interceptor will be called before the request is processed by the CSE.

			Args:
				request: The incoming CSERequest object that is being processed.
		"""
		L.isDebug and L.logDebug('Interception: Request pre-processing')

		self._checkDelayedExecution(request)
		self._checkActiveCSESchedule()
		self._checkRequestExpiration(request)
		self._checkResultExpiration(request)



	def _checkDelayedExecution(self, request:CSERequest) -> None:
		""" Check for delayed execution of the request and wait if necessary. 
		
			Args:
				request: The incoming CSERequest object that is being processed.

			Raises:
				REQUEST_TIMEOUT: If the request execution time has already passed.
		"""
		if request.oet:
			# Calculate the delay
			delay = timeUntilAbsRelTimestamp(request.oet)
			L.isDebug and L.logDebug(f'Waiting: {delay:.4f} seconds for delayed execution')
			# Just wait some time
			waitFor(delay)


	def _checkActiveCSESchedule(self) -> None:
		""" Check if the CSE is currently active according to its schedule. 
		
			Raises:
				TARGET_NOT_REACHABLE: If the CSE is currently inactive according to its schedule.
		"""
		if not self.timeManager:
			L.isDebug and L.logDebug('TimeManager plugin is disabled, cannot check CSE schedule. Defaulting to active.')
			return
		if self.timeManager.cseActiveSchedule:
			# Only check if the CSE has at least one schedule
			# Otherwise the CSE is always active
			for s in self.timeManager.cseActiveSchedule:
				if cronMatchesTimestamp(s):
					return
			# TODO not sure if this is the right error code
			raise TARGET_NOT_REACHABLE(L.logDebug('request exection time outside of CSE\'s allowed schedule'))


	def _checkRequestExpiration(self, request:CSERequest) -> None:
		""" Check if the request has already expired. 
		
			Args:
				request: The incoming CSERequest object that is being processed.

			Raises:
				REQUEST_TIMEOUT: If the request has already expired.
		"""
		if request._rqetUTCts is not None and timeUntilTimestamp(request._rqetUTCts) <= 0.0:
			raise REQUEST_TIMEOUT(L.logDebug('request timed out reached'))


	def _checkResultExpiration(self, request:CSERequest) -> None:
		""" Check if the result expiration time has already passed. 
		
			Args:
				request: The incoming CSERequest object that is being processed.

			Raises:
				REQUEST_TIMEOUT: If the result expiration time has already passed.
		"""
		if not request.rset:
			return
		if timeUntilTimestamp(request._rsetUTCts) <= 0.0:
			raise REQUEST_TIMEOUT(L.logDebug('result timed out reached'))
		if request.rqet is not None and request._rsetUTCts < request._rqetUTCts:
			raise BAD_REQUEST(L.logDebug('result expiration timestamp must be greater than request expiration timestamp'), data = request)
