#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#

from .MgmtObj import *
from Types import ResourceTypes as T, Result
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
dvcPolicies = constructPolicy([
	'can', 'att', 'cas', 'ena', 'dis', 'cus'
])
attributePolicies = addPolicy(mgmtObjAttributePolicies, dvcPolicies)


class DVC(MgmtObj):

	def __init__(self, jsn:dict=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = dvcPolicies	# only the resource type's own policies
		super().__init__(jsn, pi, mgd=T.DVC, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('can', 'unknown', overwrite=False)
			self.setAttribute('att', False, overwrite=False)
			self.setAttribute('cas', {	"acn" : "unknown", "sus" : 0 }, overwrite=False)
			self.setAttribute('cus', False, overwrite=False)
			self.setAttribute('ena', True, overwrite=True)	# always True
			self.setAttribute('dis', True, overwrite=True)	# always True


	def validate(self, originator:str=None, create:bool=False) -> Result:
		if not (res := super().validate(originator, create)).status:
			return res
		self.setAttribute('ena', True, overwrite=True)	# always set (back) to True
		self.setAttribute('dis', True, overwrite=True)	# always set (back) to True
		return Result(status=True)


	def update(self, jsn:dict=None, originator:str=None) -> Result:
		# Check for ena & dis updates 
		if jsn is not None and self.tpe in jsn:
			ena = Utils.findXPath(jsn, 'm2m:dvc/ena')
			dis = Utils.findXPath(jsn, 'm2m:dvc/dis')
			if ena is not None and dis is not None and ena and dis:
				return Result(status=False, rsc=C.rcBadRequest, dbg='both ena and dis updated to True is not allowed')

		return super().update(jsn, originator)


