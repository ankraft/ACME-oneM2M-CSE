#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, ResponseStatusCode, JSON
from ..etc import Utils
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource
from ..services.Logging import Logging as L



class DVC(MgmtObj):

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
			'can': None,
			'att': None,
			'cas': None,
			'ena': None,
			'dis': None,
			'cus': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.DVC, create = create)

		self.setAttribute('can', 'unknown', overwrite = False)
		self.setAttribute('att', False, overwrite = False)
		self.setAttribute('cas', {	"acn" : "unknown", "sus" : 0 }, overwrite = False)
		self.setAttribute('cus', False, overwrite = False)
		self.setAttribute('ena', True, overwrite = True)	# always True
		self.setAttribute('dis', True, overwrite = True)	# always True

	#
	#	Handling the special behaviour for ena and dis attributes in 
	#	validate() and update()
	#

	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		self.setAttribute('ena', True, overwrite = True)	# always set (back) to True
		self.setAttribute('dis', True, overwrite = True)	# always set (back) to True
		return Result.successResult()


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		# Check for ena & dis updates 
		ena = Utils.findXPath(dct, '{*}/ena')
		dis = Utils.findXPath(dct, '{*}/dis')
		if ena and dis:
			return Result(status = False, rsc = ResponseStatusCode.badRequest, dbg = 'Both ena and dis updated to True is not allowed')

		return super().update(dct, originator)


