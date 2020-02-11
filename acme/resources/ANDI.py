#
#	ANDI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkDeviceInfo
#

from .MgmtObj import *
from Constants import Constants as C
import Utils


defaultAreaNwkType = ''


class ANDI(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsANDI, C.mgdANDI, create=create)

		if self.json is not None:
			self.setAttribute('dvd', defaultAreaNwkType, overwrite=False)
			self.setAttribute('dvt', '', overwrite=False)
			self.setAttribute('awi', '', overwrite=False)

