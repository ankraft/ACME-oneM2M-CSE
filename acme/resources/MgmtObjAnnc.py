#
#	MgmtObjAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MgmtObj : Announceable variant
#

from ..resources.AnnouncedResource import AnnouncedResource


class MgmtObjAnnc(AnnouncedResource):
	
	def initialize(self, pi: str) -> None:
		# The "mgd" attribute is mandatory must be the unaanounced variant!
		self.setAttribute('mgd', int(self.mgmtType), overwrite=True)
		super().initialize(pi)

