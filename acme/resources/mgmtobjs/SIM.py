#
#	SIM.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:SIM from TS-0022
#

from __future__ import annotations

from ...etc.Types import AttributePolicyDict, ResourceTypes
from ..MgmtObj import MgmtObj


class SIM(MgmtObj):

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	mgmtType = ResourceTypes.SIM
	""" The management object type """

	typeShortname = mgmtType.typeShortname()
	"""	The resource's domain and type name. """

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'cstn': None,
		'acpi':None,
		'at': None,
		'aa': None,
		'ast': None,
		'daci': None,
		
		# MgmtObj attributes
		'mgd': None,
		'obis': None,
		'obps': None,
		'dc': None,
		'mgs': None,
		'cmlk': None,

		# Resource attributes
		'imsi': None,
		'icid': None,
		'sist': None,
		'sity': None,
		'spn': None,
	}
	
	
	
