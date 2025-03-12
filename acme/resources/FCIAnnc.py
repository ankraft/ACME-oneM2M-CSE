#
#	FCIAnnc.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CIN : Announceable variant
#
"""  FlexContainerInstance announced (FCIA) resource type."""

from __future__ import annotations
from typing import Optional
from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED



class FCIAnnc(AnnouncedResource):
	""" FlexContainerInstance announced (FCIA) resource type. """

	resourceType = ResourceTypes.FCIAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
	""" The allowed child-resource types. """

	# Attributes and Attribute policies for this Resource Class
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
		'ast': None,
		'loc': None,
		'lnk': None,

		# Resource attributes
		'cs': None,
		'org': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	# Forbidd updating
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None,
					 doValidateAttributes:Optional[bool] = True) -> None:
		raise OPERATION_NOT_ALLOWED('updating FCIAnnc is forbidden')

