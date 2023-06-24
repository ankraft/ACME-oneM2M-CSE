#
#	AnnouncedResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announced resources
#

from typing import Optional
from ..etc.Types import AnnounceSyncType, ResourceTypes, JSON, CSERequest, Operation
from ..etc.ResponseStatusCodes import ResponseException
from ..resources.Resource import Resource
from ..services import CSE
from ..services.Logging import Logging as L


class AnnouncedResource(Resource):

	def __init__(self, ty:ResourceTypes, 
					   dct:JSON, 
					   pi:Optional[str] = None,
					   tpe:Optional[str] = None, 
					   inheritACP:Optional[bool] = False, 
					   create:Optional[bool] = False,) -> None:
		super().__init__(ty, dct, pi, tpe = tpe, inheritACP = inheritACP, create = create)


	def updated(self, dct:Optional[JSON] = None, originator:Optional[str] = None) -> None:
		"""	Check whether we need to update the original resource.

			Args:
				dct: JSON dict with the updated data
				originator: Request originator
		"""
		super().updated(dct, originator)

		# Check whether the original resource needs to be updated
		if (ast := self.ast) is not None and ast == AnnounceSyncType.BI_DIRECTIONAL:
			L.isDebug and L.logDebug('Updating original resource')
			content:JSON = {}
			content[ResourceTypes(self.ty).fromAnnounced().tpe()] = dct[self.tpe]	# take only the resource attributes and assign to the non-announced version
			try:
				CSE.request.handleSendRequest(CSERequest(op = Operation.UPDATE, 
														 to = self.lnk, 
														 originator = CSE.cseCsi, 
														 pc = content))
			except ResponseException as e:
				L.isWarn and L.logWarn(f'Cannot update original resource on remote CSE: {self.lnk} : {e.dbg}')
				return
