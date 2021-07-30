#
#	AEAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	AE : Announceable variant
#

from etc.Types import ResourceTypes as T, JSON
from resources.AnnouncedResource import AnnouncedResource
from resources.Resource import *
from services.Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk'
])
aeAPolicies = constructPolicy([
	'apn', 'api', 'aei', 'poa', 'regs', 'trps', 'or', 'rr', 'nl', 'csz', 'esi', 'tren', 'scp', 'srv', 'ape', 'mei', 
])
attributePolicies =  addPolicy(attributePolicies, aeAPolicies)
# TODO announceSyncType


class AEAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.ACP, T.ACPAnnc, T.CNT, T.CNTAnnc, T.FCNT, T.FCNTAnnc, T.GRP, T.GRPAnnc, T.TS, T.TSAnnc ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.AEAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)

