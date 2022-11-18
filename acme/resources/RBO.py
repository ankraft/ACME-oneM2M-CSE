#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#

from __future__ import annotations
from typing import Optional

from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource
from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON
from ..etc import Utils

# TODO Shouldn't those attributes actually be always be True? According to TS-0004 D.10.1-2

class RBO(MgmtObj):

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
		'rbo': None,
		'far': None
	}
	
	
	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.RBO, create = create)

		self.setAttribute('rbo', False, overwrite = True)	# always False
		self.setAttribute('far', False, overwrite = True)	# always False


	#
	#	Handling the special behaviour for rbo and far attributes in 
	#	validate() and update()
	#

	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		self.setAttribute('rbo', False, overwrite = True)	# always set (back) to False
		self.setAttribute('far', False, overwrite = True)	# always set (back) to False
		return Result.successResult()


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		# Check for rbo & far updates 
		rbo = Utils.findXPath(dct, '{*}/rbo')
		far = Utils.findXPath(dct, '{*}/far')
		if rbo and far:
			return Result.errorResult(dbg = 'update both rbo and far to True is not allowed')

		return super().update(dct, originator)
