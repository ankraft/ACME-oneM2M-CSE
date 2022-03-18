#
#	TSI.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: timeSeriesInstance
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class TSI(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

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


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.TSI, dct, pi, create = create, inheritACP = True, readOnly = True)
		self.setAttribute('cs', Utils.getAttributeSize(self['con']))       # Set contentSize


	# Forbid updating
	def update(self, dct:JSON = None, originator:str = None) -> Result:
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'updating CIN is forbidden')

