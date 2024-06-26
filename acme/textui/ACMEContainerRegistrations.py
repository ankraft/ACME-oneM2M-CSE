#
#	ACMEContainerAbout.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Registrations* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.style import Style
from ..runtime.Logging import fontDark, fontLight
from ..runtime import CSE


class ACMEContainerRegistrations(VerticalScroll):

	def __init__(self, id:str) -> None:
		super().__init__(id = id)
		self._colors = self.app.get_css_variables()


	def compose(self) -> ComposeResult:
		yield Static(expand = True, id = 'registrations-view')


	@property
	def registrationView(self) -> Static:
		return cast(Static, self.query_one('#registrations-view'))


	def on_show(self) -> None:
		self.registrationsUpdate()


	def registrationsUpdate(self) -> None:
		self.registrationView.update(CSE.console.getRegistrationsRich(style = Style(color = self._colors['primary']),
													   		   		  textStyle = Style(color = fontDark if self.app.dark else fontLight)))

