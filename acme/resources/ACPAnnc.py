#
#	ACPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Acp : Announceable variant
#

from resources.AnnouncedResource import AnnouncedResource
from resources.Resource import *
from etc.Types import ResourceTypes as T, Permission, JSON
from services.Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk'
])
acpAPolicies = constructPolicy([
	'pv', 'pvs', 'adri', 'apri', 'airi',
])
attributePolicies =  addPolicy(attributePolicies, acpAPolicies)
# TODO announceSyncType


class ACPAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.ACPAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)


	def checkSelfPermission(self, origin:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == Permission.NONE:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor']:
				return True
		return False
