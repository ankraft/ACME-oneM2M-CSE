#
#	TGR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: TriggerRequest
#

"""	TriggerRequest (TGR) resource type.

	A <triggerRequest> resource lets an IN-CSE ask a Network Service Entity (NSE) plugin
	(e.g. SMS) to trigger a target &lt;AE> or &lt;remoteCSE> that is currently unreachable, so
	that it re-establishes a connection to the CSE. Depending on its *triggerPurpose*
	attribute, the request either just wakes up the target (*establishConnection*) or asks
	it to perform a CRUD operation once it reconnects (*executeCRUD*).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING


from ..etc.Types import CSEType, JSON, TriggerStatus, TriggerPurpose, CSERequest, ResourceTypes
from ..etc.ResponseStatusCodes import BAD_REQUEST, NOT_IMPLEMENTED, TRIGGERING_DISABLED_FOR_RECIPIENT, UNABLE_TO_REPLACE_REQUEST
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.DateUtils import fromDuration, toDuration
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources.Resource import addToInternalAttributes
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..resources.Resource import Resource
	from ..plugins.services.TriggerRequestManager import TriggerRequestManager
	from ..services.Dispatcher import Dispatcher
	from ..runtime.Storage import Storage

# Add to internal attributes 
addToInternalAttributes((Constants.attrTriggerRequestValidityTime, 
						 Constants.attrTriggerRequestAssignedNSE))


@requires(triggerRequestManager='acmecse.plugins.services.TriggerRequestManager', required=False)
@requires(dispatcher='acmecse.services.Dispatcher')
@requires(storage='acmecse.runtime.Storage')
class TGR(AnnounceableResource):
	"""	TriggerRequest (TGR) resource type.

		A <triggerRequest> resource lets an IN-CSE ask a Network Service Entity (NSE) plugin
		(e.g. SMS) to trigger a target &lt;AE> or &lt;remoteCSE> that is currently unreachable, so
		that it re-establishes a connection to the CSE. Depending on its *triggerPurpose*
		attribute, the request either just wakes up the target (*establishConnection*) or asks
		it to perform a CRUD operation once it reconnects (*executeCRUD*).
	"""

	triggerRequestManager: Optional[TriggerRequestManager] = None
	""" Injected TriggerRequestManager plugin instance. """

	storage: Storage = None
	""" Injected Storage instance. """

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	def activate(self, parentResource: Resource, originator: str, request: Optional[CSERequest] = None) -> None:
		super().activate(parentResource, originator, request)

		# Check whether the TriggerRequestManager plugin is available
		if not self.triggerRequestManager:
			raise NOT_IMPLEMENTED(L.logWarn('TriggerRequestManager plugin not enabled'))

		# Check whether the CSE is an IN-CSE, otherwise return an error
		if not RC.cseType == CSEType.IN:
			raise BAD_REQUEST(L.logWarn('TriggerRequests can only be created on an IN-CSE'))
		
		# Get TriggerPurpose 
		_tpe = self.tpe if self.tpe else TriggerPurpose.establishConnection	# default: establishConnection
		
		# Determine the NSE to forward the trigger request to. If found, then set the tst attribute to PROCESSING.
		# Otherwise, set the tst attribute to ERROR_NSE_NOT_FOUND and return normally.
		if (nse := self.triggerRequestManager.determineNSE(self)) is None:
			self.setTriggerStatus(TriggerStatus.ERROR_NSE_NOT_FOUND, False)
			return
		self.setTriggerStatus(TriggerStatus.PROCESSING, False)
		self.setAttribute(Constants.attrTriggerRequestAssignedNSE, nse)
		L.isDebug and L.logDebug(f'Determined NSE plugin for TriggerRequest: {nse}')

		# Initiate the more complex triggering process by calling the TriggerRequestManager.
		# This will handle the rest of the activation process in the background, because it may take 
		# some time to complete, depending on the underlying network and the NSE.
		self.triggerRequestManager.sendTriggerRequest(self, nse)


	def update(self, dct: JSON = None,
					 originator: Optional[str] = None, 
					 doValidateAttributes: Optional[bool] = True,
					 request: Optional[CSERequest] = None) -> None:
		super().update(dct, originator, doValidateAttributes, request)


		# Check whether the triggerStatus is in PROCESSING state. If so, then reject the update request with UNABLE_TO_REPLACE_REQUEST.
		if self.tst != TriggerStatus.PROCESSING:
			raise UNABLE_TO_REPLACE_REQUEST(L.logWarn('Cannot update/replace a TriggerRequest resource while it is not in PROCESSING state.'))

		# Check whether the NSE is still available
		_nse = self.attribute(Constants.attrTriggerRequestAssignedNSE)
		if not _nse or not self.triggerRequestManager.hasNSE(_nse):
			self.setTriggerStatus(TriggerStatus.ERROR_NSE_NOT_FOUND, False)
			return

		# Execute the trigger request to the same NSE as determined in the CREATE request
		if not self.triggerRequestManager.replaceTrigger(self):
			raise UNABLE_TO_REPLACE_REQUEST(L.logWarn('Cannot update/replace a TriggerRequest resource while it is being processed by the NSE.'))


		# >>> The following code contains the reverse logic of the above: Only if the triggerStatus is
		# >>>> not in PROCESSING state, then the update request is accepted. Otherwise, it is rejected.
		#
		#
		#
		# # Check whether the triggerStatus is in PROCESSING state. If so, then reject the update request with UNABLE_TO_REPLACE_REQUEST.
		# if self.tst == TriggerStatus.PROCESSING:
		# 	raise UNABLE_TO_REPLACE_REQUEST(L.logWarn('Cannot update a TriggerRequest resource while it is in PROCESSING state.'))

		# # Check whether the NSE is still available
		# _nse = self.attribute(Constants.attrTriggerRequestAssignedNSE)
		# if not _nse or not self.triggerRequestManager.hasNSE(_nse):
		# 	self.setTriggerStatus(TriggerStatus.ERROR_NSE_NOT_FOUND, False)
		# 	return

		# # Execute the trigger request to the same NSE as determined in the CREATE request
		# self.setTriggerStatus(TriggerStatus.PROCESSING, False)
		# self.triggerRequestManager.sendTriggerRequest(self, _nse)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:

		super().validate(originator, dct, parentResource)

		# Check triggerValidityTime duration and set an internal attribute for it in seconds.
		_tvt:float = fromDuration(self.tvt)
		if _tvt <= 0 or _tvt > Configuration.resource_tgr_maxTriggerValidityTime:
			L.isDebug and L.logDebug(f'Invalid triggerValidityTime: {_tvt} seconds. Correcting to maximum allowed value: {Configuration.resource_tgr_maxTriggerValidityTime} seconds.')
			_tvt = Configuration.resource_tgr_maxTriggerValidityTime
			self.setAttribute('tvt', toDuration(_tvt))	# Fix the excessive tvt value in the resource itself, so that it is visible to the client.
		self.setAttribute(Constants.attrTriggerRequestValidityTime, _tvt)

		# Check whether the target is an AE or a remoteCSE, and the triggerEnable attribute is set to true
		# Otherwise, reject the request with TRIGGERING_DISABLED_FOR_RECIPIENT
		if (tri := self.tri):
			# Search for AE or remoteCSE resources with the given triggerRecipientID (tri) in the CSE's database. 
			resources = self.storage.searchByFragment({ 'tri': tri, 'mei': self.mei },
											 		  lambda r: r.get('ty') in (ResourceTypes.AE, ResourceTypes.CSR))

			# Check whether there is only one target resource and it is an AE or a remoteCSE, 
			# otherwise reject the request with BAD REQUEST
			match len(resources):
				case 0:
					raise BAD_REQUEST(L.logWarn(f'Target resource for TriggerRequest not found: {tri}'))
				case 1:
					targetResource = resources[0]
					if (tren := targetResource.tren) is not None and tren == False:
						raise TRIGGERING_DISABLED_FOR_RECIPIENT(L.logWarn(f'Triggering is disabled for the target resource: {tri}'))
				case _:
					raise BAD_REQUEST(L.logWarn(f'Multiple resources found for TriggerRequest tri: {tri}'))
			
		# Check presence of various attributes if the triggerPurpose is "crud"		
		if self.tpe == TriggerPurpose.executeCRUD:
			for attr in ('tiae', 'tia', 'tio', 'tirt'):
				if not getattr(self, attr):
					raise BAD_REQUEST(L.logWarn(f'Missing mandatory attribute for TriggerRequest with triggerPurpose "executeCRUD": {attr}'))


	def deactivate(self, originator: str, parentResource: Resource) -> None:
		# Unschedule the action
		self.triggerRequestManager.terminateTriggerRequest(self)
		return super().deactivate(originator, parentResource)


	def setTriggerStatus(self, status: TriggerStatus, doUpdate: bool = True) -> None:
		""" Set the triggerStatus attribute of the TriggerRequest resource. It might also
			update the resource in the database.

			Args:
				status: The new triggerStatus value to set.
				doUpdate: Whether to update the resource in the database after setting the attribute. Default is True.
		"""
		self.setAttribute('tst', status)
		if doUpdate:
			self.dbUpdate()
