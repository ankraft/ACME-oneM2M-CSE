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
import pyperclip
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
""" The ID of the resource tab. """

tabRequests = 'tab-requests'
""" The ID of the requests tab. """

tabRegistrations = 'tab-registrations'
""" The ID of the registrations tab. """

tabConfigurations = 'tab-configurations'
""" The ID of the configurations tab. """

tabTools = 'tab-tools'
""" The ID of the tools tab. """

tabInfo = 'tab-info'
""" The ID of the info tab. """

tabAbout = 'tab-about'
""" The ID of the about tab. """

class ACMETuiQuitReason(IntEnum):
	"""	Enumeration of reasons to quit the TUI.
	"""
	undefined = auto()
	"""	Quit reason is undefined. """

	quitTUI = auto()
	"""	Quit the TUI only. """

	quitAll = auto()
	"""	Quit the TUI and the ACME. """

	restart = auto()
	"""	Restart the TUI. """


class ACMETuiApp(App):
	"""A Textual app to manage the ACME text UI."""

	from ..runtime import TextUI

	CSS_PATH = 'ACMETUI.tcss'
	"""	The path to the app's CSS file. """

	BINDINGS = 	[ Binding('#', 'quit_tui', 'Console'),
				  Binding('Q', 'quit_acme', 'Quit ACME', key_display = 'SHIFT-Q'),
				]
	"""	The key bindings for the app. """
	
	# TODO Implement command palette
	ENABLE_COMMAND_PALETTE = False
	"""	Flag to enable the command palette. Inherited from the parent class. """


	def __init__(self) -> None:
		"""	Initialize the app.
		"""

		super().__init__()
		self.debugging = False
		"""	Flag to indicate if debugging is enabled. """

		self.quitReason = ACMETuiQuitReason.undefined
		"""	The reason for quitting the TUI. """

		self.attributeExplanations = CSE.validator.getShortnameLongNameMapping()
		"""	The attribute explanations dictionary. """

		# Set some default color values
		self._colors = self.get_css_variables()
		"""	The CSS variables. """

		self.objectColor = self._colors['secondary'] if Configuration.textui_theme == 'dark' else self._colors['secondary-darken-1']
		"""	The color of the objects. """


		# Add the resource types to the attribute explanations
		for n in ResourceTypes:
			self.attributeExplanations[ResourceTypes(n).typeShortname()] = f'{ResourceTypes.fullname(n)} resource type'

		self.currentTab:TabbedContent.TabActivated = None	
		""" This is used to keep track of the current tab.
			This is a bit different from the actual current tab from the `tabs`
			attribute because at one point it is used to determine the previous tab.
		"""

		self.event_loop:asyncio.AbstractEventLoop = None
		""" The event loop. This is used to keep a pointer to the current event loop to use it
			for async calls from non-async functions.
			
			This is set in the on_load() function.
		"""

		self._tabs = TabbedContent(id = 'tabs')
		"""	The tabbed content. """

		self._containerTree = ACMEContainerTree(id = 'container-tree')
		"""	The tree view. """

		self._containerRegistrations = ACMEContainerRegistrations(id = 'container-registrations')
		"""	The registrations view. """

		self._containerConfigurations = ACMEContainerConfigurations(id = 'container-configurations')
		"""	The configurations view. """

		self._containerInfo = ACMEContainerInfo(id = 'container-info')
		"""	The info view. """

		self._containerRequests = ACMEContainerRequests(id = 'container-requests')
		"""	The requests view. """

		self._toolsView =  ACMEContainerTools(id = 'container-tools')
		"""	The tools view. """

		self._debugConsole = Static('', id = 'debug-console')
		"""	The debug console. """


	def compose(self) -> ComposeResult:
		"""Build the Main UI.

			Yields:
				The UI views.
		"""
		yield ACMEHeader(show_clock = True)
		if self.debugging:
			yield self._debugConsole

		with self._tabs:
			with TabPane('Resources', id = tabResources):
				yield self._containerTree

			with (_tr := TabPane('Requests', id = tabRequests)):
				yield self._containerRequests
				# Disable the requests tab if the operation requests are disabled
				if not Configuration.cse_operation_requests_enable:
					_tr.disabled = True

			with TabPane('Registrations', id = tabRegistrations):
				yield self._containerRegistrations

			with TabPane('Tools', id = tabTools):
				yield self._toolsView

			with TabPane('Infos', id = tabInfo):
				yield self._containerInfo

			with TabPane('Configurations', id = tabConfigurations):
				yield self._containerConfigurations

			with TabPane('About', id = tabAbout):
				yield ACMEContainerAbout()

		yield Footer()


	@property
	def tabs(self) -> TabbedContent:
		"""Return the tabbed content.

			Returns:
				The tabbed content.
		"""
		return self._tabs


	@property
	def containerTree(self) -> ACMEContainerTree:
		"""Return the tree view.
		
			Returns:
				The tree view.
		"""
		return self._containerTree


	@property
	def containerRegistrations(self) -> ACMEContainerRegistrations:
		"""Return the registrations view.
		
			Returns:
				The registrations view.
		"""
		return self._containerRegistrations


	@property
	def containerConfigs(self) -> ACMEContainerConfigurations:
		"""Return the configurations view.
		
			Returns:
				The configurations view.
		"""
		return self._containerConfigurations


	@property
	def containerInfo(self) -> ACMEContainerInfo:
		"""Return the info view.
		
			Returns:
				The info view.
		"""
		return self._containerInfo
	

	@property
	def containerTools(self) -> ACMEContainerTools:
		"""Return the tools view.

			Returns:
				The tools view.
		"""
		# This is a bit of a hack to get the containerTools object
		# because it is not available anymore after the DOM is removed.
		return self._toolsView
	

	@property
	def containerRequests(self) -> ACMEContainerRequests:
		"""Return the requests view.
		
			Returns:
				The requests view.
		"""
		return self._containerRequests


	@property
	def debugConsole(self) -> Static:
		"""Return the debug console.
		
			Returns:
				The debug console.
		"""
		return self._debugConsole
	

	def copyToClipboard(self, text: str) -> bool:
		"""	Copy text to the clipboard.

			Args:
				text: The text to copy.

			Returns:
				True if the text was copied successfully, False otherwise.
		"""
		try:
			pyperclip.copy(text)
			return True
		except pyperclip.PyperclipException as e:
			self.showNotification(f'Error copying to clipboard: {e}', 'Clipboard Error', 'error')
			return False


	def pasteFromClipboard(self) -> str:
		"""	Paste text from the clipboard.

			Returns:
				The pasted text or None if an error occurred.
		"""
		try:
			return pyperclip.paste()
		except pyperclip.PyperclipException as e:
			self.showNotification(f'Error pasting from clipboard: {e}', 'Clipboard Error', 'error')
			return None

	def on_load(self) -> None:
		"""Called when the app is loaded.
		"""
		self.dark:bool
		"""Flag to indicate if the theme is dark or light. """

		match Configuration.textui_theme:
			case 'dark':
				self.theme = 'textual-dark'
				self.dark = True
			case 'light':
				self.theme = 'textual-light'
				self.dark = False

		self.syntaxTheme = 'ansi_dark' if self.dark else 'ansi_light'
		"""	The syntax theme. Inherited from the parent class. """

		self.event_loop = asyncio.get_event_loop()

	
	@on(TabbedContent.TabActivated)
	def tabChanged(self, tab:TabbedContent.TabActivated) -> None:
		"""Called when a tab is activated.

			Args:
				tab: The activated tab.
		"""
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
		"""	Quit the TUI.
		"""
		self.quitReason = ACMETuiQuitReason.quitTUI
		self.exit()

	
	async def action_quit_restart_tui(self) -> None:
		"""	Restart the TUI.
		"""
		self.quitReason = ACMETuiQuitReason.restart
		self.exit()


	async def action_quit_acme(self) -> None:
		"""	Quit the ACME.
		"""
		self.quitReason = ACMETuiQuitReason.quitAll
		self.exit()


	async def updateFooter(self) -> None:
		"""	Hack to update the footer. 
		"""
		self.set_focus(None)


	#########################################################################

	# def action_open_file(self, filename:str) -> None:
	# 	"""	Open a file with the default application.
		
	# 		Args:
	# 			filename: Name of the file to open.
	# 	"""
	# 	openFileWithDefaultApplication(filename)


	#########################################################################

	def logDebug(self, msg:str) -> None:
		"""	Print debug msg.
		 
			Args:
				msg: The message to print.
		"""
		try:
			self.debugConsole.update(msg)
		except:
			# If the debug console is not available, just ignore
			pass


	def scriptPrint(self, scriptName:str, msg:str) -> None:
		"""	Print a message from a script.

			Args:
				scriptName: The name of the script.
				msg: The message to print.
		"""
		if self.containerTools:
			self.containerTools.scriptPrint(scriptName, msg)


	def scriptLog(self, scriptName:str, msg:str) -> None:
		"""	Log a message from a script.

			Args:
				scriptName: The name of the script.
				msg: The message to log.
		"""
		if self.containerTools:
			self.containerTools.scriptLog(scriptName, msg)


	def scriptLogError(self, scriptName:str, msg:str) -> None:
		"""	Log an error message from a script.

			Args:
				scriptName: The name of the script.
				msg: The message to log.
		"""
		if self.containerTools:
			self.containerTools.scriptLogError(scriptName, msg)
	

	def scriptClearConsole(self, scriptName:str) -> None:
		"""	Clear the console of a script.

			Args:
				scriptName: The name of the script.
		"""
		if self.containerTools:
			self.containerTools.scriptClearConsole(scriptName)
	

	def showNotification(self, message:str, 
					  		   title:str, 
							   severity:Literal['information', 'warning', 'error'], 
							   timeout:Optional[float] = None) -> None:
		"""	Show a notification.

			Args:
				message: The message to show.
				title: The title of the notification.
				severity: The severity of the notification. Must be one of 'information', 'warning', or 'error'.
				timeout: The timeout of the notification in seconds. If None, the default timeout is used.
		"""

		async def _call() -> None:
			self.notify(message = message, title = title, severity = severity, timeout = timeout)
		
		if timeout is None:
			timeout = (Configuration.textui_notificationTimeout * 5) if severity == 'error' else Configuration.textui_notificationTimeout
		
		if severity is None:
			severity = 'information'
		elif severity not in get_args(SeverityLevel):
			raise ValueError(f'Invalid severity level: {severity}')

		self.runAsyncTask(_call)


	def scriptVisualBell(self, scriptName:str) -> None:
		"""	Show a visual bell from a script.

			Args:
				scriptName: The name of the script.
		"""
		if self.containerTools:
			BackgroundWorkerPool.runJob(lambda:self.containerTools.scriptVisualBell(scriptName))


	def refreshResources(self) -> None:
		"""	Refresh the resource tree.
		"""
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
		""" Quit the TUI with an indication to restart the TUI.
		"""
		self.quitReason = ACMETuiQuitReason.restart
		self.exit()


	def cleanUp(self) -> None:
		"""	Clean up the UI before exiting.
		"""
		self.containerTools.cleanUp()
		self.event_loop = None

