#
#	ACMEContainerInfo.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Infos* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.style import Style
from ..runtime import CSE
from ..textui import ACMETuiApp
from ..runtime.Logging import fontDark, fontLight

tabInfo = 'tab-info'

class ACMEContainerInfo(VerticalScroll):

	def __init__(self, id:str) -> None:
		super().__init__(id = id)

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		self._colors = self._app.get_css_variables()
	

	def compose(self) -> ComposeResult:
		yield Static(expand = True, id = 'stats-view')


	@property
	def statsView(self) -> Static:
		return cast(Static, self.query_one('#stats-view'))


	def on_show(self) -> None:
		self.set_interval(self._app.textUI.refreshInterval, self._statsUpdate)
		self._statsUpdate(True)	# Update once at the beginning
	

	def _statsUpdate(self, force:bool = False) -> None:
		if force or self._app.tabs.active == tabInfo:
			self.statsView.update(CSE.console.getStatisticsRich(style = Style(color = self._colors['primary']), 
													   		    textStyle = Style(color = fontDark if self._app.dark else fontLight)))

