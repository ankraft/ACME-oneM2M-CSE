#
#	CSRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CSR : Announceable variant
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
csrAPolicies = constructPolicy([
	'cst', 'poa', 'cb', 'csi', 'rr', 'nl', 'csz', 'esi', 'dcse', 'mtcc', 'egid', 'tren', 'ape', 'srv'
])
attributePolicies =  addPolicy(attributePolicies, csrAPolicies)
# TODO announceSyncType


class CSRAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.CNT, T.CNTAnnc, T.CINAnnc, T.FCNT, T.FCNTAnnc, T.GRP, T.GRPAnnc, T.ACP, T.ACPAnnc,
								T.SUB, T.TS, T.TSAnnc, T.CSRAnnc, T.MGMTOBJAnnc, T.NODAnnc, T.AEAnnc ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CSRAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)


