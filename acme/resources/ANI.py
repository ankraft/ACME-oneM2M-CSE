#
#	ANI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkInfo
#

from .MgmtObj import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
aniPolicies = constructPolicy([
	'ant', 'ldv'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, aniPolicies)

defaultAreaNwkType = ''


class ANI(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = aniPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.ANI, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('ant', defaultAreaNwkType, overwrite=False)
