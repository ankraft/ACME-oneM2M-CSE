#
#	STTE.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: State
#

from __future__ import annotations
from typing import Optional, Any, Union

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnounceableResource import AnnounceableResource

# TODO annc version
# TODO add to UML diagram
# TODO add to statistics, also in console

class STTE(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR,
								   ResourceTypes.SUB
								 ]

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
		'acpi': None,
		'lbl': None,
		'cr': None,
		'cstn': None,
		'daci': None,

		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'sact': None,
		'stac': None,
		'sttrs': None,
	}

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.STTE, dct, pi, create = create)

