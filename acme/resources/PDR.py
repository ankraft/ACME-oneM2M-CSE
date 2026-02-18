#
#	PDR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PolicyDeletionRules
#

from __future__ import annotations

from ..etc.Types import ResourceTypes
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.ResponseStatusCodes import CONFLICT
from ..runtime.Logging import Logging as L


class PDR(Resource):

	def activate(self, parentResource: Resource, originator: str) -> None:

		# Check if there are less than 2 PDR under the parent NTP
		if len(CSE.dispatcher.retrieveDirectChildResources(pi=parentResource.ri, ty=ResourceTypes.PDR)) > 2:
			raise CONFLICT(L.logDebug(f'Only 2 PDR are allowed under an NTP'))
		super().activate(parentResource, originator)