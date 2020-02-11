#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#

from .MgmtObj import *
from Constants import Constants as C
import Utils

class RBO(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsRBO, C.mgdRBO, create=create)

		if self.json is not None:
			self.setAttribute('rbo', False, overwrite=True)
			self.setAttribute('far', False, overwrite=True)

