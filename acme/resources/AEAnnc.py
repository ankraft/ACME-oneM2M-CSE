#
#	AEAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	AE : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T



class AEAnnc(AnnouncedResource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.AEAnnc, jsn, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.ACP,
									   T.ACPAnnc,
									   T.CNT,
									   T.CNTAnnc,
									   T.FCNT,
									   T.FCNTAnnc,
									   T.GRP,
									   T.GRPAnnc
									 ])
