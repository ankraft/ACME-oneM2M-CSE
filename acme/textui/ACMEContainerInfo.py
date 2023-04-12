#
#	ACMEContainerInfo.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Infos* view for the ACME text UI.
"""

from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from ..services import CSE


idInfo = 'info'


class ACMEContainerInfo(Container):

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idInfo)
		self.statsView = Static(expand = True)
		self.tuiApp = tuiApp
		self.set_interval(self.tuiApp.textUI.refreshInterval, self._statsUpdate)


	def compose(self) -> ComposeResult:
		yield Container(
			Vertical(self.statsView, id = 'stats-view'))


	async def onShow(self) -> None:
		self._statsUpdate()


	def _statsUpdate(self) -> None:
		if self.tuiApp.content.current == idInfo:
			# _textUI.tuiApp.bell()
			self.statsView.update(CSE.console.getStatisticsRich())

