#
#	CSRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CSR : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy

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

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CSRAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource,
									 [ T.CNT,
									   T.CNTAnnc,
									   T.CINAnnc,
									   T.FCNT,
									   T.FCNTAnnc,
									   T.GRP,
									   T.GRPAnnc,
									   T.ACP,
									   T.ACPAnnc,
									   T.SUB,
									   T.CSRAnnc,
									   T.MGMTOBJAnnc,
									   T.NODAnnc,
									   T.AEAnnc
									 ])

