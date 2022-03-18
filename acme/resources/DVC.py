#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON
from ..etc import Utils as Utils
from ..resources.MgmtObj import *


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


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.DVC, create = create)

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

	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		self.setAttribute('ena', True, overwrite = True)	# always set (back) to True
		self.setAttribute('dis', True, overwrite = True)	# always set (back) to True
		return Result.successResult()


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		# Check for ena & dis updates 
		if dct and self.tpe in dct:
			ena = Utils.findXPath(dct, 'm2m:dvc/ena')
			dis = Utils.findXPath(dct, 'm2m:dvc/dis')
			if ena and dis:
				return Result(status=False, rsc=RC.badRequest, dbg='both ena and dis updated to True is not allowed')

		return super().update(dct, originator)


