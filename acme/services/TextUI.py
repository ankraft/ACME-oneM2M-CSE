 #
#	TextUI.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	A Textual UI for ACME CSE
#
"""	This module defines a textual UI for ACME CSE.
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Any
from enum import IntEnum, auto
import asyncio

from . import CSE
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..etc.Constants import Constants
from ..etc.Types import CSEStatus

from textual.app import App, ComposeResult
from textual.binding import Binding, Bindings
from textual.widgets import Header, Footer, Tree as TextualTree, Static, TextLog, Tabs, Tab, ContentSwitcher, Label, Button
from textual.widgets.tree import TreeNode
from textual.widgets._header import HeaderIcon, HeaderClock, HeaderTitle, HeaderClockSpace
from textual.containers import Container, Vertical, Horizontal, Content, Center, Grid
from textual.reactive import var
from textual.events import Event, Show
from textual.screen import Screen
from textual.reactive import Reactive
from textual.message import Message, MessageTarget

from rich.text import Text
from rich.pretty import Pretty


# TODO Delete resource? After better dialog option is available
# TODO Copy resource


_textUI:TextUI = None
"""	Active textUI instance """


class TextUI(object):

	__slots__ = (
		'startWithTUI',
		'theme',
		'refreshInterval',
		'tuiApp'
	)
	
	def __init__(self) -> None:
		global _textUI
		self.startWithTUI:bool = None
		self.theme:str = None
		self.refreshInterval:float = None
		self.tuiApp:ACMETuiApp = None

		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)	# type: ignore

		# Get configs
		self._assignConfig()

		# Add handlers for registrations here. This is not done in the textUI classes because it it
		# is not always clear when they are removed and re-created

		CSE.event.addHandler([CSE.event.aeHasRegistered, 									# type:ignore[attr-defined]
							  CSE.event.aeHasDeregistered, 									# type:ignore[attr-defined]
							  CSE.event.registreeCSEHasRegistered,							# type:ignore[attr-defined]
							  CSE.event.registreeCSEHasDeregistered,						# type:ignore[attr-defined]
							  CSE.event.registreeCSEUpdate,  								# type:ignore[attr-defined]
							  CSE.event.registeredToRemoteCSE], self.registrationUpdate)	# type:ignore[attr-defined]

		_textUI = self
		L.isInfo and L.log('TextUI initialized')

		
	def shutdown(self) -> bool:
		global _textUI
		if _textUI.tuiApp:
			_textUI.tuiApp.exit()
		#_textUI = None
		L.isInfo and L.log('TextUI shut down')
		return True


	def restart(self) -> None:
		"""	Restart the TextUI service.
		"""
		self._assignConfig()
		L.logDebug('TextUI restarted')


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.startWithTUI = Configuration.get('cse.textui.startWithTUI')
		self.theme = Configuration.get('cse.textui.theme')
		self.refreshInterval = Configuration.get('cse.textui.refreshInterval')
	

	def registrationUpdate(self, name:str, resource:Resource, dct:dict = None) -> None:
		if self.tuiApp and self.tuiApp.containerRegistrations:
			self.tuiApp.containerRegistrations.registrationsUpdate()

	
	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.textui.startWithTUI', 'cse.textui.theme', 'cse.textui.refreshInterval']:
			return
		
		# Configuration values
		self._assignConfig()

		# Restart TUI
		self.tuiApp.restart()
	

	def runUI(self) -> bool:

		# Disable console logging
		previousScreenLogging = L.enableScreenLogging
		L.enableScreenLogging = False

		while True and CSE.cseStatus == CSEStatus.RUNNING:
			self.tuiApp = ACMETuiApp()
			try:
				asyncio.run(self.tuiApp.run())
			except ValueError:	# This may have something to do with running in a non-async context. Ignore for now.
				L.console('Press # to return to UI')
			except Exception as e:
				L.logErr(str(e), exc = e)
			if self.tuiApp.quitReason != ACMETuiQuitReason.restart:
				break
		
		# Re-enable console logging
		L.enableScreenLogging = previousScreenLogging
		return self.tuiApp.quitReason != ACMETuiQuitReason.quitAll	# False leads to ACME quit



idTree = 'tree'
idInfo = 'info'
idRegs = 'registrations'
idConfigs = 'configurations'
idAbout = 'about'

_CSS = """
Screen {
	background: $surface-darken-1;
}

#tree-view {
	display: block; 
	scrollbar-gutter: stable;
	overflow: auto;    
	width: auto;    
	height: 100%;            
	dock: left;
	max-width: 50%;  
}


#resource-view {
	overflow: auto scroll;  
	min-width: 100%;
	padding: 1 1;
	/*background:red;*/
}

