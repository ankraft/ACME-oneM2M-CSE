#
#	ACTRAnnc.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Action announced (ACTRA) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from .AnnouncedResource import AnnouncedResource

class ACTRAnnc(AnnouncedResource):
	""" Action announced (ACTRA) resource type """

	resourceType = ResourceTypes.ACTRAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """


	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB,
													   ResourceTypes.DEPRAnnc 
													   ]

	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes for announced resources
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'acpi':None,
		'daci': None,
		'lnk': None,
		'ast': None,

		# Resource attributes
		'apy': None,
		'sri': None,
		'evc': None,
		'evm': None,
		'ecp': None,
		'dep': None,
		'orc': None,
		'apv': None,
		'ipu': None,
		'air': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """

