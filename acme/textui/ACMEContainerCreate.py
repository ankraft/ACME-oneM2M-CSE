#
#	ACMEContaineCreate.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Create* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast

from textual.app import ComposeResult
from textual.containers import Container
from .ACMEViewResponse import ACMEViewResponse
from .ACMEViewRequest import ACMEViewRequest

from ..etc.Types import Operation, ResourceTypes
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.ResourceSemaphore import CriticalSection, inCriticalSection
from ..resources.Resource import Resource


class ACMEContainerCreate(Container):
	"""	The *Create* view for the ACME text UI.
		This is a container that contains the *Create* request view and the response view.
	"""

	BINDINGS = [('c', 'show_request', 'cURL command')]
	"""	Key bindings for the *Create* view. """

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""

		super().__init__(id = id)

		self.requestOriginator = RC.cseOriginator
		"""	The request originator. """

		self.resource:Resource = None
		"""	The current resource under which a new resource will be created. """

		self.responseView:ACMEViewResponse = ACMEViewResponse(id = 'request-create-response')
		"""	The response view. """


		self.requestView:ACMEViewRequest = ACMEViewRequest(id = 'request-create-request', 
													 	   title = 'CREATE Request',
													 	   header = 'Add a new child resource.',
														   originator = self.requestOriginator,
														   buttonLabel = 'CREATE Resource',
														   callback = self.doCreate,
														   operation = Operation.CREATE,
														   selectCallback = self.selectChangedCallback,
														   responseView = self.responseView)
		"""	The request view. """


	def compose(self) -> ComposeResult:
		"""	Build the *Update* view.

			Return:
				The composed view.
		"""
		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		yield self.requestView
		yield self.responseView


	def updateResource(self, resource:Resource) -> None:
		"""	Update the resource to update.

			Args:
				resource:	The resource to update.
		"""
		self.resource = resource

		# Check whether we are currently doing a resource request (below). If so, return and don't update the editor.
		if inCriticalSection('tuiRequest'):
			return

		# Set the parent resource as the originator
		self.requestOriginator = self.resource.getOriginator()

		# Set the child resource types
		try:
			self.requestView.childResources.set_options([ (ResourceTypes.fullname(t), t)
														for t in self.resource._allowedChildResourceTypes
														if ResourceTypes.isRequestCreatable(t) and not ResourceTypes.isAnnounced(t)])
		except:
			pass

		# Update the request view
		self.requestView.updateResourceView(self.resource, 
									  		resourceType = None, 
											requestOriginator = self.requestOriginator)
		self.responseView.clear()


	def doCreate(self) -> None:
		"""	Handle the *Send CREATE Request* button event.
		"""

		# Send the request and handle the response
		if self.requestView.runRequest(self.resource):

			# The following is a critical section, because the resource tree has to be updated
			# but we don't want to update the editor. The 'updateResource()' method would do that.
			# There is a check for the critical section in the 'updateResource()' method above.
			with CriticalSection('tuiRequest', timeout = 0.0): 
				self._app.containerTree.refreshCurrentNode()
				self._app.containerTree.updateResource(self.resource)


	def action_show_request(self) -> None:
		"""	Show the last / current request as cURL command.
		"""
		self.requestView.showCurlDialog(self.resource)


	def selectChangedCallback(self, value:int) -> None:
		"""	Callback for the select change.

			Args:
				value:	The value of the select.
		"""
		self.requestView.updateResourceView(self.resource, 
									  		resourceType = self.requestView.childResourceType, 
											requestOriginator = self.requestOriginator)

