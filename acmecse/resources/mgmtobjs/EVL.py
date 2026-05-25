#
#	EVL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:EventLog
#

from __future__ import annotations
from typing import Optional

from ...etc.Types import JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ..MgmtObj import MgmtObj
from ...helpers.TextTools import findXPath

class EVL(MgmtObj):


	def initialize(self, pi: str) -> None:
		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)
		super().initialize(pi)


	def update(self, dct: Optional[JSON]=None, 
					 originator: Optional[str]=None, 
					 doValidateAttributes: Optional[bool]=True) -> None:
		# Check for rbo & far updates 
		if findXPath(dct, '{*}/lga') and findXPath(dct, '{*}/lgo'):
			raise BAD_REQUEST('update both lga and lgo to True at the same time is not allowed')

		# Always overwrite with True
		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)
		super().update(dct, originator, doValidateAttributes)
