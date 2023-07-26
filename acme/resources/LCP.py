 #
#	LCP.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: LocationPolicy
#

""" LocationPolicy (LCP) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Constants import Constants as C
from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..services.Logging import Logging as L
from ..services import CSE
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource

# TODO add annc
# TODO add to supported resources of CSE

class LCP(AnnounceableResource):
	""" Schedule (SCH) resource type. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB ]
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
		'at': None,
		'aa': None,
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


	def __init__(self, dct:Optional[JSON] = None, pi:Optional[str] = None, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.LCP, dct, pi, create = create)

