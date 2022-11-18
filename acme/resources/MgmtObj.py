#
#	MgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ManagementObject (base class for specializations)
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import ResourceTypes, JSON
from ..resources.AnnounceableResource import AnnounceableResource


class MgmtObj(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SMD, 
								   ResourceTypes.SUB ]

	def __init__(self, dct:JSON, pi:str, mgd:ResourceTypes, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.MGMTOBJ, dct, pi, tpe = mgd.tpe(), create=create)
		self.setAttribute('mgd', int(mgd), overwrite=True)

