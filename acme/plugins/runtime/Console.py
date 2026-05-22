#
#	Console.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Console functions for ACME CSE
#
"""	This plugin defines a rich console for the CSE.

	Though this is a plugin, it provides the main console functionality for the CSE. 
	It is either this plugin or the minimal console plugin that is used to run the main
	loop of the CSE.

	Note, that this plugin does not fully follow the plugin lifecycle, as
	it is not started by the PluginManager, but instead it is run
	directly by the CSE. 
"""

from __future__ import annotations
from typing import cast, Optional, Any, Callable, Tuple, TYPE_CHECKING

import webbrowser

from rich.live import Live
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import Style
from rich.table import Table
from rich.text import Text

import plotext

from acme.etc.Constants import Constants, RuntimeConstants as RC
from acme.etc.Types import ResourceTypes, TreeMode
from acme.etc.ResponseStatusCodes import ResponseException
from acme.helpers.KeyHandler import FunctionKey, loop, waitForKeypress, Commands
from acme.helpers.interpreter.PContext import PContext
from acme.helpers.interpreter.Types import PError
from acme.resources.Resource import Resource
from acme.runtime.ConsoleBase import ConsoleBase
from acme.runtime.Configuration import Configuration
from acme.runtime.Logging import Logging as L
from acme.runtime.PluginSupport import *
from acme.runtime.EventManager import *


if TYPE_CHECKING:
	from acme.runtime.Storage import Storage
	from acme.services.Dispatcher import Dispatcher
	from acme.runtime.ScriptManager import ScriptManager
	from acme.runtime.Management import ManagementSupport

# TODO support configevent!
# TODO move some of the functions to a more general place because they are used here and in the TUI


##############################################################################


