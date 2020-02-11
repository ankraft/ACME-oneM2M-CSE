#
#	ANI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkInfo
#

from .MgmtObj import *
from Constants import Constants as C
import Utils


defaultAreaNwkType = ''


class ANI(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsANI, C.mgdANI, create=create)

		if self.json is not None:
			self.setAttribute('ant', defaultAreaNwkType, overwrite=False)

