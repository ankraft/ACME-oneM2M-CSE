#
#	LCPAnnc.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: LocationPolicy Announced
#

""" LocationPolicy Announced(LCPA) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from .AnnouncedResource import AnnouncedResource


class LCPAnnc(AnnouncedResource):
	""" LocationPolicy Announced (LCPA) resource type. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
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
		'et': None,
		'lbl': None,
		'acpi':None,
		'daci': None,
		'lnk': None,
		'ast': None,

		# Resource attributes
		'los': None,
		'lit': None,
		'lou': None,
		'lot': None,
		'lor': None,
		'loi': None,
		'lon': None,
		'lost': None,
		'gta': None,
		'gec': None,
		'aid': None,
		'rlkl': None,
		'luec': None

	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.LCPAnnc, dct, pi = pi, create = create)

