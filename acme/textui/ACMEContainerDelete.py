#
#	ACMEContainerDelete.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Delete* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast

from textual.app import ComposeResult
from textual.containers import Container
from .ACMEViewRequest import ACMEViewRequest
from .ACMEViewResponse import ACMEViewResponse
from ..etc.Types import Operation
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.ResourceSemaphore import CriticalSection
from ..resources.Resource import Resource



class ACMEContainerDelete(Container):
	"""	The *Delete* view for the ACME text UI.
		This is a container that contains the *Delete* request view and the response view.
	"""

	BINDINGS = [('c', 'show_request', 'cURL command')]
	"""	Key bindings for the *Delete* view. """

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""
		super().__init__(id = id)

		self.requestOriginator = RC.cseOriginator
		"""	The request originator. """

		self.resource:Resource = None
		"""	The resource to delete. """

		self.responseView = ACMEViewResponse(id = 'request-delete-response')
		"""	The response view. """

		self.requestView:ACMEViewRequest = ACMEViewRequest(id = 'request-delete-request', 
													 	   title = 'DELETE Request',
													 	   header = 'Delete a resource and its children from the CSE.',
														   originator = self.requestOriginator,
														   buttonLabel = 'DELETE Resource',
														   buttonVariant = 'error',
														   operation = Operation.DELETE,
														   callback = self.doDelete,
														   enableEditor = False,
														   responseView = self.responseView
													)
		"""	The request view. """
		

	def compose(self) -> ComposeResult:
		"""	Build the *Delete* view.
		
			Return:
				The composed view.
		"""		
		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		yield self.requestView
		yield self.responseView
		



	def updateResource(self, resource:Resource) -> None:
		"""	Update the resource to delete.

			Args:
				resource:	The resource to delete.
		"""
		self.resource = resource

		# Update the request originator. Important for getting a default request originator
		self.requestOriginator = self.resource.getOriginator()
		if self.requestOriginator:	
			self.requestView.updateOriginator(self.requestOriginator, [RC.cseOriginator, self.requestOriginator])
		else: # No originator, use CSE originator
			self.requestView.updateOriginator(self.requestOriginator, [RC.cseOriginator])
		self.responseView.clear()
	

	def doDelete(self) -> None:
		"""	Handle the *DELETE Request* button event. This is a callback function.
		"""

		# Send the request and handle the response
		if self.requestView.runRequest(self.resource):

			# The following is a critical section, because the resource tree has to be updated
			# but we don't want to update the editor. The 'updateResource()' method would do that.
			# There is a check for the critical section in the 'updateResource()' method above.
			# Display a success message and update the container tree
			with CriticalSection('tuiRequest', timeout = 0.0):
				self._app.containerTree.refreshCurrentParrentNode()
				self._app.containerTree.updateResource(self.resource)

		
	def action_show_request(self) -> None:
		"""	Show the current request as cURL command.
		"""
		self.requestView.showCurlDialog(self.resource)

