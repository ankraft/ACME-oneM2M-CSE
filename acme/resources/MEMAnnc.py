#
#	MEMAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MEM : Announceable variant
#

from resources.MgmtObjAnnc import *
from etc.Types import ResourceTypes as T, JSON
from services.Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
memAPolicies = constructPolicy([
	'mma', 'mmt'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, memAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class MEMAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = memAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.MEM, create=create, attributePolicies=attributePolicies)

