#
#	NTPR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: notificationTargetMgmtPolicyRef 
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, CSERequest, Result
from ..etc.Constants import Constants
from ..resources.Resource import Resource
from ..resources.Resource import addToInternalAttributes
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..etc.ResponseStatusCodes import CONFLICT


# Add to internal attributes to ignore in validation etc
addToInternalAttributes(Constants.attrPCUAggregate)	


class NTPR(Resource):

	resourceType = ResourceTypes.NTPR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	resourceName = 'ntpr'
	""" Possibility for virtual sub-classes to provide a specific resource name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB ]

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
		'cstn': None,

		# Resource attributes
   		'ntu': None,
		'npi': None,
	}


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		
		# Check if other NTPR resources exist for the same subscription that have the same notificationTargetURI elements
		ntprResources = CSE.dispatcher.retrieveDirectChildResources(self.pi, ResourceTypes.NTPR)
		if ntprResources:
			for ntpr in ntprResources:
				if ntpr != self:
					# Get the notificationTargetURI from both resources
					thisNtu = self.ntu
					otherNtus = ntpr.ntu

					# Check if any element in current_ntus is also in other_ntus
					if any(ntu in otherNtus for ntu in thisNtu):
						raise CONFLICT(L.logDebug(f'Notification Target URI overlap detected between {self.ri} and {ntpr.ri}'))
		
		super().validate(originator, dct, parentResource)