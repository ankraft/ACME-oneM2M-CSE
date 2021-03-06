#
#	ACPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Acp : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T, Permission



class ACPAnnc(AnnouncedResource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.ACPAnnc, jsn, pi=pi, create=create)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, [ T.SUB ])


	def checkSelfPermission(self, origin:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == Permission.NONE:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor']:
				return True
		return False
