#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED
from ..resources.AnnounceableResource import AnnounceableResource


class FCI(AnnounceableResource):

	resourceType = ResourceTypes.FCI
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'et': None,
		'lbl': None,
		'loc': None,

		# Resource attributes
		'cs': None,
		'org': None
	}


	def __init__(self, dct:Optional[JSON] = None, typeShortname:Optional[str] = None, create:Optional[bool] = False) -> None:
		self.typeShortname = typeShortname
		super().__init__(dct, create = create)


	# Forbidd updating
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None,
					 doValidateAttributes:Optional[bool] = True) -> None:
		raise OPERATION_NOT_ALLOWED('updating FCI is forbidden')

