#
#	Console.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Console functions for ACME CSE
#

from __future__ import annotations
from typing import List, cast
import datetime, json, os, sys, webbrowser
from enum import IntEnum, auto
from rich.style import Style
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live
from rich.text import Text
import plotext as plt



from ..helpers.KeyHandler import loop, stopLoop, waitForKeypress
from ..helpers import TextTools
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..helpers.Interpreter import PContext, PError
from ..helpers import TextTools as TextTools
from ..etc.Constants import Constants as C
from ..etc.Types import CSEType, ResourceTypes as T
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..resources.Resource import Resource
from ..services import CSE as CSE, Statistics as Statistics
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L


# TODO support configevent!



class TreeMode(IntEnum):
	""" Available modes do display the resource tree
	"""
	NORMAL				= auto()
	CONTENT				= auto()
	COMPACT				= auto()
	CONTENTONLY			= auto()

	def __str__(self) -> str:
		return self.name

	def succ(self) -> TreeMode:
		"""	Return the next enum value, and cycle at the end.
		"""
		members:list[TreeMode] = list(self.__class__)
		index = members.index(self) + 1
		return members[index] if index < len(members) else members[0]
	

	@classmethod
	def to(cls, t:str) -> TreeMode:
		"""	Return the enum from a string.
		"""
		return dict(cls.__members__.items()).get(t.upper())


	@classmethod
	def names(cls) -> list[str]:
		"""	Return all the enum names.
		"""
		return list(cls.__members__.keys())

##############################################################################


