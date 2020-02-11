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
import Utils

defaultDeviceType = 'unknown'
defaultModel = "unknown"
defaultManufacturer = "unknown"
defaultDeviceLabel = "unknown serial id"

class DVI(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsDVI, C.mgdDVI, create=create)

		if self.json is not None:
			self.setAttribute('dty', defaultDeviceType, overwrite=False)
			self.setAttribute('mod', defaultModel, overwrite=False)
			self.setAttribute('man', defaultManufacturer, overwrite=False)
			self.setAttribute('dlb', defaultDeviceLabel, overwrite=False)
