#
#	EVLAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	EVL : Announceable variant
#

from ..etc.Types import ResourceTypes as T, JSON
from ..services.Validator import constructPolicy, addPolicy
from ..resources.MgmtObjAnnc import *

# Attribute policies for this resource are constructed during startup of the CSE
evlAPolicies = constructPolicy([
	'lgt', 'lgd', 'lgst', 'lga', 'lgo'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, evlAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class EVLAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = evlAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.EVL, create=create, attributePolicies=attributePolicies)

