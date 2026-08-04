#
#	PDR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PolicyDeletionRules
#
"""	Implementation of the PolicyDeletionRules (PDR) resource type. """

from __future__ import annotations

from typing import TYPE_CHECKING, Optional	

from ..etc.Types import ResourceTypes, CSERequest
from ..resources.Resource import Resource
from ..etc.ResponseStatusCodes import CONFLICT
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher


@requires(dispatcher='acmecse.services.Dispatcher')
class PDR(Resource):
	"""	Class for the PolicyDeletionRules (PDR) resource type. """

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	def activate(self, parentResource: Resource, originator: str, request: Optional[CSERequest] = None) -> None:

		# Check if there are less than 2 PDR under the parent NTP
		if len(self.dispatcher.retrieveDirectChildResources(pi=parentResource.ri, ty=ResourceTypes.PDR)) > 2:
			raise CONFLICT(L.logDebug(f'Only 2 PDR are allowed under an NTP'))
		super().activate(parentResource, originator, request)