class Console(object):

	def __init__(self) -> None:
		self.refreshInterval 			 = Configuration.get('cse.console.refreshInterval')
		self.hideResources  			 = Configuration.get('cse.console.hideResources')
		self.treeMode	     			 = Configuration.get('cse.console.treeMode')
		self.treeIncludeVirtualResources = Configuration.get('cse.console.treeIncludeVirtualResources')
		self.confirmQuit     			 = Configuration.get('cse.console.confirmQuit')
		self.interruptContinous			 = False
		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore
		if L.isInfo: L.log('Console initialized')


	def shutdown(self) -> bool:
		if L.isInfo: L.log('Console shut down')
		return True


	def restart(self) -> None:
		"""	Restart the TimeSeriesManager service.
		"""
		self.interruptContinous = True	# This will indirectly interrupt a running continous console command
		L.isDebug and L.logDebug('Console restarted')



	def run(self) -> None:
		#
		#	Enter an endless loop.
		#	Execute keyboard commands in the keyboardHandler's loop() function.
		#
		commands = {
			'?'     : self.help,
			'h'		: self.help,
			'A'		: self.about,
			'\n'	: lambda c: L.console(),	# 1 empty line
			'\r'	: lambda c: L.console(),	# 1 empty line
			'\x03'  : self.shutdownCSE,			# See handler below
			'c'		: self.configuration,
			'C'		: self.clearScreen,
			'D'		: self.deleteResource,
			'E'		: self.exportResources,
			'\x07'	: self.continuesPlotGraph,
			'G'		: self.plotGraph,
			'i'		: self.inspectResource,
			'I'		: self.inspectResourceChildren,
			'k'		: self.katalogScripts,
			'l'     : self.toggleScreenLogging,
			'L'     : self.toggleLogging,
			'Q'		: self.shutdownCSE,		# See handler below
			'r'		: self.cseRegistrations,
			'R'		: self.runScript,
			's'		: self.statistics,
			'\x13'	: self.continuesStatistics,
			't'		: self.resourceTree,
			'\x14'	: self.continuesTree,
			'T'		: self.childResourceTree,
			'u'		: self.openWebUI,
			'w'		: self.workers,
			#'Z'		: self.resetCSE,
		}

		#	Endless runtime loop. This handles key input & commands
		#	The CSE's shutdown happens in one of the key handlers below
		if not CSE.isHeadless:
			L.console('Press ? for help')

		loop(commands, 
			 catchKeyboardInterrupt = True, 
			 headless = CSE.isHeadless,
			 catchAll = lambda ch: CSE.event.keyboard(ch))	# type: ignore [attr-defined]
		CSE.shutdown()


	def stop(self) -> None:
		stopLoop()

	##############################################################################
	#
	#	Various keyboard command handlers
	#

	def _about(self, header:str = None) -> None:
		L.console(f'\n[white]{C.textLogo} ', plain = True, end = '')
		L.console(f'oneM2M CSE {C.version}', nl = False,)
		if header:
			L.console(header, nl = True, isHeader = True)
	

	def help(self, key:str) -> None:
		"""	Print help for keyboard commands.

			Args:
				key: Not used
		"""
		self._about('Console Commands')

		# Built-in Console commands
		commands = [
			# (Key, description, built-in)
			('h, ?', 'This help'),
			('A', 'About'),
			('Q, ^C', 'Shutdown CSE'),
			('c', 'Show configuration'),
			('C', 'Clear the console screen'),
			('D', 'Delete resource'),
			('E', 'Export resource tree to *init* directory'),
			('G', 'Plot graph (only for container)'),
			('^G', 'Plot & refresh graph continuously (only for container)'),
			('i', 'Inspect resource'),
			('I', 'Inspect resource and child resources'),
			('k', 'Catalog of scripts'),
			('l', 'Toggle screen logging on/off'),
			('L', 'Toggle through log levels'),
			('r', 'Show CSE registrations'),
			('s', 'Show statistics'),
			('^S', 'Show & refresh statistics continuously'),
			('t', 'Show resource tree'),
			('T', 'Show child resource tree'),
			('^T', 'Show & refresh resource tree continuously'),
			('u', 'Open web UI'),
			('w', 'Show workers and threads status'),
		]

		table = Table(row_styles = [ '', L.tableRowStyle])
		table.add_column('Key', no_wrap=True, justify = 'left')
		table.add_column('Description', no_wrap=True)
		table.add_column('Script', no_wrap=True, justify='center')
		for each in commands:
			table.add_row(each[0], each[1], '', end_section = each == commands[-1])

		# Add Scripts that have a key binding
		for eachScript in (scripts :=  sorted(CSE.script.findScripts(meta = 'onkey'), key = lambda x: x.getMeta('onkey'))):
			table.add_row(eachScript.meta.get('onkey'), eachScript.meta.get('description'), '✔︎')
		L.console(table, nl=True)


	def about(self, key:str) -> None:
		"""	Print QR-code for keyboard commands.
		"""
		self._about()
		L.console(Text("""An open source CSE Middleware for Education

(c) 2022 by Andreas Kraft
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
		"""
		L.enableScreenLogging = not L.enableScreenLogging
		L.console(f'Screen logging enabled -> **{L.enableScreenLogging}**')


	def toggleLogging(self, key:str) -> None:
		"""	Toggle through the log levels.
		"""
		L.setLogLevel(L.logLevel.next())
		L.console(f'New log level -> **{str(L.logLevel)}**')


	def workers(self, key:str) -> None:
		"""	Print the worker and actor ts.
		"""
		L.console('Worker & Actor Threads', isHeader=True)
		table = Table(row_styles = [ '', L.tableRowStyle])
		table.add_column('Name', no_wrap = True)
		table.add_column('Type', no_wrap = True)
		table.add_column('Intvl (s)', no_wrap = True, justify = 'right')
		table.add_column('Runs', no_wrap = True, justify = 'right')
		for w in sorted(BackgroundWorkerPool.backgroundWorkers.values(), key = lambda w: w.name.lower()):
			a = 'Actor' if w.maxCount == 1 else 'Worker'
			table.add_row(w.name, a, str(float(w.interval)) if w.interval > 0.0 else '', str(w.numberOfRuns) if w.interval > 0.0 else '')
		L.console(table, nl=True)

		# Threads
		L.console('System Threads', isHeader=True)

		table = Table(row_styles = [ '', L.tableRowStyle])
		table.add_column('Thread Queues', no_wrap = True)
		table.add_column('Count', no_wrap = True)
		r, p = BackgroundWorkerPool.countJobs()
		table.add_row('Running', str(r))
		table.add_row('Paused', str(p))
		L.console(table, nl = True)




	def configuration(self, key:str) -> None:
		"""	Print the configuration.
		"""
		L.console('Configuration', isHeader = True)
		conf = Configuration.print().split('\n')
		conf.sort()
			
		table = Table(row_styles = [ '', L.tableRowStyle])
		table.add_column('Key', no_wrap=True)
		table.add_column('Value', no_wrap=False)
		for c in conf:
			if c.startswith('Configuration:'):
				continue
			kv = c.split(' = ', 1)
			if len(kv) == 2:
				table.add_row(kv[0].strip(), kv[1])
		L.console(table, nl = True)


	def clearScreen(self, _:str) -> None:
		"""	Clear the console screen.
		"""
		L.consoleClear()


	def resourceTree(self, _:str) -> None:
		"""	Render the CSE's resource tree.
		"""
		L.console('Resource Tree', isHeader = True)
		L.console(self.getResourceTreeRich())
		L.console()


	previousTreeRi = ''
	def childResourceTree(self, _:str) -> None:
		"""	Render the CSE's resource tree, beginning with a child resource.
		"""
		L.console('Child Resource Tree', isHeader = True)
		L.off()
		
		if not (ri := L.consolePrompt('ri', default = Console.previousTreeRi)):
			Console.previousTreeRi = ri
			L.console()
		elif len(ri) > 0:
			if tree := self.getResourceTreeRich(parent = ri):
				L.console(tree)
			else:
				L.console('not found', isError = True)

		L.on()


	def continuesTree(self, key:str) -> None:
		L.off()
		self.interruptContinous = False
		self.clearScreen(key)
		self._about('Resource Tree')
		with Live(self.getResourceTreeRich(style = L.terminalStyle), auto_refresh = False) as live:

			def _updateTree(_:Resource = None) -> None:
				"""	Callback to update the on-screen tree on an event.
				"""
				live.update(self.getResourceTreeRich(style = L.terminalStyle), refresh = True)
			
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


	def cseRegistrations(self, _:str) -> None:
		"""	Render CSE registrations.
		"""
		L.console('CSE Registrations', isHeader=True)
		L.console(self.getCSERegistrationsRich())
		L.console()


	def statistics(self, _:str) -> None:
		""" Render various statistics & counts.
		"""
		L.console('Statistics', isHeader=True)
		L.console(self.getStatisticsRich())
		L.console()


	def continuesStatistics(self, key:str) -> None:
		L.off()
		self.interruptContinous = False
		self.clearScreen(key)
		self._about('Statistics')
		with Live(self.getStatisticsRich(style=L.terminalStyle), auto_refresh=False) as live:
			while not waitForKeypress(self.refreshInterval):
				live.update(self.getStatisticsRich(style = L.terminalStyle), refresh=True)
				if self.interruptContinous:
					break

		self.clearScreen(key)
		L.on()


	def deleteResource(self, _:str) -> None:
		"""	Delete a resource from the CSE.
		"""
		L.console('Delete Resource', isHeader=True)
		L.off()
		if (ri := L.consolePrompt('ri')):
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError=True)
			else:
				if not (res := CSE.dispatcher.deleteResource(res.resource, withDeregistration=True)).resource:
					L.console(res.dbg, isError=True)
				else:
					L.console('ok')
		L.on()


	previousInspectRi = ''
	def inspectResource(self, _:str) -> None:
		"""	Show a resource.
		"""
		L.console('Inspect Resource', isHeader = True)
		L.off()

		if (ri := L.consolePrompt('ri', default = Console.previousInspectRi)):
			Console.previousInspectRi = ri
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError = True)
			else:
				L.console(res.resource.asDict())
		L.on()		


	previosInspectChildrenRi = ''
	def inspectResourceChildren(self, _:str) -> None:
		"""	Show a resource and its children.
		"""
		L.console('Inspect Resource and Children', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('ri', default = Console.previosInspectChildrenRi)):
			Console.previosInspectChildrenRi = ri
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError = True)
			else: 
				if not (resdis := CSE.dispatcher.discoverResources(ri, originator = CSE.cseOriginator)).status:
					L.console(resdis.dbg, isError = True)
				else:
					CSE.dispatcher.resourceTreeDict(cast(List[Resource], resdis.data), res.resource)	# the function call add attributes to the target resource
					L.console(res.resource.asDict())
		L.on()


	def katalogScripts(self, _:str) -> None:
		"""	List the loaded scripts.
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
				key = n.getMeta('onkey')
				table.add_row(n.scriptName, 
							  desc, 
							  '✔︎' if ut else '',
							  key,
							  at )
		L.console(table, nl = True)
		L.on()


	def exportResources(self, _:str) -> None:
		L.console('Export Resources', isHeader = True)
		L.off()
		if not (resdis := CSE.dispatcher.discoverResources(CSE.cseRi, originator = CSE.cseOriginator)).status:
			L.console(resdis.dbg, isError=True)
		else:
			resources:list[Resource] = []
			for r in cast(List[Resource], resdis.data):
				if r.isImported:
					continue
				resources.append(r)
			if resources:
				fn = f'{datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")}.as'
				fpn = f'{CSE.importer.resourcePath}/{fn}'
				L.console(f'Exporting to {fn}')
				with open(fpn, 'w') as exportFile:
					for r in resources:
						exportFile.write('importRaw\n')
						json.dump(r.asDict(), exportFile, indent=4, sort_keys=True)
						exportFile.write('\n')
			L.console(f'Exported {len(resources)} resources')
		L.on()
	

	previousScript = ''
	previousArgument = ''
	def runScript(self, _:str) -> None:

		def finished(pcontext:PContext, argument:str) -> None:
			if (error := pcontext.error)[0] == PError.noError:
				L.console(f'Result: {pcontext.result}')
			else:
				L.console(f'Error in {pcontext.scriptName}:{error[1]}: {error[2]}', isError = True)


		L.console('Run ACMEScript', isHeader = True)
		L.off()		
		if (name := L.consolePrompt('Script name', nl = False, default = Console.previousScript)):
			Console.previousScript = name
			if len(scripts := CSE.script.findScripts(name = name)) != 1:
				L.console(f'Script {name} not found', isError = True, nlb = True)
				L.on()
				return
			argument = L.consolePrompt('Arguments', default = Console.previousArgument)
			Console.previousArgument = argument
			pcontext = scripts[0]
			L.on()	# Turn on log before running the script
			CSE.script.runScript(pcontext, argument = argument, background = True, finished = finished)

		L.on()


	def openWebUI(self, _:str) -> None:
		"""	Open the web UI in the default web browser.
		"""
		webbrowser.open(f'{CSE.httpServer.serverAddress}?open')


	def _plotGraph(self, resource:Resource) -> None:
			
		# plot
		try:
			cins = CSE.dispatcher.directChildResources(resource.ri, T.CIN)
			x = range(1, (lcins := len(cins)) + 1)
			y = [ float(each.con) for each in cins ]
			cols, rows = plt.terminal_size()

			plt.canvas_color('default')
			plt.axes_color('default')
			plt.ticks_color(L.terminalStyleRGBTupple)
			plt.frame(True)
			plt.plot_size(None, rows/2)
			plt.xticks([1, int(lcins/4), int(lcins/4) * 2, int(lcins/4) * 3, lcins])

			plt.title(f'{resource[Resource._srn]} ({resource.ri})')
			plt.plot(x, y, color = L.terminalStyleRGBTupple)
			plt.show()
			plt.clear_figure()
		except Exception as e:
			L.logErr(str(e), exc = e)
		

	previousGraphRi = ''
	def plotGraph(self, _:str) -> None:
		L.console('Plot Graph', isHeader = True)
		L.off()		
		if (ri := L.consolePrompt('Container ri', default = Console.previousGraphRi)):
			Console.previousGraphRi = ri
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError = True)
			else:
				if res.resource.ty != T.CNT:
					L.console('resource must be a <container>', isError = True)
				self._plotGraph(res.resource)
		L.on()


	def continuesPlotGraph(self, key:str) -> None:

		pri:str = None

		def _plot(resource:Resource) -> bool:
			if resource.ri != pri:	# filter only the container we want to observe
				return True
			self.clearScreen(None)
			L.console('Plot Graph', isHeader = True)
			self._plotGraph(resource)
			return True

		L.off()
		if (ri := L.consolePrompt('Container ri', default = Console.previousGraphRi)):
			Console.previousGraphRi = ri
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError = True)
			else:
				if res.resource.ty != T.CNT:
					L.console('resource must be a <container>', isError = True)
			
				# Register for chil-added event (which would lead to a re-drawing of the graph)
				CSE.event.addHandler(CSE.event.createChildResource,  _plot)		# type:ignore [attr-defined]

				# Remember the parent ri
				pri = res.resource.ri

				# Plot grapth for the first time
				_plot(res.resource)	

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


	#########################################################################
	#
	#	Generators for rich output
	#

	def getCSERegistrationsRich(self) -> str:
		"""	Return an overview in Rich format about the registrar, registrees, and
			descendant CSE's.
		"""

		result = ''
		if CSE.cseType != CSEType.IN and CSE.remote.remoteAddress:
			registrarCSE = CSE.remote.registrarCSE
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
			result += f'- **Registrar CSE**  \n{CSE.remote.registrarCSI[1:]} ({registrarType}) @ {CSE.remote.remoteAddress}\n'

		if CSE.cseType != CSEType.ASN:
			if len(CSE.remote.descendantCSR) > 0:
				result += f'- **Registree CSEs**\n'
				for desc in CSE.remote.descendantCSR.keys():
					(csr, _) = CSE.remote.descendantCSR[desc]
					if csr:
						result += f'  - {desc[1:]} ({CSEType(csr.cst).name}) @ {csr.poa}\n'
						for desc2 in CSE.remote.descendantCSR.keys():
							(csr2, atCsi2) = CSE.remote.descendantCSR[desc2]
							if not csr2 and atCsi2 == desc:
								result += f'    - {desc2[1:]}\n'
	
		return result if len(result) else 'None'
		

# TODO events transit requests
# TODO notifications
	def getStatisticsRich(self, style:Style=Style()) -> Table:
		"""	Generate an overview about various resources and event counts.
		"""

		stats = CSE.statistics.getStats()

		if CSE.statistics.statisticsEnabled:
			resourceOps  =  '[underline]Operations[/underline]\n'
			resourceOps += 	'\n'
			resourceOps +=  f'Created       : {stats.get(Statistics.createdResources, 0)}\n'
			resourceOps +=  f'Updated       : {stats.get(Statistics.updatedResources, 0)}\n'
			resourceOps +=  f'Deleted       : {stats.get(Statistics.deletedResources, 0)}\n'
			resourceOps +=  f'Expired       : {stats.get(Statistics.expiredResources, 0)}\n'
			resourceOps +=  f'Notifications : {stats.get(Statistics.notifications, 0)}\n'
			resourceOps +=  f'\n[dim]Includes virtual\nresources[/dim]'

			httpReceived  = '[underline]HTTP:R[/underline]\n'
			httpReceived += 	'\n'
			httpReceived += f'C : {stats.get(Statistics.httpCreates, 0)}\n'
			httpReceived += f'R : {stats.get(Statistics.httpRetrieves, 0)}\n'
			httpReceived += f'U : {stats.get(Statistics.httpUpdates, 0)}\n'
			httpReceived += f'D : {stats.get(Statistics.httpDeletes, 0)}\n'

			httpSent  = 	'[underline]HTTP:S[/underline]\n'
			httpSent += 	'\n'
			httpSent += 	f'C : {stats.get(Statistics.httpSendCreates, 0)}\n'
			httpSent += 	f'R : {stats.get(Statistics.httpSendRetrieves, 0)}\n'
			httpSent += 	f'U : {stats.get(Statistics.httpSendUpdates, 0)}\n'
			httpSent += 	f'D : {stats.get(Statistics.httpSendDeletes, 0)}\n'

			mqttReceived  = '[underline]MQTT:R[/underline]\n'
			mqttReceived += 	'\n'
			mqttReceived += f'C : {stats.get(Statistics.mqttCreates, 0)}\n'
			mqttReceived += f'R : {stats.get(Statistics.mqttRetrieves, 0)}\n'
			mqttReceived += f'U : {stats.get(Statistics.mqttUpdates, 0)}\n'
			mqttReceived += f'D : {stats.get(Statistics.mqttDeletes, 0)}\n'

			mqttSent  = 	'[underline]MQTT:S[/underline]\n'
			mqttSent += 	'\n'
			mqttSent += 	f'C : {stats.get(Statistics.mqttSendCreates, 0)}\n'
			mqttSent += 	f'R : {stats.get(Statistics.mqttSendRetrieves, 0)}\n'
			mqttSent += 	f'U : {stats.get(Statistics.mqttSendUpdates, 0)}\n'
			mqttSent += 	f'D : {stats.get(Statistics.mqttSendDeletes, 0)}\n'


			logs  = '[underline]Logs[/underline]\n'
			logs += '\n'
			logs += f'LogLevel : {str(L.logLevel)}\n'
			logs += f'Errors   : {stats.get(Statistics.logErrors, 0)}\n'
			logs += f'Warnings : {stats.get(Statistics.logWarnings, 0)}\n'

		else:
			resourceOps  = '\n[dim]statistics are disabled[/dim]\n'
			httpReceived = '\n[dim]statistics are disabled[/dim]\n'
			httpSent     = '\n[dim]statistics are disabled[/dim]\n'
			logs         = '\n[dim]statistics are disabled[/dim]\n'


		misc  = '[underline]Misc[/underline]\n'
		misc += '\n'
		misc += f'StartTime : {datetime.datetime.fromtimestamp(DateUtils.fromAbsRelTimestamp(cast(str, stats[Statistics.cseStartUpTime]), withMicroseconds=False))} (UTC)\n'
		misc += f'Uptime    : {stats.get(Statistics.cseUpTime, "")}\n'
		if hasattr(os, 'getloadavg'):
			load = os.getloadavg()
			misc += f'Load      : {load[0]:.2f} | {load[1]:.2f} | {load[2]:.2f}\n'
		else:
			misc += '\n'
		misc += f'Platform  : {sys.platform}\n'
		misc += f'Python    : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'

		# Adapt the following line when adding resources to keep formatting. 
		# It fills up the right columns to match the length of the left column.
		misc += '\n' * ( 2 if CSE.statistics.statisticsEnabled else 7)

		requestsGrid = Table.grid(expand = True)
		requestsGrid.add_column(ratio = 28)
		requestsGrid.add_column(ratio = 18)
		requestsGrid.add_column(ratio = 18)
		requestsGrid.add_column(ratio = 18)
		requestsGrid.add_column(ratio = 18)
		requestsGrid.add_row(resourceOps, httpReceived, httpSent, mqttReceived, mqttSent)

		infoGrid = Table.grid(expand=True)
		infoGrid.add_column(ratio = 33)
		infoGrid.add_column(ratio = 67)
		infoGrid.add_row(logs, misc)

		rightGrid = Table.grid(expand=True)
		rightGrid.add_column()
		rightGrid.add_row(Panel(requestsGrid, style = style))
		rightGrid.add_row(Panel(infoGrid, style = style))

		resourceTypes = '[underline]Resource Types[/underline]\n'
		resourceTypes += '\n'
		resourceTypes += f'AE      : {CSE.dispatcher.countResources(T.AE)}\n'
		resourceTypes += f'ACP     : {CSE.dispatcher.countResources(T.ACP)}\n'
		resourceTypes += f'CB      : {CSE.dispatcher.countResources(T.CSEBase)}\n'
		resourceTypes += f'CIN     : {CSE.dispatcher.countResources(T.CIN)}\n'
		resourceTypes += f'CNT     : {CSE.dispatcher.countResources(T.CNT)}\n'
		resourceTypes += f'CSR     : {CSE.dispatcher.countResources(T.CSR)}\n'
		resourceTypes += f'FCNT    : {CSE.dispatcher.countResources(T.FCNT)}\n'
		resourceTypes += f'FCI     : {CSE.dispatcher.countResources(T.FCI)}\n'
		resourceTypes += f'GRP     : {CSE.dispatcher.countResources(T.GRP)}\n'
		resourceTypes += f'MgmtObj : {CSE.dispatcher.countResources(T.MGMTOBJ)}\n'
		resourceTypes += f'NOD     : {CSE.dispatcher.countResources(T.NOD)}\n'
		resourceTypes += f'PCH     : {CSE.dispatcher.countResources(T.PCH)}\n'
		resourceTypes += f'REQ     : {CSE.dispatcher.countResources(T.REQ)}\n'
		resourceTypes += f'SUB     : {CSE.dispatcher.countResources(T.SUB)}\n'
		resourceTypes += f'TS      : {CSE.dispatcher.countResources(T.TS)}\n'
		resourceTypes += f'TSB     : {CSE.dispatcher.countResources(T.TSB)}\n'
		resourceTypes += f'TSI     : {CSE.dispatcher.countResources(T.TSI)}\n'
		resourceTypes += '\n'
		resourceTypes += f'[bold]Total[/bold]   : {int(stats[Statistics.resourceCount]) - CSE.dispatcher.countResources((T.CNT_LA, T.CNT_OL, T.FCNT_LA, T.FCNT_OL, T.TS_LA, T.TS_OL, T.GRP_FOPT, T.PCH_PCU, T.TSB))}\n'	# substract the virtual resources
		
		result = Table.grid(expand = True)
		result.add_column(width=15)
		result.add_column()
		result.add_row(Panel(resourceTypes, style = style), rightGrid )

		return result


	def getResourceTreeRich(self, maxLevel:int=0, parent:str=None, style:Style=Style()) -> Tree:
		"""	This function will generate a Rich tree of a CSE's resource structure.
		"""

		#import resources.FCNT

		def info(res:Resource) -> str:

			# Determine extra infos
			extraInfo = ''
			if self.treeMode not in [ TreeMode.COMPACT, TreeMode.CONTENTONLY ]: 
				# if res.ty in [ T.FCNT, T.FCI] :
				# 	extraInfo = f' (cnd={res.cnd})'
				if res.ty in [ T.CIN, T.TS ]:
					extraInfo = f' ({res.cnf})' if res.cnf else ''
				elif res.ty in [ T.CSEBase, T.CSEBaseAnnc, T.CSR ]:
					extraInfo = f' (csi={res.csi})'
			
			# Determine content
			contentInfo = ''
			if self.treeMode in [ TreeMode.CONTENT, TreeMode.CONTENTONLY ]:
				if res.ty in [ T.CIN, T.TSI ]:
					contentInfo = f'{res.con}' if res.con else ''
				elif res.ty in [ T.FCNT, T.FCI ]:	# All the custom attributes
					contentInfo = ', '.join([ f'{attr}={str(res[attr])}' for attr in res.dict if CSE.validator.isExtraResourceAttribute(attr, res) ])

			# construct the info
			info = ''
			if self.treeMode == TreeMode.COMPACT:
				info = f'-> {res.__rtype__}'
			elif self.treeMode == TreeMode.CONTENT:
				if len(contentInfo) > 0:
					info = f'-> {res.__rtype__}{extraInfo} | {contentInfo}'
				else:
					info = f'-> {res.__rtype__}{extraInfo}'
			elif self.treeMode == TreeMode.CONTENTONLY:
				if len(contentInfo) > 0:
					info = f'-> {contentInfo}'
			else: # self.treeMode == NORMAL
				if res.isVirtual():
					info = f'-> {res.__rtype__}{extraInfo} (virtual)'
				else:
					info = f'-> {res.__rtype__}{extraInfo} | ri={res.ri}'

			return f'{res.rn} [dim]{info}[/dim]'


		def getChildren(res:Resource, tree:Tree, level:int) -> None:
			""" Find and print the children in the tree structure. """
			if maxLevel > 0 and level == maxLevel:
				return
			chs = CSE.dispatcher.directChildResources(res.ri)
			for ch in chs:
				if ch.isVirtual() and not self.treeIncludeVirtualResources:	# Ignore virual resources
					continue
				# Ignore resources/resource patterns 
				ri = ch.ri
				if len([ p for p in self.hideResources if TextTools.simpleMatch(p, ri) ]) > 0:
					continue
				branch = tree.add(info(ch))
				getChildren(ch, branch, level+1)

		if parent:
			if not (res := CSE.dispatcher.retrieveResource(parent).resource):
				return None
		else:
			res = Utils.getCSE().resource
		if not res:
			return None
		tree = Tree(info(res), style = style, guide_style = style)
		getChildren(res, tree, 0)
		return tree


	def getResourceTreeText(self, maxLevel:int = 0) -> str:
		"""	This function will generate a Text tree of a CSE's resource structure.
		"""
		from rich.console import Console as RichConsole

		console = RichConsole(color_system=None)
		console.begin_capture()
		console.print(self.getResourceTreeRich())
		return '\n'.join([item.rstrip() for item in console.end_capture().splitlines()])

