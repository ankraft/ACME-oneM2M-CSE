#
#	FCNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" FlexContainerAnnounced resource class """

from __future__ import annotations
from typing import Optional


from ..etc.Types import JSON
from ..resources.AnnouncedResource import AnnouncedResource


class FCNTAnnc(AnnouncedResource):
	""" FlexContainerAnnounced resource class """

	def __init__(self, dct: Optional[JSON]=None, typeShortname: Optional[str]=None, create: Optional[bool]=False) -> None:
		self.typeShortname = typeShortname
		super().__init__(dct, create=create)
