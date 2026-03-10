#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#
""" MgmtObj:Reboot (RBO) resource type."""

from __future__ import annotations
from typing import Optional

from ..MgmtObj import MgmtObj
from ..Resource import Resource
from ...etc.Types import JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ...helpers.TextTools import findXPath

class RBO(MgmtObj):
	""" MgmtObj:Reboot (RBO) resource type. """
	
	def initialize(self, pi: str) -> None:
		self.setAttribute('rbo', False, overwrite=True)	# always False
		self.setAttribute('far', False, overwrite=True)	# always False
		super().initialize(pi)


	#
	#	Handling the special behaviour for rbo and far attributes in 
	#	validate() and update()
	#

	def validate(self, originator: Optional[str]=None, 
					   dct: Optional[JSON]=None, 
					   parentResource: Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)
		self.setAttribute('rbo', False, overwrite=True)	# always set (back) to False
		self.setAttribute('far', False, overwrite=True)	# always set (back) to False


	def update(self, dct: Optional[JSON]=None, 
					 originator: Optional[str]=None, 
					 doValidateAttributes: Optional[bool]=True) -> None:
		# Check for rbo & far updates 
		rbo = findXPath(dct, '{*}/rbo')
		far = findXPath(dct, '{*}/far')
		if rbo and far:
			raise BAD_REQUEST('update both rbo and far to True is not allowed')

		super().update(dct, originator, doValidateAttributes)
