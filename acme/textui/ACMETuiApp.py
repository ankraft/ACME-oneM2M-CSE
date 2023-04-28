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
from textual.widgets import Tabs, Tab, Footer, ContentSwitcher, TabbedContent, TabPane, Static
from textual.binding import Binding
from textual.containers import Container
from textual.design import ColorSystem
from ..textui.ACMEHeader import ACMEHeader
from ..textui.ACMEContainerAbout import ACMEContainerAbout, idAbout
from ..textui.ACMEContainerConfigurations import ACMEContainerConfigurations, idConfigs
from ..textui.ACMEContainerInfo import ACMEContainerInfo, tabInfo
from ..textui.ACMEContainerTree import ACMEContainerTree, idTree
from ..textui.ACMEContainerRegistrations import ACMEContainerRegistrations, idRegs
from ..textui.ACMEContainerRequests import ACMEContainerRequests, idRequests



tabResources = 'tab-resources'
tabRequests = 'tab-requests'
tabRegistrations = 'tab-registrations'
tabConfigurations = 'tab-configurations'
tabAbout = 'tab-about'

# AYU theme (see https://github.com/Textualize/textual/discussions/1407)
CUSTOM_COLORS = {
	'dark': ColorSystem(
		primary = '#39BAE6',      # syntax.tag
		secondary = '#FFB454',    # syntax.func
		accent = '#59C2FF',       # syntax.entity
		warning = '#E6B450',      # common.accent
		error = '#D95757',        # common.error
		success = '#7FD962',      # vcs.added
		background = '#0B0E14',   # ui.bg
		boost = '#47526633',      # ui.selection.normal
		surface = '#0F131A',      # ui.panel.bg
		panel = '#565B66',        # ui.fg
		dark = True,
	),

	'light': ColorSystem(
		primary = '#55B4D4',
		secondary = '#F2AE49',
		accent = '#399EE6',
		warning = '#FFAA33',
		error = '#E65050',
		success = '#6CBF43',
		background = '#F8F9FA',
		boost = '#6B7D8F1F',
		surface = '#F3F4F5',
		panel = '#8A9199',
		dark = False,
	)
}


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
		self.textUI = textUI	# Keep backward link to the textUI manager
		self.dark = self.textUI.theme == 'dark'
		self.quitReason = ACMETuiQuitReason.undefined
		self.debugging = False
		#self.app.DEFAULT_COLORS = CUSTOM_COLORS

		self.tabs = TabbedContent()
		self.containerTree = ACMEContainerTree()
		self.containerRequests = ACMEContainerRequests(self)
		self.containerRegistrations = ACMEContainerRegistrations(self)
		self.containerConfigs = ACMEContainerConfigurations(self)
		self.containerInfo = ACMEContainerInfo(self)
		self.containerAbout = ACMEContainerAbout()
		self.debugConsole = Static('', id = 'debug-console')

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""

		yield ACMEHeader(show_clock = True)
		if self.debugging:
			yield self.debugConsole
		with self.tabs:
			with TabPane('Resources', id = tabResources):
				yield self.containerTree
			with TabPane('Requests', id = tabRequests):
				yield self.containerRequests
			with TabPane('Registrations', id = tabRegistrations):
				yield self.containerRegistrations
			with TabPane('Configurations', id = tabConfigurations):
				yield self.containerConfigs
			with TabPane('Infos', id = tabInfo):
				yield self.containerInfo
			with TabPane('About', id = tabAbout):
				yield self.containerAbout
		yield Footer()


	def on_mount(self) -> None:
		#self.design = CUSTOM_COLORS
		self.refresh_css()
	

	async def action_quit_tui(self) -> None:
		self.quitReason = ACMETuiQuitReason.quitTUI
		self.exit()

	
	async def action_quit_restart_tui(self) -> None:
		self.quitReason = ACMETuiQuitReason.restart
		self.exit()


	async def action_quit_acme(self) -> None:
		self.quitReason = ACMETuiQuitReason.quitAll
		self.exit()


	async def updateFooter(self) -> None:
		"""	Hack to update the footer. 
		"""
		self.set_focus(None)


	#########################################################################

	def logDebug(self, msg:str) -> None:
		"""	Print debug msg """
		self.debugConsole.update(msg)


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
