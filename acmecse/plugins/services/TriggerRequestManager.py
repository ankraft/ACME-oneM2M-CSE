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

from typing import Optional, TYPE_CHECKING

from acmecse.runtime.PluginSupport import plugin, init, start, stop, configure, validate, pluginManager
from acmecse.runtime.Logging import Logging as L
from acmecse.runtime.Configuration import Configuration, ConfigurationError
from acmecse.etc.Types import TriggerStatus
from acmecse.helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from acmecse.etc.DateUtils import waitFor

from acmecse.resources.TGR import TGR

# TODO: add magic strings as constants
@plugin(property='triggerRequestManager', tags=['acme', 'core'])
class TriggerRequestManager:
	""" Manager for TriggerRequest functionality. 
	
		Note:
			This is a placeholder implementation that will be extended in the future to provide 
			the actual functionality for managing TriggerRequests.
	"""

	triggerRequestActors: dict[str, BackgroundWorker] = {}

	@init
	def init(self) -> None:
		""" Initialize the TriggerRequestManager. 
		"""
		L.isInfo and L.log('TriggerRequestManager initialized')
		

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
		L.isDebug and L.logDebug('Stopping TriggerRequestManager')
		# TODO stop any background workers that are still running
		for actorName, actor in self.triggerRequestActors.items():
			L.isDebug and L.logDebug(f'Stopping TriggerRequest actor: {actorName}')
			actor.stop()

		L.isInfo and L.log('TriggerRequestManager stopped')


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
			for endpoint in pluginManager.endpoints(service.pluginName):
				if endpoint.endpointName == 'acceptsM2MExtID' and \
				   pluginManager.callEndpoint(endpoint.pluginName, 'acceptsM2MExtID', tgr.mei):
					return service.pluginName
		return None


	def handleTriggerRequestSending(self, tgr: TGR, nse: str) -> None:
		""" Handle the sending of a TriggerRequest to the determined NSE.
		
			This method is responsible for initiating the process of sending the TriggerRequest to the 
			determined NSE. The actual sending process may be asynchronous and handled in the background.

			Args:
				tgr: The TriggerRequest resource to be sent.
				nse: The name of the NSE service handler plugin to which the TriggerRequest should be sent.
		"""		

		# Create and start an actor for the TriggerRequest to handle the sending process in the background.
		# Add the actor to the triggerRequestActors dictionary for tracking.
		actor = BackgroundWorkerPool.newActor(self._triggerHandler, name=f'tgr_{tgr.ri}')
		self.triggerRequestActors[tgr.ri] = actor
		actor.start(tgr=tgr, nse=nse, actor=actor)


	def unscheduleTriggerRequest(self, tgr: TGR) -> None:
		""" Unschedule a TriggerRequest that is currently being processed.
		
			This method is responsible for stopping any background processing related to the provided 
			TriggerRequest. It should be called when a TriggerRequest is deleted or no longer needs to be processed.

			Args:
				tgr: The TriggerRequest resource to be unscheduled.
		"""
		if (actor := self.triggerRequestActors.get(tgr.ri)):
			L.isDebug and L.logDebug(f'Unscheduling TriggerRequest: {tgr.ri}')
			actor.stop()
			del self.triggerRequestActors[tgr.ri]

			# TODO call the NSE to terminate the trigger request if possible, depending on the underlying network and NSE capabilities


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
		# Have a short delay to let the CSE finish processing the request and sending the response to the originator.
		actor.sleep(2)	# TODO make this configurable
		L.consoleBanner(f'Handling TriggerRequest sending for resource: {tgr.ri} to NSE: {nse}')


		# TODO have a couple of support functions, e.g. to set the correct triggerStatus and update the TGR resource in the database

		# TODO test trigger validity at the right places
			

		# To continue processing the request, the Receiver shall submit a trigger request to the
		#  NSE via the Mcn triggering procedure as defined in clause 9. The message shall contain information needed
		#  by the NSE to generate a trigger request for the corresponding underlying network.
		#  For a 3GPP trigger request, the required information within the trigger request message is captured in 
		# clause 7.5.1 of oneM2M TS-0026 [43].

		# Upon receipt of trigger response(s) from the NSE, the Receiver shall set the triggerStatus attribute of 
		# the <triggerRequest> resource:
		# 
		# If the Receiver receives a confirmation from the NSE that the trigger was accepted, 
		# the Receiver shall set the triggerStatus attribute to TRIGGER_TRIGGERED.
		#
		# If the Receiver receives an indication that the trigger request was successfully delivered,
		# the Receiver shall set the triggerStatus attribute to TRIGGER_DELIVERED.
		#
		# If the Receiver receives an indication that the trigger request was not accepted or the delivery was
		#  not successful, the Receiver shall set the triggerStatus attribute to TRIGGER_FAILED.
		#
		# If the Receiver receives an indication that the trigger request expired before completion,
		#  the Receiver shall set the triggerStatus attribute to TRIGGER_EXPIRED.
		#
		# If the Receiver receives an indication that the trigger request is terminated before completion, 
		# the Receiver shall set the triggerStatus attribute to TRIGGER_TERMINATED.
		#
		# If the Receiver receives an indication that the delivery of the trigger request is not confirmed, 
		# the Receiver shall set the triggerStatus attribute to TRIGGER_UNCONFIRMED.
