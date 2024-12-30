#
#	STTE.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: State
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, ProcessState
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED, INVALID_PROCESS_CONFIGURATION, NOT_FOUND
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources.Resource import Resource
from ..runtime import CSE


# TODO annc version
# TODO add to UML diagram
# TODO add to statistics, also in console

class STTE(AnnounceableResource):

	resourceType = ResourceTypes.STTE
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR,
								   ResourceTypes.SUB
								 ]

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
		'cr': None,
		'cstn': None,
		'daci': None,

		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'sact': None,
		'stac': None,
		'sttrs': None,
	}
	

	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)

		# step 1: Check parent resource is disabled
		if parentResource.prst != ProcessState.Disabled:
			raise OPERATION_NOT_ALLOWED('Parent <processManagement> resource must be in state "Disabled"')
		
		# step 2 check if all referenced states exist, have access, and are direct child resources

		if (sttrs := self.sttrs):
			# EXPERIMENTAL Not the request originator is used but the originator of the state resource or the custotian
			_orig = self.getCurrentOriginator()
			for sttr in sttrs:
				# check whether state resource exist
				try:
					nxstID = sttr['nxst']
					# Check access
					# EXPRIMENTAL assuming a subject rsource ID attribute in stateTransition
					CSE.action.checkEvalCriteria(sttr['evc'], sttr['sri'], _orig)

					# Check parent of references next state resource
					stateResource = CSE.dispatcher.retrieveResource(nxstID)
					if stateResource.pi != self.pi:
						raise INVALID_PROCESS_CONFIGURATION(f'Referenced state resource "{nxstID}" is not a direct child of this state\'s parent resource')

				except NOT_FOUND:
					raise INVALID_PROCESS_CONFIGURATION(f'Referenced state resource "{nxstID}" does not exist')
				

	def update(self, dct:JSON = None, 
					 originator:Optional[str] = None,
					 doValidateAttributes:Optional[bool] = True) -> None:
		
		# Get parent resource
		parentResource = CSE.dispatcher.retrieveResource(self.pi)

		# Check if state resource is still active (ie. not disabled)
		if parentResource.prst != ProcessState.Disabled:
			raise OPERATION_NOT_ALLOWED('Parent <processManagement> resource must be in state "Disabled"')
		
		super().update(dct, originator, doValidateAttributes)




# 2) If the request is attempting to update the stateTransitions attribute, the Receiver shall check if after processing the request, the value of the stateActive attribute of the <state> resource will equal “False”. If not, the receiver shall return a response primitive with a Response Status Code indicating an "OPERATION_NOT_ALLOWED" error.

# 3) The Receiver shall check the existence and accessibility of an <action> child resource, if any, referenced by the stateAction attribute of the request. If the referenced <action> child resource does not exist, does not have retrieve privileges for the Originator, or is not a child resource of this <state> resource, then the Receiver shall return a response primitive with a Response Status Code indicating an "INVALID_PROCESS_CONFIGURATION" error.

# 4) The Receiver shall check the existence and accessibility of any <state> resources referenced by the stateTransitions attribute of the request. If any of the referenced <state> child resources do not exist, do not have retrieve privileges for the Originator or are not child resources of the parent <processManagement> resource, then the Receiver shall return a response primitive with a Response Status Code indicating "INVALID_PROCESS_CONFIGURATION" error.

# 5) For any evalCriteria defined in the stateTransitions attribute of the request, the Receiver shall check the existence and accessibility of any resource and attribute referenced by the subject element of the evalCriteria. If any of the referenced resources or attributes do not exist or do not have retrieve privileges for the Originator, then the Receiver shall return a response primitive with a Response Status Code indicating an "INVALID_PROCESS_CONFIGURATION" error.

# 6) For any evalCriteria defined in the stateTransitions attribute of the request, the Receiver shall check the value provided for the threshold element of the evalCriteria attribute is within the value space (as defined in [3]) of the data type of the subject element of the evalCriteria attribute. The Receiver shall also check that the value provided for the operator element of the evalCriteria attribute is a valid value based on Table 6.3.4.2.86-1. If either check fails, the receiver shall return a response primitive with a Response Status Code indicating an "INVALID_PROCESS_CONFIGURATION" error.


	def willBeDeactivated(self, originator: str, parentResource: Resource) -> None:
		# Check own stateActive attribute
		if self.sact:
			raise OPERATION_NOT_ALLOWED('State resource is still active. Deletion not allowed.')
		
		# Check parent resource's processStatus. Cannot delete states from running processes
		if parentResource.prst != ProcessState.Disabled:
			raise OPERATION_NOT_ALLOWED('Parent <processManagement> resource must be in state "Disabled"')
	
		super().willBeDeactivated(originator, parentResource)
