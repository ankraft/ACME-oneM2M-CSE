#
#	ACMEContentDialog.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines a modal dialog for displaying content in the ACME text UI.
"""

from __future__ import annotations
from typing import Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.events import Click
from textual.containers import Center, ScrollableContainer, Vertical
from rich.syntax import Syntax
import pyperclip

class ACMEContentDialog(ModalScreen):
	""" A modal dialog for displaying content in the ACME text UI.
	"""

	BINDINGS = [("c", "dismiss", "Dismiss"), 
			 	('escape', "dismiss", "Dismiss")]
	
	def __init__(self, content:str, title:Optional[str] = '', buttonEnabled:Optional[bool] = True) -> None:
		self.content = content
		self.borderTitle = title
		super().__init__()

		# Create the copy button
		self.button = Button('Copy', variant='primary', id='dialog-copy')
		self.button.disabled = not buttonEnabled


	def compose(self) -> ComposeResult:
		content = Vertical(
			ScrollableContainer(Label(Syntax(self.content, 'shell', theme = self.app.syntaxTheme)), id = 'dialog-content'),
			Center(self.button, id = 'dialog-button'),
			id='dialog-area'		
		)
		content.border_title = self.borderTitle
		yield content


	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'dialog-copy':
			pyperclip.copy(self.content)
	
	def on_click(self, event:Click) -> None:
		""" Dismiss the screen when clicking outside the dialog.

			Args:
				event:	The click event.
		"""
		if self.get_widget_at(event.screen_x, event.screen_y)[0] is self:
			self.app.pop_screen()

