#
#	CSRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CSR : Announceable variant
#


from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *


class CSRAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	T.ACTR, T.ACTRAnnc,  T.CNT, T.CNTAnnc, T.CINAnnc, T.FCNT, T.FCNTAnnc, T.GRP, T.GRPAnnc, T.ACP, T.ACPAnnc,
									T.SUB, T.TS, T.TSAnnc, T.CSRAnnc, T.MGMTOBJAnnc, T.NODAnnc, T.AEAnnc, T.TSB, T.TSBAnnc ]


	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes for announced resources
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'acpi':None,
		'daci': None,
		'ast': None,
		'loc': None,
		'lnk': None,
	
		# Resource attributes
		'cst': None,
		'poa': None,
		'cb': None,
		'csi': None,
		'rr': None,
		'nl': None,
		'csz': None,
		'esi': None,
		'dcse': None,
		'egid': None,
		'mtcc': None,
		'tren': None,
		'ape': None,
		'srv': None
	}
		

	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.CSRAnnc, dct, pi = pi, create = create)


