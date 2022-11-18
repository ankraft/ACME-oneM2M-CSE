#
#	WIFI.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:WifiClient
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, Result
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource


class WIFIC(MgmtObj):

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
		'ssid': None,
		'wcrds': None,
		'maca': None,
		'chanl': None,
		'cons': None,
		'scan': None,
		'scanr': None,
		'ud': None,
		'uds': None,
		'trdst': None,
		'rdst': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.WIFIC, create = create)

		self.setAttribute('ssi', '', overwrite = False)
		self.setAttribute('scan', False)
		self.setAttribute('scanr', [])
		self.setAttribute('ud', False)
		self.setAttribute('trdst', False)
		self.setAttribute('rdst', False)


	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		if self.wcrds:
			enct = self.attribute('wcrds/enct')
			unm = self.attribute('wcrds/unm')
			pwd = self.attribute('wcrds/pwd')
			wepk = self.attribute('wcrds/wepk')
			wpap = self.attribute('wcrds/wpap')

			if (unm or pwd) and not enct in [ 6, 7, 8 ]:
				return Result.errorResult(dbg = f'unm and pwd is only allowed for enct = 6, 7, or 8')
			if enct in [ 6, 7, 8 ] and not (unm or pwd):
				return Result.errorResult(dbg = f'unm and pwd must be present for enct = 6, 7, or 8')

			if wepk and enct != 2:
				return Result.errorResult(dbg = f'wepk is only allowed for enct = 2')
			if enct == 2 and not wepk:
				return Result.errorResult(dbg = f'wepk must be present for enct = 2')

			if wpap and not enct in [ 3, 4, 5 ]:
				return Result.errorResult(dbg = f'wpap is only allowed for enct = 3, 4, or 5')
			if enct in [ 3, 4, 5 ] and not wpap:
				return Result.errorResult(dbg = f'wpap must be present for enct = 3, 4, or 5')

		self.setAttribute('trdst', False)	# always set (back) to False
		self.setAttribute('rdst', False)	# always set (back) to False
		return Result.successResult()