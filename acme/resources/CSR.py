#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#

from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T
from Configuration import Configuration
from .Resource import *

class CSR(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, rn: str = None, create: bool = False) -> None:
		super().__init__(T.CSR, jsn, pi, rn=rn, create=create)

		if self.json is not None:
			self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
			self['ri'] = self.csi.split('/')[-1]				# overwrite ri (only after /'s')
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource : Resource) -> bool:
		return super()._canHaveChild(resource,
									 [ T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.ACP,
									   T.SUB
									 ])


	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator), create)[0] == False:
			return res
		self.normalizeURIAttribute('poa')
		return True, C.rcOK, None
