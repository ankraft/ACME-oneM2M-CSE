#
#	ANI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkInfo
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
aniPolicies = constructPolicy([
	'ant', 'ldv'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, aniPolicies)

defaultAreaNwkType = ''


class ANI(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.ANI, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('ant', defaultAreaNwkType, overwrite=False)


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(aniPolicies), C.rcOK, None
