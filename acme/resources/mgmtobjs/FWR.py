#
#	FWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Firmware
#

from __future__ import annotations

from ...etc.Types import Status
from ..MgmtObj import MgmtObj
from ..Resource import Resource


class FWR(MgmtObj):

	def activate(self, parentResource: Resource, originator: str) -> None:
		self.setAttribute('uds', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		super().activate(parentResource, originator)
