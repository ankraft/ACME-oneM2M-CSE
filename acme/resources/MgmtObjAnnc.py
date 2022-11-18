#
#	MgmtObjAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MgmtObj : Announceable variant
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class MgmtObjAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SUB ]


	def __init__(self, dct:JSON, pi:str, mgd:ResourceTypes, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.MGMTOBJAnnc, dct, pi, tpe = mgd.announced().tpe(), create = create)
		self.setAttribute('mgd', int(mgd), overwrite = True)

