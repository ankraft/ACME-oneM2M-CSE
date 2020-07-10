#
#	DVI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceInfo
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
dviPolicies = constructPolicy([
	'dlb', 'man', 'mfdl', 'mfd', 'mod', 'smod', 'dty', 'dvnm', 'fwv', 'swv', 
	'hwv', 'osv', 'cnty', 'loc', 'syst', 'spur', 'purl', 'ptl'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, dviPolicies)
print(attributePolicies)

defaultDeviceType = 'unknown'
defaultModel = "unknown"
defaultManufacturer = "unknown"
defaultDeviceLabel = "unknown serial id"

class DVI(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.DVI, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('dty', defaultDeviceType, overwrite=False)
			self.setAttribute('mod', defaultModel, overwrite=False)
			self.setAttribute('man', defaultManufacturer, overwrite=False)
			self.setAttribute('dlb', defaultDeviceLabel, overwrite=False)


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(dviPolicies), C.rcOK, None