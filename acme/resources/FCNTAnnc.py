#
#	FCNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	FCNT : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from Typoes import ResourceTypes as T



class FCNTAnnc.py(AnnouncedResource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.FCNTAnnc, jsn, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.CNT,
									   T.CNTAnnc
									   T.CIN,
									   T.CINAnnc,
									   T.FCNT,
									   T.FCNTAnnc,
									   T.FCIN,
									   T.FCINAnnc,
									   T.SUB
									 ])

		 

