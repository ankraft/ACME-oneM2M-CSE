#
#	FWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Firmware
#

from __future__ import annotations

from ...etc.Types import AttributePolicyDict, ResourceTypes, Status
from ..MgmtObj import MgmtObj
from ..Resource import Resource


class FWR(MgmtObj):

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	mgmtType = ResourceTypes.FWR
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
		'vr': None,
		'fwn': None,
		'url': None,
		'uds': None,
		'ud': None
	}


	def activate(self, parentResource:Resource, originator: str) -> None:
		self.setAttribute('uds', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		super().activate(parentResource, originator)
