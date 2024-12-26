#
#	FWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Firmware
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, Status
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource


class FWR(MgmtObj):

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	typeShortname = resourceType.typeShortname()
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


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.FWR)


	def activate(self, parentResource:Resource, originator: str) -> None:
		super().activate(parentResource, originator)
		self.setAttribute('uds', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
