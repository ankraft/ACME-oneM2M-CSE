#
#	TSI.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: timeSeriesInstance
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED
from ..etc.ACMEUtils import getAttributeSize
from ..resources.AnnounceableResource import AnnounceableResource


class TSI(AnnounceableResource):

	resourceType = ResourceTypes.TSI
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
		'lt': None,
		'et': None,
		'lbl': None,
		'at': None,
		'aa': None,
		'ast': None,
		'cr': None,
		'loc': None,


		# Resource attributes
   		'dgt': None,
		'con': None,
		'cs': None,
		'snr': None
	}


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('cs', getAttributeSize(self['con']))       # Set contentSize
		super().initialize(pi, originator)


	# Forbid updating
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		raise OPERATION_NOT_ALLOWED('updating TSI is forbidden')

