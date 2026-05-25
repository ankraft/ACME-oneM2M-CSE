#
#	SWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Software
#

from __future__ import annotations

from ...etc.Types import Status
from ..MgmtObj import MgmtObj
from ..Resource import Resource


class SWR(MgmtObj):

	def activate(self, parentResource: Resource, originator: str) -> None:
		self.setAttribute('ins', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		self.setAttribute('acts', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		self.setAttribute('in', False, overwrite = False)
		self.setAttribute('un', False, overwrite = False)
		self.setAttribute('act', False, overwrite = False)
		self.setAttribute('dea', False, overwrite = False)
		super().activate(parentResource, originator)

