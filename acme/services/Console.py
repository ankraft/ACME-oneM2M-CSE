#
#	Console.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Console functions for ACME CSE
#
"""	This module defines console functions for the CSE.
"""

from __future__ import annotations
from typing import List, cast, Optional, Any, Tuple

import datetime, json, os, sys, webbrowser, socket
from enum import IntEnum, auto
from rich.live import Live
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
import plotext

from ..helpers.KeyHandler import FunctionKey, loop, stopLoop, waitForKeypress
from ..helpers.TextTools import simpleMatch
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..helpers.Interpreter import PContext, PError
from ..helpers.OrderedSet import OrderedSet
from ..etc.Constants import Constants
from ..etc.Types import CSEType, ResourceTypes, Operation
from ..etc.ResponseStatusCodes import ResponseException
from ..helpers.NetworkTools import getIPAddress
from ..etc.DateUtils import fromAbsRelTimestamp, toISO8601Date
from ..resources.Resource import Resource
from ..resources.CSEBase import getCSE
from ..services import CSE, Statistics
from ..services.Configuration import Configuration, documentationLinks
from ..services.Logging import Logging as L

# Used in many "rich" functions
_markup = Text.from_markup

# TODO support configevent!



class TreeMode(IntEnum):
	""" Available modes do display the resource tree
	"""

	NORMAL				= auto()
	"""	Mode - Normal """

	CONTENT				= auto()
	""" Mode - Show content """

	COMPACT				= auto()
	""" Mode - Compact """

	CONTENTONLY			= auto()
	"""	Mode - Content only """


	def __str__(self) -> str:
		"""	String representation of the TreeMode.

			Return:
				String representation.
		"""
		return self.name


	def succ(self) -> TreeMode:
		"""	Return the next enum value, and cycle to the beginning when reaching the end.

			Return:
				TreeMode value.
		"""
		members:list[TreeMode] = list(self.__class__)
		index = members.index(self) + 1
		return members[index] if index < len(members) else members[0]
	

	@classmethod
	def to(cls, t:str) -> TreeMode:
		"""	Return the enum from a string.

			Args:
				t: String representation of an enum value.

			Return:
				Enum value or *None*.
		"""
		return dict(cls.__members__.items()).get(t.upper())


	@classmethod
	def names(cls) -> list[str]:
		"""	Return all the enum names.

			Return:
				List of enum value.
		"""
		return list(cls.__members__.keys())

##############################################################################


