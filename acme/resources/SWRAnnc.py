#
#	SWRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	SWR : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T, JSON
import Utils
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
swrAPolicies = constructPolicy([
	'vr', 'swn', 'url', 'ins', 'acts', 'in', 'un', 'act', 'dea'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, swrAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class SWRAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = swrAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.SWR, create=create, attributePolicies=attributePolicies)

