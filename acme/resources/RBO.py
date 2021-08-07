#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#

from resources.MgmtObj import *
from etc.Types import ResourceTypes as T, ResponseCode as RC, Result, JSON
from services.Validator import constructPolicy, addPolicy
import etc.Utils as Utils

# Attribute policies for this resource are constructed during startup of the CSE
rboPolicies = constructPolicy([
	'rbo', 'far'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, rboPolicies)

# TODO Shouldn't those attributes actually be always be True? According to TS-0004 D.10.1-2

class RBO(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = rboPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.RBO, create=create, attributePolicies=attributePolicies)

		self.setAttribute('rbo', False, overwrite=True)	# always False
		self.setAttribute('far', False, overwrite=True)	# always False


	#
	#	Handling the special behaviour for rbo and far attributes in 
	#	validate() and update()
	#

	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		self.setAttribute('rbo', False, overwrite=True)	# always set (back) to False
		self.setAttribute('far', False, overwrite=True)	# always set (back) to False
		return Result(status=True)


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		# Check for rbo & far updates 
		if dct and self.tpe in dct:
			rbo = Utils.findXPath(dct, 'm2m:rbo/rbo')
			far = Utils.findXPath(dct, 'm2m:rbo/far')
			if rbo is not None and far is not None and rbo and far:
				return Result(status=False, rsc=RC.badRequest, dbg='update both rbo and far to True is not allowed')

		return super().update(dct, originator)
