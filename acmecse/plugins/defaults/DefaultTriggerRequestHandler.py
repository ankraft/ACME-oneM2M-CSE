#
#	DefaultTriggerRequestHandler.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Default handler for TriggerRequest functionality. 
"""

from __future__ import annotations

from acmecse.runtime.PluginSupport import Service, plugin, endpoint
from acmecse.runtime.Logging import Logging as L
from acmecse.etc.Constants import Constants as C
from acmecse.resources.TGR import TGR
from acmecse.etc.Types import TriggerStatus
from acmecse.etc.ResponseStatusCodes import BAD_REQUEST, INTERNAL_SERVER_ERROR

@plugin(tags=['acme', 'core', 'triggerRequestHandler', 'default'], priority=100)
class DefaultTriggerRequestHandler(Service):
	"""	Default handler for TriggerRequest functionality.

		This is a default handler for TriggerRequest functionality.
		It has the lowest priority and will be used if no other handler is available.

		This handler returns as a trigger result the TriggerStatus according to the first part of the *M2M-EXT-ID* 
		of the TriggerRequest resource, which is expected to be one of the following values:

		- *TRIGGER_DELIVERED* : The TriggerRequest was successfully processed and the trigger was executed.
		- *TRIGGER_FAILED* : The TriggerRequest was processed but the trigger could not be executed because of an error.
		- *TRIGGER_REPLACED* : The TriggerRequest was processed but the trigger could not be executed because it was replaced
		- *TRIGGER_UNCONFIRMED* : The TriggerRequest was processed but the trigger could not be executed because it was unconfirmed.

		If the value is *TRIGGER_EXPIRED* then status will not be changed and the TriggerRequest is expected to be terminated by the
		TriggerRequestManager plugin after the validity time has expired. The TriggerStatus will then be set to *TRIGGER_EXPIRED*.

		Any other value will be defaulted to *TRIGGER_FAILED*.

		Examples:
			- *TRIGGER_DELIVERED*@example.com -> The TriggerRequest was successfully processed and the trigger was executed.
			- *TRIGGER_FAILED*@example.com -> The TriggerRequest was processed but the trigger could not be executed because of an error.
			- *TRIGGER_REPLACED*@example.com -> The TriggerRequest was processed but the trigger could not be executed because it was replaced.
			- *TRIGGER_UNCONFIRMED*@example.com -> The TriggerRequest was processed but the trigger could not be executed because it was unconfirmed.
			- *TRIGGER_EXPIRED*@example.com -> The TriggerRequest was processed but the trigger could not be executed because it expired.
	"""

	_expectedTriggerResult: dict[str, TriggerStatus] = {}
	""" Internal dictionary to keep track of the expected trigger results for each TriggerRequest resource. 
		The key is the resource ID of the TriggerRequest resource, and the value is the expected trigger status. """


	@endpoint('acceptsM2MExtID')
	def acceptsM2MExtID(self, m2mExtID: str) -> bool:
		"""	Check whether the given m2mExtID is valid for this NSE handler, 
			that this handler can be used for triggering.

			Note:
				This is a default implementation that returns True for M2M-EXT-IDs that
				matches the domain "...@example.com" as part of the M2M-EXT-ID and False otherwise.

			Args:
				m2mExtID: The m2mExtID to check.

			Returns:
				True if the m2mExtID is valid for this handler, False otherwise.
		"""
		return m2mExtID.endswith(f'@{C.exampleDomain}')


	@endpoint('sendTriggerRequest')
	def sendTriggerRequest(self, tgr: TGR, replace: bool = False) -> None:
		""" Send a TriggerRequest to the assigned NSE handler.

			Note:
				This is a default implementation that only internally sends the TriggerRequest.

			Args:
				tgr: The TriggerRequest resource to be sent.
				replace: A boolean indicating whether this is a replacement of an existing TriggerRequest. 
					If True, the NSE handler may handle the request differently.

			Raises:
				INTERNAL_SERVER_ERROR: If the TriggerRequest resource is not valid for sending.
		"""
		L.isDebug and L.logDebug(f'Simulated sending of TriggerRequest {tgr.ri} to NSE {tgr.attribute(C.attrTriggerRequestAssignedNSE)}')

		# Add the expected trigger status result to the internal dictionary for later checking
		try:
			_status = TriggerStatus.to(tgr.mei.split('@')[0])
		except ValueError as e:
			L.isDebug and L.logDebug(f'Invalid M2M-EXT-ID for the default TriggerRequest handler: {tgr.mei}. Defaulting to TRIGGER_FAILED. ({e})')
			_status = TriggerStatus.TRIGGER_FAILED

		match _status:
			case	TriggerStatus.TRIGGER_DELIVERED | \
					TriggerStatus.TRIGGER_FAILED | \
					TriggerStatus.TRIGGER_REPLACED | \
					TriggerStatus.TRIGGER_UNCONFIRMED:
				pass

			case TriggerStatus.TRIGGER_EXPIRED:
				# Do not set any expected trigger result for TRIGGER_EXPIRED, because the TriggerRequestManager 
				# will handle this case after the validity time has expired.
				_status = TriggerStatus.PROCESSING

			case _:
				raise INTERNAL_SERVER_ERROR(L.logWarn(f'Invalid TriggerStatus in M2M-EXT-ID for the default TriggerRequest handler: {tgr.mei}'))

		L.isDebug and L.logDebug(f'Setting expected trigger result for TriggerRequest {tgr.ri} to {_status}')
		self._expectedTriggerResult[tgr.ri] = _status


	@endpoint('checkTriggerRequestStatus')
	def checkTriggerRequestStatus(self, tgr: TGR) -> TriggerStatus:
		""" Check the status of a TriggerRequest that is currently being processed.

			Note:
				This is a default implementation that only checks the internal status of the TriggerRequest.

			Args:
				tgr: The TriggerRequest resource to be checked.

			Returns:
				The current trigger status of the TriggerRequest.

			Raises:
				INTERNAL_SERVER_ERROR: In case an unknown TriggerRequest is provided.
		"""
		if tgr.ri in self._expectedTriggerResult:
			return self._expectedTriggerResult[tgr.ri]
		raise INTERNAL_SERVER_ERROR(L.logWarn(f'TriggerRequest {tgr.ri} not found in expected trigger results.'))
	

	@endpoint('terminateTriggerRequest')
	def terminateTriggerRequest(self, tgr: TGR, replace: bool = False) -> None:
		""" Terminate a TriggerRequest that is currently being processed.

			Note:
				This is a default implementation that only internally terminates the TriggerRequest.

			Args:
				tgr: The TriggerRequest resource to be terminated.
				replace: A boolean indicating whether this termination is part of a replacement process. 
					If True, the NSE handler may handle the termination differently.
		"""
		# Remove trigger from the internal list of currently processed TriggerRequests
		if tgr.ri in self._expectedTriggerResult:
			del self._expectedTriggerResult[tgr.ri]
		return

