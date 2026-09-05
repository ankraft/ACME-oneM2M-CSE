#
#	DAC.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: DynamicAuthorizationConsultation
#
""" DynamicAuthorizationConsultation (DAC) resource type. """

from __future__ import annotations
from typing import Optional

from ..resources.Resource import Resource
from ..etc.ACMEUtils import replaceDashInID
from ..etc.Types import JSON

class DAC(Resource):
	""" DynamicAuthorizationConsultation (DAC) resource type. """

	def validate(self, originator: Optional[str]=None, 
					   dct: Optional[JSON]=None, 
					   parentResource: Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)

		# Cleanup identfiers
		self.setAttribute('dap', [replaceDashInID(a) for a in self.dap], overwrite=True)
