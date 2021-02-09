#
#	BATAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	BAT : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T, JSON
import Utils
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
batAPolicies = constructPolicy([
	'btl', 'bts'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, batAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class BATAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = batAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.BAT, create=create, attributePolicies=attributePolicies)

