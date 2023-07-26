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


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.AEAnnc, dct, pi = pi, create = create)

