#
#	FWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Firmware
#

from .MgmtObj import *
from Constants import Constants as C
import Utils


statusUninitialized = 0
statusSuccessful = 1
statusFailure = 2
statusInProcess = 3

defaultFirmwareName = 'unknown'
defaultVersion = '0.0'
defaultURL = 'unknown'
defaultUDS = { 'acn' : '', 'sus' : statusUninitialized }



class FWR(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsFWR, C.mgdFWR, create=create)

		if self.json is not None:
			self.setAttribute('vr', defaultVersion, overwrite=False)
			self.setAttribute('fwn', defaultFirmwareName, overwrite=False)
			self.setAttribute('url', defaultURL, overwrite=False)
			self.setAttribute('uds', defaultUDS, overwrite=True)
			self.setAttribute('ud', False, overwrite=True)


