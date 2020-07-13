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
			self.setAttribute('rbo', False, overwrite=False)
			self.setAttribute('far', False, overwrite=False)

