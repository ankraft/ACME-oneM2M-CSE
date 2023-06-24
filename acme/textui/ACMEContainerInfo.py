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

tabInfo = 'tab-info'


class ACMEContainerInfo(Container):

	DEFAULT_CSS = '''
#stats-view {
	display: block;
	overflow: auto auto;  
	min-width: 100%;
}
'''
	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__()
		self.statsView = Static(expand = True)
		self.tuiApp = tuiApp


	def compose(self) -> ComposeResult:
		with Vertical(id = 'stats-view'):
			yield self.statsView


	def on_mount(self) -> None:
		self.set_interval(self.tuiApp.textUI.refreshInterval, self._statsUpdate)
		self._statsUpdate(True)	# Update once at the beginning
	

	def on_show(self) -> None:
		self._statsUpdate(True)
	

	def _statsUpdate(self, force:bool = False) -> None:
		# self.tuiApp.logDebug(self.tuiApp.tabs.active)
		if force or self.tuiApp.tabs.active == tabInfo:
			self.statsView.update(CSE.console.getStatisticsRich())

