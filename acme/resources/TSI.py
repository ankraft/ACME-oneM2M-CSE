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

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, ResponseStatusCode, JSON
from ..etc import Utils
from ..resources.AnnounceableResource import AnnounceableResource


class TSI(AnnounceableResource):

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


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.TSI, dct, pi, create = create, inheritACP = True, readOnly = True)
		self.setAttribute('cs', Utils.getAttributeSize(self['con']))       # Set contentSize


	# Forbid updating
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		return Result.errorResult(rsc = ResponseStatusCode.operationNotAllowed, dbg = 'updating CIN is forbidden')

