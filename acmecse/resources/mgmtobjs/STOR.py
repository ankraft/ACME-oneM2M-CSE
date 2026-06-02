#
#	STOR.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Storage
#
""" MgmtObj:Storage (STOR) resource type."""

from __future__ import annotations
from typing import Optional

from ...etc.Types import JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ...helpers.TextTools import findXPath
from ..MgmtObj import MgmtObj
from ..Resource import Resource
from ...runtime.Logging import Logging as L


class STOR(MgmtObj):
	""" MgmtObj:Storage (STOR) resource type. """

	def initialize(self, pi: str) -> None:
		self.setAttribute('avaSe', 0, overwrite=False)
		self.setAttribute('totSe', 0, overwrite=False)
		self.setAttribute('write', False, overwrite=False)
		super().initialize(pi)

	def update(self, dct: Optional[JSON] = None, 
					 originator: Optional[str] = None, 
					 doValidateAttributes: Optional[bool] = True) -> None:
		
		super().update(dct, originator, doValidateAttributes)
		
		# Check for formt & unmot updates 
		formt = findXPath(dct, '{*}/formt')
		unmot = findXPath(dct, '{*}/unmot')
		if formt is not None and unmot is not None:
			raise BAD_REQUEST('formt and unmot cannot be updated at the same time')
		if formt == True:
			L.isDebug and L.logDebug(f'Initiated format')
		if unmot == True:
			L.isDebug and L.logDebug(f'Initiated unmount')



	def validate(self, originator: Optional[str] = None, 
					   dct: Optional[JSON] = None, 
					   parentResource: Optional[Resource] = None) -> None:
		L.isDebug and L.logDebug(f'Validating timeSeriesBeacon: {self.ri}')
		super().validate(originator, dct, parentResource)
		
		if self.stoTe and self.stoTe not in [0, 1]:
			raise BAD_REQUEST(f'stoTe must be either 0 or 1')
		if self.stoPe and self.stoPe not in [0, 1]:
			raise BAD_REQUEST(f'stoPe must be either 0 or 1')
		if self.sus and self.sus not in [0, 1]:
			raise BAD_REQUEST(f'sus must be either 0 or 1')


