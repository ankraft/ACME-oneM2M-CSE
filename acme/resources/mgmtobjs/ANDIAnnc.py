#
#	ANDIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ANDI : Announceable variant
#

""" [AreaNwkDeviceInfo] announced (ANDIA) `MgmtObjAnnc` specialization. """

from __future__ import annotations

from ...etc.Types import AttributePolicyDict, ResourceTypes
from ..MgmtObjAnnc import MgmtObjAnnc

# TODO resourceMappingRules, announceSyncType, owner

class ANDIAnnc(MgmtObjAnnc):
	""" [AreaNwkDeviceInfo] announced (ANDIA) `MgmtObjAnnc` specialization. """

	resourceType = ResourceTypes.MGMTOBJAnnc
	""" The resource type """

	mgmtType = ResourceTypes.ANDI
	""" The management object type """

	typeShortname = mgmtType.announced().typeShortname()
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
		'dvd': None,
		'dvt': None,
		'awi': None,
		'sli': None,
		'sld': None,
		'ss': None,
		'lnh': None
	}

