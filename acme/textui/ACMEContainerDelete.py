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

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from .ACMEViewRequest import ACMEViewRequest
from .ACMEViewResponse import ACMEViewResponse
from ..etc.Types import Operation, ResponseStatusCode
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.DateUtils import getResourceDate
from ..etc.ACMEUtils import uniqueRI
from ..resources.Resource import Resource
from ..runtime import CSE

class ACMEContainerDelete(Container):

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""
		super().__init__(id = id)

		self.requestOriginator = CSE.cseOriginator
		"""	The request originator. """

		self.resource:Resource = None
		"""	The resource to delete. """

		self.deleteRequest:ACMEViewRequest = ACMEViewRequest(id = 'request-delete-request', 
													 	   title = 'DELETE Request',
													 	   header = 'Delete a resource and its children from the CSE.',
														   originator = self.requestOriginator,
														   buttonLabel = 'DELETE Resource',
														   buttonVariant = 'error',
														   callback = self.doDelete,
														   enableEditor = False
													)
		"""	The request view. """
		
		self.deleteResponse = ACMEViewResponse(id = 'request-delete-response')
		"""	The response view. """


	def compose(self) -> ComposeResult:
		"""	Build the *Delete* view.
		"""		
		yield self.deleteRequest
		yield self.deleteResponse


	def updateResource(self, resource:Resource) -> None:
		"""	Update the resource to delete.

			Args:
				resource:	The resource to delete.
		"""
		self.resource = resource
		# Update the request originator. Important for getting a default request originator
		self.requestOriginator = self.resource.getOriginator()
		if self.requestOriginator:	
			self.deleteRequest.updateOriginator(self.requestOriginator, [CSE.cseOriginator, self.requestOriginator])
		else: # No originator, use CSE originator
			self.deleteRequest.updateOriginator(self.requestOriginator, [CSE.cseOriginator])
		self.deleteResponse.clear()
	

	def doDelete(self) -> None:
		"""	Handle the *DELETE Request* button event. This is a callback function.
		"""
		from .ACMETuiApp import ACMETuiApp

		try:			
			# Prepare request structure
			result = CSE.request.handleRequest( {
					'op': Operation.DELETE,
					'fr': self.deleteRequest.originator,
					'to': self.resource.ri, 
					'rvi': CSE.releaseVersion,
					'rqi': uniqueRI(), 
					'ot': getResourceDate(),
				})
			if result.rsc != ResponseStatusCode.DELETED:
				raise ResponseException(result.rsc, result.dbg)
			
			# Display a success message and update the container tree
			cast(ACMETuiApp, self.app).showNotification(f'Resource {self.resource.ri} deleted', 'DELETE Resource', 'information')
			cast(ACMETuiApp, self.app).containerTree.update()
		except ResponseException as e:
			self.deleteResponse.error(e.dbg, rsc = e.rsc)

