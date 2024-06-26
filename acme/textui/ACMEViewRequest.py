#
#	ACMEViewRequest.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines a view to display requests.
"""

from __future__ import annotations
from typing import Optional, Callable

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container
from textual.widgets import Label, Button, TextArea
from textual.widgets.button import ButtonVariant
from .ACMEFieldOriginator import ACMEFieldOriginator
from ..runtime import CSE

class ACMEViewRequest(VerticalScroll):
	"""	View to display request.
	"""

	def __init__(self, id:str, 
			  		   title:str,
			  		   header:str, 
					   originator:str,
					   buttonLabel:str, 
					   buttonVariant:Optional[ButtonVariant] = 'primary',
					   callback:Optional[Callable] = None,
					   enableEditor:bool = True):
		"""	Initialize the view.

			Args:
				id:	The view ID.
				title: The title of the view.
				header: The header text.
				originator: The originator.
				buttonLabel: The label of the button.
				buttonVariant: The button variant.
				callback: The callback for the button action
				enableEditor: Enable the editor.
		"""
		super().__init__(id = id, classes = 'request-view')
		self.header = Label(header, classes = 'request-header')
		self.button = Button(buttonLabel, variant = buttonVariant, id = 'request-button', classes = 'request-button')
		self.inputOriginator = ACMEFieldOriginator(originator, 
											 	   suggestions = [CSE.cseOriginator, originator])
		self.resourceTextArea = TextArea('', 
						 	 			 classes = 'request-resource-textarea', 
										 language = 'json', 
										 soft_wrap = False,
										 tab_behavior = 'indent',
				  						 show_line_numbers = True,
										 theme = 'monokai')
		self.border_title = title
		self.callback = callback
		self.enableEditor = enableEditor


	def compose(self) -> ComposeResult:
		with Horizontal():
			yield self.header
			yield self.button

		with Container(classes = 'request-originator'):
			yield self.inputOriginator
		if self.enableEditor:
			yield self.resourceTextArea


	@property
	def originator(self) -> str:
		"""	Return the originator.

			Returns:
				The originator.
		"""
		return self.inputOriginator.value


	def updateOriginator(self, originator:str, suggestions:list[str] = []) -> None:
		"""	Update the originator.

			Args:
				originator: The originator.
				suggestions: The suggestions.
		"""
		self.inputOriginator.update(originator, suggestions = suggestions)


	@property
	def resource(self) -> str:
		"""	Return the resource text.

			Returns:
				The resource text.
		"""
		return self.resourceTextArea.text
	

	@resource.setter
	def resource(self, resource:str) -> None:
		"""	Set the resource text.

			Args:
				resource: The resource text.
		"""
		self.resourceTextArea.text = resource


	@on(Button.Pressed, '#request-button')
	def buttonExecute(self) -> None:
		"""	Execute the callback.
		"""
		if self.callback:
			self.callback()

