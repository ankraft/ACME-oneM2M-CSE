#
#	AEAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Application Entity announced (AEA) resource type """

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *


class AEAnnc(AnnouncedResource):
	""" Application Entity announced (AEA) resource type """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ T.ACP, T.ACPAnnc, T.ACTR, T.ACTRAnnc, T.CNT, T.CNTAnnc, T.FCNT, T.FCNTAnnc, T.GRP, T.GRPAnnc, T.TS, T.TSAnnc ]

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
	"""	Attributes and `AttributePolicy' for this resource type. """


	def __init__(self, dct:JSON=None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.AEAnnc, dct, pi = pi, create = create)

