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

from ..etc.Types import AttributePolicyDict, BeaconCriteria, ResourceTypes, JSON
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.DateUtils import fromDuration
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration


# Add to internal attributes 
addToInternalAttributes(Constants.attrBCNI)	
addToInternalAttributes(Constants.attrBCNT)


# DISCUSS Only one TSB with loss_of_sync, but only one is relevant for a requester. Only one is allowed? Check in update/create



class TSB(AnnounceableResource):

	resourceType = ResourceTypes.TSB
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

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



# DISCUSS beaconRequester prerequisites are not specifically mentioned in CREATE and UPDATE procedure. ->
#  good would be that, if not present, the CSE provides a value. Add to TS-0004 procedures


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('bcnc', BeaconCriteria.PERIODIC, overwrite = False)
		super().initialize(pi, originator)


# TODO activate: add to interval updater
# TODO update:
# TODO deactivate

	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		CSE.time.addTimeSyncBeacon(self)
	

	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		originalBcnc = self.bcnc
		super().update(dct, originator, doValidateAttributes)
		CSE.time.updateTimeSyncBeacon(self, originalBcnc)
	

	def deactivate(self, originator: str, parentResource:Resource) -> None:
		super().deactivate(originator, parentResource)
		CSE.time.removeTimeSyncBeacon(self)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		L.isDebug and L.logDebug(f'Validating timeSeriesBeacon: {self.ri}')
		super().validate(originator, dct, parentResource)
		
		# Check length of beaconNotificationURI
		if len(self.bcnu) == 0:
			raise BAD_REQUEST(f'beaconNotificationURI attribute shall shall contain at least one URI')

		# Check beaconInterval
		if self.hasAttribute('bcni') and self.bcnc != BeaconCriteria.PERIODIC:
			raise BAD_REQUEST(L.logWarn(f'beaconInterval attribute shall only be present when beaconCriteria is PERIODIC'))
		if self.bcnc == BeaconCriteria.PERIODIC and not self.hasAttribute('bcni'):
			self.setAttribute('bcni', Configuration.resource_tsb_bcni)
		if self.hasAttribute('bcni'):
			self.setAttribute(Constants.attrBCNI, fromDuration(self.bcni))
		
		# Check beaconThreshold
		if self.hasAttribute('bcnt') and self.bcnc != BeaconCriteria.LOSS_OF_SYNCHRONIZATION:
			raise BAD_REQUEST(L.logWarn(f'beaconThreshold attribute shall only be present when beaconCriteria is LOSS_OF_SYNCHRONIZATION'))
		if self.bcnc == BeaconCriteria.LOSS_OF_SYNCHRONIZATION and not self.hasAttribute('bcnt'):
			self.setAttribute('bcnt', Configuration.resource_tsb_bcnt)
		if self.hasAttribute('bcnt'):
			self.setAttribute(Constants.attrBCNI, fromDuration(self.bcnt))
		
		# Check beaconRequester
		if self.hasAttribute('bcnr'):
			if self.bcnc == BeaconCriteria.PERIODIC:
				raise BAD_REQUEST(L.logWarn(f'beaconRequester attribute shall only be present when beaconCriteria is LOSS_OF_SYNCHRONIZATION'))
		else:
			if self.bcnc == BeaconCriteria.LOSS_OF_SYNCHRONIZATION:
				raise BAD_REQUEST(L.logWarn(f'beaconRequester attribute shall be present when beaconCriteria is PERIODIC'))


	def getInterval(self) -> float:
		"""	Return the real beacon interval in seconds instead of the ISO period.
		
			Returns:
				Beacon interval as a float representing seconds.
		"""
		return self[Constants.attrBCNI]

