#
#	ACMEContentDialog.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines a modal dialog for displaying content in the ACME text UI.
"""

from __future__ import annotations
from typing import Optional, cast

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.events import Click
from textual.containers import Center, ScrollableContainer, Vertical
from rich.syntax import Syntax

class ACMEContentDialog(ModalScreen):
	""" A modal dialog for displaying content in the ACME text UI.
	"""

	BINDINGS = [("c", "dismiss", "Dismiss"), 
			 	('escape', "dismiss", "Dismiss")]
	"""	Key bindings for the dialog. """
	
	def __init__(self, content:str, title:Optional[str] = '', buttonEnabled:Optional[bool] = True) -> None:
		"""	Initialize the dialog.

			Args:
				content:		The content to display.
				title:			The title of the dialog.
				buttonEnabled:	Whether the copy button is enabled. 
		"""
		self.content = content
		"""	The content to display. """

		self.borderTitle = title
		"""	The title of the dialog. """

		super().__init__()

		# Create the copy button
		self.button = Button('Copy', variant='primary', id='dialog-copy')
		"""	The copy button. """
		self.button.disabled = not buttonEnabled

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """


	def compose(self) -> ComposeResult:
		""" Compose the dialog.

			Yields:
				The dialog content.
		"""
		content = Vertical(
			ScrollableContainer(Label(Syntax(self.content, 'shell', theme = self._app.syntaxTheme)), id = 'dialog-content'),
			Center(self.button, id = 'dialog-button'),
			id='dialog-area'		
		)
		content.border_title = self.borderTitle
		yield content


	def on_button_pressed(self, event: Button.Pressed) -> None:
		""" Handle the button press event.

			Args:
				event:	The button press event.
		"""
		if event.button.id == 'dialog-copy':
			if self._app.copyToClipboard(self.content):
				self.app.pop_screen()
				self.app.notify('Copied to clipboard.')
			else:
				self.app.pop_screen()

	
	def on_click(self, event:Click) -> None:
		""" Dismiss the screen when clicking outside the dialog.

			Args:
				event:	The click event.
		"""
		if self.get_widget_at(event.screen_x, event.screen_y)[0] is self:
			self.app.pop_screen()

