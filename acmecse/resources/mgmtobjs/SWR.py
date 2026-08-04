#
#	SWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Software
#

from __future__ import annotations
from typing import Optional

from ...etc.Types import Status, CSERequest
from ..MgmtObj import MgmtObj
from ..Resource import Resource


class SWR(MgmtObj):

	def activate(self, parentResource: Resource, originator: str, request: Optional[CSERequest] = None) -> None:
		self.setAttribute('ins', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		self.setAttribute('acts', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		self.setAttribute('in', False, overwrite=False)
		self.setAttribute('un', False, overwrite=False)
		self.setAttribute('act', False, overwrite=False)
		self.setAttribute('dea', False, overwrite=False)
		super().activate(parentResource, originator, request)

