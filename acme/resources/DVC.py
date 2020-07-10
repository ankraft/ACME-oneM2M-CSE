#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
dvcPolicies = constructPolicy([
	'can', 'att', 'cas', 'ena', 'dis', 'cus'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, dvcPolicies)


class DVC(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.DVC, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('can', 'unknown', overwrite=False)
			self.setAttribute('att', False, overwrite=False)
			self.setAttribute('cas', {	"acn" : "unknown", "sus" : 0 }, overwrite=False)
			self.setAttribute('cus', False, overwrite=False)


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(dvcPolicies), C.rcOK, None
		