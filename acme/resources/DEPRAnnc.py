#
#	DEPRAnnc.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Dependency announced (DEPRA) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from .AnnouncedResource import AnnouncedResource

class DEPRAnnc(AnnouncedResource):
	""" Action announced (DEPRA) resource type """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB,
													#    ResourceTypes.DEBAnnc 
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
		'sfc': None,
		'evc': None,
		'rri': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.DEPRAnnc, dct, pi = pi, create = create)

