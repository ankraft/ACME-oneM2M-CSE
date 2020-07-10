#
#	BAT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Battery
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
batPolicies = constructPolicy([
	'btl', 'bts'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, batPolicies)


btsNORMAL			 = 1
btsCHARGING			 = 2
btsCHARGING_COMPLETE = 3
btsDAMAGED			 = 4
btsLOW_BATTERY		 = 5
btsNOT_INSTALLED	 = 6
btsUNKNOWN			 = 7


defaultBatteryLevel  = 100
defaultBatteryStatus = btsUNKNOWN

class BAT(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.BAT, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('btl', defaultBatteryLevel, overwrite=False)
			self.setAttribute('bts', defaultBatteryStatus, overwrite=False)


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(batPolicies), C.rcOK, None