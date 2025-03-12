#
#	DVI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceInfo
#

from __future__ import annotations

from ...etc.Types import AttributePolicyDict, ResourceTypes
from ..MgmtObj import MgmtObj

class DVI(MgmtObj):

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	mgmtType = ResourceTypes.DVI
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


