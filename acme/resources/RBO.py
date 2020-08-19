#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
rboPolicies = constructPolicy([
	'rbo', 'far'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, rboPolicies)


class RBO(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		self.resourceAttributePolicies = rboPolicies	# only the resource type's own policies
		super().__init__(jsn, pi, mgd=T.RBO, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('rbo', False, overwrite=True)	# always False
			self.setAttribute('far', False, overwrite=True)	# always False


	#
	#	Handling the special behaviour for rbo and far attributes in 
	#	validate() and update()
	#

	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator, create))[0] == False:
			return res
		self.setAttribute('rbo', False, overwrite=True)	# always set (back) to True
		self.setAttribute('far', False, overwrite=True)	# always set (back) to True
		return True, C.rcOK, None


	def update(self, jsn:dict=None, originator:str=None) -> Tuple[bool, int, str]:
		# Check for rbo & far updates 
		if jsn is not None and self.tpe in jsn:
			rbo = Utils.findXPath(jsn, 'm2m:rbo/rbo')
			far = Utils.findXPath(jsn, 'm2m:rbo/far')
			if rbo is not None and far is not None and rbo and far:
				return False, C.rcBadRequest, 'update both rbo and far to True is not allowed'

		return super().update(jsn, originator)
