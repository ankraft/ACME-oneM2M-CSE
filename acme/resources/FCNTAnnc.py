#
#	FCNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	FCNT : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T


class FCNTAnnc(AnnouncedResource):

	def __init__(self, dct:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.FCNTAnnc, dct, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.CNT,
									   T.CNTAnnc,
									   T.CIN,
									   T.CINAnnc,
									   T.FCNT,
									   T.FCNTAnnc,
									   T.FCI,
									   T.FCIAnnc,
									   T.SUB
									 ])

		 

