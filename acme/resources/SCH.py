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
from typing import Optional

from ..etc.Constants import Constants as C
from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..services.Logging import Logging as L
from ..services import CSE
from ..resources.Resource import Resource
from ..etc.ResponseStatusCodes import CONTENTS_UNACCEPTABLE, NOT_IMPLEMENTED
from ..resources.AnnounceableResource import AnnounceableResource


class SCH(AnnounceableResource):
	""" Schedule (SCH) resource type. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB
													 ]
	""" The allowed child-resource types. """

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
		'lbl': None,
		'acpi':None,
		'et': None,
		'daci': None,
		'cstn': None,
		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'se': None,
		'nco': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:Optional[JSON] = None, pi:Optional[str] = None, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.SCH, dct, pi, create = create)



	def activate(self, parentResource:Resource, originator:str) -> None:
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
		CSE.storage.upsertSchedule(self)

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
		CSE.storage.upsertSchedule(self)
	

	def validate(self, originator: str | None = None, dct: JSON | None = None, parentResource: Resource | None = None) -> None:
		super().validate(originator, dct, parentResource)

		# Set the active schedule in the CSE when updated
		if parentResource.ty == ResourceTypes.CSEBase:
			CSE.cseActiveSchedule = self.getFinalResourceAttribute('se/sce', dct)
			L.isDebug and L.logDebug(f'Setting active schedule in CSE to {CSE.cseActiveSchedule}')


	def deactivate(self, originator: str) -> None:

		# TODO When <SoftwareCampaign> is supported
		# a) The request shall be rejected with the "OPERATION_NOT_ALLOWED" Response Status Code 
		# if the target resource is a <softwareCampaign> resource that has a campaignEnabled attribute with a value of true.
		
		super().deactivate(originator)

		# Remove the schedule from the schedules DB
		CSE.storage.removeSchedule(self)

