#
#	ANDIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ANDI : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T, JSON
import Utils
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
andiAPolicies = constructPolicy([
	'dvd', 'dvt', 'awi', 'sli', 'sld', 'ss', 'lnh'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, andiAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class ANDIAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = andiAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.ANDI, create=create, attributePolicies=attributePolicies)

