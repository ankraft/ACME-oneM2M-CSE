#
#	DAC.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: DynamicAuthorizationConsultation
#
""" DynamicAuthorizationConsultation (DAC) resource type. """

from __future__ import annotations
from typing import Optional
from ..etc.Types import AttributePolicyDict, EvalMode, ResourceTypes, JSON, Permission, EvalCriteriaOperator, Operation
from ..resources.Resource import Resource

class DAC(Resource):
	""" DynamicAuthorizationConsultation (DAC) resource type. """

	resourceType = ResourceTypes.DAC
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB
												   	   # + Transaction
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

		# Resource attributes
		'dae': None,
		'dap': None,
		'dal': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """

