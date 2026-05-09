#
#	SCH.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Schedule
#

""" Schedule (SCH) resource type. """

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from ..etc.Constants import Constants as C
from ..etc.Types import ResourceTypes, JSON
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires
from ..etc.ResponseStatusCodes import CONTENTS_UNACCEPTABLE, NOT_IMPLEMENTED
from ..resources.AnnounceableResource import AnnounceableResource

if TYPE_CHECKING:
	from ..resources.Resource import Resource
	from ..runtime.Storage import Storage
	from ..plugins.services.TimeManager import TimeManager


@requires(timeManager='acme.plugins.services.TimeManager', required=False)
@requires(storage='acme.runtime.Storage')
class SCH(AnnounceableResource):
	""" Schedule (SCH) resource type. """

	timeManager: Optional[TimeManager] = None
	"""	Reference to the TimeManager plugin instance. """

	storage:Storage = None
	"""	Storage singleton instance. """


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)

		# Check if the parent is not a <node> resource then the "nco" attribute is not set
		_nco = self.nco
		if parentResource.ty != ResourceTypes.NOD:
			if _nco is not None:
				raise CONTENTS_UNACCEPTABLE (L.logWarn(f'"nco" must not be set for a SCH resource that is not a child of a <node> resource'))
		

		# If nco is set to true, NOT_IMPLEMENTED is returned
		if _nco is not None and _nco == True and not C.networkCoordinationSupported:
			raise NOT_IMPLEMENTED (L.logWarn(f'Network Coordinated Operation is not supported by this CSE'))

		# Add the schedule to the schedules DB
		self.storage.upsertSchedule(self)

		# TODO When <SoftwareCampaign> is supported
		# c)The request shall be rejected with the "OPERATION_NOT_ALLOWED" Response Status Code if the target resource 
		# is a <softwareCampaign> resource that has a campaignEnabled attribute with a value of true.

	
	def update(self, dct: JSON = None, originator: str | None = None, doValidateAttributes: bool | None = True) -> None:
		
		_nco = self.getFinalResourceAttribute('nco', dct)
		_parentResource = self.retrieveParentResource()
		
		# Check if the parent is not a <node> resource then the "nco" attribute is not set
		if _parentResource.ty != ResourceTypes.NOD:
			if _nco is not None:
				raise CONTENTS_UNACCEPTABLE (L.logWarn(f'"nco" must not be set for a SCH resource that is not a child of a <node> resource'))

		# If nco is set to true, NOT_IMPLEMENTED is returned
		if _nco is not None and _nco == True and not C.networkCoordinationSupported:
			raise NOT_IMPLEMENTED (L.logWarn(f'Network Coordinated Operation is not supported by this CSE'))

		# TODO When <SoftwareCampaign> is supported
		# c)The request shall be rejected with the "OPERATION_NOT_ALLOWED" Response Status Code 
		# if thetarget resource is a <softwareCampaign> resource that has a campaignEnabled attribute with a value of true.
		
		super().update(dct, originator, doValidateAttributes)

		# Update the schedule in the schedules DB
		self.storage.upsertSchedule(self)
	

	def validate(self, originator: str | None = None, dct: JSON | None = None, parentResource: Resource | None = None) -> None:
		super().validate(originator, dct, parentResource)

		# Set the active schedule in the CSE when updated
		if parentResource.ty == ResourceTypes.CSEBase:
			if not self.timeManager:
				raise NOT_IMPLEMENTED(L.logWarn('TimeManager plugin is disabled, cannot set active schedule in CSE'))
			self.timeManager.cseActiveSchedule = self.getFinalResourceAttribute('se/sce', dct)
			L.isDebug and L.logDebug(f'Setting active schedule in CSE to {self.timeManager.cseActiveSchedule}')


	def deactivate(self, originator: str, parentResource: Resource) -> None:

		# TODO When <SoftwareCampaign> is supported
		# a) The request shall be rejected with the "OPERATION_NOT_ALLOWED" Response Status Code 
		# if the target resource is a <softwareCampaign> resource that has a campaignEnabled attribute with a value of true.
		
		super().deactivate(originator, parentResource)

		# Remove the schedule from the schedules DB
		self.storage.removeSchedule(self)

