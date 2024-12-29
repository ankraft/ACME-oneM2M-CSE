#
#	MgmtObjAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MgmtObj : Announceable variant
#

from __future__ import annotations

from ..etc.Types import ResourceTypes
from ..resources.AnnouncedResource import AnnouncedResource


class MgmtObjAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SUB ]

	
	def initialize(self, pi:str, originator:str) -> None:
		# The "mgd" attribute is mandatory must be the unaanounced variant!
		self.setAttribute('mgd', int(self.mgmtType), overwrite = True)
		super().initialize(pi, originator)

