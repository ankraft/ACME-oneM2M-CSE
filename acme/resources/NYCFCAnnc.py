#
#	NYCFCnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	NYCFC : Announceable variant
#

from ..etc.Types import ResourceTypes as T, JSON
from ..services.Validator import constructPolicy, addPolicy
from ..resources.MgmtObjAnnc import *

# Attribute policies for this resource are constructed during startup of the CSE
nycfcAPolicies = constructPolicy([
	'suids', 'mcff', 'mcfc'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, nycfcAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class NYCFCAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = nycfcAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.NYCFC, create=create, attributePolicies=attributePolicies)

