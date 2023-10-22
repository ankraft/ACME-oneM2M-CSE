#
#	ACMETuiApp.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the main text UI App view for the ACME text UI.
"""

from __future__ import annotations
from typing import Callable
from typing_extensions import Literal, get_args
import asyncio
from enum import IntEnum, auto
from textual.app import App, ComposeResult
from textual import on
from textual.widgets import Tab, Footer, TabbedContent, TabPane, Static
from textual.binding import Binding
from textual.design import ColorSystem
from textual.notifications import Notification, SeverityLevel

from ..textui.ACMEHeader import ACMEHeader
from ..textui.ACMEContainerAbout import ACMEContainerAbout
from ..textui.ACMEContainerConfigurations import ACMEContainerConfigurations
from ..textui.ACMEContainerInfo import ACMEContainerInfo, tabInfo
from ..textui.ACMEContainerTree import ACMEContainerTree
from ..textui.ACMEContainerRegistrations import ACMEContainerRegistrations
from ..textui.ACMEContainerRequests import ACMEContainerRequests
from ..textui.ACMEContainerTools import ACMEContainerTools
from ..services import CSE
from ..etc.Types import ResourceTypes
from ..helpers.BackgroundWorker import BackgroundWorkerPool




tabResources = 'tab-resources'
tabRequests = 'tab-requests'
tabRegistrations = 'tab-registrations'
tabConfigurations = 'tab-configurations'
tabTools = 'tab-tools'
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
		self.debugging = False

		self.textUI = textUI	# Keep backward link to the textUI manager
		self.quitReason = ACMETuiQuitReason.undefined
		self.attributeExplanations = CSE.validator.getShortnameLongNameMapping()

		# Add the resource types to the attribute explanations
		for n in ResourceTypes:
			self.attributeExplanations[ResourceTypes(n).tpe()] = f'{ResourceTypes.fullname(n)} resource type'

		# This is used to keep track of the current tab.
		# This is a bit different from the actual current tab from the self.tabs
		# attribute because at one point it is used to determine the previous tab.
		self.currentTab:Tab = None	

		# This is used to keep a pointer to the current event loop to use it
		# for async calls from non-async functions.
		# This is set in the on_load() function.
		self.event_loop:asyncio.AbstractEventLoop = None

		self.tabs = TabbedContent()
		self.containerTree = ACMEContainerTree()
		self.containerRequests = ACMEContainerRequests(self)
		self.containerRegistrations = ACMEContainerRegistrations(self)
		self.containerConfigs = ACMEContainerConfigurations(self)
		self.containerInfo = ACMEContainerInfo(self)
		self.containerTools = ACMEContainerTools(self)
		self.containerAbout = ACMEContainerAbout()
		self.debugConsole = Static('', id = 'debug-console')


	def compose(self) -> ComposeResult:
		"""Build the Main UI."""
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
			with TabPane('Tools', id = tabTools):
				yield self.containerTools
			with TabPane('Infos', id = tabInfo):
				yield self.containerInfo
			with TabPane('Configurations', id = tabConfigurations):
				yield self.containerConfigs
			with TabPane('About', id = tabAbout):
				yield self.containerAbout
		yield Footer()


	def on_load(self) -> None:
		self.dark = self.textUI.theme == 'dark'
		self.syntaxTheme = 'ansi_dark' if self.dark else 'ansi_light'
		self.event_loop = asyncio.get_event_loop()
		# self.design = CUSTOM_COLORS
		# self.refresh_css()

	
	@on(TabbedContent.TabActivated)
	def tabChanged(self, tab:TabbedContent.TabActivated) -> None:
		# Use the self.currentTab shortly to determine where we come from and call a 
		if self.currentTab is not None and self.currentTab.id == tabTools:
			self.containerTools.leaving_tab()
			# if callable(_f := getattr(_c, "leaving_tab", None)):
			# 	_f()
		# Set self.currenTab to the new tab.
		self.currentTab = tab.tab


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
	
	
	def scriptPrint(self, scriptName:str, msg:str) -> None:
		if self.containerTools:
			self.containerTools.scriptPrint(scriptName, msg)


	def scriptLog(self, scriptName:str, msg:str) -> None:
		if self.containerTools:
			self.containerTools.scriptLog(scriptName, msg)


	def scriptLogError(self, scriptName:str, msg:str) -> None:
		if self.containerTools:
			self.containerTools.scriptLogError(scriptName, msg)
	

	def scriptClearConsole(self, scriptName:str) -> None:
		if self.containerTools:
			self.containerTools.scriptClearConsole(scriptName)
	

	def scriptShowNotification(self, message:str, title:str, severity:Literal['information', 'warning', 'error'], timeout:float) -> None:

		async def _call() -> None:
			self.notify(message = message, title = title, severity = severity, timeout = timeout)
		
		if timeout is None:
			timeout = Notification.timeout
		
		if severity is None:
			severity = 'information'
		elif severity not in get_args(SeverityLevel):
			raise ValueError(f'Invalid severity level: {severity}')

		self.runAsyncTask(_call)


	def scriptVisualBell(self, scriptName:str) -> None:
		if self.containerTools:
			BackgroundWorkerPool.runJob(lambda:self.containerTools.scriptVisualBell(scriptName))

	def refreshResources(self) -> None:
		if self.containerTree:
			self.containerTree.update()

	#########################################################################


	def runAsyncTask(self, task:Callable) -> None:
		"""	Run an async task from a non-async function.

			Args:
				task: The async task to run.
		"""
		if self.event_loop:
			self.event_loop.create_task(task())


	def restart(self) -> None:
		self.quitReason = ACMETuiQuitReason.restart
		self.exit()


	def cleanUp(self) -> None:
		"""	Clean up the UI before exiting.
		"""
		self.containerTools.cleanUp()
		self.event_loop = None


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
