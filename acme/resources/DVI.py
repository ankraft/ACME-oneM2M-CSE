#
#	DVI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceInfo
#

from .MgmtObj import *
from Constants import Constants as C
from Validator import constructPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
	'dlb', 'man', 'mfdl', 'mfd', 'mod', 'smod', 'dty', 'dvnm', 'fwv', 'swv', 
	'hwv', 'osv', 'cnty', 'loc', 'syst', 'spur', 'purl', 'ptl'
])

defaultDeviceType = 'unknown'
defaultModel = "unknown"
defaultManufacturer = "unknown"
defaultDeviceLabel = "unknown serial id"

class DVI(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsDVI, C.mgdDVI, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('dty', defaultDeviceType, overwrite=False)
			self.setAttribute('mod', defaultModel, overwrite=False)
			self.setAttribute('man', defaultManufacturer, overwrite=False)
			self.setAttribute('dlb', defaultDeviceLabel, overwrite=False)