class Console(object):
	"""	Console Manager class.
	
		Attributes:
			refreshInterval: Configuration setting. Refresh interval for various continuous display functions.
			hideResources: Configuration setting. List of resources to hide from tree view.
			treeMode: Configuration setting. Default tree mode.
			treeIncludeVirtualResources: Configuration setting. Indicates whether the tree view will include or exclude virtual resources.
			confirmQuit: Configuration setting. Terminating and quitting the CSE must be confirmed.

			interruptContinous: Indication whether any continuous display function should terminate.
			previousTreeRi: Resource ID of the previous sub-tree display.
			previousInspectRi: Resource ID of the previous resource inspection.
			previosInspectChildrenRi: Resource ID of the previous resource + child resource inspection.
			previousScript: Name of the previous script run.
			previousArgument: Previous script arguments.
			previousGraphRi: Resource ID of the previous graph display.
	"""

	__slots__ = (
		'interruptContinous',
		'previousTreeRi',
		'previousInspectRi',
		'previosInspectChildrenRi',
		'previousScript',
		'previousArgument',
		'previousGraphRi',
		'previousRequestRi',
		'tuiApp',
		
		'refreshInterval',
		'hideResources',
		'treeMode',
		'treeIncludeVirtualResources',
		'confirmQuit',
		'theme',

		'_eventKeyboard',
		'_exitFromTUI',

		
	)

	def __init__(self) -> None:
		"""	Initialization of a *Console* instance.
		"""

		# Get the configuration settings
		self._assignConfig()

		self.interruptContinous = False
		self.previousTreeRi = ''
		self.previousInspectRi = ''
		self.previousRequestRi = ''
		self.previosInspectChildrenRi = ''
		self.previousScript = ''
		self.previousArgument = ''
		self.previousGraphRi = ''

		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)			# type: ignore

		# Add handler for restart event
		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore

		self._eventKeyboard = CSE.event.keyboard			# type: ignore [attr-defined]
		self._exitFromTUI = False

		L.isInfo and L.log('Console initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the *Console* instance.
			
			Return:
				Always returns *True*.
		"""
		L.isInfo and L.log('Console shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the TimeSeriesManager service.
		"""
		self.interruptContinous = True	# This will indirectly interrupt a running continous console command
		L.isDebug and L.logDebug('Console restarted')


	def _assignConfig(self) -> None:
		"""	Assign configuration settings.
		"""
		self.refreshInterval:float = Configuration.get('console.refreshInterval')
		self.hideResources:list[str] = Configuration.get('console.hideResources')
		self.treeMode:TreeMode = Configuration.get('console.treeMode')
		self.treeIncludeVirtualResources:bool = Configuration.get('console.treeIncludeVirtualResources')
		self.confirmQuit:bool = Configuration.get('console.confirmQuit')
		self.theme:str = Configuration.get('console.theme')


	def configUpdate(self, name:str,
						   key:Optional[str] = None, 
						   value:Any = None) -> None:
		"""	Handle configuration updates.

			Args:
				name: Event name.
				key: The key for the configuration setting that is updated.
				value: The new configuration setting.
		"""
		if key not in [ 'console.refreshInterval',
						'console.hideResources',
						'console.treeMode',
						'console.treeIncludeVirtualResources',
						'console.confirmQuit']:
			return
		self._assignConfig()


	def run(self) -> None:
		"""	Run the console.
		"""
		#
		#	Enter an endless loop.
		#	Execute keyboard commands in the keyboardHandler's loop() function.
		#
		commands = {
			'?'    			 	: self.help,
			'h'					: self.help,
			FunctionKey.F1		: self.help,
			'A'					: self.about,
			FunctionKey.CR		: lambda c: L.console(),	# 1 empty line
			FunctionKey.LF		: lambda c: L.console(),	# 1 empty line
			FunctionKey.CTRL_C 	: self.shutdownCSE,			# See handler below
			'c'					: self.configuration,
			'C'					: self.clearScreen,
			'D'					: self.deleteResource,
			# 'E'					: self.exportResources,
			'f'					: self.showRequests,
			'F'					: self.showAllRequests,
			FunctionKey.CTRL_F	: self.deleteRequests,
			FunctionKey.CTRL_G	: self.continuesPlotGraph,
			'G'					: self.plotGraph,
			'i'					: self.inspectResource,
			'I'					: self.inspectResourceChildren,
			FunctionKey.CTRL_I	: self.continuousInspectResource,
			'k'					: self.katalogScripts,
			'l'     			: self.toggleScreenLogging,
			'L'     			: self.toggleLogging,
			'Q'					: self.shutdownCSE,		# See handler below
			'r'					: self.registrations,
			'R'					: self.runScript,
			's'					: self.statistics,
			FunctionKey.CTRL_S	: self.continuousStatistics,
			't'					: self.resourceTree,
			FunctionKey.CTRL_T	: self.continuousTree,
			'T'					: self.childResourceTree,
			'u'					: self.openWebUI,
			'='					: self.printLine,
			'#'					: self.runTUI,
			#'Z'		: self.resetCSE,
		}
		#	Endless runtime loop. This handles key input & commands
		#	The CSE's shutdown happens in one of the key handlers below
		if not CSE.isHeadless:
			L.console('Press "?" for help, or "#" for the Text UI.')
		
		loop(commands, 
			 catchKeyboardInterrupt = True, 
			 headless = CSE.isHeadless,
			 catchAll = lambda ch: CSE.event.keyboard(ch), # type: ignore [attr-defined]
			 nextKey = '#' if CSE.textUI.startWithTUI else None,
			 postCommandHandler = self._postCommandHandler,
			 ignoreException = False,
			 exceptionHandler = lambda ch: L.setEnableScreenLogging(True))
		CSE.shutdown()


	def stop(self) -> None:
		"""	Stop the console.
		"""
		stopLoop()

	##############################################################################
	#
	#	Various keyboard command handlers
	#

	def _about(self, header:str = None) -> None:
		"""	Print a headline for a command.

			Args:
				header: Optional header to print.
		"""
		L.console(f'\n[white]{Constants.textLogo} ', plain = True, end = '')
		L.console(f'oneM2M CSE {Constants.version}', nl = False,)
		if header:
			L.console(header, nl = True, isHeader = True)
	

	def _postCommandHandler(self, key:str) -> str:
		# TODO doc
		if self._exitFromTUI:
			if key in ['Q', FunctionKey.CTRL_C]:
				return '#'
			self._exitFromTUI = False
		return None


	def help(self, key:str) -> None:
		"""	Print help for keyboard commands.

			Args:
				key: Input key. Ignored.
		"""
		self._about('Console Commands')

		# Built-in Console commands
		commands = [
			# (Key, description, built-in)
			('h, ?, F1', 'This help'),
			('A', 'About'),
			('Q, ^C', 'Shutdown CSE'),
			('c', 'Show configuration'),
			('C', 'Clear the console screen'),
			('D', 'Delete resource'),
			# ('E', 'Export resource tree to [i]init[/i] directory'),
			('f', 'Show requests history for a resource'),
			('F', 'Show all requests history'),
			('^F', 'Clear requests history'),
			('G', 'Plot graph (only for container)'),
			('^G', 'Plot & refresh graph continuously (only for container)'),
			('i', 'Inspect resource'),
			('I', 'Inspect resource and child resources'),
			('k', 'Catalog of scripts'),
			('^K', 'Show resource continuously'),
			('l', 'Toggle screen logging on/off'),
			('L', 'Toggle through log levels'),
			('r', 'Show CSE registrations'),
			('s', 'Show statistics'),
			('^S', 'Show & refresh statistics continuously'),
			('t', 'Show resource tree'),
			('T', 'Show child resource tree'),
			('^T', 'Show & refresh resource tree continuously'),
			('u', 'Open web UI'),
			('#', 'Open/close text UI'),
			('=', 'Print a separator line to the log'),
		]

		table = Table(row_styles = [ '', L.tableRowStyle])
		table.add_column('Key', no_wrap = True, justify = 'left', min_width = 10)
		table.add_column('Description', no_wrap = False)
		table.add_column('Script', no_wrap = True, justify = 'center', min_width = 6)
		for each in commands:
			table.add_row(each[0], each[1], '', end_section = each == commands[-1])

		# Add Scripts that have a key binding
		for eachScript in (scripts :=  sorted(CSE.script.findScripts(meta = 'onKey'), key = lambda x: x.getMeta('onKey'))):
			# table.add_row(eachScript.meta.get('onkey'), eachScript.meta.get('description'), '✔︎')
			table.add_row(eachScript.meta.get('onKey'), eachScript.meta.get('description'), '+')
		L.console(table, nl=True)


	def about(self, key:str) -> None:
		"""	Print QR-code for keyboard commands.


		Args:
			key: Input key. Ignored.
		"""
		self._about()
		L.console(Text(f"""An open source CSE Middleware for Education

{Constants.copyright}

Available under the BSD 3-Clause License
"""))
		L.console(Text('https://github.com/ankraft/ACME-oneM2M-CSE', style='link https://github.com/ankraft/ACME-oneM2M-CSE'), nl=True)
		L.console(Text("""
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
▀▀▀▀▀▀▀ ▀▀ ▀▀▀      ▀    ▀▀▀▀ ▀ ▀
"""), nl=True)



	def shutdownCSE(self, key:str) -> None:
		"""	Shutdown the CSE. Confirm shutdown before actually doing that.

			Args:
				key: Input key. Ignored.
		"""
		if not CSE.isHeadless:
			if self.confirmQuit:
				L.off()
				L.console('Press quit-key again to confirm -> ', plain=True, end='')
				if waitForKeypress(5) not in ['Q', '\x03']:
					L.console('canceled')
					L.on()
					return
				L.console('confirmed')
				L.on()
		sys.exit()


	def toggleScreenLogging(self, key:str) -> None:
		"""	Toggle screen logging.

			Args:
				key: Input key. Ignored.
		"""
		L.enableScreenLogging = not L.enableScreenLogging
		L.console(f'Screen logging enabled -> **{L.enableScreenLogging}**')


	def toggleLogging(self, key:str) -> None:
		"""	Toggle through the log levels.

			Args:
				key: Input key. Ignored.
		"""
		L.setLogLevel(L.logLevel.next())
		L.console(f'New log level -> **{str(L.logLevel)}**')
	

	def printLine(self, key:str) -> None:
		"""	Print a separator Line to the log.

			Args:
				key: Input key. Ignored.
		"""
		L.logDivider()


	def configuration(self, key:str) -> None:
		"""	Print the configuration.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Configuration', isHeader = True)
		L.console(self.getConfigurationRich())


	def clearScreen(self, key:str) -> None:
		"""	Clear the console screen.

			Args:
				key: Input key. Ignored.
		"""
		L.consoleClear()


	def resourceTree(self, key:str) -> None:
		"""	Render the CSE's resource tree.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Resource Tree', isHeader = True)
		L.console(self.getResourceTreeRich())
		L.console()


	def childResourceTree(self, key:str) -> None:
		"""	Render the CSE's resource tree, beginning with a child resource.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Child Resource Tree', isHeader = True)
		L.off()
		
		if not (ri := L.consolePrompt('ri', default = self.previousTreeRi)):
			self.previousTreeRi = ri
			L.console()
		elif len(ri) > 0:
			if tree := self.getResourceTreeRich(parent = ri, withProgress = False):
				L.console(tree)
			else:
				L.console('not found', isError = True)

		L.on()


	def continuousTree(self, key:str) -> None:
		"""	Render a continuous CSE resource tree view.

			Args:
				key: Input key. Ignored.
		"""

		L.off()
		self.interruptContinous = False
		self.clearScreen(key)
		self._about('Resource Tree')
		with Live(self.getResourceTreeRich(style = L.terminalStyle, withProgress = False), auto_refresh = False) as live:

			def _updateTree(name:str = None, _:Resource = None) -> None:
				"""	Callback to update the on-screen tree on an event.
				"""
				live.update(self.getResourceTreeRich(style = L.terminalStyle, withProgress = False), refresh = True)
			
			# Register events for which the tree is refreshed
			CSE.event.addHandler([CSE.event.createResource, CSE.event.deleteResource, CSE.event.updateResource],  _updateTree)		# type:ignore[attr-defined]

			while (ch := waitForKeypress(self.refreshInterval)) in [None, '\x14']:
				if ch == '\x14':	# Toggle through tree modes
					self.treeMode = self.treeMode.succ()
					_updateTree()
				if self.interruptContinous:
					break

			# Remove the event callback for the events 
			CSE.event.removeHandler([CSE.event.createResource, CSE.event.deleteResource, CSE.event.updateResource], _updateTree)	# type:ignore[attr-defined]

		# Reset the screen and logging
		self.clearScreen(key)
		L.on()


	def registrations(self, key:str) -> None:
		"""	Render CSE registrations.

			Args:
				key: Input key. Ignored.
		"""
		L.console('CSE Registrations', isHeader = True)
		# poas = '\n'.join([f'    - {poa}' for poa in CSE.csePOA])
		# L.console(f'- **Point of Access**\n{poas}\n{self.getRegistrationsRich()}')
		L.console()
		try:
			L.console(self.getRegistrationsRich())
		except Exception as e:
			L.logErr('', exc = e)


	def statistics(self, key:str) -> None:
		""" Render various statistics & counts.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Statistics', isHeader = True)
		L.console(self.getStatisticsRich())
		L.console()


	def continuousStatistics(self, key:str) -> None:
		"""	Render a continous statistics view.
		
			Args:
				key: Input key. Ignored.
		"""
		L.off()
		self.interruptContinous = False
		self.clearScreen(key)
		self._about('Statistics')
		with Live(self.getStatisticsRich(style = L.terminalStyle, withProgress = False), auto_refresh = False) as live:
			while not waitForKeypress(self.refreshInterval):
				live.update(self.getStatisticsRich(style = L.terminalStyle, withProgress = False), refresh=True)
				if self.interruptContinous:
					break

		self.clearScreen(key)
		L.on()


	def deleteResource(self, key:str) -> None:
		"""	Delete a resource from the CSE.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Delete Resource', isHeader = True)
		L.off()
		if (ri := L.consolePrompt('ri')):
			try:
				resource = CSE.dispatcher.retrieveResource(ri)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else:
				try:
					CSE.dispatcher.deleteLocalResource(resource, withDeregistration = True)
				except ResponseException as e:
					L.console(e.dbg, isError = True)
				else:
					L.console('ok')
		L.on()


	def inspectResource(self, key:str) -> None:
		"""	Show a resource.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Inspect Resource', isHeader = True)
		L.off()

		if (ri := L.consolePrompt('ri', default = self.previousInspectRi)):
			self.previousInspectRi = ri
			resource = CSE.dispatcher.retrieveResource(ri)
			L.console(resource.asDict())
		L.on()		


	def inspectResourceChildren(self, key:str) -> None:
		"""	Show a resource and its children.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Inspect Resource and Children', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('ri', default = self.previosInspectChildrenRi)):
			self.previosInspectChildrenRi = ri
			try:
				resource = CSE.dispatcher.retrieveResource(ri)
				children = CSE.dispatcher.discoverResources(ri, originator = CSE.cseOriginator)
				CSE.dispatcher.resourceTreeDict(children, resource)	# the function call add attributes to the target resource
				L.console(resource.asDict())
			except ResponseException as e:
				L.console(e.dbg, isError = True)
		L.on()


	def continuousInspectResource(self, key:str) -> None:
		"""	Render a resource continuously.


			Args:
				key: Input key. Ignored.
		"""
		L.console('Inspect Resource Continuously', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('ri', default = self.previousInspectRi)):
			self.previousInspectRi = ri
			try:
				resource = CSE.dispatcher.retrieveResource(ri, postRetrieveHook = True)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else: 
				self.clearScreen(key)
				self._about(f'Inspect Resource: {ri}')
				self.interruptContinous = False
				endMessage:str = None
				with Live(Pretty(resource.asDict()), console = L._console, auto_refresh = False) as live:

					def _updateResource(name:str, r:Resource = None) -> None:
						"""	Callback to update the on-screen resource on an event.
						"""
						try:
							resource = CSE.dispatcher.retrieveResource(ri, postRetrieveHook = True)
						except ResponseException as e:
							endMessage = f'Resource is not available anymore: {ri}'
							self.interruptContinous = True
							return
						live.update(Pretty(resource.asDict()), refresh = True)
					
					# Register events for which the resource is refreshed
					CSE.event.addHandler([CSE.event.createResource, CSE.event.deleteResource, CSE.event.updateResource],  _updateResource)		# type:ignore[attr-defined]

					while waitForKeypress(self.refreshInterval) in [None, '\x09']:
						if self.interruptContinous:
							break

					# Remove the event callback for the events 
					CSE.event.removeHandler([CSE.event.createResource, CSE.event.deleteResource, CSE.event.updateResource], _updateResource)	# type:ignore[attr-defined]

				# Reset the screen and show error message if there is one
				self.clearScreen(key)
				if endMessage:
					L.console(endMessage, isError = True)

		# re-enable logging
		L.on()


	def katalogScripts(self, key:str) -> None:
		"""	List a catalog of the loaded scripts.

			Args:
				key: Input key. Ignored.
		"""
		from rich.style import Style
		L.console('Script Catalog', isHeader = True)
		L.off()
		table = Table(row_styles = [ '', L.tableRowStyle])
		table.add_column('Script', no_wrap = True)
		table.add_column('Description / Usage')
		table.add_column('UT ', no_wrap = True, justify = 'center')
		table.add_column('Key ', no_wrap = True, justify = 'center')
		table.add_column('Run at', no_wrap = True, justify = 'center')
		for n in CSE.script.findScripts(name = '*'):
			if 'hidden' not in n.meta:
				desc = f'{n.getMeta("description")}\n[dim]{n.getMeta("usage")}'
				ut = n.meta.get('uppertester') is not None
				at = n.getMeta('at')
				key = n.getMeta('onKey')
				table.add_row(n.scriptName, 
							  desc, 
							  # '✔︎' if ut else '',
							  '+' if ut else '',
							  key,
							  at )
		L.console(table, nl = True)
		L.on()


	# def exportResources(self, key:str) -> None:
	# 	"""	Export resources to the initialization directory.

	# 		Only resources that have **not** been imported are exported.
	# 		The result is a script that can be used to re-build a previous resource tree.

	# 		Args:
	# 			key: Input key. Ignored.
	# 	"""
	# 	L.console('Export Resources', isHeader = True)
	# 	L.off()
	# 	try:
	# 		if not (resdis := CSE.dispatcher.discoverResources(CSE.cseRi, originator = CSE.cseOriginator)).status:
	# 			L.console(resdis.dbg, isError=True)
	# 		else:
	# 			resources:list[Resource] = []
	# 			for r in cast(List[Resource], resdis.data):
	# 				if r.isImported:
	# 					continue
	# 				resources.append(r)
	# 			if resources:
	# 				fn = f'{datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")}.as'
	# 				fpn = f'{CSE.importer.resourcePath}/{fn}'
	# 				L.console(f'Exporting to {fn}')
	# 				with open(fpn, 'w') as exportFile:
	# 					exportFile.write(f'expandMacros off\n')
	# 					for r in resources:
	# 						exportFile.write(f'originator {r.getOriginator()}\n')
	# 						exportFile.write(f'print Importing {r.ri}\n')
	# 						exportFile.write('importraw\n')
	# 						json.dump(r.asDict(), exportFile, indent=4, sort_keys=True)
	# 						exportFile.write('\n')
	# 					exportFile.write(f'expandMacros on\n')
	# 			L.console(f'Exported {len(resources)} resources')
	# 	except Exception as e:
	# 		import traceback
	# 		print(traceback.format_exc())
	# 		L.inspect(e)
	# 	L.on()
	

	def runScript(self, key:str) -> None:
		"""	Run a script from one of the script directories.

			Args:
				key: Input key. Ignored.		
		"""

		def finished(pcontext:PContext, argument:str) -> None:
			if (error := pcontext.error)[0] == PError.noError:
				L.console(f'Result: {pcontext.result}')
			else:
				L.console(f'Error in {pcontext.scriptName}:{error[1]}: {error[2]}', isError = True)


		L.console('Run ACMEScript', isHeader = True)
		L.off()		
		if (name := L.consolePrompt('Script name', nl = False, default = self.previousScript)):
			self.previousScript = name
			if len(scripts := CSE.script.findScripts(name = name)) != 1:
				L.console(f'Script {name} not found', isError = True, nlb = True)
				L.on()
				return
			argument = L.consolePrompt('Arguments', default = self.previousArgument)
			self.previousArgument = argument
			pcontext = scripts[0]
			L.on()	# Turn on log before running the script
			try:
				CSE.script.runScript(pcontext, arguments = argument, background = True, finished = finished)
			except Exception as e:
				L.logErr(f'Exception during script execution: {str(e)}', exc = e)

		L.on()


	def openWebUI(self, key:str) -> None:
		"""	Open the web UI in the default web browser.

			Args:
				key: Input key. Ignored.
		"""
		webbrowser.open(f'{CSE.httpServer.serverAddress}?open')


	def _plotGraph(self, resource:Resource) -> None:
		"""	Plot a single graph from the child-resources of a container-like resource.

			Args:
				resource: The parent resource for the data instance resources.
		"""
			
		# plot
		try:
			cins = CSE.dispatcher.retrieveDirectChildResources(resource.ri, ResourceTypes.CIN)
			x = range(1, (lcins := len(cins)) + 1)
			y = [ float(each.con) for each in cins ]
			cols, rows = plotext.terminal_size()

			plotext.canvas_color('default')
			plotext.axes_color('default')
			plotext.ticks_color(L.terminalStyleRGBTupple)
			plotext.frame(True)
			plotext.plot_size(None, rows/2)
			plotext.xticks([1, int(lcins/4), int(lcins/4) * 2, int(lcins/4) * 3, lcins])

			plotext.title(f'{resource.getSrn()} ({resource.ri})')
			plotext.plot(x, y, color = L.terminalStyleRGBTupple)
			plotext.show()
			plotext.clear_figure()
		except Exception as e:
			L.logErr(str(e), exc = e)
		

	def plotGraph(self, key:str) -> None:
		"""	Plot a graph from the instance data of a container.

			Attention:
				Only `CNT` and `CIN` resources are currently supported.

			Args:
				key: Input key. Ignored.
		"""
		# TODO doc
		L.console('Plot Graph', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('Container ri', default = self.previousGraphRi)):
			self.previousGraphRi = ri
			try:
				resource = CSE.dispatcher.retrieveResource(ri)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else:
				if resource.ty != ResourceTypes.CNT:
					L.console('resource must be a <container>', isError = True)
				self._plotGraph(resource)
		L.on()


	def continuesPlotGraph(self, key:str) -> None:
		"""	Continuous plot a graph from the instance data of a container.
		
			See also:
				- `plotGraph()`

			Args:
				key: Input key. Ignored.
		"""

		pri:str = None

		def _plot(name:str = None, resource:Resource = None) -> bool:
			if resource.ri != pri:	# filter only the container we want to observe
				return True
			self.clearScreen(None)
			L.console('Plot Graph', isHeader = True)
			self._plotGraph(resource)
			return True

		L.off()
		if (ri := L.consolePrompt('Container ri', default = self.previousGraphRi)):
			self.previousGraphRi = ri
			try:
				resource = CSE.dispatcher.retrieveResource(ri)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else:
				if resource.ty != ResourceTypes.CNT:
					L.console('resource must be a <container>', isError = True)
			
				# Register for chil-added event (which would lead to a re-drawing of the graph)
				CSE.event.addHandler(CSE.event.createChildResource,  _plot)		# type:ignore [attr-defined]

				# Remember the parent ri
				pri = resource.ri

				# Plot grapth for the first time
				_plot(resource = resource)	

				# Wait for any keypress
				self.interruptContinous = False
				while waitForKeypress(self.refreshInterval) is None:
					if self.interruptContinous:
						break

				# Remove the event callback for the events 
				CSE.event.removeHandler(CSE.event.createChildResource, _plot)	# type:ignore[attr-defined]
				self.clearScreen(key)

		# Reset the screen and logging
		L.on()


	def runTUI(self, key:str) -> None:
		"""	Open the text UI.
		
			Args:
				key: Input key. Ignored.
		"""
		if not CSE.textUI.runUI():
			raise KeyboardInterrupt()


	def showRequests(self, key:str) -> None:
		"""	Show the requests for a resource.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Resource Requests', isHeader = True)
		L.off()
		if (ri := L.consolePrompt('ri', default = self.previousRequestRi)):
			self.previousRequestRi = ri
			table, uml = self.getRequestsRich(ri)
			L.console(table)
			L.console(uml, plain = True)
		L.on()		


	def showAllRequests(self, key:str) -> None:
		"""	Show all the requests.

			Args:
				key: Input key. Ignored.
		"""
		L.off()
		table, uml = self.getRequestsRich()
		L.console(table)
		L.console(uml, plain = True)
		L.on()
	

	def deleteRequests(self, key:str) -> None:
		"""	Delete all requests.
		
			Args:
				key: Input key. Ignored.
		"""
		L.console('Delete all requests')
		CSE.storage.deleteRequests()



	#########################################################################
	#
	#	Generators for rich output
	#

	def getRegistrationsRich(self) -> Table:
		"""	Create and return an overview about the registrar, registrees, and
			descendant CSE's.

			Return:
				Rich formatted string.
		"""

		def _addCSERow(table:Table, style:Style, cse:Resource, registrarCSE:Resource, registrees:List[str]) -> None:
			table.add_row(cse.csi, 
						  CSEType(cse.cst.value if isinstance(cse.cst, CSEType) else cse.cst).name, 
						  cse.rn, 
						  cse.ri, 
						  '' if not cse.srv else ', '.join(cse.srv),
						  str(cse.rr), 
						  '' if cse.poa is None else ', '.join(cse.poa),
						  '' if not registrarCSE else registrarCSE.csi,
						  '' if not registrees else ', '.join(registrees),
						  style = style)

		tableCSE = Table(row_styles = [ '', L.tableRowStyle], box = None, expand = True)
		tableCSE.add_column(_markup('[u]CSE-ID[/u]\n'), no_wrap = True)
		tableCSE.add_column(_markup('[u]Type[/u]\n'), no_wrap = True)
		tableCSE.add_column(_markup('[u]Name[/u]\n'), no_wrap = True)
		tableCSE.add_column(_markup('[u]Resource ID[/u]\n'), width = 12, no_wrap = True)
		tableCSE.add_column(_markup('[u]Release[/u]\n'), no_wrap = False)
		tableCSE.add_column(_markup('[u]Reachable[/u]\n'), no_wrap = True)
		tableCSE.add_column(_markup('[u]POA[/u]\n'), no_wrap = False)
		tableCSE.add_column(_markup('[u]Registrar[/u]\n'), no_wrap = True)
		tableCSE.add_column(_markup('[u]Registrees[/u]\n'), no_wrap = False)

		cse = getCSE()
		_addCSERow(tableCSE, Style(italic = True, bold = True), cse, CSE.remote.registrarCSE, CSE.remote.descendantCSR.keys()) #type:ignore[arg-type]
		for csr in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.CSR):
			if CSE.remote.registrarCSE and csr.csi == CSE.remote.registrarCSE.csi:
				_addCSERow(tableCSE, None, csr, None, [cse.csi] + csr.dcse)
			else:
				_addCSERow(tableCSE, None, csr, cse, csr.dcse)
		
		gridCSE = Table.grid(expand = True)
		gridCSE.add_column()
		gridCSE.add_row(_markup('[u b]Common Services Entities (CSE)[/u b]\n\n'))
		gridCSE.add_row(tableCSE)
		

		tableAE = Table(row_styles = [ '', L.tableRowStyle], box = None, expand = True)
		tableAE.add_column(_markup('[u]AE-ID[/u]\n'), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]Name[/u]\n'), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]Resource ID[/u]\n'), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]APP-ID[/u]\n'), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]Reachable[/u]\n'), width = 5, no_wrap = True)
		tableAE.add_column(_markup('[u]POA[/u]\n'), width = 15, no_wrap = False)

		for ae in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.AE):
			tableAE.add_row(ae.aei, 
							ae.rn, 
							ae.ri, 
							ae.api, 
							str(ae.rr), 
							'' if ae.poa is None else ', '.join(ae.poa))

		gridAE = Table.grid(expand = True)
		gridAE.add_column()
		gridAE.add_row(_markup('[u b]Application Entities (AE)[/u b]\n\n'))
		gridAE.add_row(tableAE)


		result = Table.grid(expand = True)
		result.add_column()
		# result.add_row(_markup('[u b]Common Services Entities (CSE)[/u b]\n'))
		# result.add_row(Panel(tableCSE))
		result.add_row(Panel(gridCSE))
		# result.add_row(Text(' '))
		# result.add_row(_markup('[u b]Application Entities (AE)[/u b]\n'))
		# result.add_row(Panel(tableAE))
		result.add_row(Panel(gridAE))

		return result
		# result = ''

		# if CSE.cseType != CSEType.IN:
		# 	result += f'- **Registrar CSE**\n'
		# 	if CSE.remote.registrarAddress:
		# 		registrarCSE = CSE.remote.registrarCSE
		# 		registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
		# 		result += f'    - {CSE.remote.registrarCSI[1:]} ({registrarType}) @ {CSE.remote.registrarAddress}\n'
		# 	else:
		# 		result += '   - None'

		# if CSE.cseType != CSEType.ASN:
		# 	result += f'- **Registree CSEs**\n'
		# 	if len(CSE.remote.descendantCSR) > 0:
		# 		for desc in CSE.remote.descendantCSR.keys():
		# 			(csr, _) = CSE.remote.descendantCSR[desc]
		# 			if csr:
		# 				result += f'  - {desc[1:]} ({CSEType(csr.cst).name}) @ {csr.poa}\n'
		# 				for desc2 in CSE.remote.descendantCSR.keys():
		# 					(csr2, atCsi2) = CSE.remote.descendantCSR[desc2]
		# 					if not csr2 and atCsi2 == desc:
		# 						result += f'    - {desc2[1:]}\n'
		# 	else:
		# 		result += '    - None'
	
		# return result if len(result) else 'None'
		

# TODO events transit requests
# TODO notifications
	def getStatisticsRich(self, 
						  style:Optional[Style] = Style(), 
						  withProgress:Optional[bool] = True) -> Table:
		"""	Generate an overview about various resources, event counts, and more.

			Args:
				style: Rich style.
				withProgress: Display with progress indicator.
			
			Return:
				Rich Table object.
		"""

		def _stats() -> Table:
			#
			#	Right columns
			#

			stats = CSE.statistics.getStats()

			if CSE.statistics.statisticsEnabled:
				resourceOps  =  _markup('[underline]Operations[/underline]\n')
				resourceOps += 	'\n'
				resourceOps +=  f'Created       : {stats.get(Statistics.createdResources, 0)}\n'
				resourceOps +=  f'Updated       : {stats.get(Statistics.updatedResources, 0)}\n'
				resourceOps +=  f'Deleted       : {stats.get(Statistics.deletedResources, 0)}\n'
				resourceOps +=  f'Expired       : {stats.get(Statistics.expiredResources, 0)}\n'
				resourceOps +=  f'Notifications : {stats.get(Statistics.notifications, 0)}\n'
				resourceOps +=  _markup(f'\n[dim]Includes virtual\nresources[/dim]')

				httpReceived  = _markup('[underline]HTTP:R[/underline]\n')
				httpReceived += 	'\n'
				httpReceived += f'C : {stats.get(Statistics.httpCreates, 0)}\n'
				httpReceived += f'R : {stats.get(Statistics.httpRetrieves, 0)}\n'
				httpReceived += f'U : {stats.get(Statistics.httpUpdates, 0)}\n'
				httpReceived += f'D : {stats.get(Statistics.httpDeletes, 0)}\n'

				httpSent  = 	_markup('[underline]HTTP:S[/underline]\n')
				httpSent += 	'\n'
				httpSent += 	f'C : {stats.get(Statistics.httpSendCreates, 0)}\n'
				httpSent += 	f'R : {stats.get(Statistics.httpSendRetrieves, 0)}\n'
				httpSent += 	f'U : {stats.get(Statistics.httpSendUpdates, 0)}\n'
				httpSent += 	f'D : {stats.get(Statistics.httpSendDeletes, 0)}\n'

				mqttReceived  = _markup('[underline]MQTT:R[/underline]\n')
				mqttReceived += 	'\n'
				mqttReceived += f'C : {stats.get(Statistics.mqttCreates, 0)}\n'
				mqttReceived += f'R : {stats.get(Statistics.mqttRetrieves, 0)}\n'
				mqttReceived += f'U : {stats.get(Statistics.mqttUpdates, 0)}\n'
				mqttReceived += f'D : {stats.get(Statistics.mqttDeletes, 0)}\n'

				mqttSent  = 	_markup('[underline]MQTT:S[/underline]\n')
				mqttSent += 	'\n'
				mqttSent += 	f'C : {stats.get(Statistics.mqttSendCreates, 0)}\n'
				mqttSent += 	f'R : {stats.get(Statistics.mqttSendRetrieves, 0)}\n'
				mqttSent += 	f'U : {stats.get(Statistics.mqttSendUpdates, 0)}\n'
				mqttSent += 	f'D : {stats.get(Statistics.mqttSendDeletes, 0)}\n'


				logs  = _markup('[underline]Logs[/underline]\n')
				logs += '\n'
				logs += f'LogLevel : {str(L.logLevel)}\n'
				logs += f'Errors   : {stats.get(Statistics.logErrors, 0)}\n'
				logs += f'Warnings : {stats.get(Statistics.logWarnings, 0)}\n'

			else:
				resourceOps  = _markup('\n[dim]statistics are disabled[/dim]\n')
				httpReceived = _markup('\n[dim]statistics are disabled[/dim]\n')
				httpSent     = _markup('\n[dim]statistics are disabled[/dim]\n')
				logs         = _markup('\n[dim]statistics are disabled[/dim]\n')


			misc  = _markup('[underline]Misc[/underline]\n')
			misc += '\n'
			misc += f'CSE-ID | CSE-Name : {CSE.cseCsi}  |  {CSE.cseRn}\n'
			misc += f'Hostname          : {socket.gethostname()}\n'
			# misc += f'IP-Address : {socket.gethostbyname(socket.gethostname() + ".local")}\n'
			try:
				misc += f'IP-Address        : {getIPAddress()}\n'
			except Exception as e:
				print(e)
			misc += f'PoA               : {CSE.csePOA[0]}\n'
			if len(CSE.csePOA) > 1:
				misc += ''.join([f'                    {poa}\n' for poa in CSE.csePOA[1:] ])

			misc += f'StartTime         : {datetime.datetime.fromtimestamp(fromAbsRelTimestamp(cast(str, stats[Statistics.cseStartUpTime]), withMicroseconds=False))} (UTC)\n'
			misc += f'Uptime            : {stats.get(Statistics.cseUpTime, "")}\n'

			misc += '\n'
			if hasattr(os, 'getloadavg'):
				load = os.getloadavg()
				misc += f'Load              : {load[0]:.2f} | {load[1]:.2f} | {load[2]:.2f}\n'
			else:
				misc += '\n'
			misc += f'Platform          : {sys.platform}\n'
			misc += f'Python            : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'

			# Adapt the following line when adding resources to keep formatting. 
			# It fills up the right columns to match the length of the left column.
			misc += '\n' * ( (2 if CSE.statistics.statisticsEnabled else 3) - len(CSE.csePOA))

			workers = _markup('[underline]Workers[/underline]\n')
			workers += '\n'
			tableWorkers = Table(row_styles = [ '', L.tableRowStyle], box = None)
			tableWorkers.add_column(_markup('[u]Name[/u]\n'), no_wrap = True)
			tableWorkers.add_column(_markup('[u]Type[/u]\n'), no_wrap = True)
			tableWorkers.add_column(_markup('[u]Intvl (s)[/u]\n'), no_wrap = True, justify = 'right')
			tableWorkers.add_column(_markup('[u]#Runs[/u]\n'), no_wrap = True, justify = 'right')
			for w in sorted(BackgroundWorkerPool.backgroundWorkers.values(), key = lambda w: w.name.lower()):
				a = 'Actor' if w.maxCount == 1 else 'Worker'
				tableWorkers.add_row(w.name, a, str(float(w.interval)) if w.interval > 0.0 else '', str(w.numberOfRuns) if w.interval > 0.0 else '')
			
			threads = _markup('[underline]Threads[/underline]\n')
			threads += '\n'
			tableThreads = Table(row_styles = [ '', L.tableRowStyle], box = None)
			tableThreads.add_column(_markup('[u]Thread Queues\n[/u]'), no_wrap = True)
			tableThreads.add_column(_markup('[u]Count\n[/u]'), no_wrap = True)
			r, p = BackgroundWorkerPool.countJobs()
			tableThreads.add_row('Running', str(r))
			tableThreads.add_row('Paused', str(p))

			requestsGrid = Table.grid(expand = True)
			requestsGrid.add_column(ratio = 28)
			requestsGrid.add_column(ratio = 18)
			requestsGrid.add_column(ratio = 18)
			requestsGrid.add_column(ratio = 18)
			requestsGrid.add_column(ratio = 18)
			requestsGrid.add_row(resourceOps, httpReceived, httpSent, mqttReceived, mqttSent)

			infoGrid = Table.grid(expand=True)
			infoGrid.add_column(ratio = 64)
			infoGrid.add_column(ratio = 36)
			infoGrid.add_row(misc, logs)

			workerGrid = Table.grid(expand = True)
			workerGrid.add_column(ratio = 64)
			workerGrid.add_column(ratio = 36)
			workerGrid.add_row(workers, threads)
			workerGrid.add_row(tableWorkers, tableThreads)

			rightGrid = Table.grid(expand = True)
			rightGrid.add_column()
			rightGrid.add_row(Panel(requestsGrid, style = style))
			rightGrid.add_row(Panel(workerGrid, style = style))
			rightGrid.add_row(Panel(infoGrid, style = style))

			_virtualCount = CSE.dispatcher.countResources(( ResourceTypes.CNT_LA, 
															ResourceTypes.CNT_OL,
															ResourceTypes.FCNT_LA,
															ResourceTypes.FCNT_OL,
															ResourceTypes.TS_LA,
															ResourceTypes.TS_OL, 
															ResourceTypes.GRP_FOPT, 
															ResourceTypes.PCH_PCU))

			#
			#	Left column
			#

			resourceTypes = _markup('[underline]Resources[/underline]\n')
			resourceTypes += '\n'
			resourceTypes += f'AE      : {CSE.dispatcher.countResources(ResourceTypes.AE)}\n'
			resourceTypes += f'ACP     : {CSE.dispatcher.countResources(ResourceTypes.ACP)}\n'
			resourceTypes += f'ACTR    : {CSE.dispatcher.countResources(ResourceTypes.ACTR)}\n'
			resourceTypes += f'CB      : {CSE.dispatcher.countResources(ResourceTypes.CSEBase)}\n'
			resourceTypes += f'CIN     : {CSE.dispatcher.countResources(ResourceTypes.CIN)}\n'
			resourceTypes += f'CNT     : {CSE.dispatcher.countResources(ResourceTypes.CNT)}\n'
			resourceTypes += f'CRS     : {CSE.dispatcher.countResources(ResourceTypes.CRS)}\n'
			resourceTypes += f'CSR     : {CSE.dispatcher.countResources(ResourceTypes.CSR)}\n'
			resourceTypes += f'DEPR    : {CSE.dispatcher.countResources(ResourceTypes.DEPR)}\n'
			resourceTypes += f'FCNT    : {CSE.dispatcher.countResources(ResourceTypes.FCNT)}\n'
			resourceTypes += f'FCI     : {CSE.dispatcher.countResources(ResourceTypes.FCI)}\n'
			resourceTypes += f'GRP     : {CSE.dispatcher.countResources(ResourceTypes.GRP)}\n'
			resourceTypes += f'LCP     : {CSE.dispatcher.countResources(ResourceTypes.LCP)}\n'
			resourceTypes += f'MgmtObj : {CSE.dispatcher.countResources(ResourceTypes.MGMTOBJ)}\n'
			resourceTypes += f'NOD     : {CSE.dispatcher.countResources(ResourceTypes.NOD)}\n'
			resourceTypes += f'PCH     : {CSE.dispatcher.countResources(ResourceTypes.PCH)}\n'
			resourceTypes += f'REQ     : {CSE.dispatcher.countResources(ResourceTypes.REQ)}\n'
			resourceTypes += f'SCH     : {CSE.dispatcher.countResources(ResourceTypes.SCH)}\n'
			resourceTypes += f'SMD     : {CSE.dispatcher.countResources(ResourceTypes.SMD)}\n'
			resourceTypes += f'SUB     : {CSE.dispatcher.countResources(ResourceTypes.SUB)}\n'
			resourceTypes += f'TS      : {CSE.dispatcher.countResources(ResourceTypes.TS)}\n'
			resourceTypes += f'TSB     : {CSE.dispatcher.countResources(ResourceTypes.TSB)}\n'
			resourceTypes += f'TSI     : {CSE.dispatcher.countResources(ResourceTypes.TSI)}\n'
			resourceTypes += '\n'
			resourceTypes += '\n'
			resourceTypes += _markup(f'[bold]Total[/bold]   : {int(stats[Statistics.resourceCount]) - _virtualCount}\n')	# substract the virtual resources
			# Correct height
			resourceTypes += '\n' * (tableWorkers.row_count + 4)


			result = Table.grid(expand = True)
			result.add_column(width = 15)
			result.add_column()
			result.add_row(Panel(resourceTypes, style = style), rightGrid )

			return result

		if withProgress:
			with L.consoleStatusWait('Collecting...'):
				return _stats()
		else:
			return _stats()


	def getConfigurationRich(self,
							 style:Optional[Style] = Style()) -> Table:
	
		keys:list[Tuple[str, ...]] = []

		# Prepare
		for k in list(Configuration.all().keys()):
			t = k.rsplit('.', maxsplit = 1) + [ k ]
			keys.append(tuple(t))
		keys.sort(key = lambda x : (x[0], x[1]))

		# Init the result grid
		result = Table.grid(expand = True)
		result.add_column()

		def _addTableToResult() -> None:
			if table:
				grid = Table.grid(expand = True)
				grid.add_column()
				grid.add_row(_markup(f'[u b]{previousTop}[/u b]  ') + Text('(info)\n\n', style = f'link {documentationLinks.get(previousTop)}'))
				grid.add_row(table)

				result.add_row(Panel(grid, style = style))


		previousTop = None
		table:Table = None
		for section in keys:
			if len(section) == 3:
				if section[0] != previousTop:

					# Finish the previous topic's table 
					_addTableToResult()
					# Assign a new headline topic
					previousTop = section[0]
				
					# Create a table for the new topic
					table = Table(row_styles = [ '', L.tableRowStyle], box = None, expand = True)
					table.add_column(_markup('[u]Setting[/u]\n'), no_wrap = True, ratio = 30)
					table.add_column(_markup('[u]Value(s)[/u]\n'), ratio = 70)
				_v = Configuration.get(section[2])
				if isinstance(_v, list) and len(_v) and isinstance(_v[0], tuple):
					_v = [ str(x) for x in _v  ]
				
				#L.logDebug(_v)
				table.add_row(section[1], str(_v) if not isinstance(_v, list) else ', '.join(list(_v)))
		
		# Add the final table to the result
		_addTableToResult()

		return result


	def getResourceTreeRich(self, 
							maxLevel:int = 0, 
							parent:Optional[str] = None, 
							style:Optional[Style] = Style(),
							withProgress:Optional[bool] = True) -> Tree:
		"""	This function will generate a Rich tree structure of a CSE's resource structure.

			Args:
				maxLevel: The maximum level for the result tree.
				parent: The resource ID from where to start the tree. The default is the CSEBase.
				style: The Rich Style to use.
				withProgress: Display a progress indicator while gathering the tree.
			Return:
				Return a Rich Tree object.
		"""

		def info(res:Resource) -> str:
			"""	Retrieve further information about the current resource.
			
				This depends on the current `treeMode` mode.
				
				Args:
					res: The resource to handle.
			"""

			# Determine extra infos
			extraInfo = ''
			if self.treeMode not in [ TreeMode.COMPACT, TreeMode.CONTENTONLY ]: 
				# if res.ty in [ T.FCNT, T.FCI] :
				# 	extraInfo = f' (cnd={res.cnd})'
				match res.ty:
					case ResourceTypes.FCNT | ResourceTypes.FCI:
						extraInfo = f' ({res.cnf})' if res.cnf else ''
					case ResourceTypes.CSEBase | ResourceTypes.CSEBaseAnnc | ResourceTypes.CSR:
						extraInfo = f' (csi={res.csi})'

			# Determine content
			contentInfo = ''
			if self.treeMode in [ TreeMode.CONTENT, TreeMode.CONTENTONLY ]:
				match res.ty:
					case ResourceTypes.CIN | ResourceTypes.TSI:
						contentInfo = f'{res.con}' if res.con else ''
					case ResourceTypes.FCNT | ResourceTypes.FCI:
						contentInfo = ', '.join([ f'{attr}={str(res[attr])}' for attr in res.dict if CSE.validator.isExtraResourceAttribute(attr, res) ])

			# construct the info
			info = ''
			match self.treeMode:
				case TreeMode.COMPACT:
					info = f'-> {res.__rtype__}'
				case TreeMode.CONTENT:
					if len(contentInfo) > 0:
						info = f'-> {res.__rtype__}{extraInfo} | {contentInfo}'
					else:
						info = f'-> {res.__rtype__}{extraInfo}'
				case TreeMode.CONTENTONLY:
					if len(contentInfo) > 0:
						info = f'-> {contentInfo}'
				case _: # self.treeMode == NORMAL
					if res.isVirtual():
						info = f'-> {res.__rtype__}{extraInfo} (virtual)'
					else:
						info = f'-> {res.__rtype__}{extraInfo} | ri={res.ri}'

			return f'{res.rn} [dim]{info}[/dim]'


		def getChildren(res:Resource, tree:Tree, level:int) -> None:
			""" Recursively find and print the children in the tree structure. 

				Args:
					res: Current resource to handle.
					tree: The current Rich Tree node.
					level: The current resource tree level.
			"""
			if maxLevel > 0 and level == maxLevel:
				return
			chs = CSE.dispatcher.retrieveDirectChildResources(res.ri)
			for ch in chs:
				if ch.isVirtual() and not self.treeIncludeVirtualResources:	# Ignore virual resources
					continue
				# Ignore resources/resource patterns 
				ri = ch.ri
				if len([ p for p in self.hideResources if simpleMatch(p, ri) ]) > 0:
					continue
				branch = tree.add(info(ch))
				getChildren(ch, branch, level+1)
		

		def getTree() -> Optional[Tree]:
			"""	Build and return the resource tree.

				Return:
					A Rich Tree object, or *None*.
			"""
			if parent:
				if not (res := CSE.dispatcher.retrieveResource(parent)):
					return None
			else:
				res = getCSE()
			if not res:
				return None
			tree = Tree(info(res), style = style, guide_style = style)
			getChildren(res, tree, 0)
			return tree

		if withProgress:
			with L.consoleStatusWait('Collecting...'):
				tree = getTree()
		else:
			tree = getTree()

		return tree


	def getResourceTreeText(self, maxLevel:int = 0) -> str:
		"""	This function will generate a Text tree of a CSE's resource structure.

			Args: 
				maxLevel: Maximum tree level to render. Currently not supported.
			
			Return:
				Pure text rendering of the resource tree.

			Todo:
				Support the *maxLevel* parameter.
		"""
		from rich.console import Console as RichConsole

		console = RichConsole(color_system=None)
		console.begin_capture()
		console.print(self.getResourceTreeRich(withProgress = False))
		return '\n'.join([item.rstrip() for item in console.end_capture().splitlines()])


	def getRequestsRich(self, id:Optional[str] = None) -> Tuple[Table, str]:


		table = Table(row_styles = [ '', L.tableRowStyle],  expand = True)
		table.add_column(_markup('[u]Timestamp[/u]\n'), no_wrap = True)
		table.add_column(_markup('[u]Originator[/u]\n'), no_wrap = True)
		table.add_column(_markup('[u]Operation[/u]\n'), no_wrap = True)
		if not id:
			table.add_column(_markup('[u]Resource ID[/u]\n'), no_wrap = True)
		table.add_column(_markup('[u]Request[/u]\n'))
		table.add_column(_markup('[u]Response[/u]\n'))

		uml = """\
