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
from textual.containers import Container, Center, VerticalScroll
from textual.widgets import Button, Static, Label
from .ACMEFieldOriginator import ACMEFieldOriginator
from ..etc.Types import Operation, ResponseStatusCode
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.DateUtils import getResourceDate
from ..etc.ACMEUtils import uniqueRI
from ..resources.Resource import Resource
from ..runtime import CSE


def validateOriginator(value: str) -> bool:
	"""	Validate the originator.
	
		Args:	
			value:	The value to validate.

		Returns:
			True if the value is valid, otherwise False.
	"""
	return len(value) > 1 and value.startswith('C')

class ACMEContainerDelete(Container):

	DEFAULT_CSS = """
	#request-delete-view {
		height: 12;
	}

	#request-delete-input-view {
		width: 100%;
		height: 6;
	}

	#request-delete-response-label {
		width: 1fr;
		display: block;
		overflow: auto;
		height: 1;
		content-align: center middle;
		background: $panel;
	}

	#request-delete-response-response {
		margin: 1 1 1 1;
	}
	"""
	"""	The CSS for the *Delete* view. """

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""
		super().__init__(id = id)

		self.requestOriginator = 'CAdmin'
		"""	The request originator. """

		self.resource:Resource = None
		"""	The resource to delete. """


	def compose(self) -> ComposeResult:
		"""	Build the *Delete* view.
		"""
		self.fieldOriginator =ACMEFieldOriginator(self.requestOriginator, suggestions = [CSE.cseOriginator, self.requestOriginator])
		with VerticalScroll(id = 'request-delete-view'):
			with Container(id = 'request-delete-input-view'):
				yield self.fieldOriginator
			with Center():
				yield Button('Send DELETE Request', variant = 'error', id = 'request-delete-button')
		with VerticalScroll(id = 'request-delete-response'):
			yield Label('[u b]Response[/u b]', id = 'request-delete-response-label')
			yield Static('', id = 'request-delete-response-response')


	@property
	def deleteResponse(self) -> Static:
		""" Get the delete response widget.

			Returns:
				The delete response widget.
		"""
		return cast(Static, self.query_one('#request-delete-response-response'))


	def updateResource(self, resource:Resource) -> None:
		"""	Update the resource to delete.

			Args:
				resource:	The resource to delete.
		"""
		self.resource = resource
		# Update the request originator. Important for getting a default request originator
		self.requestOriginator = self.resource.getOriginator()
		if self.requestOriginator:	
			self.fieldOriginator.update(self.requestOriginator, [CSE.cseOriginator, self.requestOriginator])
		else: # No originator, use CSE originator
			self.fieldOriginator.update(CSE.cseOriginator, [CSE.cseOriginator])
		self.deleteResponse.update('')	# Clear the response field
	

	@on(Button.Pressed, '#request-delete-button')
	def buttonExecute(self) -> None:
		"""	Handle the *Send DELETE Request* button event.
		"""
		from .ACMETuiApp import ACMETuiApp

		try:			
			# Prepare request structure
			result = CSE.request.handleRequest( {
					'op': Operation.DELETE,
					'fr': self.fieldOriginator.originator,
					'to': self.resource.ri, 
					'rvi': CSE.releaseVersion,
					'rqi': uniqueRI(), 
					'ot': getResourceDate(),
				})
			if result.rsc != ResponseStatusCode.DELETED:
				raise ResponseException(result.rsc, result.dbg)
			
			cast(ACMETuiApp, self.app).containerTree.update()
		except ResponseException as e:
			self.deleteResponse.update(f'Response Status: {e.rsc}\n\n[red]{e.dbg}[/red]')


	@on(ACMEFieldOriginator.Submitted)
	def inputFieldSubmitted(self, value:str) -> None:
		"""	Handle the input field submission event.

			Args:
				value:	The value of the input field.
		"""
		self.buttonExecute()
