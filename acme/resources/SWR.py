#
#	SWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Software
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, Status
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource


class SWR(MgmtObj):

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
		'swn': None,
		'url': None,
		'ins': None,
		'acts': None,
		'in': None,
		'un': None,
		'act': None,
		'dea': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.SWR, create = create)



	def activate(self, parentResource:Resource, originator: str) -> None:
		super().activate(parentResource, originator)
		self.setAttribute('uds', { 'acn' : '', 'sus' : Status.UNINITIALIZED })

		self.setAttribute('ins', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		self.setAttribute('acts', { 'acn' : '', 'sus' : Status.UNINITIALIZED })
		self.setAttribute('in', False, overwrite = False)
		self.setAttribute('un', False, overwrite = False)
		self.setAttribute('act', False, overwrite = False)
		self.setAttribute('dea', False, overwrite = False)