@startuml
hide footbox
!theme plain
skinparam backgroundcolor transparent
skinparam BoxPadding 60

"""

		participants = OrderedSet()
		targets = OrderedSet()
		seqs = ''
		origPrefix = '<originator>\\n'

		for r in CSE.storage.getRequests(id, sortedByOt = True):
			req = r['req']
			op = req['op']

			ri = r.get('ri', '(unknown)')
			if op == Operation.NOTIFY:
				ri = f'"{origPrefix}{ri}"'
			else:
				ri = f'"{ri}"'

			org = r['org']
			if org == CSE.cseCsi:
				participants.add(orig := f'"{org[1:]}"')	# CSI without the leading /
			else:
				participants.add(orig := f'"{origPrefix}{org}"')
			

			ty = req.get('ty') if op == 1 else None

			if id:
				table.add_row(toISO8601Date(r['ts']), 
							org,
							Operation(op).name, 
							Pretty(req, indent_size = 2),
							Pretty(r['rsp'], indent_size = 2))
			else:
				table.add_row(toISO8601Date(r['ts']), 
							org,
							Operation(op).name, 
							ri, 
							Pretty(req, indent_size = 2),
							Pretty(r['rsp'], indent_size = 2))
			
			if ri not in participants:
				targets.add(ri)
			tyn = ResourceTypes(ty).name if ResourceTypes.has(ty) else f'UNKNOWN_TYPE_{ty}'
			seqs += f'{orig} -> {ri}: {Operation(op).name} {"<" + tyn + ">" if ty else ""} \n'
			seqs += f'{orig} <- {ri}: RSC: {r["rsp"]["rsc"]} \n'
		

		uml += '\n'.join([f'participant {p}' for p in participants]) + '\n'
		uml += f'box "CSE {CSE.cseCsi}" #f8f8f8\n'
		uml += '\n'.join([f'participant {p}' for p in targets]) + '\n'
		uml += 'end box\n'
		uml += seqs
		uml += '@enduml\n'

		return (table, uml)
