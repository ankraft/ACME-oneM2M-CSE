#
#	VirtualResource.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This module implements the base class for all oneM2M virtual resource types. """

from __future__ import annotations
from typing import TYPE_CHECKING

from ..etc.Types import ResourceTypes, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, NOT_FOUND
from ..resources.Resource import Resource
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher
	from ..services.NotificationManager import NotificationManager

@requires(dispatcher='acmecse.services.Dispatcher')
@requires(notificationManager='acmecse.services.NotificationManager')
class VirtualResource(Resource):
	""" Base class for all oneM2M virtual resource types. 
		It adds methods for virtual resources.
	"""

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	notificationManager: NotificationManager = None
	""" Injected NotificationManager instance. """

	def initialize(self, pi: str) -> None:

		# Virtual resources have a fixed resource name that is provided in the sub-class
		self.setResourceName(self.resourceName)

		super().initialize(pi)


	def retrieveLatestOldest(self, request: CSERequest, 
								   originator: str, 
								   typ: ResourceTypes, 
								   oldest: bool) -> Result:
		""" Retrieve the latest or oldest instance of a container resource.

			Args:
				request: The request
				originator: The originator
				typ: The resource type of the instances
				oldest: Whether to retrieve the oldest instance

			Returns:
				The result of the operation.
		"""

		if not (resource := self.dispatcher.retrieveLatestOldestInstance(self.pi, typ, oldest=oldest)):
			raise NOT_FOUND(f'no instance for <{"oldest" if oldest else "latest"}>')

		# Take the resource, either a FCIN or self and check whether a blocking RETRIEVE
		# is necessary
		# EXPERIMENTAL
		self.notificationManager.checkPerformBlockingRetrieve(resource, 
															  request, 
															  finished=lambda: self.dbReloadDict())

		# Then retrieve the latest instance resource again(!) because it might have changed during the 
		# blocking RETRIEVE
		if not (resource := self.dispatcher.retrieveLatestOldestInstance(self.pi, typ, oldest=oldest)):
			raise NOT_FOUND(f'no instance for <{"oldest" if oldest else "latest"}>')
		
		# Do again some checks with the final resource, but no subscription checks! (we did this already)
		resource.willBeRetrieved(originator, request, subCheck=False)
		
		return Result(rsc=ResponseStatusCode.OK, resource=resource)

