#
#	ACMETuiApp.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the main text UI App view for the ACME text UI.
"""

from __future__ import annotations
from enum import IntEnum, auto
from textual.app import App, ComposeResult
from textual.widgets import Tabs, Tab, Footer, ContentSwitcher
from textual.binding import Binding
from textual.containers import Container
from ..textui.ACMEHeader import ACMEHeader
from ..textui.ACMEContainerAbout import ACMEContainerAbout, idAbout
from ..textui.ACMEContainerConfigurations import ACMEContainerConfigurations, idConfigs
from ..textui.ACMEContainerInfo import ACMEContainerInfo, idInfo
from ..textui.ACMEContainerTree import ACMEContainerTree, idTree
from ..textui.ACMEContainerRegistrations import ACMEContainerRegistrations, idRegs
from ..textui.ACMEContainerRequests import ACMEContainerRequests, idRequests


tabResources = 'tab-resources'
tabRequests = 'tab-requests'
tabRegistrations = 'tab-registrations'
tabConfigurations = 'tab-configurations'
tabInfo = 'tab-info'
tabAbout = 'tab-about'

class ACMETuiQuitReason(IntEnum):
	undefined = auto()
	quitTUI = auto()
	quitAll = auto()
	restart = auto()


class ACMETuiApp(App):
	"""A Textual app to manage the ACME text UI."""

	from ..services import TextUI

	CSS_PATH = 'ACMETUI.css'

	BINDINGS = 	[ Binding('#', 'quit_tui', 'Console'),
				  Binding('Q', 'quit_acme', 'Quit ACME', key_display = 'SHIFT-Q'),
				]


	def __init__(self, textUI:TextUI.TextUI):
		super().__init__()
		self.textUI = textUI	# Keep backward link
		self.quitReason = ACMETuiQuitReason.undefined


	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""

		self.dark = self.textUI.theme == 'dark'

		self.content = ContentSwitcher(initial = idTree)
		self.containerTree = ACMEContainerTree()
		self.containerRequests = ACMEContainerRequests(self)
		self.containerRegistrations = ACMEContainerRegistrations(self)
		self.containerConfigs = ACMEContainerConfigurations(self)
		self.containerInfo = ACMEContainerInfo(self)
		self.containerAbout = ACMEContainerAbout()


		# self.logPanel = TextLog(id = 'log')
		yield ACMEHeader(show_clock = True)
		yield Tabs(
			Tab('Resources', id = tabResources),
			# Tab('AEs', id = 'tab-aes'),
			# Tab('Logs', id = 'tab-logs'),
			Tab('Requests', id = tabRequests),
			Tab('Registrations', id = tabRegistrations),
			Tab('Configurations', id = tabConfigurations),
			Tab('Infos', id = tabInfo),
			Tab('About', id = tabAbout),
		)
		with self.content:
			yield self.containerTree
			yield self.containerRequests
			yield self.containerRegistrations
			yield self.containerConfigs
			yield self.containerInfo
			yield self.containerAbout
			yield Container(id = 'empty')

		yield Footer()


	async def on_tabs_tab_activated(self, event:Tabs.TabActivated) -> None:
		"""Handle TabActivated message sent by Tabs."""
		if event.tab.id == tabResources:
			await self.containerTree.onShow()
			self.content.current = idTree
		elif event.tab.id == tabRequests:
			self.content.current = idRequests
			await self.containerRequests.onShow()
		elif event.tab.id == tabRegistrations:
			self.content.current = idRegs
			await self.containerRegistrations.onShow()
		elif event.tab.id == tabConfigurations:
			self.content.current = idConfigs
			await self.containerConfigs.onShow()
		elif event.tab.id == tabInfo:
			self.content.current = idInfo
			await self.containerInfo.onShow()
		elif event.tab.id == tabAbout:
			self.content.current = idAbout
			await self.containerInfo.onShow()
		# else:
		# 	self.content.current = 'empty'


	async def action_quit_tui(self) -> None:
		self.quitReason = ACMETuiQuitReason.quitTUI
		self.exit()

	
	async def action_quit_restart_tui(self) -> None:
		self.quitReason = ACMETuiQuitReason.restart
		self.exit()


	async def action_quit_acme(self) -> None:
		self.quitReason = ACMETuiQuitReason.quitAll
		self.exit()

	#########################################################################

	def restart(self) -> None:
		self.quitReason = ACMETuiQuitReason.restart
		self.exit()




#
#	TODO
#

# class QuitScreen(Screen):
# 	def compose(self) -> ComposeResult:
# 		yield Vertical(
# 			Static('Are you sure you want to quit?', id="question"),
# 			Static(' '),
# 			Horizontal(
# 				Button("Quit", variant="error", id="quit", classes = 'button'),
# 				Button("Cancel", variant="primary", id="cancel", classes = 'button')),
# 			id="dialog",
# 		)

# 	def on_button_pressed(self, event: Button.Pressed) -> None:
# 		if event.button.id == "quit":
# 			self.app.exit()
# 		else:
# 			self.app.pop_screen()
