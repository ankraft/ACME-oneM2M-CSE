#
#	ACMEContentConformDialog.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines a modal dialog for displaying content in the ACME text UI.
"""

from __future__ import annotations
from typing import Optional, cast, Any

from textual import on
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen, SystemModalScreen
from textual.widgets import Label, Button
from textual.events import Click
from textual.containers import Center, ScrollableContainer, Vertical, Horizontal

class ACMEContentConfirmDialog(SystemModalScreen[bool]):
	""" A modal dialog for confirming actions in the ACME text UI.
	"""

	BINDINGS = [('escape', "dismiss", "Dismiss")]
	"""	Key bindings for the dialog. """

	def __init__(self,	content:str, 
			  			title:Optional[str]='', 
						confirmButtonText:Optional[str]='Confirm',
						cancelButtonText:Optional[str]='Cancel') -> None:
		"""	Initialize the dialog.

			Args:
				content:		The content to display.
				title:			The title of the dialog.
				confirmButtonText:	The text for the confirm button.
				cancelButtonText:	The text for the cancel button.
		"""
		self.content = content
		"""	The content to display. """

		self.borderTitle = title
		"""	The title of the dialog. """

		self.result:bool = False
		"""	The result of the confirmation dialog. """

		super().__init__()

		# Create the confirm button
		self.confirmButton = Button(confirmButtonText, variant='success', id='dialog-confirm-button')
		"""	The confirm button. """
		self.cancelButton = Button(cancelButtonText, variant='primary', id='dialog-cancel-button')
		"""	The cancel button. """

		from .ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """


	def compose(self) -> ComposeResult:
		""" Compose the dialog.

			Yields:
				The dialog content.
		"""
		content = Vertical(
			ScrollableContainer(Label(self.content), id='dialog-content'),
			Horizontal(
				Center(self.cancelButton, id='dialog-cancel-button'),
				Center(self.confirmButton, id='dialog-confirm-button'),
				id='dialog-buttons'
			),
			id='dialog-area'
		)
		content.border_title = self.borderTitle
		yield content


	def on_button_pressed(self, event: Button.Pressed) -> None:
		""" Handle the button press event.
			This sets the result based on the button pressed and dismisses the dialog.

			Args:
				event:	The button press event.
		"""
		self.result = event.button.id == 'dialog-confirm-button'
		self.dismiss(self.result)

	
	def on_click(self, event:Click) -> None:
		""" Dismiss the screen when clicking outside the dialog.
			This also returns the result as None, indicating no confirmation.

			Args:
				event:	The click event.
		"""
		if self.get_widget_at(event.screen_x, event.screen_y)[0] is self:
			self.result = None
			self.dismiss(None)
