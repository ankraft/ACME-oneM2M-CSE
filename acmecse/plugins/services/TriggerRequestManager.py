#
#	TriggerRequestManager.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Manager for TriggerRequest functionality
#
"""	TriggerRequestManager is responsible for managing the TriggerRequest functionality in the CSE.

	Note:
		This is a placeholder implementation that will be extended in the future to provide 
		the actual functionality for managing TriggerRequests.
	"""

from typing import Optional

from acmecse.runtime.PluginSupport import plugin, restart, start, stop, pluginManager
from acmecse.runtime.Logging import Logging as L
from acmecse.etc.Types import TriggerStatus
from acmecse.etc.Constants import Constants as C
from acmecse.helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from acmecse.etc.DateUtils import utcTime

from acmecse.resources.TGR import TGR

# TODO: add magic strings to constants

@plugin(property='triggerRequestManager', tags=['acme', 'core'])
class TriggerRequestManager:
	""" Manager for TriggerRequest functionality. 
	
		Note:
			This is a placeholder implementation that will be extended in the future to provide 
			the actual functionality for managing TriggerRequests.
	"""

	triggerRequestActors: dict[str, tuple[BackgroundWorker, TGR]] = {}

	@start
	def start(self) -> None:
		""" Start the TriggerRequestManager.
		"""
		L.isInfo and L.log('TriggerRequestManager started')
		for service in pluginManager.services('triggerRequestHandler'):
			L.isDebug and L.logDebug(f'Found TriggerRequestHandler service: {service.pluginName}, tags: {service.tags}, metadata: {service.metadata}, priority: {service.priority}')


	@stop
	def stop(self) -> None:
		""" Stop the TriggerRequestManager.
		"""
		# stop any background workers that are still running
		self._terminateAllTriggerRequests()
		L.isInfo and L.log('TriggerRequestManager stopped')


	@restart
	def restart(self) -> None:
		""" Restart the TriggerRequestManager.
		"""
		self._terminateAllTriggerRequests()
		L.isInfo and L.log('TriggerRequestManager restarted')


	##############################################################################
	

	def determineNSE(self, tgr: TGR) -> Optional[str]:
		""" Determine the NSE (Network Service Entity) for a given TriggerRequest. 
		
			This method iterates through the registered triggerRequestHandler services 
			that have the *triggerRequestHandler* tag and calls their ``acceptsM2MExtID```
			endpoint to determine if they can handle the provided TriggerRequest's M2M-Ext-ID.

			Args:
				tgr: The TriggerRequest resource for which to determine the NSE.

			Returns:
				The first NSE service handler plugin's name if found, otherwise None.

		"""
		for service in pluginManager.services('triggerRequestHandler'):
			try:
				if pluginManager.callEndpoint(service.pluginName, 'acceptsM2MExtID', tgr.mei):
					L.isDebug and L.logDebug(f'TriggerRequest {tgr.ri} accepted by NSE handler: {service.pluginName}')
					return service.pluginName
			except Exception as e:
				L.isWarn and L.logWarn(f'Error while calling service endpoint "acceptsM2MExtID" on NSE handler {service.pluginName}: {e}')
				continue
		L.isDebug and L.logDebug(f'No NSE handler found for TriggerRequest {tgr.ri} with M2M-Ext-ID: {tgr.mei}')
		return None


	def hasNSE(self, nse: str) -> bool:
		""" Check if a given NSE is available. 
		
			Args:
				nse: The name of the NSE service handler plugin to check.

			Returns:
				True if the NSE is available, False otherwise.
		"""
		pi = pluginManager.getPluginByName(nse)
		if pi and 'triggerRequestHandler' in pi.tags:
			return True

		L.isDebug and L.logDebug(f'NSE handler {nse} not found or does not have the required tag "triggerRequestHandler"')
		return False


	def handleTriggerRequestSending(self, tgr: TGR, nse: str) -> None:
		""" Handle the sending of a TriggerRequest to the determined NSE.
		
			This method is responsible for initiating the process of sending the TriggerRequest to the 
			determined NSE. The actual sending process may be asynchronous and handled in the background.

			Args:
				tgr: The TriggerRequest resource to be sent.
				nse: The name of the NSE service handler plugin to which the TriggerRequest should be sent.
		"""		

		# Create and start an actor for the TriggerRequest to handle the sending and checking process in the background.
		# Add the actor to the triggerRequestActors dictionary for tracking.
		# After the actor has completed its work, it should call the _triggerHandlerCompleted method to clean up.
		actor = BackgroundWorkerPool.newActor(self._triggerHandler, 
											  name=f'tgr_{tgr.ri}', 
											  finished=self._triggerHandlerCompleted)
		self.triggerRequestActors[tgr.ri] = (actor, tgr) # Store the actor and the TriggerRequest in the dictionary for later reference
		actor.start(tgr=tgr, nse=nse, actor=actor)
		L.isDebug and L.logDebug(f'Started background actor for TriggerRequest: {tgr.ri} to NSE: {nse}')


	def _triggerHandler(self, tgr: TGR, nse: str, actor: BackgroundWorker) -> None:
		""" Internal method to handle the actual sending of the TriggerRequest to the NSE.
		
			This method is executed in a background worker and is responsible for the actual communication
			with the NSE. It should handle any necessary retries, error handling, and updating of the 
			TriggerRequest's status based on the response from the NSE.

			Args:
				tgr: The TriggerRequest resource to be sent.
				nse: The name of the NSE service handler plugin to which the TriggerRequest should be sent.
				actor: The background worker actor handling this trigger request.
		"""

		if tgr.tst != TriggerStatus.PROCESSING:
			L.isWarn and L.logWarn(f'TriggerRequest {tgr.ri} is not in PROCESSING state, current state: {tgr.tst}. Aborting trigger handling.')
			return

		# Determine the real validity time for the trigger request
		_endTime = utcTime() + tgr.attribute(C.attrTriggerRequestValidityTime)	

		# Have a short delay to let the CSE finish processing the request and sending the response to the originator.
		try:
			actor.sleep(1)	# TODO make this configurable
		except InterruptedError:
			L.isWarn and L.logWarn(f'TriggerRequest {tgr.ri} actor interrupted during initial sleep. Aborting trigger handling.')
			return

		# Send the TriggerRequest to the assigned NSE service handler plugin by calling its *sendTriggerRequest* endpoint
		if _endTime > utcTime():
			try:
				pluginManager.callEndpoint(nse, 'sendTriggerRequest', tgr)
				L.isDebug and L.logDebug(f'TriggerRequest {tgr.ri} sent to NSE {nse}')
			except Exception as e:
				L.isWarn and L.logWarn(f'Failed to send TriggerRequest {tgr.ri} to NSE {nse}: {e}')
				tgr.setTriggerStatus(TriggerStatus.TRIGGER_FAILED)
				return

		# Wait for the trigger request to be processed by the NSE, checking its status periodically until it is no longer in PROCESSING state or until the validity time expires.
		while actor.running and tgr.tst == TriggerStatus.PROCESSING and _endTime > utcTime():

			# Short sleep to avoid busy waiting, but also check the status of the TriggerRequest periodically.
			try:
				actor.sleep(1)	# TODO make this configurable
			except InterruptedError:
				L.isWarn and L.logWarn(f'TriggerRequest {tgr.ri} actor interrupted during sleep. Aborting trigger handling.')
				return

			# Call the *checkTriggerRequestStatus* endpoint of the assigned NSE service handler plugin to check the status of the TriggerRequest
			try:
				status = pluginManager.callEndpoint(nse, 'checkTriggerRequestStatus', tgr)
				if status != tgr.tst:
					L.isDebug and L.logDebug(f'TriggerRequest {tgr.ri} status updated from {TriggerStatus(tgr.tst)} to {status}')
					tgr.setTriggerStatus(status)	# Also update the status in the database
			except Exception as e:
				L.isWarn and L.logWarn(f'Failed to call checkTriggerRequestStatus on NSE handler {nse}: {e}')

		# Check if the trigger request has expired
		if actor.running and tgr.tst == TriggerStatus.PROCESSING and _endTime <= utcTime():
			L.isWarn and L.logWarn(f'TriggerRequest {tgr.ri} has expired without receiving a response from NSE {nse}. Setting status to TRIGGER_EXPIRED.')
			tgr.setTriggerStatus(TriggerStatus.TRIGGER_EXPIRED)	# Also update the status in the database


	def _triggerHandlerCompleted(self, tgr: TGR, nse: str, actor: BackgroundWorker) -> None:
		""" Internal method called when the trigger handler actor has completed its execution.
		
			This method is responsible for cleaning up after the trigger handling process, including 
			removing the actor from the triggerRequestActors dictionary and performing any necessary 
			finalization steps.

			Args:
				tgr: The TriggerRequest resource that was being processed.
				nse: The name of the NSE service handler plugin to which the TriggerRequest was sent.
				actor: The background worker actor that handled this trigger request.
		"""
		if tgr.ri in self.triggerRequestActors:
			del self.triggerRequestActors[tgr.ri]
			L.isDebug and L.logDebug(f'Background actor for TriggerRequest {tgr.ri} has completed and been removed from tracking.')


	def terminateTriggerRequest(self, tgr: TGR) -> None:
		""" Terminate (or recall) a TriggerRequest that is currently being processed.
		
			This method is responsible for stopping any background processing related to the provided 
			TriggerRequest. It should be called when a TriggerRequest is deleted or no longer needs to be processed.

			This method also removes the TriggerRequest's actor from the triggerRequestActors dictionary and calls the
			*terminateTriggerRequest* endpoint of the assigned NSE service handler plugin to notify it of the termination.

			Args:
				tgr: The TriggerRequest resource to be terminated.
		"""
		if (actorTgr := self.triggerRequestActors.get(tgr.ri)):
			actor, tgr = actorTgr
			L.isDebug and L.logDebug(f'Unscheduling TriggerRequest: {tgr.ri}')
			actor.stop()

			# Call the *terminateTriggerRequest* endpoint of the assigned NSE service handler plugin to notify it of the termination
			try:
				pluginManager.callEndpoint(tgr.attribute(C.attrTriggerRequestAssignedNSE), 'terminateTriggerRequest', tgr)
				tgr.setTriggerStatus(TriggerStatus.TRIGGER_TERMINATED)
			except Exception as e:
				L.isWarn and L.logWarn(f'Failed to call terminateTriggerRequest on NSE handler {tgr.attribute(C.attrTriggerRequestAssignedNSE)}: {e}')

			# Remove the actor from the dictionary to clean up
			del self.triggerRequestActors[tgr.ri]	


	def _terminateAllTriggerRequests(self) -> None:
		""" Terminate all currently active TriggerRequests. 
			This method is called when the TriggerRequestManager is stopped or restarted.
		"""
		L.isDebug and L.logDebug('Terminating all active TriggerRequests')
		for actorName, actorTgr in self.triggerRequestActors.items():
			actor, tgr = actorTgr
			L.isDebug and L.logDebug(f'Terminating TriggerRequest: {tgr.ri}')
			self.terminateTriggerRequest(tgr)
		self.triggerRequestActors.clear()
