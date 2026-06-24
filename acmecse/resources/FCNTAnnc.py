#
#	FCNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" FlexContainerAnnounced resource class """

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..resources.AnnouncedResource import AnnouncedResource
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..runtime.Logging import Logging as L

if TYPE_CHECKING:
	from ..resources.Resource import Resource
	from ..etc.Types import JSON

class FCNTAnnc(AnnouncedResource):
	""" FlexContainerAnnounced resource class """

	def __init__(self, dct: Optional[JSON] = None, typeShortname: Optional[str] = None, create: Optional[bool] = False) -> None:
		self.typeShortname = typeShortname
		"""	Shortname of the flexContainer type. """

		super().__init__(dct, create=create)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# Validate containerDefinition
		if (t := self.validator.getFlexContainerSpecialization(self.typeShortname)):
			if t[0] and t[0] != self.cnd:
				raise BAD_REQUEST(L.logDebug(f'Wrong cnd: {self.cnd} for specialization: {self.typeShortname}. Must be: {t[0]}'))
