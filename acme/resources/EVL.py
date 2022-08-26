#
#	EVL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:EventLog
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.MgmtObj import *

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
	

	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.EVL, create = create)

		self.setAttribute('lgt', defaultLogTypeId, overwrite = False)
		self.setAttribute('lgd', '', overwrite = False)
		self.setAttribute('lgst', defaultLogStatus, overwrite = False)
		self.setAttribute('lga', False)
		self.setAttribute('lgo', False)


	def update(self, dct:JSON = None, originator:str = None, doValidateAttributes:bool = True) -> Result:
		# Check for rbo & far updates 
		if Utils.findXPath(dct, '{*}/lga') and Utils.findXPath(dct, '{*}/lgo'):
			return Result.errorResult(dbg = 'update both lga and lgo to True at the same time is not allowed')

		return super().update(dct, originator)
