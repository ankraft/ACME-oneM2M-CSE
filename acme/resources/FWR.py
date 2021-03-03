#
#	FWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Firmware
#

from .MgmtObj import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
fwrPolicies = constructPolicy([
	'vr', 'fwn', 'url', 'uds', 'ud'
])
attributePolicies =  addPolicy(mgmtObjAttributePolicies, fwrPolicies)


statusUninitialized = 0
statusSuccessful = 1
statusFailure = 2
statusInProcess = 3

defaultFirmwareName = 'unknown'
defaultVersion = '0.0'
defaultURL = 'unknown'
defaultUDS = { 'acn' : '', 'sus' : statusUninitialized }


class FWR(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = fwrPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.FWR, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('vr', defaultVersion, overwrite=False)
			self.setAttribute('fwn', defaultFirmwareName, overwrite=False)
			self.setAttribute('url', defaultURL, overwrite=False)
			self.setAttribute('uds', defaultUDS, overwrite=False)
			self.setAttribute('ud', False, overwrite=False)

