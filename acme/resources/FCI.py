#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""  FlexContainerInstance (FCI) resource type."""

from __future__ import annotations
from typing import Optional

from ..etc.Types import JSON
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED
from ..resources.AnnounceableResource import AnnounceableResource


class FCI(AnnounceableResource):
	""" FlexContainerInstance (FCI) resource type. """

	def __init__(self, dct:	Optional[JSON]=None, 
			  		   typeShortname: Optional[str]=None, 
					   create: Optional[bool]=False) -> None:
		self.typeShortname = typeShortname
		super().__init__(dct, create = create)


	# Forbidd updating
	def update(self, dct: Optional[JSON]=None, 
					 originator: Optional[str]=None,
					 doValidateAttributes: Optional[bool]=True) -> None:
		raise OPERATION_NOT_ALLOWED('updating FCI is forbidden')