#stats-view {
	display: block;
	overflow: auto scroll;  
	min-width: 100%;
	padding: 1 1;
	/*background:red;*/
}

#regs-view {
	display: block;
	overflow: auto scroll;  
	min-width: 100%;
	padding: 1 1;
	/*background:red;*/
}

#configs-view {
	display: block;
	overflow: auto scroll;  
	min-width: 100%;
	padding: 1 1;
	/*background:red;*/
}

#about-view {
	display: block;
	overflow: auto scroll;  
	min-width: 100%;
	padding: 1 1;
	/*background:red;*/
}

#code {
	width: auto;    
}

.box {
	height: 100%;
	border: solid green;
}


"""


class ACMETuiQuitReason(IntEnum):
	undefined = auto()
	quitTUI = auto()
	quitAll = auto()
	restart = auto()


class ACMEHeaderTitle(HeaderTitle):
	"""Display the title / subtitle in the header."""

	def render(self) -> Text:
		return Text.from_markup(f'{Constants.textLogo}[dim] {CSE.cseType.name}-CSE : {CSE.cseCsi}', overflow = 'ellipsis')


class ACMEHeader(Header):

	def compose(self) -> ComposeResult:
		yield HeaderIcon()
		yield ACMEHeaderTitle()
		yield HeaderClock() if self._show_clock else HeaderClockSpace()


#
#	Resource Tree
#

class ACMEResourceTree(TextualTree):

	parentContainer:ACMEContainerTree = None

	async def _on_compose(self) -> None:
		self._update_tree()
		return await super()._on_compose()

	def _update_tree(self) -> None:
		self.clear()
		for r in self._retrieve_children(CSE.cseRi):
			self.root.add(r[0].rn, data = r[0].ri, allow_expand = r[1])
	

	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		if (_r := CSE.dispatcher.retrieveLocalResource(node.node.data)).status:
			# _textUI.tuiApp.resourceView.update(Pretty(_r.resource.asDict()))
			self.parentContainer.resourceView.update(Pretty(_r.resource.asDict()))


	def on_tree_node_selected(self, node:TextualTree.NodeSelected) -> None:
		if (_r := CSE.dispatcher.retrieveLocalResource(node.node.data)).status:
			# _textUI.tuiApp.resourceView.update(Pretty(_r.resource.asDict()))
			self.parentContainer.resourceView.update(Pretty(_r.resource.asDict(), expand_all = True))
		else:
			self.parentContainer.resourceView.update('[red]Resource not found')


	def on_tree_node_expanded(self, node:TextualTree.NodeSelected) -> None:
		node.node._children = []	# no available method?
		for r in self._retrieve_children(node.node.data):
			node.node.add(r[0].rn, data = r[0].ri, allow_expand = r[1])


	def _retrieve_children(self, ri:str) -> List[Tuple[Resource, bool]]:
		result:List[Tuple[Resource, bool]] = []
		for r in CSE.dispatcher.directChildResources(ri):
			if not r.isVirtual():
				result.append((r, len(CSE.dispatcher.directChildResources(r.ri)) > 0))
		return result


class ACMEContainerTree(Container):

	resourceTree:ACMEResourceTree

	BINDINGS = 	[ Binding('r', "refresh_tree", 'Refresh resource tree') 
				
				# TODO copy resource
				# TODO delete
				]

	def __init__(self) -> None:
		super().__init__(id = idTree)
		self.resourceTree = ACMEResourceTree(CSE.cseRn, data = CSE.cseRi, id = 'tree-view')
		self.resourceTree.parentContainer = self
		self.resourceView = Static('resource', expand = True)


	def compose(self) -> ComposeResult:
		self.resourceTree.focus()
		yield Container(
			self.resourceTree,
			Vertical(self.resourceView, id = 'resource-view'),
		)
	

	def action_refresh_tree(self) -> None:
		# _textUI.tuiApp.bell()
		self.resourceTree._update_tree()

	async def onShow(self) -> None:
		self.resourceTree._update_tree()
		self.resourceTree.focus()


#
#	Registrations
#

class ACMEContainerRegistrations(Container):

	def __init__(self) -> None:
		super().__init__(id = idRegs)
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
		if _textUI.tuiApp.content.current == idRegs:
			self.registrationsView.update(CSE.console.getRegistrationsRich())


#
#	Configurations
#

class ACMEContainerConfigurations(Container):

	def __init__(self) -> None:
		super().__init__(id = idConfigs)
		self.configurationsView = Static(expand = True)
		self._configurationsUpdate()


	def compose(self) -> ComposeResult:
		yield Container(
			Vertical(self.configurationsView, id = 'configs-view')
		)


	async def onShow(self) -> None:
		self._configurationsUpdate()


	def _configurationsUpdate(self) -> None:
		if _textUI.tuiApp.content.current == idConfigs:
			#_textUI.tuiApp.bell()
			self.configurationsView.update(CSE.console.getConfigurationRich())




#
#	Statistics
#

class ACMEContainerInfo(Container):

	def __init__(self) -> None:
		super().__init__(id = idInfo)
		self.statsView = Static(expand = True)
		self.set_interval(_textUI.refreshInterval, self._statsUpdate)

	def compose(self) -> ComposeResult:
		yield Container(
			Vertical(self.statsView, id = 'stats-view'),
		)


	async def onShow(self) -> None:
		self._statsUpdate()

	def _statsUpdate(self) -> None:
		if _textUI.tuiApp.content.current == idInfo:
			# _textUI.tuiApp.bell()
			self.statsView.update(CSE.console.getStatisticsRich())


#
#	Statistics
#

class ACMEContainerAbout(Container):

# 	logo = \
# f"""\
# [dim]███[/dim]     [{Constants.logoColor}] █████   ██████ ███    ███ ███████[/{Constants.logoColor}]     [dim]███[/dim] 
# [dim]██ [/dim]     [{Constants.logoColor}]██   ██ ██      ████  ████ ██     [/{Constants.logoColor}]     [dim] ██[/dim] 
# [dim]██ [/dim]     [{Constants.logoColor}]███████ ██      ██ ████ ██ █████  [/{Constants.logoColor}]     [dim] ██[/dim] 
# [dim]██ [/dim]     [{Constants.logoColor}]██   ██ ██      ██  ██  ██ ██     [/{Constants.logoColor}]     [dim] ██[/dim] 
# [dim]███[/dim]     [{Constants.logoColor}]██   ██  ██████ ██      ██ ███████[/{Constants.logoColor}]     [dim]███[/dim]""" 

	text = \
