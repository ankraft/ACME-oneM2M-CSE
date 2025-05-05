 #
#	NTP.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: NotificationTargetPolicy
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, LogicalOperator
from ..etc.Constants import RuntimeConstants as RC
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.ResponseStatusCodes import BAD_REQUEST

_defaultPLBL = 'Default'
""" Default policy label for NTP resources. """

class NTP(Resource):

	resourceType = ResourceTypes.NTP
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [	ResourceTypes.SUB,
														ResourceTypes.PDR,
	]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = { 
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'et': None,
		'acpi':None,
		'ct': None,
		'lbl': None,
		'lt': None,
		'daci': None,
		'cr': None,
		'cstn': None,

		# Resource attributes
   		'acn': None,
		'plbl': None,
		'rrs': None
	}


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		# Check that the creator attribute is not set when the resource is created by the CSE admin
		if self.cr is not None and originator == RC.cseOriginator:
			raise BAD_REQUEST(f'Creator attribute: {self.cr} is not allowed for CSE admin created NTP resources.')


	def validate(self, originator:str=None, dct:Optional[JSON]=None, parentResource:Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)

		# Set a default value for the rrs attribute if not provided
		if self.rrs is None:
			# Set the default value for rrs if not provided
			self.setAttribute('rrs', LogicalOperator.AND.value)	# EXPERIMENTAL Check spec change for default value

		# Validate that only one NTP resource with the same creator and label exists
		res = CSE.storage.searchByFragment({ 'ty': ResourceTypes.NTP, 'cr': self.cr, 'plbl': self.plbl })
		for r in res:
			if r.ri != self.ri:	# ignore self
				if r.plbl == self.plbl and r.cr == self.cr:
					raise BAD_REQUEST(f'Only one NTP resource with the same creator and policyLabel is allowed. Existing NTP: {r.ri}')

	
	def willBeDeactivated(self, originator:str, parentResource:Resource) -> None:
		# Check that the system default policy is not deleted
		if self.plbl == _defaultPLBL and self.getOriginator() == RC.cseOriginator:
			raise BAD_REQUEST(f'The system default NTP resource cannot be deleted.')
		super().willBeDeactivated(originator, parentResource)
	