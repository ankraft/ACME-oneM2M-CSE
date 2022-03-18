#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON
from ..resources.Resource import *


class FCI(Resource):

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
		'et': None,
		'lbl': None,

		# Resource attributes
		'cs': None,
		'or': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, fcntType:str = None, create:bool = False) -> None:
		super().__init__(T.FCI, dct, pi, tpe = fcntType, create = create, inheritACP = True, readOnly = True)


	# Forbidd updating
	def update(self, dct:JSON=None, originator:str=None) -> Result:
		return Result.errorResult(rsc = RC.operationNotAllowed, dbg = 'updating FCIN is forbidden')

