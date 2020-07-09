#
#	CNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CNT : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from Typoes import ResourceTypes as T



class CNTAnnc.py(AnnouncedResource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.CNTAnnc, jsn, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.CNT,
									   T.CNTAnnc
									   T.CIN,
									   T.CINAnnc,
									   T.FCNT,
									   T.FCNTAnnc,
									   T.SUB
									 ])

