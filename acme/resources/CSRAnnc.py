#
#	CSRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CSR : Announceable variant
#
""" CSR announced (CSRA) resource type. """

from __future__ import annotations

from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..resources.AnnouncedResource import AnnouncedResource


class CSRAnnc(AnnouncedResource):
	""" CSR announced (CSRA) resource type. """

	resourceType = ResourceTypes.CSRAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	ResourceTypes.ACTR, 
									ResourceTypes.ACTRAnnc,  
									ResourceTypes.ACP, 
									ResourceTypes.ACPAnnc,
									ResourceTypes.AEAnnc, 
									ResourceTypes.CNT, 
									ResourceTypes.CNTAnnc, 
									ResourceTypes.CINAnnc, 
									ResourceTypes.CSRAnnc, 
									ResourceTypes.FCNT, 
									ResourceTypes.FCNTAnnc, 
									ResourceTypes.GRP, 
									ResourceTypes.GRPAnnc, 
									ResourceTypes.LCPAnnc,
									ResourceTypes.MGMTOBJAnnc, 
									ResourceTypes.NODAnnc, 
								    ResourceTypes.PRMR,
								    ResourceTypes.PRMRAnnc,
									ResourceTypes.SCHAnnc,
									ResourceTypes.SUB, 
									ResourceTypes.TS, 
									ResourceTypes.TSAnnc, 
									ResourceTypes.TSB, 
									ResourceTypes.TSBAnnc ]
	""" The allowed child-resource types. """


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
		'spi': None,
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
	""" Attributes and `AttributePolicy` for this resource type. """

