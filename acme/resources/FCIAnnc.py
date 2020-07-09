#
#	FCIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	FCI : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from Typoes import ResourceTypes as T


class FCINAnnc.py(AnnouncedResource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.FCIAnnc, jsn, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, [])

		 

