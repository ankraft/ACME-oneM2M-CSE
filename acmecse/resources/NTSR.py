#
#	NTSR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: NotificationTargetSelfReference virtual resource
#
"""	Implementation of the NotificationTargetSelfReference (NTSR) virtual resource type. """

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import CSERequest, Result
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException, OPERATION_NOT_ALLOWED
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires
from ..resources.VirtualResource import VirtualResource
from ..resources.Resource import addToInternalAttributes

if TYPE_CHECKING:
	from ..services.NotificationManager import NotificationManager

# Add to internal attributes to ignore in validation etc
addToInternalAttributes(Constants.attrPCUAggregate)	


@requires(notificationManager='acmecse.services.NotificationManager')
class NTSR(VirtualResource):
	"""	Class for the NotificationTargetSelfReference (NTSR) virtual resource type. """

	notificationManager: NotificationManager = None
	"""	Injected NotificationManager instance. """


	# Disallowing CREATE is handled in the handleCreateRequest() method in Dispatcher

	def handleRetrieveRequest(self, request: Optional[CSERequest] = None, 
									id: Optional[str] = None, 
									originator: Optional[str] = None) -> Result:
		raise OPERATION_NOT_ALLOWED(L.logDebug(f'RETRIEVE not allowed for {self.typeShortname} resource'))


	def handleUpdateRequest(self, request: Optional[CSERequest] = None, 
									id: Optional[str] = None, 
									originator: Optional[str]=None) -> Result:
		raise OPERATION_NOT_ALLOWED(L.logDebug(f'UPDATE not allowed for {self.typeShortname} resource'))


	def handleDeleteRequest(self, request: Optional[CSERequest] = None, 
									id: Optional[str] = None, 
									originator: Optional[str] = None) -> Result:
			
		try:
			self.notificationManager.removeNotificationTarget(self, originator)
		except ResponseException as e:
			return Result(rsc=e.rsc, dbg=e.dbg, request=request)

		return Result(rsc=ResponseStatusCode.DELETED, resource=None, request=request)

