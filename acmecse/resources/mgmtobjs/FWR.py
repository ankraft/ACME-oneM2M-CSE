#
#	FWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Firmware
#

from __future__ import annotations
from typing import Optional

from ...etc.Types import Status, CSERequest
from ..MgmtObj import MgmtObj
from ..Resource import Resource


class FWR(MgmtObj):

	def activate(self, parentResource: Resource, originator: str, request: Optional[CSERequest] = None) -> None:
		self.setAttribute('uds', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		super().activate(parentResource, originator, request)
