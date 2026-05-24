#
#	FCIAnnc.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CIN : Announceable variant
#
"""  FlexContainerInstance announced (FCIA) resource type."""

from __future__ import annotations
from typing import Optional
from ..etc.Types import JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED


class FCIAnnc(AnnouncedResource):
	""" FlexContainerInstance announced (FCIA) resource type. """


	# Forbidd updating
	def update(self, dct: Optional[JSON]=None, 
					 originator: Optional[str]=None,
					 doValidateAttributes: Optional[bool]=True) -> None:
		raise OPERATION_NOT_ALLOWED('updating FCIAnnc is forbidden')

