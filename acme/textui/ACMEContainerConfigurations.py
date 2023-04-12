#
#	ACMEContainerConfigurations.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Configurations* view for the ACME text UI.
"""

from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from ..services import CSE

idConfigs = 'configurations'


class ACMEContainerConfigurations(Container):

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idConfigs)
		self.tuiApp = tuiApp
		self.configurationsView = Static(expand = True)
		self._configurationsUpdate()


	def compose(self) -> ComposeResult:
		yield Container(
			Vertical(self.configurationsView, id = 'configs-view')
		)


	async def onShow(self) -> None:
		self._configurationsUpdate()


	def _configurationsUpdate(self) -> None:
		if self.tuiApp.content.current == idConfigs:
			#_textUI.tuiApp.bell()
			self.configurationsView.update(CSE.console.getConfigurationRich())

