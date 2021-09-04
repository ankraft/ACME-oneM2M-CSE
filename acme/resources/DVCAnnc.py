#
#	DVCAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVC : Announceable variant
#

from ..etc.Types import ResourceTypes as T, JSON
from ..services.Validator import constructPolicy, addPolicy
from ..resources.MgmtObjAnnc import *

# Attribute policies for this resource are constructed during startup of the CSE
dvcAPolicies = constructPolicy([
	'can', 'att', 'cas', 'ena', 'dis', 'cus'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, dvcAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class DVCAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = dvcAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.DVC, create=create, attributePolicies=attributePolicies)

