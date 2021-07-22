#
#	DVIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVI : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T, JSON
import Utils
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
dviAPolicies = constructPolicy([
	'dlb', 'man', 'mfdl', 'mfd', 'mod', 'smod', 'dty', 'dvnm', 'fwv', 'swv', 
	'hwv', 'osv', 'cnty', 'loc', 'syst', 'spur', 'purl', 'ptl'
])
attributePolicies =  addPolicy(mgmtObjAAttributePolicies, dviAPolicies)
# TODO resourceMappingRules, announceSyncType, owner

class DVIAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = dviAPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.DVI, create=create, attributePolicies=attributePolicies)

