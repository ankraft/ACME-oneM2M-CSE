#
#	CRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CrossResourceSubscription
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, JSON
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L


class CRS(Resource):

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
		'acpi': None,
		'lbl': None,
		'cr': None,
		'cstn': None,
		'daci': None,

		# Resource attributes
		'exc': None,
		'nu': None,
		'nec': None,
		'su': None,
		'rrat': None,
		'srat': None,
		'twt': None,
		'tws': None,
		'encs': None, 

	}

	# TODO notificationStatsEnable - nse  support
	# TODO notificationStatsInfo - nsi	support


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.CRS, dct, pi, create = create)



	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		L.isDebug and L.logDebug(f'Validating crossResourceSubscription: {self.ri}')

		# Check that at least rrat or srat is present
		if self.rrat is None and self.srat is None:
			return Result.errorResult(dbg = L.logDebug(f'At least one of regularResourcesAsTarget or subscriptionResourcesAsTarget attributes shall be present'))
		return Result.successResult()