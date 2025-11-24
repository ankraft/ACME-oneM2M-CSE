#
#	PDR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PolicyDeletionRules
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.ResponseStatusCodes import CONFLICT
from ..runtime.Logging import Logging as L


class PDR(Resource):

	resourceType = ResourceTypes.PDR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [	ResourceTypes.SUB,
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
		'cstn': None,

		# Resource attributes
   		'dr': None,
		'drr': None
	}


	def activate(self, parentResource:Resource, originator:str) -> None:

		# Check if there are less than 2 PDR under the parent NTP
		if len(CSE.dispatcher.retrieveDirectChildResources(pi=parentResource.ri, ty=ResourceTypes.PDR)) > 2:
			raise CONFLICT(L.logDebug(f'Only 2 PDR are allowed under an NTP'))
		super().activate(parentResource, originator)