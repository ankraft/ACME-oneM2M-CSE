#
#	MEM.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Memory
#

from etc.Types import ResourceTypes as T, JSON
from resources.MgmtObj import *
from services.Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
memPolicies = constructPolicy([
	'mma', 'mmt'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, memPolicies)


defaultMemoryAvailable = 0
defaultMemTotal = 0


class MEM(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = memPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.MEM, create=create, attributePolicies=attributePolicies)

		self.setAttribute('mma', defaultMemoryAvailable, overwrite=False)
		self.setAttribute('mmt', defaultMemTotal, overwrite=False)

