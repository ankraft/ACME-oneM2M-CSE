#
#	EVL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:EventLog
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, Result
from ..resources.MgmtObj import MgmtObj
from ..etc import Utils

lgtSystem = 1
lgtSecurity	= 2
lgtEvent = 3
lgtTrace = 4 
lgTPanic = 5

lgstStarted = 1
lgstStopped = 2
lgstUnknown = 3
lgstNotPresent = 4
lgstError = 5

defaultLogTypeId = lgtSystem
defaultLogStatus = lgstUnknown


class EVL(MgmtObj):

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
		'cstn': None,
		'acpi':None,
		'at': None,
		'aa': None,
		'ast': None,
		'daci': None,
		
		# MgmtObj attributes
		'mgd': None,
		'obis': None,
		'obps': None,
		'dc': None,
		'mgs': None,
		'cmlk': None,

		# Resource attributes
		'lgt': None,
		'lgd': None,
		'lgst': None,
		'lga': None,
		'lgo': None
	}
	

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.EVL, create = create)

		self.setAttribute('lgt', defaultLogTypeId, overwrite = False)
		self.setAttribute('lgd', '', overwrite = False)
		self.setAttribute('lgst', defaultLogStatus, overwrite = False)
		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		# Check for rbo & far updates 
		if Utils.findXPath(dct, '{*}/lga') and Utils.findXPath(dct, '{*}/lgo'):
			return Result.errorResult(dbg = 'update both lga and lgo to True at the same time is not allowed')

		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)
		return super().update(dct, originator)
