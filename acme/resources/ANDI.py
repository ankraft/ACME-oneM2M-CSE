#
#	ANDI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkDeviceInfo
#

from .MgmtObj import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
andiPolicies = constructPolicy([
	'dvd', 'dvt', 'awi', 'sli', 'sld', 'ss', 'lnh'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, andiPolicies)

defaultDeviceID = ''


class ANDI(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = andiPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.ANDI, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('dvd', defaultDeviceID, overwrite=False)
			self.setAttribute('dvt', '', overwrite=False)
			self.setAttribute('awi', '', overwrite=False)
