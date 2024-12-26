#
#	AEAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Application Entity announced (AEA) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource

class AEAnnc(AnnouncedResource):
	""" Application Entity announced (AEA) resource type """

	resourceType = ResourceTypes.AEAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.ACP,
													   ResourceTypes.ACPAnnc,
													   ResourceTypes.ACTR,
													   ResourceTypes.ACTRAnnc,
													   ResourceTypes.CNT,
													   ResourceTypes.CNTAnnc,
													   ResourceTypes.FCNT, 
													   ResourceTypes.FCNTAnnc, 
													   ResourceTypes.GRP, 
													   ResourceTypes.GRPAnnc,
													   ResourceTypes.LCPAnnc,
													   ResourceTypes.PRMRAnnc,
													   ResourceTypes.TS, 
													   ResourceTypes.TSAnnc ]

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
			'lnk': None,
			'ast': None,

			'loc': None,	

				
			# Resource attributes
			'apn': None,
			'api': None,
			'aei': None,
			'poa': None,
			'nl': None,
			'rr': None,
			'csz': None,
			'esi': None,
			'mei': None,
			'srv': None,
			'regs': None,
			'trps': None,
			'scp': None,
			'tren': None,
			'ape': None,
			'or': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


