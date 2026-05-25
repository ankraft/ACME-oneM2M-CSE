#
#	DATC.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:dataCollection
#

from __future__ import annotations
from typing import Optional

from ...etc.Types import JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ...helpers.TextTools import findXPath
from ..MgmtObj import MgmtObj
from ..Resource import Resource
from ...runtime.Logging import Logging as L


class DATC(MgmtObj):

	def validate(self, originator: Optional[str]=None, 
					   dct: Optional[JSON]=None, 
					   parentResource: Optional[Resource]=None) -> None:
		L.isDebug and L.logDebug(f'Validating semanticDescriptor: {self.ri}')
		super().validate(originator, dct, parentResource)

		# Test for unique occurence of either mesc and meil
		mescNew = findXPath(dct, '{*}/mesc')		
		meilNew = findXPath(dct, '{*}/meil')		
		if (mescNew or self.mesc) and (meilNew or self.meil):
			raise BAD_REQUEST(L.logDebug(f'mesc and meil shall not be set together'))
	
