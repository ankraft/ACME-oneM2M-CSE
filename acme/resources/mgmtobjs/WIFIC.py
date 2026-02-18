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

from ...etc.Types import JSON, Status
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ..MgmtObj import MgmtObj
from ..Resource import Resource


class WIFIC(MgmtObj):

	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)
		self.setAttribute('ssi', '', overwrite = False)
		self.setAttribute('scan', False)
		self.setAttribute('scan', False)
		self.setAttribute('scanr', [])
		self.setAttribute('ud', False)
		self.setAttribute('trdst', False)
		self.setAttribute('rdst', False)
		self.setAttribute('uds', { 'acn' : '', 'sus' : Status.UNINITIALIZED }, False)


	def validate(self, originator: Optional[str]=None, 
					   dct: Optional[JSON]=None, 
					   parentResource: Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)
		if self.wcrds:
			enct = self.attribute('wcrds/enct')
			unm = self.attribute('wcrds/unm')
			pwd = self.attribute('wcrds/pwd')
			wepk = self.attribute('wcrds/wepk')
			wpap = self.attribute('wcrds/wpap')

			if (unm or pwd) and not enct in [ 6, 7, 8 ]:
				raise BAD_REQUEST(f'unm and pwd is only allowed for enct = 6, 7, or 8')
			if enct in [ 6, 7, 8 ] and not (unm or pwd):
				raise BAD_REQUEST(f'unm and pwd must be present for enct = 6, 7, or 8')

			if wepk and enct != 2:
				raise BAD_REQUEST(f'wepk is only allowed for enct = 2')
			if enct == 2 and not wepk:
				raise BAD_REQUEST(f'wepk must be present for enct = 2')

			if wpap and not enct in [ 3, 4, 5 ]:
				raise BAD_REQUEST(f'wpap is only allowed for enct = 3, 4, or 5')
			if enct in [ 3, 4, 5 ] and not wpap:
				raise BAD_REQUEST(f'wpap must be present for enct = 3, 4, or 5')

		self.setAttribute('trdst', False)	# always set (back) to False
		self.setAttribute('rdst', False)	# always set (back) to False