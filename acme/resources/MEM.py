#
#	MEM.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Memory
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
memPolicies = constructPolicy([
	'mma', 'mmt'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, memPolicies)


defaultMemoryAvailable = 0
defaultMemTotal = 0


class MEM(MgmtObj):

	def __init__(self, jsn:dict = None, pi: str = None, create: bool = False) -> None:
		self.resourceAttributePolicies = memPolicies	# only the resource type's own policies
		super().__init__(jsn, pi, mgd=T.MEM, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('mma', defaultMemoryAvailable, overwrite=False)
			self.setAttribute('mmt', defaultMemTotal, overwrite=False)

