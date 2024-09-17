#
#	ACMETuiApp.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the main text UI App view for the ACME text UI.
"""

from __future__ import annotations
from typing import Callable, cast, Optional

from typing_extensions import Literal, get_args
import asyncio
from enum import IntEnum, auto
from textual.app import App, ComposeResult
from textual import on
from textual.widgets import Footer, TabbedContent, TabPane, Static
from textual.binding import Binding
from textual.notifications import SeverityLevel

from ..textui.ACMEHeader import ACMEHeader
from ..textui.ACMEContainerAbout import ACMEContainerAbout
from ..textui.ACMEContainerConfigurations import ACMEContainerConfigurations
from ..textui.ACMEContainerInfo import ACMEContainerInfo
from ..textui.ACMEContainerTree import ACMEContainerTree
from ..textui.ACMEContainerRegistrations import ACMEContainerRegistrations
from ..textui.ACMEContainerRequests import ACMEContainerRequests
from ..textui.ACMEContainerTools import ACMEContainerTools
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..etc.Types import ResourceTypes
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.Utils import openFileWithDefaultApplication

tabResources = 'tab-resources'
tabRequests = 'tab-requests'
tabRegistrations = 'tab-registrations'
tabConfigurations = 'tab-configurations'
tabTools = 'tab-tools'
tabInfo = 'tab-info'
tabAbout = 'tab-about'

class ACMETuiQuitReason(IntEnum):
	undefined = auto()
	quitTUI = auto()
	quitAll = auto()
	restart = auto()

class ACMETuiApp(App):
	"""A Textual app to manage the ACME text UI."""

	from ..runtime import TextUI

	CSS_PATH = 'ACMETUI.tcss'

	BINDINGS = 	[ Binding('#', 'quit_tui', 'Console'),
				  Binding('Q', 'quit_acme', 'Quit ACME', key_display = 'SHIFT-Q'),
				]

	def __init__(self) -> None:
		super().__init__()
		self.debugging = False

		self.quitReason = ACMETuiQuitReason.undefined
		self.attributeExplanations = CSE.validator.getShortnameLongNameMapping()

		# Set some default color values
		self._colors = self.get_css_variables()
		self.objectColor = self._colors['secondary'] if Configuration.textui_theme == 'dark' else self._colors['secondary-darken-1']


		# Add the resource types to the attribute explanations
		for n in ResourceTypes:
			self.attributeExplanations[ResourceTypes(n).typeShortname()] = f'{ResourceTypes.fullname(n)} resource type'

		# This is used to keep track of the current tab.
		# This is a bit different from the actual current tab from the self.tabs
		# attribute because at one point it is used to determine the previous tab.
		self.currentTab:TabbedContent.TabActivated = None	

		# This is used to keep a pointer to the current event loop to use it
		# for async calls from non-async functions.
		# This is set in the on_load() function.
		self.event_loop:asyncio.AbstractEventLoop = None


	def compose(self) -> ComposeResult:
		"""Build the Main UI."""
		yield ACMEHeader(show_clock = True)
		if self.debugging:
			yield Static('', id = 'debug-console')

		with TabbedContent(id = 'tabs'):
			with TabPane('Resources', id = tabResources):
				yield ACMEContainerTree(id = 'container-tree')

			with TabPane('Requests', id = tabRequests):
				yield ACMEContainerRequests(id = 'container-requests')

			with TabPane('Registrations', id = tabRegistrations):
				yield ACMEContainerRegistrations(id = 'container-registrations')

			with TabPane('Tools', id = tabTools):
				self._toolsView =  ACMEContainerTools(id = 'container-tools')
				yield self._toolsView

			with TabPane('Infos', id = tabInfo):
				yield ACMEContainerInfo(id = 'container-info')

			with TabPane('Configurations', id = tabConfigurations):
				yield ACMEContainerConfigurations(id = 'container-configurations')

			with TabPane('About', id = tabAbout):
				yield ACMEContainerAbout()

		yield Footer()


	@property
	def tabs(self) -> TabbedContent:
		return cast(TabbedContent, self.query_one('#tabs'))


	@property
	def containerTree(self) -> ACMEContainerTree:
		return cast(ACMEContainerTree, self.query_one('#container-tree'))


	@property
	def containerRegistrations(self) -> ACMEContainerRegistrations:
		return cast(ACMEContainerRegistrations, self.query_one('#container-registrations'))


	@property
	def containerConfigs(self) -> ACMEContainerConfigurations:
		return cast(ACMEContainerConfigurations, self.query_one('#container-configurations'))


	@property
	def containerInfo(self) -> ACMEContainerInfo:
		return cast(ACMEContainerInfo, self.query_one('#container-info'))
	

	@property
	def containerTools(self) -> ACMEContainerTools:
		# This is a bit of a hack to get the containerTools object
		# because it is not available anymore after the DOM is removed.
		return self._toolsView
	

	@property
	def containerRequests(self) -> ACMEContainerRequests:
		return cast(ACMEContainerRequests, self.query_one('#container-requests'))


	@property
	def debugConsole(self) -> Static:
		return cast(Static, self.query_one('#debug-console'))
	

	def on_load(self) -> None:
		self.dark = Configuration.textui_theme == 'dark'
		self.syntaxTheme = 'ansi_dark' if self.dark else 'ansi_light'
		self.event_loop = asyncio.get_event_loop()

	
	@on(TabbedContent.TabActivated)
	def tabChanged(self, tab:TabbedContent.TabActivated) -> None:
		# Use the self.currentTab shortly to determine where we come from and call a 
		if self.currentTab is not None:
			match self.currentTab.pane.id:
				case _i if _i == tabTools:
					self.containerTools.leaving_tab()
		
		# Set self.currenTab to the new tab.
		self.currentTab = tab

		# Notify containers that the tab has changed
		self.containerInfo.tab_changed(self.currentTab.pane.id)
		

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

	def action_open_file(self, filename:str) -> None:
		"""	Open a file with the default application.
		
			Args:
				filename: Name of the file to open.
		"""
		openFileWithDefaultApplication(filename)


	#########################################################################

	def logDebug(self, msg:str) -> None:
		"""	Print debug msg """
		try:
			self.debugConsole.update(msg)
		except:
			# If the debug console is not available, just ignore
			pass

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
	

	def showNotification(self, message:str, 
					  		   title:str, 
							   severity:Literal['information', 'warning', 'error'], 
							   timeout:Optional[float] = None) -> None:

		async def _call() -> None:
			self.notify(message = message, title = title, severity = severity, timeout = timeout)
		
		if timeout is None:
			timeout = Configuration.textui_notificationTimeout
		
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

