#
#	ANDI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkDeviceInfo
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
andiPolicies = constructPolicy([
	'dvd', 'dvt', 'awi', 'sli', 'sld', 'ss', 'lnh'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, andiPolicies)

defaultDeviceID = ''


class ANDI(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.ANDI, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('dvd', defaultDeviceID, overwrite=False)
			self.setAttribute('dvt', '', overwrite=False)
			self.setAttribute('awi', '', overwrite=False)


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(andiPolicies), C.rcOK, None
