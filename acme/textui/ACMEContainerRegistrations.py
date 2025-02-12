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
	"""	The *Registrations* view for the ACME text UI.
	"""

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""
		super().__init__(id = id)
		
		# Some resources upfront
		self._registrationView = Static(expand = True, id = 'registrations-view')
		"""	The registrations view. """


	def compose(self) -> ComposeResult:
		"""	Compose the view.

			Yields:
				The view content.
		"""
		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		yield self._registrationView


	@property
	def registrationView(self) -> Static:
		"""	Return the registrations view.

			Returns:
				The registrations view.
		"""
		return self._registrationView


	def on_show(self) -> None:
		"""	Called when the view is shown.
		"""
		self.registrationsUpdate()


	def registrationsUpdate(self) -> None:
		"""	Update the registrations view.
		"""
		self.registrationView.update(CSE.console.getRegistrationsRich(style = Style(color = self.app.get_css_variables()['primary']),
													   		   		  textStyle = Style(color = fontDark if self._app.dark else fontLight)))

