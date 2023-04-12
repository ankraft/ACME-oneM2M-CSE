#
#	ACMEContainerAbout.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Registrations* view for the ACME text UI.
"""

from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static
from ..services import CSE

idRegs = 'registrations'


class ACMEContainerRegistrations(Container):

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idRegs)
		self.tuiApp = tuiApp
		self.registrationsView = Static(expand = True)
		self.registrationsUpdate()
		#self.set_interval(_textUI.refreshInterval, self.registrationsUpdate)


	def compose(self) -> ComposeResult:
		yield Container(
			Vertical(self.registrationsView, id = 'regs-view')
		)


	async def onShow(self) -> None:
		self.registrationsUpdate()


	def registrationsUpdate(self) -> None:
		# _textUI.tuiApp.bell()
		if self.tuiApp.content.current == idRegs:
			self.registrationsView.update(CSE.console.getRegistrationsRich())


