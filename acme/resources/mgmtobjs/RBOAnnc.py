#
#	RBOAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	RBO : Announceable variant
#
""" MgmtObj:Reboot announced (RBOA) resource type. """

from __future__ import annotations

from ...etc.Types import AttributePolicyDict, ResourceTypes
from ..MgmtObjAnnc import MgmtObjAnnc


class RBOAnnc(MgmtObjAnnc):
	""" MgmtObj:Reboot announced (RBOA) resource type. """

	resourceType = ResourceTypes.MGMTOBJAnnc
	""" The resource type """

	mgmtType = ResourceTypes.RBO
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
		'rbo': None,
		'far': None
	}
	""" The allowed attributes and their policy for this resource type."""


