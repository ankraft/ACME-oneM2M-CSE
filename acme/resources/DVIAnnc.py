#
#	DVIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVI : Announceable variant
#
from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc import ACMEUtils
from ..resources.MgmtObjAnnc import MgmtObjAnnc

class DVIAnnc(MgmtObjAnnc):

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
		'dlb': None,
		'man': None,
		'mfdl': None,
		'mfd': None,
		'mod': None,
		'smod': None,
		'dty': None,
		'dvnm': None,
		'fwv': None,
		'swv': None,
		'hwv': None,
		'osv': None,
		'cnty': None,
		'loc': None,
		'syst': None,
		'spur': None,
		'purl': None,
		'ptl': None
	}

	
	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.DVI, create = create)

