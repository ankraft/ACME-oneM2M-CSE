#
#	SWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Software
#

from .MgmtObj import *
from Constants import Constants as C
import Utils


statusUninitialized = 0
statusSuccessful = 1
statusFailure = 2
statusInProcess = 3

defaultSoftwareName = 'unknown'
defaultVersion = '0.0'
defaultURL = 'unknown'
defaultStatus = { 'acn' : '', 'sus' : statusUninitialized }


class SWR(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsSWR, C.mgdSWR, create=create)

		if self.json is not None:
			self.setAttribute('vr', defaultVersion, overwrite=False)
			self.setAttribute('swn', defaultSoftwareName, overwrite=False)
			self.setAttribute('url', defaultURL, overwrite=False)
			self.setAttribute('ins', defaultStatus, overwrite=True)
			self.setAttribute('acts', defaultStatus, overwrite=True)
			self.setAttribute('in', False, overwrite=True)
			self.setAttribute('un', False, overwrite=True)
			self.setAttribute('act', False, overwrite=True)
			self.setAttribute('dea', False, overwrite=True)

