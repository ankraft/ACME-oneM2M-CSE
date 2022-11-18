#
#	TSB.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: TimeSyncBeacon
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, BeaconCriteria, ResourceTypes, Result, JSON
from ..etc import DateUtils
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..services import CSE
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration


# DISCUSS Only one TSB with loss_of_sync, but only one is relevant for a requester. Only one is allowed? Check in update/create


class TSB(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SUB ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'acpi': None,
		'lbl': None,
		'cstn': None,
		'daci': None,

		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'bcnr': None,
		'bcnc': None,
		'bcni': None,
		'bcnt': None,
		'bcnu': None,
	}

	# internal attributes to store durations in s
	_bcni	= '__bcni__'
	_bcnt	= '__bcnt__'




# DISCUSS beaconRequester prerequisites are not specifically mentioned in CREATE and UPDATE procedure. ->
#  good would be that, if not present, the CSE provides a value. Add to TS-0004 procedures


# TODO Implement Annc


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.TSB, dct, pi, create = create)
		# Add to internal attributes to ignore in validation etc
		self._addToInternalAttributes(self._bcni)	
		self._addToInternalAttributes(self._bcnt)

		self.setAttribute('bcnc', BeaconCriteria.PERIODIC, overwrite = False)


# TODO activate: add to interval updater
# TODO update:
# TODO deactivate

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		return CSE.time.addTimeSyncBeacon(self)
	

	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		originalBcnc = self.bcnc
		if not (res := super().update(dct, originator)).status:
			return res
		return CSE.time.updateTimeSyncBeacon(self, originalBcnc)
	

	def deactivate(self, originator: str) -> None:
		super().deactivate(originator)
		CSE.time.removeTimeSyncBeacon(self)


	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		L.isDebug and L.logDebug(f'Validating timeSeriesBeacon: {self.ri}')
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		
		# Check length of beaconNotificationURI
		if len(self.bcnu) == 0:
			L.logWarn(dbg := f'beaconNotificationURI attribute shall shall contain at least one URI')
			return Result.errorResult(dbg = dbg)

		# Check beaconInterval
		if self.hasAttribute('bcni') and self.bcnc != BeaconCriteria.PERIODIC:
			return Result.errorResult(dbg = L.logWarn(f'beaconInterval attribute shall only be present when beaconCriteria is PERIODIC'))
		if self.bcnc == BeaconCriteria.PERIODIC and not self.hasAttribute('bcni'):
			self.setAttribute('bcni', Configuration.get('cse.tsb.bcni'))
		if self.hasAttribute('bcni'):
			self.setAttribute(self._bcni, DateUtils.fromDuration(self.bcni))
		
		# Check beaconThreshold
		if self.hasAttribute('bcnt') and self.bcnc != BeaconCriteria.LOSS_OF_SYNCHRONIZATION:
			return Result.errorResult(dbg = L.logWarn(f'beaconThreshold attribute shall only be present when beaconCriteria is LOSS_OF_SYNCHRONIZATION'))
		if self.bcnc == BeaconCriteria.LOSS_OF_SYNCHRONIZATION and not self.hasAttribute('bcnt'):
			self.setAttribute('bcnt', Configuration.get('cse.tsb.bcnt'))
		if self.hasAttribute('bcnt'):
			self.setAttribute(self._bcnt, DateUtils.fromDuration(self.bcnt))
		
		# Check beaconRequester
		if self.hasAttribute('bcnr'):
			if self.bcnc == BeaconCriteria.PERIODIC:
				return Result.errorResult(dbg = L.logWarn(f'beaconRequester attribute shall only be present when beaconCriteria is LOSS_OF_SYNCHRONIZATION'))
		else:
			if self.bcnc == BeaconCriteria.LOSS_OF_SYNCHRONIZATION:
				return Result.errorResult(dbg = L.logWarn(f'beaconRequester attribute shall be present when beaconCriteria is PERIODIC'))

		return Result.successResult()
		

	def getInterval(self) -> float:
		"""	Return the real beacon interval in seconds instead of the ISO period.
		
			Returns:
				Beacon interval as a float representing seconds.
		"""
		return self[self._bcni]

