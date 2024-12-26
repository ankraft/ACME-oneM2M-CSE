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
from ..resources.Resource import Resource


class MgmtObj(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SMD, 
								   ResourceTypes.SUB ]

	def __init__(self, dct:JSON, pi:str, mgd:ResourceTypes) -> None:
		super().__init__(dct, pi, typeShortname = mgd.typeShortname())
		self.setAttribute('mgd', int(mgd), overwrite=True)
	

	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

