#
#	GRPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	GRP : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T, JSON


class NODAnnc(AnnouncedResource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.NODAnnc, dct, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, 
									[ T.MGMTOBJAnnc,
									  T.SUB
									])


