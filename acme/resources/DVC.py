#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#

from .MgmtObj import *
from Constants import Constants as C
import Utils


class DVC(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsDVC, C.mgdDVC, create=create)

		if self.json is not None:
			self.setAttribute('can', 'unknown', overwrite=False)
			self.setAttribute('att', False, overwrite=False)
			self.setAttribute('cas', {	"acn" : "unknown", "sus" : 0 }, overwrite=False)
			self.setAttribute('cus', False, overwrite=False)

