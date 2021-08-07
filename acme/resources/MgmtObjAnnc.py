#
#	MgmtObjAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MgmtObj : Announceable variant
#

from copy import deepcopy
from resources.AnnouncedResource import AnnouncedResource
from resources.Resource import *
from etc.Types import ResourceTypes as T, JSON, AttributePolicies
from services.Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk'
])
mgmtObjAPolicies = constructPolicy([
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
])
mgmtObjAAttributePolicies =  addPolicy(attributePolicies, mgmtObjAPolicies)
# TODO resourceMappingRules, announceSyncType


class MgmtObjAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB ]


	def __init__(self, dct:JSON, pi:str, mgd:T, create:bool=False, attributePolicies:AttributePolicies=None) -> None:
		super().__init__(T.MGMTOBJAnnc, dct, pi, tpe=f'{mgd.tpe()}A', create=create, attributePolicies=attributePolicies)
		
		self.resourceAttributePolicies:AttributePolicies = deepcopy(self.resourceAttributePolicies)	# We dont want to change the original policy list
		self.resourceAttributePolicies.update(mgmtObjAAttributePolicies)							# add mgmtobjA policies

		self.setAttribute('mgd', int(mgd), overwrite=True)

