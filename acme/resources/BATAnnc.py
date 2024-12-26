#
#	BATAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	BAT : Announceable variant
#
""" [BatteryAnnc] (BATA) management object specialization """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.MgmtObjAnnc import MgmtObjAnnc


class BATAnnc(MgmtObjAnnc):
	""" [BatteryAnnc] (BATA) management object specialization """

	resourceType = ResourceTypes.MGMTOBJAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	
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
		'lnk': None,

		# MgmtObj attributes
		'mgd': None,
		'obis': None,
		'obps': None,
		'dc': None,
		'mgs': None,
		'cmlk': None,

			# Resource attributes
			'btl': None,
			'bts': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.BAT)

