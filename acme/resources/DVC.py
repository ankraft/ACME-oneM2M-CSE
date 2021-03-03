#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#

from .MgmtObj import *
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
dvcPolicies = constructPolicy([
	'can', 'att', 'cas', 'ena', 'dis', 'cus'
])
attributePolicies = addPolicy(mgmtObjAttributePolicies, dvcPolicies)


class DVC(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = dvcPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.DVC, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('can', 'unknown', overwrite=False)
			self.setAttribute('att', False, overwrite=False)
			self.setAttribute('cas', {	"acn" : "unknown", "sus" : 0 }, overwrite=False)
			self.setAttribute('cus', False, overwrite=False)
			self.setAttribute('ena', True, overwrite=True)	# always True
			self.setAttribute('dis', True, overwrite=True)	# always True

	#
	#	Handling the special behaviour for ena and dis attributes in 
	#	validate() and update()
	#

	def validate(self, originator:str=None, create:bool=False, dct:JSON=None) -> Result:
		if not (res := super().validate(originator, create, dct)).status:
			return res
		self.setAttribute('ena', True, overwrite=True)	# always set (back) to True
		self.setAttribute('dis', True, overwrite=True)	# always set (back) to True
		return Result(status=True)


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		# Check for ena & dis updates 
		if dct is not None and self.tpe in dct:
			ena = Utils.findXPath(dct, 'm2m:dvc/ena')
			dis = Utils.findXPath(dct, 'm2m:dvc/dis')
			if ena is not None and dis is not None and ena and dis:
				return Result(status=False, rsc=RC.badRequest, dbg='both ena and dis updated to True is not allowed')

		return super().update(dct, originator)