@eventHandler
@plugin(tags=['acme', 'ui'])
@requires(dispatcher='acme.services.Dispatcher')
@requires(scriptManager='acme.runtime.ScriptManager')
@requires(storage='acme.runtime.Storage')
@requires(managementSupport='acme.runtime.Management')
@requires(cseSetConsole='acme.runtime.CSE.setConsole')
@requires(cseShutdown='acme.runtime.CSE.shutdown')
class Console(ConsoleBase):
	"""	Console Manager class. This class provides the main console functionality for the CSE. 
		It is either this plugin or the minimal console plugin that is used to run the main loop of the CSE.
	"""

	dispatcher: Dispatcher = None
	""" Injected IDispatcher instance. """

	storage: Storage = None	
	""" Injected Storage instance. """

	scriptManager: ScriptManager = None
	""" Injected ScriptManager instance. """

	managementSupport: ManagementSupport = None
	""" Injected ManagementSupport instance. """

	cseSetConsole: Callable[[ConsoleBase], None] = None
	""" Injected function to set the console instance in the CSE. """

	cseShutdown: Callable[[], None] = None
	""" Injected function to shutdown the CSE. """

	__slots__ = (
		'interruptContinous',
		'previousTreeRi',
		'previousInspectRi',
		'previosInspectChildrenRi',
		'previousScript',
		'previousArgument',
		'previousGraphRi',
		'previousRequestRi',
		'previousExportRi',
		'previousInstanceExportRi',
		'tuiApp',
		
		'treeMode',
	)
	""" The slots for the Console to optimize memory usage. """

	@start
	def startConsole(self) -> None:
		"""	Initialize the console plugin. Set the console instance in the CSE. 
		"""
		self.cseSetConsole(self)

		# Get the configuration settings
		self._assignConfig()

		self.interruptContinous = False
		""" Indication whether any continuous display function """

		self.previousTreeRi = ''
		""" Resource ID of the previous sub-tree display. This is used as the default value for the next sub-tree display. """
		
		self.previousInspectRi = ''
		""" Resource ID of the previous resource inspection. This is used as the default value for the next resource inspection. """#

		self.previousRequestRi = ''
		""" Resource ID of the previous request display. This is used as the default value for the next request display. """

		self.previosInspectChildrenRi = ''
		""" Resource ID of the previous resource + child resource inspection. This is used as the default value for the next resource + child resource inspection. """
		
		self.previousScript = ''
		""" Name of the previous script run. This is used as the default value for the next script to run. """

		self.previousArgument = ''
		""" Previous script arguments. This is used as the default value for the next script to run. """

		self.previousGraphRi = ''
		""" Resource ID of the previous graph display. This is used as the default value for the next graph display. """

		self.previousExportRi = ''
		""" Resource ID of the previous export. This is used as the default value for the next export. """

		self.previousInstanceExportRi = ''
		""" Resource ID of the previous instance export. This is used as the default value for the next instance export. """

		self.treeMode:TreeMode = None
		""" Current tree mode for the resource tree display. This is used to determine how the resource tree is displayed. """

		L.isDebug and L.logDebug('Rich Console initialized')


	@restart
	def restart(self) -> None:
		"""	Restart the Console service.
		"""
		self.interruptContinous = True	# This will indirectly interrupt a running continous console command
		L.isDebug and L.logDebug('Console restarted')


	def _assignConfig(self) -> None:
		"""	Assign configuration settings.
		"""
		self.treeMode = cast(TreeMode, Configuration.console_treeMode)	# Assigned because it is changed during runtime


	@onEvent(eventManager.configUpdate)
	def configUpdate(self, eventData: EventData) -> None:
		"""	Handle configuration updates.

			Args:
				eventData: The event data, containing the name of the updated configuration setting and its new value.
		"""
		key:Optional[str] = eventData[0]
		value:Any = eventData[1]

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
		commands:Commands = {
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
			'E'					: self.exportResources,
			FunctionKey.CTRL_E	: self.exportInstances,
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
		if not RC.isHeadless:
			L.console('Press "?" for help, or "#" for the Text UI.')
		
		loop(commands, 
			 catchKeyboardInterrupt=True, 
			 headless=RC.isHeadless,
			 catchAll=lambda ch: eventManager.keyboard(EventData(payload=ch)), # type: ignore [attr-defined]
			 nextKey='#' if self.doStartWithTextUI() else None,
			 ignoreException=False,
			 exceptionHandler=lambda ch: L.setEnableScreenLogging(True))
		self.cseShutdown()

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
			('E', 'Export a resource and its children to the [i]tmp[/i] directory as [i]curl[/i] commands'),
			('^E', 'Export the instances of a container resource to a CSV file in the [i]tmp[/i] directory'),
			('f', 'Show requests history for a resource'),
			('F', 'Show all requests history'),
			('^F', 'Clear requests history'),
			('G', 'Plot graph (only for container)'),
			('^G', 'Plot & refresh graph continuously (only for container)'),
			('i', 'Inspect resource'),
			('I', 'Inspect resource and child resources'),
			('^I', 'Show resource continuously'),
			('k', 'Catalog of scripts'),
			('l', 'Toggle screen logging on/off'),
			('L', 'Toggle through log levels'),
			('r', 'Show CSE registrations'),
			('R', 'Run script'),
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
		for eachScript in (scripts :=  sorted(self.scriptManager.findScripts(meta='onKey'), key=lambda x: x.getMeta('onKey'))):
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
		L.console(Text('https://acmecse.net', style='link https://acmecse.net'), nl=True)
		L.console(Text("""\
█████████████████████████████████
█████████████████████████████████
████ ▄▄▄▄▄ ██▄▀ ▄█  ▀█ ▄▄▄▄▄ ████
████ █   █ ██▄▄▀▄█ ▄██ █   █ ████
████ █▄▄▄█ █▀█ ▄█ █ ▄█ █▄▄▄█ ████
████▄▄▄▄▄▄▄█▄▀ ▀ █▄█▄█▄▄▄▄▄▄▄████
████ ▀█ ▀▄▄▀ ▄  ▀██▄▄ ▀▄████▀████
█████▄▀▀▀ ▄ ▄▀█▄██▀▀ ▀ ▀ ██▄▄████
█████ ▄█▀▀▄▀█ █▀ ███▄  ▀█ ▀▄ ████
████▄▀█ ▄▄▄▄▀▄▄█ ▀▀████▄ █▄▀▄████
████▄▄▄█▄█▄▄▀▀▀▄█▄▄█ ▄▄▄  ▄█▀████
████ ▄▄▄▄▄ █▀█▀▀█ █▄ █▄█  ▀▄ ████
████ █   █ █▀█▀  ▀▄█ ▄▄   ▀▄▄████
████ █▄▄▄█ ████   ▄▀▀▀█▄▄▀▄█▄████
████▄▄▄▄▄▄▄█▄█▄▄██▄▄▄▄▄▄███▄▄████
█████████████████████████████████
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\
"""), nl=True)#
		
		# curl qrcode.show  -H "X-QR-Quiet-Zone: true" -H "X-QR-Max-Width: 40" -H "X-QR-Max-Height: 40" -d https://acmecse.net


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
		L.console(self.managementSupport.getResourceTreeRich())
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
			if tree := self.managementSupport.getResourceTreeRich(parent = ri, withProgress = False):
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
		with Live(self.managementSupport.getResourceTreeRich(style=L.terminalStyle, withProgress=False), auto_refresh=False) as live:

			def _updateTree(_: Any, eventData: EventData) -> None:
				"""	Callback to update the on-screen tree on an event.
				"""
				live.update(self.managementSupport.getResourceTreeRich(style=L.terminalStyle, withProgress=False), refresh=True)
			
			# Register events for which the tree is refreshed
			# Only used temporarily during the continuous tree display to update the tree on changes. 
			eventManager.addHandler([eventManager.createResource, 
									 eventManager.deleteResource, 
									 eventManager.updateResource],  _updateTree)		# type:ignore[attr-defined]

			while (ch := waitForKeypress(Configuration.console_refreshInterval)) in [None, '\x14']:
				if ch == '\x14':	# Toggle through tree modes
					self.treeMode = self.treeMode.succ()
					_updateTree(None, None)	# type: ignore [arg-type]
				if self.interruptContinous:
					break

			# Remove the event callback for the events 
			eventManager.removeHandler([eventManager.createResource, 
										eventManager.deleteResource, 
										eventManager.updateResource], _updateTree)	# type:ignore[attr-defined]

		# Reset the screen and logging
		self.clearScreen(key)
		L.on()


	def registrations(self, key:str) -> None:
		"""	Render CSE registrations.

			Args:
				key: Input key. Ignored.
		"""
		L.console('CSE Registrations', isHeader = True)
		L.console()
		try:
			L.console(self.managementSupport.getRegistrationsRich())
		except Exception as e:
			L.logErr('', exc = e)


	def statistics(self, key:str) -> None:
		""" Render various statistics & counts.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Statistics', isHeader=True)
		L.console(self.managementSupport.getStatusRich())
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
		with Live(self.managementSupport.getStatusRich(style=L.terminalStyle, withProgress=False), auto_refresh=False) as live:
			while not waitForKeypress(Configuration.console_refreshInterval):
				live.update(self.managementSupport.getStatusRich(style=L.terminalStyle, withProgress=False), refresh=True)
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
				resource = self.dispatcher.retrieveResource(ri)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else:
				try:
					self.dispatcher.deleteLocalResource(resource, withDeregistration = True)
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
			try:
				resource = self.dispatcher.retrieveResource(ri)
				L.console(resource.asDict())
			except ResponseException as e:
				L.console(e.dbg, isError = True)
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
				resource = self.dispatcher.retrieveResource(ri)
				children = self.dispatcher.discoverResources(ri, originator = RC.cseOriginator)
				self.dispatcher.resourceTreeDict(children, resource.dict)	# the function call add attributes to the target resource
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
				resource = self.dispatcher.retrieveResource(ri, postRetrieveHook = True)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else: 
				self.clearScreen(key)
				self._about(f'Inspect Resource: {ri}')
				self.interruptContinous = False
				endMessage:str = None
				with Live(Pretty(resource.asDict()), console = L._console, auto_refresh = False) as live:

					def _updateResource(_: Any, eventData: EventData) -> None:
						"""	Callback to update the on-screen resource on an event.
						"""
						try:
							resource = self.dispatcher.retrieveResource(ri, postRetrieveHook = True)
						except ResponseException as e:
							endMessage = f'Resource is not available anymore: {ri}'
							self.interruptContinous = True
							return
						live.update(Pretty(resource.asDict()), refresh = True)
					
					# Register events for which the resource is refreshed
					eventManager.addHandler([eventManager.createResource, 
						   					 eventManager.deleteResource, 
											 eventManager.updateResource],  _updateResource)		# type:ignore[attr-defined]

					while waitForKeypress(Configuration.console_refreshInterval) in [None, '\x09']:
						if self.interruptContinous:
							break

					# Remove the event callback for the events 
					eventManager.removeHandler([eventManager.createResource, 
							  					eventManager.deleteResource, 
												eventManager.updateResource], _updateResource)	# type:ignore[attr-defined]

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
		L.console('Script Catalog', isHeader=True)
		L.off()
		table = Table(row_styles=[ '', L.tableRowStyle])
		table.add_column('Script', no_wrap=True)
		table.add_column('Description / Usage')
		table.add_column('UT ', no_wrap=True, justify='center')
		table.add_column('Key ', no_wrap=True, justify='center')
		table.add_column('Run at', no_wrap=True, justify='center')
		for n in self.scriptManager.findScripts(name='*'):
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


	def exportResources(self, key: str) -> None:
		"""	Export resources to the tmp directory.
			The result is a shell script that can be used to re-build a previous resource tree.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Export Resource and Children', isHeader=True)
		L.off()		
		if (ri := L.consolePrompt('ri', default=self.previousExportRi)):
			self.previousExportRi = ri
			self.managementSupport.doExportResource(ri)
		L.on()


	def exportInstances(self, key: str) -> None:
		"""	Export instances of a container resource to a CSV file in the tmp directory.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Export instance resources', isHeader=True)
		L.off()		
		if (ri := L.consolePrompt('ri', default=self.previousInstanceExportRi)):
			self.previousInstanceExportRi = ri
			self.managementSupport.doExportInstances(ri)
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
	# 		if not (resdis := ispatcher.discoverResources(RC.cseRi, originator = RC.cseOriginator)).status:
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


		L.console('Run ACMEScript', isHeader=True)
		L.off()		
		if (name := L.consolePrompt('Script name', nl=False, default=self.previousScript)):
			self.previousScript = name
			if len(scripts := self.scriptManager.findScripts(name=name)) != 1:
				L.console(f'Script {name} not found', isError=True, nlb=True)
				L.on()
				return
			argument = L.consolePrompt('Arguments', default=self.previousArgument)
			self.previousArgument = argument
			pcontext = scripts[0]
			L.on()	# Turn on log before running the script
			try:
				self.scriptManager.runScript(pcontext, arguments=argument, background=True, finished=finished)
			except Exception as e:
				L.logErr(f'Exception during script execution: {str(e)}', exc=e)

		L.on()


	def openWebUI(self, key:str) -> None:
		"""	Open the web UI in the default web browser.

			Args:
				key: Input key. Ignored.
		"""
		webbrowser.open(f'{Configuration.http_address}?open')


	def _plotGraph(self, resource:Resource) -> None:
		"""	Plot a single graph from the child-resources of a container-like resource.

			Args:
				resource: The parent resource for the data instance resources.
		"""
			
		# plot
		try:
			cins = self.dispatcher.retrieveDirectChildResources(resource.ri, ResourceTypes.CIN)
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
				Only `CNT.CNT` and `CIN.CIN` resources are currently supported.

			Args:
				key: Input key. Ignored.
		"""
		# TODO doc
		L.console('Plot Graph', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('Container ri', default = self.previousGraphRi)):
			self.previousGraphRi = ri
			try:
				resource = self.dispatcher.retrieveResource(ri)
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
				resource = self.dispatcher.retrieveResource(ri)
			except ResponseException as e:
				L.console(e.dbg, isError = True)
			else:
				if resource.ty != ResourceTypes.CNT:
					L.console('resource must be a <container>', isError = True)
			
				# Register for chil-added event (which would lead to a re-drawing of the graph)
				eventManager.addHandler(eventManager.createChildResource,  _plot)		# type:ignore [attr-defined]

				# Remember the parent ri
				pri = resource.ri

				# Plot grapth for the first time
				_plot(resource = resource)	

				# Wait for any keypress
				self.interruptContinous = False
				while waitForKeypress(Configuration.console_refreshInterval) is None:
					if self.interruptContinous:
						break

				# Remove the event callback for the events 
				eventManager.removeHandler(eventManager.createChildResource, _plot)	# type:ignore[attr-defined]
				self.clearScreen(key)

		# Reset the screen and logging
		L.on()


	def showRequests(self, key:str) -> None:
		"""	Show the requests for a resource.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Resource Requests', isHeader = True)
		L.off()
		if (ri := L.consolePrompt('ri', default = self.previousRequestRi)):
			self.previousRequestRi = ri
			table, uml = self.managementSupport.getRequestsRich(ri)
			L.console(table)
			L.console(uml, plain = True)
		L.on()		


	def showAllRequests(self, key:str) -> None:
		"""	Show all the requests.

			Args:
				key: Input key. Ignored.
		"""
		L.off()
		table, uml = self.managementSupport.getRequestsRich()
		L.console(table)
		L.console(uml, plain = True)
		L.on()
	

	def deleteRequests(self, key:str) -> None:
		"""	Delete all requests.
		
			Args:
				key: Input key. Ignored.
		"""
		L.console('Delete all requests')
		self.storage.deleteRequests()



	#########################################################################
	#
	#	Generators for rich output
	#

		

	def getConfigurationRich(self,
							 style:Optional[Style]=Style()) -> Table:
		"""	Generate a rich table for the configuration settings.
		
			Args:
				style: Optional style for the table.
			
			Returns:
				A rich Table object representing the configuration settings.
		"""
	
		keys:list[Tuple[str, ...]] = []

		# Prepare
		for k in list(Configuration.all().keys()):
			t = k.rsplit('.', maxsplit=1) + [ k ]
			keys.append(tuple(t))
		keys.sort(key=lambda x : (x[0], x[1]))

		# Init the result grid
		result = Table.grid(expand=True)
		result.add_column()

		def _addTableToResult() -> None:
			if table:
				grid = Table.grid(expand=True)
				grid.add_column()
				# grid.add_row(_markupText(f'[u b]{previousTop}[/u b]'))
				grid.add_row(table)
				grid.add_row()

				result.add_row(Panel(grid, 
						 			 title=f'[ {previousTop} ]',
									 title_align='left',
									 style=style))


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
					table = Table(row_styles=[ '', L.tableRowStyle], box=None, expand=True)
					table.add_column(no_wrap=True, ratio=30)
					table.add_column(ratio=70)
				_v = Configuration.get(section[2])
				if isinstance(_v, list) and len(_v) and isinstance(_v[0], tuple):
					_v = [ str(x) for x in _v  ]
				
				#L.logDebug(_v)
				table.add_row(section[1], str(_v) if not isinstance(_v, list) else ', '.join(list(_v)))
		
		# Add the final table to the result
		_addTableToResult()

		return result


