#
#	ACTR.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Action
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services.Configuration import Configuration
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources import Factory as Factory


class ACTR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ] # TODO Dependecy

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
		'hld': None,
		'at': None,
		'aa': None,
		'ast': None,
		'cr': None,

		# Resource attributes
		'apy': None,
		'sri': None,
		'evc': None,
		'evm': None,
		'ecp': None,
		'dep': None,
		'orc': None,
		'apv': None,
		'ipu': None,
		'air': None,
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.ACTR, dct, pi, create = create)

		# TODO set defaults
		# self.setAttribute('mdd', True, overwrite = False)	# Default is False if not provided

		# self.setAttribute('cni', 0, overwrite = False)
		# self.setAttribute('cbs', 0, overwrite = False)
		# if Configuration.get('cse.ts.enableLimits'):	# Only when limits are enabled
		# 	self.setAttribute('mni', Configuration.get('cse.ts.mni'), overwrite = False)
		# 	self.setAttribute('mbs', Configuration.get('cse.ts.mbs'), overwrite = False)
		# 	self.setAttribute('mdn', Configuration.get('cse.ts.mdn'), overwrite = False)

		self.__validating = False	# semaphore for validating