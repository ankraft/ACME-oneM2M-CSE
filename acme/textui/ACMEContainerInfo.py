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
from textual.timer import Timer
from rich.style import Style
from ..runtime import CSE
from ..runtime.Logging import fontDark, fontLight
from ..runtime.Configuration import Configuration
from ..textui import ACMETuiApp

class ACMEContainerInfo(VerticalScroll):

	def __init__(self, id:str) -> None:
		super().__init__(id = id)

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """
		self._updateTimer:Timer = None
		"""	The timer to update the statistics. """

		self._colors = self._app.get_css_variables()
	

	def compose(self) -> ComposeResult:
		yield Static(expand = True, id = 'stats-view')


	@property
	def statsView(self) -> Static:
		return cast(Static, self.query_one('#stats-view'))


	def tab_changed(self, id:str) -> None:
		"""	Called when the tab is changed.

			Args:
				id:	The ID of the tab.
		"""
		if id == ACMETuiApp.tabInfo:
			if not self._updateTimer:
				self._updateTimer = self.set_interval(Configuration.textui_refreshInterval, self._statsUpdate)
			self._updateTimer.resume() # resume timer when tab becomes active again
			self._statsUpdate(True)
		else:
			# Switch of the update when the tab is not active
			if self._updateTimer:
				self._updateTimer.pause()


	def _statsUpdate(self, force:bool = False) -> None:
		if force or self._app.tabs.active == ACMETuiApp.tabInfo:
			self.statsView.update(CSE.console.getStatisticsRich(style = Style(color = self._colors['primary']), 
																	textStyle = Style(color = fontDark if self._app.dark else fontLight)))