f"""\
[dim]███╗[/dim]    [{Constants.logoColor}] █████╗  ██████╗███╗   ███╗███████╗[/{Constants.logoColor}]    [dim]███╗[/dim]
[dim]██╔╝[/dim]    [{Constants.logoColor}]██╔══██╗██╔════╝████╗ ████║██╔════╝[/{Constants.logoColor}]    [dim]╚██║[/dim]
[dim]██║ [/dim]    [{Constants.logoColor}]███████║██║     ██╔████╔██║█████╗  [/{Constants.logoColor}]    [dim] ██║[/dim]
[dim]██║ [/dim]    [{Constants.logoColor}]██╔══██║██║     ██║╚██╔╝██║██╔══╝  [/{Constants.logoColor}]    [dim] ██║[/dim]
[dim]███╗[/dim]    [{Constants.logoColor}]██║  ██║╚██████╗██║ ╚═╝ ██║███████╗[/{Constants.logoColor}]    [dim]███║[/dim]
[dim]╚══╝[/dim]    [{Constants.logoColor}]╚═╝  ╚═╝ ╚═════╝╚═╝     ╚═╝╚══════╝[/{Constants.logoColor}]    [dim]╚══╝[/dim]

{Constants.version}


An open source CSE Middleware for Education

(c) 2022 by Andreas Kraft

Available under the BSD 3-Clause License"""

	socialLink =  Text('Social: ') + Text('@acmeCSE@mstdn.social', style='link https://mstdn.social/@acmeCSE') + Text(' ')

	link =  Text('GitHub: ') + Text('https://github.com/ankraft/ACME-oneM2M-CSE', style='link https://github.com/ankraft/ACME-oneM2M-CSE') + Text(' ')

	qrcode = \
