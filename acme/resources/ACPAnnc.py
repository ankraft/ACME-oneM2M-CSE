#
#	ACPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Acp : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from Types import ResourceTypes as T



class CPAnnc.py(AnnouncedResource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.ACPAnnc, jsn, pi=pi, create=create)


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
