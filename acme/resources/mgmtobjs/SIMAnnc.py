#
#	SIMAnnc.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	SIM : Announceable variant
#

from __future__ import annotations
from typing import Optional

from ...etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..MgmtObjAnnc import MgmtObjAnnc


class SIMAnnc(MgmtObjAnnc):

	resourceType = ResourceTypes.SIMAnnc
	""" The resource type """

	mgmtType = ResourceTypes.SIM
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
		'imsi': None,
		'icid': None,
		'sist': None,
		'sity': None,
		'spn': None,
	}


