#
#	FWRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	FWR : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T, JSON
import Utils
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
fwrAPolicies = constructPolicy([
	'vr', 'fwn', 'url', 'uds', 'ud'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, fwrAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class FWRAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = fwrAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.FWR, create=create, attributePolicies=attributePolicies)

