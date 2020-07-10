#
#	MgmtObjAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MgmtObj : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from Types import ResourceTypes as T


class MgmtObjAnnc(AnnouncedResource):

	def __init__(self, jsn: dict, pi: str, mgd: T, create: bool = False) -> None:
		super().__init__(T.MGMTOBJ, jsn, pi, tpe='%sA' % mgd.tpe(), create=create)
		
		if self.json is not None:
			self.setAttribute('mgd', int(mgd), overwrite=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.SUB
									 ])

		 

