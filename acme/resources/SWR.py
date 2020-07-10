#
#	SWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Software
#

from .MgmtObj import *
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
swrPolicies = constructPolicy([
	'vr', 'swn', 'url', 'ins', 'acts', 'in', 'un', 'act', 'dea'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, swrPolicies)


statusUninitialized = 0
statusSuccessful = 1
statusFailure = 2
statusInProcess = 3

defaultSoftwareName = 'unknown'
defaultVersion = '0.0'
defaultURL = 'unknown'
defaultStatus = { 'acn' : '', 'sus' : statusUninitialized }


class SWR(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, mgd=T.SWR, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('vr', defaultVersion, overwrite=False)
			self.setAttribute('swn', defaultSoftwareName, overwrite=False)
			self.setAttribute('url', defaultURL, overwrite=False)
			self.setAttribute('ins', defaultStatus, overwrite=False)
			self.setAttribute('acts', defaultStatus, overwrite=False)
			self.setAttribute('in', False, overwrite=False)
			self.setAttribute('un', False, overwrite=False)
			self.setAttribute('act', False, overwrite=False)
			self.setAttribute('dea', False, overwrite=False)


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(swrPolicies), C.rcOK, None
		