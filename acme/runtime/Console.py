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

import csv, datetime, json, os, sys, webbrowser, socket, platform, io

from rich.live import Live
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich import box 

import plotext

from ..runtime import CSE

from ..helpers.KeyHandler import FunctionKey, loop, stopLoop, waitForKeypress, Commands
from ..helpers.TextTools import simpleMatch
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..helpers.Interpreter import PContext, PError
from ..helpers.OrderedSet import OrderedSet
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.Types import CSEType, ResourceTypes, Operation, RequestOptionality, TreeMode
from ..etc.ResponseStatusCodes import ResponseException
from ..helpers.NetworkTools import getIPAddress
from ..etc.DateUtils import fromAbsRelTimestamp, toISO8601Date, getResourceDate
from ..resources.Resource import Resource
from ..resources.CSEBase import getCSE
from ..runtime import Statistics
from ..runtime.Configuration import Configuration
from .Configuration import Configuration
from .Logging import Logging as L

# Used in many "rich" functions
_markup = Text.from_markup

# TODO support configevent!
# TODO move some of the functions to a more general place because they are used here and in the TUI


##############################################################################


class Console(object):
	"""	Console Manager class.
	
		Attributes:
			interruptContinous: Indication whether any continuous display function should terminate.
			previousTreeRi: Resource ID of the previous sub-tree display.
			previousInspectRi: Resource ID of the previous resource inspection.
			previosInspectChildrenRi: Resource ID of the previous resource + child resource inspection.
			previousScript: Name of the previous script run.
			previousArgument: Previous script arguments.
			previousGraphRi: Resource ID of the previous graph display.
			previousRequestRi: Resource ID of the previous request display.
			previousExportRi: Resource ID of the previous export.
			previousInstanceExportRi: Resource ID of the previous instance export.
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
		'previousExportRi',
		'previousInstanceExportRi',
		'tuiApp',
		
		'treeMode',

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
		self.previousExportRi = ''
		self.previousInstanceExportRi = ''

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
		self.treeMode:TreeMode = cast(TreeMode, Configuration.console_treeMode)	# Assigned because it is changed during runtime


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
			 catchKeyboardInterrupt = True, 
			 headless = RC.isHeadless,
			 catchAll = lambda ch: CSE.event.keyboard(ch), # type: ignore [attr-defined]
			 nextKey = '#' if Configuration.textui_startWithTUI else None,
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
			('E', 'Export a resource and its children to the [i]tmp[/i] directory as [i]curl[/i] commands'),
			('^E', 'Export the instances of a container resource to a CSV file in the [i]tmp[/i] directory'),
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



	def shutdownCSE(self, key:str) -> None:
		"""	Shutdown the CSE. Confirm shutdown before actually doing that.

			Args:
				key: Input key. Ignored.
		"""
		if not RC.isHeadless:
			if Configuration.console_confirmQuit:
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

			while (ch := waitForKeypress(Configuration.console_refreshInterval)) in [None, '\x14']:
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
		# poas = '\n'.join([f'    - {poa}' for poa in RC.csePOA])
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
			while not waitForKeypress(Configuration.console_refreshInterval):
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
			try:
				resource = CSE.dispatcher.retrieveResource(ri)
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
				resource = CSE.dispatcher.retrieveResource(ri)
				children = CSE.dispatcher.discoverResources(ri, originator = RC.cseOriginator)
				CSE.dispatcher.resourceTreeDict(children, resource.dict)	# the function call add attributes to the target resource
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

					while waitForKeypress(Configuration.console_refreshInterval) in [None, '\x09']:
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


	def doExportResource(self, ri:str, withChildResources:bool = False) -> Tuple[int, str]:
		try:

			if withChildResources:
				resdis = CSE.dispatcher.discoverResources(ri, originator = RC.cseOriginator)
				# insert the parent resource at the beginning of the list
				resdis.insert(0, CSE.dispatcher.retrieveResource(ri))
			else:
				resdis = [CSE.dispatcher.retrieveResource(ri)]

			# Counter for the number of resources exported
			count = 0

			# Create a temporary directory for the export
			outdir = f'{CSE.Configuration.baseDirectory}/tmp'
			os.makedirs(outdir, exist_ok = True)

			filename = f'export-{getResourceDate().rsplit(",", 1)[0]}.sh'
			path = f'{outdir}/{filename}'
			cseUrl = Configuration.http_address
			with open(path, 'w') as f:

				# Write shell file header
				f.write(f'''#!/bin/bash
# Exported {ri} from {RC.cseRi} at {getResourceDate()}

cseURL={cseUrl}

function uniqueNumber() {{
	unique_number=""
	for i in {{1..10}}
	do
		unique_number+=$RANDOM
	done
	unique_number=${{unique_number:0:10}}
	echo "$unique_number"
}}

function createResource() {{
	printf '\\nCreating child resource under %s\\n' $cseURL/$4
	printf 'Result: '		  
	curl -X POST -H "X-M2M-Origin: $1" -H "X-M2M-RVI: {RC.releaseVersion}" -H "X-M2M-RI: $(uniqueNumber)" -H "Content-Type: application/json;ty=$2" -d "$3" $cseURL/$4
	printf '\\n'
}}
			
''')

				# Write createResource commands for all resources
				for r in resdis:
					typeShortname = r.typeShortname
					attributes = {}
					for attr in r.getAttributes():
						policy = CSE.validator.getAttributePolicy(r.ty, attr)
						if policy.optionalCreate != RequestOptionality.NP:
							attributes[attr] = r[attr]
					
					# Special handling for some attributes
					if 'et' in attributes:
						del attributes['et']

					attributes = { typeShortname : attributes }
					parentSrn = r.getSrn().rsplit('/', 1)[0]
					# f.write(f'createResource {r.getOriginator()} {r.ty} \'{json.dumps(attributes).replace("\'", "\\\'")}\' \'{parentSrn}\'\n')
					f.write('createResource ' + r.getOriginator() + ' ' + str(r.ty) +' \'' + json.dumps(attributes).replace("\'", "\\\'") + '\' \'' + parentSrn + '\'\n')
					count += 1
			L.console(f'Exported {count} resource(s) to {path}')

		except ResponseException as e:
			L.console(e.dbg, isError = True)
			return 0, e.dbg
		
		return count, f'tmp/{filename}'


	def exportResources(self, key:str) -> None:
		"""	Export resources to the tmp directory.
			The result is a shell script that can be used to re-build a previous resource tree.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Export Resource and Children', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('ri', default = self.previousExportRi)):
			self.previousExportRi = ri
			self.doExportResource(ri)
		L.on()



	def doExportInstances(self, ri:str, asString:bool = False) -> Tuple[int, str]:
		"""	Export instances of a container resource to a CSV file in the tmp directory, or return as a string.

			Args:
				ri: Resource ID of the container resource.
				asString: Return the CSV string instead of writing to a file.

			Return:
				Tuple with the number of instances exported, and the filename of the exported file or the CSV string.

		"""
		_instanceMapping = {
			ResourceTypes.CNT: ResourceTypes.CIN,
			ResourceTypes.CNTAnnc: ResourceTypes.CINAnnc,
			ResourceTypes.FCNT: ResourceTypes.FCI,
			ResourceTypes.TS: ResourceTypes.TSI,
			ResourceTypes.TSAnnc: ResourceTypes.TSIAnnc
		}

		count:int = 0

		def _writeTo(f:io.TextIOWrapper, instances:List[Resource]) -> None:
			nonlocal count

			writer = csv.writer(f)
			# Write CIN and TSI instances
			writer.writerow(['ri', 'st', 'ct', 'con', 'cnf', 'structured_resource_identifier'])
			for instance in instances:
				writer.writerow([instance.ri, instance.st, instance.ct, instance.con, instance.cnf, instance.getSrn()])
				count += 1


		try:
			L.console('Export Instance Resources', isHeader = True)
			container = CSE.dispatcher.retrieveResource(ri)
			if container.ty in [ResourceTypes.FCNT, ResourceTypes.FCNTAnnc]:
				# TODO FCNT export not supported at the moment
				return 0, L.console(f'Export of FCNT {ri} not supported', isError = True)

			if not ResourceTypes.isContainerResource(container.ty):
				return 0, L.console(f'{ri} is not a container resource', isError = True)
			if not (instances := CSE.dispatcher.retrieveDirectChildResources(ri, _instanceMapping[container.ty])):
				L.console(f'No instances found under {ri}', isError = True)
				return 0, f'No instances found under {ri}'

			else:
				if not asString:
					# Create a temporary directory for the export
					outdir = f'{CSE.Configuration.baseDirectory}/tmp'
					os.makedirs(outdir, exist_ok = True)

					# get the filename and open the file for writing
					filename = f'instances-{getResourceDate().rsplit(",", 1)[0]}.csv'
					path = f'{outdir}/{filename}'
					with open(path, 'w') as f:
						_writeTo(f, instances)
					L.console(f'Exported {count} instances to {filename}')
					return count, f'tmp/{filename}'
				
				# return the CSV string
				else:
					with io.StringIO() as csvString:
						_writeTo(csvString, instances)
						return count, csvString.getvalue()
		except Exception as e:
			if hasattr(e, 'dbg'):
				L.console(e.dbg, isError = True)
				return 0, e.dbg
			else:
				L.console(str(e), isError = True)
				return 0, str(e)
		

	def exportInstances(self, key:str) -> None:
		"""	Export instances of a container resource to a CSV file in the tmp directory.

			Args:
				key: Input key. Ignored.
		"""
		L.console('Export instance resources', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('ri', default = self.previousInstanceExportRi)):
			self.previousInstanceExportRi = ri
			self.doExportInstances(ri)
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
	# 		if not (resdis := CSE.dispatcher.discoverResources(RC.cseRi, originator = RC.cseOriginator)).status:
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
		webbrowser.open(f'{Configuration.http_address}?open')


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
				while waitForKeypress(Configuration.console_refreshInterval) is None:
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

	def getRegistrationsRich(self, style:Optional[Style] = Style(), 
						  		   textStyle:Optional[Style] = None) -> Table:
		"""	Create and return an overview about the registrar, registrees, and
			descendant CSE's.

			Args:
				style: Style for the general output.
				textStyle: Style for the text.

			Return:
				Rich formatted string.
		"""

		# Assign the text style if not None.
		if textStyle is None:
			textStyle = style

		def _addCSERow(table:Table, style:Style, cse:Resource, registrarCSE:Resource, registrees:List[str]) -> None:
			table.add_row(cse.csi, 
						  CSEType(cse.cst.value if isinstance(cse.cst, CSEType) else cse.cst).name, 
						  cse.rn, 
						  cse.ri, 
						  '' if not cse.srv else ', '.join(cse.srv),
						  str(cse.rr) if cse.rr is not None else '', 
						  '' if cse.poa is None else ', '.join(cse.poa),
						  '' if not registrarCSE else registrarCSE.csi,
						  '' if not registrees else ', '.join(registrees),
						  style = style)

		tableCSE = Table(row_styles = [ '', L.tableRowStyle], box = None, expand = True)
		tableCSE.add_column(_markup('[u]CSE-ID[/u]\n', style = textStyle), no_wrap = True)
		tableCSE.add_column(_markup('[u]Type[/u]\n', style = textStyle), no_wrap = True)
		tableCSE.add_column(_markup('[u]Name[/u]\n', style = textStyle), no_wrap = True)
		tableCSE.add_column(_markup('[u]Resource ID[/u]\n', style = textStyle), width = 12, no_wrap = True)
		tableCSE.add_column(_markup('[u]Release[/u]\n', style = textStyle), no_wrap = False)
		tableCSE.add_column(_markup('[u]Reachable[/u]\n', style = textStyle), no_wrap = True)
		tableCSE.add_column(_markup('[u]POA[/u]\n', style = textStyle), no_wrap = False)
		tableCSE.add_column(_markup('[u]Registrar[/u]\n', style = textStyle), no_wrap = True)
		tableCSE.add_column(_markup('[u]Registrees[/u]\n', style = textStyle), no_wrap = False)

		cse = getCSE()
		_addCSERow(tableCSE, 
			 	   Style.combine((Style(italic = True, bold = True), textStyle)), 
				   cse, 
				   CSE.remote.registrarCSE, 
				   CSE.remote.descendantCSR.keys()) #type:ignore[arg-type]
		# _addCSERow(tableCSE, Style(italic = True, bold = True), cse, CSE.remote.registrarCSE, CSE.remote.descendantCSR.keys()) #type:ignore[arg-type]
		for csr in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.CSR):
			if CSE.remote.registrarCSE and csr.csi == CSE.remote.registrarCSE.csi:
				_addCSERow(tableCSE, textStyle, csr, None, [cse.csi] + csr.dcse)
			else:
				_addCSERow(tableCSE, textStyle, csr, cse, csr.dcse)
		
		panelCSE = Panel(tableCSE, 
				  		 box=box.ROUNDED, 
						 title=_markup('[b]Common Services Entities (CSE)[/b]'), 
						 title_align='left', 
						 padding = (1, 0, 0, 0),
						 expand=True,
						 style = style)
		

		tableAE = Table(row_styles = [ '', L.tableRowStyle], box = None, expand = True)
		tableAE.add_column(_markup('[u]AE-ID[/u]\n', style = textStyle), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]Name[/u]\n', style = textStyle), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]Resource ID[/u]\n', style = textStyle), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]APP-ID[/u]\n', style = textStyle), width = 10, no_wrap = True)
		tableAE.add_column(_markup('[u]Reachable[/u]\n', style = textStyle), width = 5, no_wrap = True)
		tableAE.add_column(_markup('[u]POA[/u]\n', style = textStyle), width = 15, no_wrap = False)

		for ae in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.AE):
			tableAE.add_row(ae.aei, 
							ae.rn, 
							ae.ri, 
							ae.api, 
							str(ae.rr), 
							'' if ae.poa is None else ', '.join(ae.poa),
							style = textStyle)

		panelAE = Panel(tableAE, 
				  		box=box.ROUNDED, 
						title=_markup('[b]Application Entities (AE)[/b]'), 
						title_align='left', 
						padding = (1, 0, 0, 0),
						expand=True,
						style = style)

		result = Table.grid(expand = True)
		result.add_column()
		result.add_row(panelCSE)
		result.add_row(panelAE)

		return result
		# result = ''

		# if RC.cseType != CSEType.IN:
		# 	result += f'- **Registrar CSE**\n'
		# 	if CSE.remote.registrarAddress:
		# 		registrarCSE = CSE.remote.registrarCSE
		# 		registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
		# 		result += f'    - {Configuration.cse_registrar_cseID[1:]} ({registrarType}) @ {CSE.remote.registrarAddress}\n'
		# 	else:
		# 		result += '   - None'

		# if RC.cseType != CSEType.ASN:
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
						  withProgress:Optional[bool] = True,
						  textStyle:Optional[Style] = None) -> Table:
		"""	Generate an overview about various resources, event counts, and more.

			Args:
				style: Rich style.
				withProgress: Display with progress indicator.
				textStyle: Rich text style. If this is not set then the style is used for the text as well.
			
			Return:
				Rich Table object.
		"""

		def _stats() -> Table:
			#
			#	Right columns
			#
			stats = CSE.statistics.getStats()

			#
			#	Misc
			#

			miscLeft  = Text(style = textStyle)
			miscLeft += f'CSE-ID | CSE-Name : {RC.cseCsi}  |  {RC.cseRn}\n'
			miscLeft += f'Hostname          : {socket.gethostname()}\n'
			# misc += f'IP-Address : {socket.gethostbyname(socket.gethostname() + ".local")}\n'
			try:
				miscLeft += f'IP-Address        : {getIPAddress()}\n'
			except Exception as e:
				print(e)
			miscLeft += f'PoA               : {RC.csePOA[0]}\n'
			if len(RC.csePOA) > 1:
				miscLeft += ''.join([f'                    {poa}\n' for poa in RC.csePOA[1:] ])

			miscLeft += '\n'
			miscLeft += f'CWD               : {os.getcwd()}\n'
			miscLeft += f'Runtime Directory : {Configuration.baseDirectory}\n'
			miscLeft += f'Config File       : {Configuration.configfile}\n'
			miscLeft += '\n'
			miscLeft += f'StartTime         : {datetime.datetime.fromtimestamp(fromAbsRelTimestamp(cast(str, stats[Statistics.cseStartUpTime]), withMicroseconds=False))} (UTC)\n'
			miscLeft += f'Uptime            : {stats.get(Statistics.cseUpTime, "")}\n'

			miscLeft += '\n'
			if hasattr(os, 'getloadavg'):
				load = os.getloadavg()
				miscLeft += f'Load              : {load[0]:.2f} | {load[1]:.2f} | {load[2]:.2f}\n'
			else:
				miscLeft += '\n'
			miscLeft += f'Platform          : {platform.platform(terse=True)} ({platform.machine()})\n'
			miscLeft += f'Python Version    : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'
			miscLeft += f'ACME CSE Version  : {Constants.version}'

			miscHeight = len(miscLeft.split('\n'))

			panelMiscLeft = Panel(miscLeft, 
								  box = box.ROUNDED, 
								  title = _markup('[b]Misc[/b]'), 
								  title_align = 'left', 
								  padding = (1, 1, 0, 1),
								  expand = True,
								  style = style)

			#
			#	Request stats
			#

			if Configuration.cse_statistics_enable:
				resourceOps  =  _markup('[underline]Operations[/underline]\n', style = textStyle)
				resourceOps += 	'\n'
				resourceOps +=  f'Create:   {stats.get(Statistics.createdResources, 0)}\n'
				resourceOps +=  f'Retrieve: {stats.get(Statistics.retrievedResources, 0)}\n'
				resourceOps +=  f'Update:   {stats.get(Statistics.updatedResources, 0)}\n'
				resourceOps +=  f'Delete:   {stats.get(Statistics.deletedResources, 0)}\n'
				resourceOps +=  f'Notify:   {stats.get(Statistics.notifications, 0)}\n'
				resourceOps +=  f'Expire:   {stats.get(Statistics.expiredResources, 0)}\n'
				resourceOps +=  _markup(f'\n[dim]Includes virtual\nresources[/dim]')

				coapReceived  = _markup('[underline]CoAP:R[/underline]\n', style = textStyle)
				coapReceived += '\n'
				coapReceived += f'C: {stats.get(Statistics.coCreates, 0)}\n'
				coapReceived += f'R: {stats.get(Statistics.coRetrieves, 0)}\n'
				coapReceived += f'U: {stats.get(Statistics.coUpdates, 0)}\n'
				coapReceived += f'D: {stats.get(Statistics.coDeletes, 0)}\n'
				coapReceived += f'N: {stats.get(Statistics.coNotifies, 0)}\n'

				coapSent  = 	_markup('[underline]CoAP:S[/underline]\n', style = textStyle)
				coapSent += 	'\n'
				coapSent += 	f'C: {stats.get(Statistics.coSendCreates, 0)}\n'
				coapSent += 	f'R: {stats.get(Statistics.coSendRetrieves, 0)}\n'
				coapSent += 	f'U: {stats.get(Statistics.coSendUpdates, 0)}\n'
				coapSent += 	f'D: {stats.get(Statistics.coSendDeletes, 0)}\n'
				coapSent += 	f'N: {stats.get(Statistics.coSendNotifies, 0)}\n'


				httpReceived  = _markup('[underline]HTTP:R[/underline]\n', style = textStyle)
				httpReceived += '\n'
				httpReceived += f'C: {stats.get(Statistics.httpCreates, 0)}\n'
				httpReceived += f'R: {stats.get(Statistics.httpRetrieves, 0)}\n'
				httpReceived += f'U: {stats.get(Statistics.httpUpdates, 0)}\n'
				httpReceived += f'D: {stats.get(Statistics.httpDeletes, 0)}\n'
				httpReceived += f'N: {stats.get(Statistics.httpNotifies, 0)}\n'

				httpSent  = 	_markup('[underline]HTTP:S[/underline]\n', style = textStyle)
				httpSent += 	'\n'
				httpSent += 	f'C: {stats.get(Statistics.httpSendCreates, 0)}\n'
				httpSent += 	f'R: {stats.get(Statistics.httpSendRetrieves, 0)}\n'
				httpSent += 	f'U: {stats.get(Statistics.httpSendUpdates, 0)}\n'
				httpSent += 	f'D: {stats.get(Statistics.httpSendDeletes, 0)}\n'
				httpSent += 	f'N: {stats.get(Statistics.httpSendNotifies, 0)}\n'

				mqttReceived  = _markup('[underline]MQTT:R[/underline]\n', style = textStyle)
				mqttReceived += 	'\n'
				mqttReceived += f'C: {stats.get(Statistics.mqttCreates, 0)}\n'
				mqttReceived += f'R: {stats.get(Statistics.mqttRetrieves, 0)}\n'
				mqttReceived += f'U: {stats.get(Statistics.mqttUpdates, 0)}\n'
				mqttReceived += f'D: {stats.get(Statistics.mqttDeletes, 0)}\n'
				mqttReceived += f'N: {stats.get(Statistics.mqttNotifies, 0)}\n'

				mqttSent  = 	_markup('[underline]MQTT:S[/underline]\n', style = textStyle)
				mqttSent += 	'\n'
				mqttSent += 	f'C: {stats.get(Statistics.mqttSendCreates, 0)}\n'
				mqttSent += 	f'R: {stats.get(Statistics.mqttSendRetrieves, 0)}\n'
				mqttSent += 	f'U: {stats.get(Statistics.mqttSendUpdates, 0)}\n'
				mqttSent += 	f'D: {stats.get(Statistics.mqttSendDeletes, 0)}\n'
				mqttSent += 	f'N: {stats.get(Statistics.mqttSendNotifies, 0)}\n'

				wsReceived  =	_markup('[underline]WS:R[/underline]\n', style = textStyle)
				wsReceived +=	'\n'
				wsReceived +=	f'C: {stats.get(Statistics.wsCreates, 0)}\n'
				wsReceived +=	f'R: {stats.get(Statistics.wsRetrieves, 0)}\n'
				wsReceived +=	f'U: {stats.get(Statistics.wsUpdates, 0)}\n'
				wsReceived +=	f'D: {stats.get(Statistics.wsDeletes, 0)}\n'
				wsReceived +=	f'N: {stats.get(Statistics.wsNotifies, 0)}\n'

				wsSent  =   	_markup('[underline]WS:S[/underline]\n', style = textStyle)
				wsSent +=   	'\n'
				wsSent +=   	f'C: {stats.get(Statistics.wsSendCreates, 0)}\n'
				wsSent +=   	f'R: {stats.get(Statistics.wsSendRetrieves, 0)}\n'
				wsSent +=   	f'U: {stats.get(Statistics.wsSendUpdates, 0)}\n'
				wsSent +=   	f'D: {stats.get(Statistics.wsSendDeletes, 0)}\n'
				wsSent +=   	f'N: {stats.get(Statistics.wsSendNotifies, 0)}\n'

				#
				#	Logs
				#

				miscLogs  = Text(style = textStyle)
				miscLogs += f'LogLevel : {str(L.logLevel)}\n'
				miscLogs += f'Errors   : {stats.get(Statistics.logErrors, 0)}\n'
				miscLogs += f'Warnings : {stats.get(Statistics.logWarnings, 0)}'

				panelMiscLogs = Panel(miscLogs, 
									  box = box.ROUNDED, 
									  title = _markup('[b]Logs[/b]'), 
									  title_align = 'left', 
									  padding = (1, 1, 0, 1),
									  expand = True,
									  style = style)


				#
				#	Database
				#

				miscDB  = Text(style = textStyle)
				miscDB += f'Type     : {Configuration.database_type}\n'
				match Configuration.database_type:
					case 'postgresql':
						miscDB += f'Host     : {Configuration.database_postgresql_host}:{Configuration.database_postgresql_port}\n'
						miscDB += f'Role     : {Configuration.database_postgresql_role}\n'
						miscDB += f'Database : {Configuration.database_postgresql_database}\n'
						miscDB += f'Schema   : {Configuration.database_postgresql_schema}\n'
					case 'tinydb':
						miscDB += f'Path     : ./{os.path.relpath(Configuration.database_tinydb_path, Configuration.baseDirectory)}\n'
						miscDB += '\n\n\n'
					case 'memory':
						miscDB += '\n\n\n\n'
				
				panelMiscDB = Panel(miscDB, 
									box = box.ROUNDED, 
									title = _markup('[b]Database[/b]'), 
									title_align = 'left', 
									padding = (1, 1, (miscHeight - 12), 1),	# adapt height accoring to misc panel height
									expand = True,
									style = style)


			else:
				resourceOps  = _markup('\n[dim]statistics are disabled[/dim]\n', style = textStyle)
				httpReceived = _markup('\n[dim]statistics are disabled[/dim]\n', style = textStyle)
				httpSent     = _markup('\n[dim]statistics are disabled[/dim]\n', style = textStyle)
				miscRight    = _markup('\n[dim]statistics are disabled[/dim]\n', style = textStyle)


			tableWorkers = Table(expand=True, row_styles = [ '', L.tableRowStyle], box = None, padding = (0, 0, 0, 1))
			tableWorkers.add_column(_markup('[u]Name[/u]\n', style = textStyle), no_wrap = True)
			tableWorkers.add_column(_markup('[u]Type[/u]\n', style = textStyle), no_wrap = True)
			tableWorkers.add_column(_markup('[u]Intvl (s)[/u]\n', style = textStyle), no_wrap = True, justify = 'right')
			tableWorkers.add_column(_markup('[u]#Runs[/u]\n', style = textStyle), no_wrap = True, justify = 'right')
			for w in sorted(BackgroundWorkerPool.backgroundWorkers.values(), key = lambda w: w.name.lower()):
				a = 'Actor' if w.maxCount == 1 else 'Worker'
				tableWorkers.add_row(w.name, a, str(float(w.interval)) if w.interval > 0.0 else '', str(w.numberOfRuns) if w.interval > 0.0 else '', style = textStyle)
			
			panelWorkers = Panel(tableWorkers, 
								 box = box.ROUNDED, 
								 title = _markup('[b]Workers[/b]'), 
								 title_align = 'left', 
								 padding = (1, 1, 0, 1),
								 expand = True,
								 style = style)

			tableThreads = Table(box = None, padding = (0, 0))
			tableThreads.add_column(_markup('[u]Queues[/u]    \n', style = textStyle), no_wrap = True)
			tableThreads.add_column(_markup('[u]Count[/u]\n', style = textStyle), no_wrap = True, justify = 'right')
			r, p = BackgroundWorkerPool.countJobs()
			tableThreads.add_row('Running', str(r), style = textStyle)
			tableThreads.add_row('Paused', str(p), style = textStyle)
			import threading
			tableThreads.add_row('Native', str(threading.active_count()), style = textStyle)
			for _ in range(len(tableWorkers.rows)-3):	# Fill up lines
				tableThreads.add_row('', '')
			
			panelThreads = Panel(tableThreads, 
						   box = box.ROUNDED, 
						   title = _markup('[b]Threads[/b]'), 
						   title_align = 'left', 
						   padding = (1, 1, 0, 1),
						   expand = True,
						   style = style)


			requestsGrid = Table.grid(expand = True)
			requestsGrid.add_column(ratio = 28)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_column(ratio = 12)
			requestsGrid.add_row(resourceOps, coapReceived, coapSent, httpReceived, httpSent, mqttReceived, mqttSent, wsReceived, wsSent)

			panelRequests = Panel(requestsGrid, 
								  box = box.ROUNDED, 
								  title = _markup('[b]Requests[/b]'), 
								  title_align = 'left', 
								  padding = (1, 0, 0, 1),
								  expand = True,
								  style = style)


			panelMiscRight = Table.grid(expand = True,)
			panelMiscRight.add_column()
			panelMiscRight.add_row(panelMiscLogs)
			panelMiscRight.add_row(panelMiscDB)

			infoGrid = Table.grid(expand=True, padding = (0, 1, 0, 0))
			infoGrid.add_column(ratio = 70, no_wrap=True)
			infoGrid.add_column(ratio = 30)
			infoGrid.add_row(panelMiscLeft, panelMiscRight)

			workerGrid = Table.grid(expand = True, padding = (0, 1, 0, 0))
			workerGrid.add_column(ratio = 70)
			workerGrid.add_column(ratio = 30)
			workerGrid.add_row(panelWorkers, panelThreads)

			rightGrid = Table.grid(expand = True)
			rightGrid.add_column()
			rightGrid.add_row(panelRequests)
			rightGrid.add_row(workerGrid)
			rightGrid.add_row(infoGrid)

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

			resourceTypes = Text(style = textStyle)
			resourceTypes += f'AE      : {(_cAE   := CSE.dispatcher.countResources(ResourceTypes.AE))}\n'
			resourceTypes += f'ACP     : {(_cACP  := CSE.dispatcher.countResources(ResourceTypes.ACP))}\n'
			resourceTypes += f'ACTR    : {(_cACTR := CSE.dispatcher.countResources(ResourceTypes.ACTR))}\n'
			resourceTypes += f'CB      : {(_cCB   := CSE.dispatcher.countResources(ResourceTypes.CSEBase))}\n'
			resourceTypes += f'CIN     : {(_cCIN  := CSE.dispatcher.countResources(ResourceTypes.CIN))}\n'
			resourceTypes += f'CNT     : {(_cCNT  := CSE.dispatcher.countResources(ResourceTypes.CNT))}\n'
			resourceTypes += f'CRS     : {(_cCRS  := CSE.dispatcher.countResources(ResourceTypes.CRS))}\n'
			resourceTypes += f'CSR     : {(_cCSR  := CSE.dispatcher.countResources(ResourceTypes.CSR))}\n'
			resourceTypes += f'DEPR    : {(_cDEPR := CSE.dispatcher.countResources(ResourceTypes.DEPR))}\n'
			resourceTypes += f'FCNT    : {(_cFCNT := CSE.dispatcher.countResources(ResourceTypes.FCNT))}\n'
			resourceTypes += f'FCI     : {(_cFCI  := CSE.dispatcher.countResources(ResourceTypes.FCI))}\n'
			resourceTypes += f'GRP     : {(_cGRP  := CSE.dispatcher.countResources(ResourceTypes.GRP))}\n'
			resourceTypes += f'LCP     : {(_cLCP  := CSE.dispatcher.countResources(ResourceTypes.LCP))}\n'
			resourceTypes += f'MgmtObj : {(_cMOBJ := CSE.dispatcher.countResources(ResourceTypes.MGMTOBJ))}\n'
			resourceTypes += f'NOD     : {(_cNOD  := CSE.dispatcher.countResources(ResourceTypes.NOD))}\n'
			resourceTypes += f'PCH     : {(_cPCH  := CSE.dispatcher.countResources(ResourceTypes.PCH))}\n'
			resourceTypes += f'REQ     : {(_cREQ  := CSE.dispatcher.countResources(ResourceTypes.REQ))}\n'
			resourceTypes += f'SCH     : {(_cSCH  := CSE.dispatcher.countResources(ResourceTypes.SCH))}\n'
			resourceTypes += f'SMD     : {(_cSMD  := CSE.dispatcher.countResources(ResourceTypes.SMD))}\n'
			resourceTypes += f'SUB     : {(_cSUB  := CSE.dispatcher.countResources(ResourceTypes.SUB))}\n'
			resourceTypes += f'TS      : {(_cTS   := CSE.dispatcher.countResources(ResourceTypes.TS))}\n'
			resourceTypes += f'TSB     : {(_cTSB  := CSE.dispatcher.countResources(ResourceTypes.TSB))}\n'
			resourceTypes += f'TSI     : {(_cTSI  := CSE.dispatcher.countResources(ResourceTypes.TSI))}\n'
			resourceTypes += '\n'
			# resourceTypes += _markup(f'[bold]Total[/bold]   : {int(stats[Statistics.resourceCount]) - _virtualCount}')	# substract the virtual resources
			resourceTypes += _markup(f'[bold]Total[/bold]   : {_cAE + _cACP + _cACTR + _cCB + _cCIN + _cCNT + _cCRS + _cCSR + _cDEPR + _cFCNT + _cFCI + _cGRP + _cLCP + _cMOBJ + _cNOD + _cPCH + _cREQ + _cSCH + _cSMD + _cSUB + _cTS + _cTSB + _cTSI }')	# substract the virtual resources

			# Not sure why rich does not use 1 per line for padding. For some unknown reasons
			# we need to multiply the number of lines with 2 to get the correct padding.
			_padding = 16 + (miscHeight - 15) * 2
			
			panelResources = Panel(resourceTypes, 
								   box = box.ROUNDED, 
								   title = _markup('[b]Resources[/b]'), 
								   title_align = 'left', 
								   padding = (1, 0, _padding, 1),
								   expand = True,
								   style = style)

			result = Table.grid(expand = True, padding = (0, 1, 0, 0))
			result.add_column(width = 15)
			result.add_column()
			result.add_row(panelResources, rightGrid )

			return result

		# Assign the text style if not None.
		if textStyle is None:
			textStyle = style
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
				grid.add_row(_markup(f'[u b]{previousTop}[/u b]'))
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
					info = f'-> {res[Constants.attrRtype]}'
				case TreeMode.CONTENT:
					if len(contentInfo) > 0:
						info = f'-> {res[Constants.attrRtype]}{extraInfo} | {contentInfo}'
					else:
						info = f'-> {res[Constants.attrRtype]}{extraInfo}'
				case TreeMode.CONTENTONLY:
					if len(contentInfo) > 0:
						info = f'-> {contentInfo}'
				case _: # self.treeMode == NORMAL
					if res.isVirtual():
						info = f'-> {res[Constants.attrRtype]}{extraInfo} (virtual)'
					else:
						info = f'-> {res[Constants.attrRtype]}{extraInfo} | ri={res.ri}'

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
				if ch.isVirtual() and not Configuration.console_treeIncludeVirtualResource:	# Ignore virual resources
					continue
				# Ignore resources/resource patterns 
				ri = ch.ri
				if len([ p for p in Configuration.console_hideResources if simpleMatch(p, ri) ]) > 0:
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
			if org == RC.cseCsi:
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
		uml += f'box "CSE {RC.cseCsi}" #f8f8f8\n'
		uml += '\n'.join([f'participant {p}' for p in targets]) + '\n'
		uml += 'end box\n'
		uml += seqs
		uml += '@enduml\n'

		return (table, uml)
