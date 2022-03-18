#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#

from ..resources.MgmtObj import *
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseStatusCode as RC, Result, JSON
from ..etc import Utils as Utils

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
	
	
	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.RBO, create = create)

		self.setAttribute('rbo', False, overwrite = True)	# always False
		self.setAttribute('far', False, overwrite = True)	# always False


	#
	#	Handling the special behaviour for rbo and far attributes in 
	#	validate() and update()
	#

	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		self.setAttribute('rbo', False, overwrite = True)	# always set (back) to False
		self.setAttribute('far', False, overwrite = True)	# always set (back) to False
		return Result.successResult()


	def update(self, dct:JSON = None, originator:str = None) -> Result:
		# Check for rbo & far updates 
		if dct and self.tpe in dct:
			rbo = Utils.findXPath(dct, 'm2m:rbo/rbo')
			far = Utils.findXPath(dct, 'm2m:rbo/far')
			if rbo and far:
				return Result.errorResult(dbg='update both rbo and far to True is not allowed')

		return super().update(dct, originator)