"""\
█▀▀▀▀▀█ ▀▀▀▀▀▄█▀▄▄█  ▄█ ▄ █▀▀▀▀▀█
█ ███ █ ▀█▀▀  ███ █▄▄ █▀  █ ███ █
█ ▀▀▀ █ ▄▀▀▀▄██▀█▄▀▀██▀▀▀ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀▄█ █ ▀ ▀ █ ▀ ▀ ▀ ▀▀▀▀▀▀▀
▀▄▀▄ ▄▀▀ ███ ▀ ▀  ▄██ ▀█▄ ▄▀ ▄▀▄▀
▀▄▄█▄▀▀▄▄▀▄██▀█▄▄▀█▀ ▀█▀▀██▄▄█▀▀▄
▀ ▀ ██▀▄██ ▄▄██▀█▀█▀███ █ ▀ █ ▄██
█▀▄▀▀ ▀▀▀█▄▀  ▄▄█ ▀▄█  ▀ ▄▄██▄▄ ▀
▀▀▀ ▄ ▀▄▀████▄▄▄ ▄ ▄█▄ ██ █▀ ▄▀▀
█ ▄  █▀█▄▀█▄▀▄ ▀▀▄ █▄▄ ▀██▄▀▄█▀█▀
▀▄▀█ ▀▀ ▄█▀█ █ ▀ ▀   ▀ ▀▄▄▀█▀ ▄ ▄
▀▀▀ █▄▀▀▄ ▄▀▀█▄▀ ▀█▀  █ █▄█   ▄ █
▀▀ ▀  ▀ █ ▀▄▄▀ █▀  █▀  ██▀▀▀█ ▀█▄
█▀▀▀▀▀█ ▀ ▄▄▄▀ ▀█▀█▀▄▀█▄█ ▀ ██▀ █
█ ███ █  ▄▄▄ ▀▀▀█▀█ ████▀█▀██ ▄█  
█ ▀▀▀ █ ▀█▄▄▀▀▀▄█  ▄█ ▄█ ▀ ██▄▀▀▀
▀▀▀▀▀▀▀ ▀▀ ▀▀▀      ▀    ▀▀▀▀ ▀ ▀"""

												   
	def __init__(self) -> None:
		super().__init__(id = idAbout)
	
		self.logoView = Center(_l := Label(self.text))
		_l.styles.text_align = 'center'
		self.logoView.styles.padding = (4, 0, 0, 0)

		self.linkView = Center(Label(self.link))
		self.linkView.styles.padding = (2, 0, 0, 0)

		self.socialLinkView = Center(Label(self.socialLink))
		self.socialLinkView.styles.padding = (1, 0, 0, 0)

		self.qrcodeView = Center(Label(self.qrcode))
		self.qrcodeView.styles.padding = (8, 0, 0, 0)

		self.aboutView = Vertical(self.logoView, 
								  self.linkView,
								  self.socialLinkView,
								  self.qrcodeView,
								  id = 'about-view')


	def compose(self) -> ComposeResult:
		yield self.aboutView

	async def onShow(self) -> None:
		...


class QuitScreen(Screen):
	def compose(self) -> ComposeResult:
		yield Vertical(
			Static('Are you sure you want to quit?', id="question"),
			Static(' '),
			Horizontal(
				Button("Quit", variant="error", id="quit", classes = 'button'),
				Button("Cancel", variant="primary", id="cancel", classes = 'button')),
			id="dialog",
		)

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "quit":
			self.app.exit()
		else:
			self.app.pop_screen()



#
#	Main text UI
#

class ACMETuiApp(App):
	"""A Textual app to manage stopwatches."""

	BINDINGS = 	[ Binding('#', 'quit_tui', 'Console'),
				  Binding('Q', 'quit_acme', 'Quit ACME'),
				]

	CSS = _CSS


	logPanel:TextLog
	containerTree:ACMEContainerTree
	containerInfo:ACMEContainerInfo
	containerRegistrations:ACMEContainerRegistrations
	quitReason:ACMETuiQuitReason = ACMETuiQuitReason.undefined


	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""

		self.dark = _textUI.theme == 'dark'

		self.content = ContentSwitcher(initial = idTree)
		self.containerTree = ACMEContainerTree()
		self.containerRegistrations = ACMEContainerRegistrations()
		self.containerConfigs = ACMEContainerConfigurations()
		self.containerInfo = ACMEContainerInfo()
		self.containerAbout = ACMEContainerAbout()


		# self.logPanel = TextLog(id = 'log')
		yield ACMEHeader(show_clock = True)
		yield Tabs(
			Tab('Resources', id = 'tab-tree'),
			# Tab('AEs', id = 'tab-aes'),
			# Tab('Logs', id = 'tab-logs'),
			Tab('Registrations', id = 'tab-registrations'),
			Tab('Configurations', id = 'tab-configurations'),
			Tab('Infos', id = 'tab-info'),
			Tab('About', id = 'tab-about'),
		)
		with self.content:
			yield self.containerTree
			yield self.containerRegistrations
			yield self.containerConfigs
			yield self.containerInfo
			yield self.containerAbout
			yield Container(id = 'empty')

		yield Footer()


	async def on_tabs_tab_activated(self, event:Tabs.TabActivated) -> None:
		"""Handle TabActivated message sent by Tabs."""
		if event.tab.id == 'tab-tree':
			await self.containerTree.onShow()
			self.content.current = idTree
		elif event.tab.id == 'tab-registrations':
			self.content.current = idRegs
			await self.containerRegistrations.onShow()
		elif event.tab.id == 'tab-configurations':
			self.content.current = idConfigs
			await self.containerConfigs.onShow()
		elif event.tab.id == 'tab-info':
			self.content.current = idInfo
			await self.containerInfo.onShow()
		elif event.tab.id == 'tab-about':
			self.content.current = idAbout
			await self.containerInfo.onShow()
		else:
			self.content.current = 'empty'


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
