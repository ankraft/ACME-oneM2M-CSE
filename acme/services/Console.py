#
#	Console.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Console functions for ACME CSE
#

from __future__ import annotations
from typing import Dict, cast
import datetime, os, sys, webbrowser
from enum import IntEnum, auto
from rich.style import Style
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live


from helpers.KeyHandler import loop, stopLoop, readline, waitForKeypress
import helpers.TextTools
from helpers.BackgroundWorker import BackgroundWorkerPool
from etc.Constants import Constants as C
from etc.Types import CSEType, ResourceTypes as T
from services.Logging import Logging as L
from services.Configuration import Configuration
from resources.Resource import Resource
import etc.Utils as Utils, etc.DateUtils as DateUtils, services.CSE as CSE, services.Statistics as Statistics


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
		self.refreshInterval = Configuration.get('cse.console.refreshInterval')
		self.hideResources   = Configuration.get('cse.console.hideResources')
		self.treeMode	     = Configuration.get('cse.console.treeMode')
		self.confirmQuit     = Configuration.get('cse.console.confirmQuit')
		if L.isInfo: L.log('Console initialized')


	def shutdown(self) -> bool:
		if L.isInfo: L.log('Console shut down')
		return True


	def run(self) -> None:
		#
		#	Enter an endless loop.
		#	Execute keyboard commands in the keyboardHandler's loop() function.
		#
		commands = {
			'?'     : self.help,
			'h'		: self.help,
			'\n'	: lambda c: print(),		# 1 empty line
			'\x03'  : self.shutdownCSE,			# See handler below
			'c'		: self.configuration,
			'C'		: self.clearScreen,
			'D'		: self.deleteResource,
			'i'		: self.inspectResource,
			'I'		: self.inspectResourceChildren,
			'l'     : self.toggleScreenLogging,
			'L'     : self.toggleLogging,
			'Q'		: self.shutdownCSE,		# See handler below
			'r'		: self.cseRegistrations,
			's'		: self.statistics,
			'\x13'	: self.continuesStatistics,
			't'		: self.resourceTree,
			'\x14'	: self.continuesTree,
			'T'		: self.childResourceTree,
			'u'		: self.openWebUI,
			'w'		: self.workers,
			'Z'		: self.resetCSE,
		}

		#	Endless runtime loop. This handles key input & commands
		#	The CSE's shutdown happens in one of the key handlers below
		loop(commands, catchKeyboardInterrupt=True, headless=CSE.isHeadless)
		CSE.shutdown()


	def stop(self) -> None:
		stopLoop()

	##############################################################################
	#
	#	Various keyboard command handlers
	#

	def _about(self, header:str=None) -> None:
		L.console(f'\n[white][dim][[/dim][red][i]ACME[/i][/red][dim]] CSE {C.version}', plain=True, nl=True)
		if header:
			L.console(f'**{header}**',nl=True)


	def help(self, key:str) -> None:
		"""	Print help for keyboard commands.
		"""
		self._about('Console Commands')
		L.console("""- h, ?  - This help
- Q, ^C - Shutdown CSE
- c     - Show configuration
- C     - Clear the console screen
- D     - Delete resource
- i     - Inspect resource
- I     - Inspect resource and child resources
- l     - Toggle screen logging on/off
- L     - Toggle through log levels
- r     - Show CSE registrations
- s     - Show statistics
- ^S    - Show & refresh statistics continuously
- t     - Show resource tree
- T     - Show child resource tree
- ^T    - Show & refresh resource tree continuously
- w     - Show worker threads status
- u     - Open web UI
- Z     - Reset the CSE
""", nl=True)


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
				L.console('Shutdown CSE')
				L.on()
			else:
				L.console('Shutdown CSE')
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
		"""	Print the worker and actor threads.
		"""
		from rich.table import Table

		L.console('Worker & Actor Threads', isHeader=True)
		table = Table()
		table.add_column('Name', no_wrap=True)
		table.add_column('Type', no_wrap=True)
		table.add_column('Interval', no_wrap=True)
		table.add_column('Runs', no_wrap=True)
		for w in BackgroundWorkerPool.backgroundWorkers.values():
			a = 'Actor' if w.maxCount == 1 else 'Worker'
			table.add_row(w.name, a, str(float(w.interval)) if w.interval > 0.0 else '', str(w.numberOfRuns) if w.interval > 0.0 else '')
		L.console(table, nl=True)


	def configuration(self, key:str) -> None:
		"""	Print the configuration.
		"""
		from rich.table import Table

		L.console('Configuration', isHeader=True)
		conf = Configuration.print().split('\n')
		conf.sort()
		table = Table()
		table.add_column('Key', no_wrap=True)
		table.add_column('Value', no_wrap=False)
		for c in conf:
			if c.startswith('Configuration:'):
				continue
			kv = c.split(' = ', 1)
			if len(kv) == 2:
				table.add_row(kv[0].strip(), kv[1])
		L.console(table, nl=True)


	def clearScreen(self, _:str) -> None:
		"""	Clear the console screen.
		"""
		L.consoleClear()


	def resourceTree(self, _:str) -> None:
		"""	Render the CSE's resource tree.
		"""
		L.console('Resource Tree', isHeader=True)
		L.console(self.getResourceTreeRich())
		L.console()


	def childResourceTree(self, _:str) -> None:
		"""	Render the CSE's resource tree, beginning with a child resource.
		"""
		L.console('Child Resource Tree', isHeader=True)
		L.off()
		
		if not (ri := readline('ri=')):
			L.console()
		elif len(ri) > 0:
			if tree := self.getResourceTreeRich(parent=ri):
				L.console(tree)
			else:
				L.console('not found', isError=True)

		L.on()


	def continuesTree(self, key:str) -> None:
		L.off()
		self.clearScreen(key)
		self._about('Resource Tree')
		with Live(self.getResourceTreeRich(style=L.terminalStyle), auto_refresh=False) as live:

			def _updateTree(_:Resource=None) -> None:
				"""	Callback to update the on-screen tree on an event.
				"""
				live.update(self.getResourceTreeRich(style=L.terminalStyle), refresh=True)
			
			# Register events for which the tree is refreshed
			CSE.event.addHandler([CSE.event.createResource, CSE.event.deleteResource, CSE.event.updateResource],  _updateTree)		# type:ignore[attr-defined]

			while (ch := waitForKeypress(self.refreshInterval)) in [None, '\x14']:
				if ch == '\x14':	# Toggle through tree modes
					self.treeMode = self.treeMode.succ()
					_updateTree()

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

	
	# def continuesStatistics(self, key:str) -> None:
	# 	L.off()
	# 	while True:
	# 		self.clearScreen(key)
	# 		self._about()
	# 		self.statistics(key)
	# 		L.console('(Press any key to return)', plain=True, end='')
	# 		if waitForKeypress(self.refreshInterval) is not None:
	# 			break
	# 	self.clearScreen(key)
	# 	L.on()


	def continuesStatistics(self, key:str) -> None:
		L.off()
		self.clearScreen(key)
		self._about('Statistics')
		with Live(self.getStatisticsRich(style=L.terminalStyle), auto_refresh=False) as live:
			while not waitForKeypress(self.refreshInterval):
				live.update(self.getStatisticsRich(style=L.terminalStyle), refresh=True)
		self.clearScreen(key)
		L.on()


	def deleteResource(self, _:str) -> None:
		"""	Delete a resource from the CSE.
		"""
		L.console('Delete Resource', isHeader=True)
		L.off()
		if not (ri := readline('ri=')):
			L.console()
		elif len(ri) > 0:
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError=True)
			else:
				if not (res := CSE.dispatcher.deleteResource(res.resource, withDeregistration=True)).resource:
					L.console(res.dbg, isError=True)
				else:
					L.console('ok')
		L.on()


	def inspectResource(self, _:str) -> None:
		"""	Show a resource.
		"""
		L.console('Inspect Resource', isHeader=True)
		L.off()

		if not (ri := readline('ri=')):
			L.console()
		elif len(ri) > 0:
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError=True)
			else:
				L.console(res.resource.asDict())
		L.on()		


	def inspectResourceChildren(self, _:str) -> None:
		"""	Show a resource and its children.
		"""
		L.console('Inspect Resource and Children', isHeader=True)
		L.off()		
		if not (ri := readline('ri=')):
			L.console()
		elif len(ri) > 0:
			if not (res := CSE.dispatcher.retrieveResource(ri)).resource:
				L.console(res.dbg, isError=True)
			else: 
				if not (resdis := CSE.dispatcher.discoverResources(ri, originator=CSE.cseOriginator)).status:
					L.console(resdis.dbg, isError=True)
				else:
					CSE.dispatcher.resourceTreeDict(resdis.lst, res.resource)	# the function call add attributes to the target resource
					L.console(res.resource.asDict())
		L.on()


	def resetCSE(self, key:str) -> None:
		"""	Reset the CSE. Remove all resources and do the importing again.
		"""
		L.console('Resetting CSE', isHeader=True)
		L.enableScreenLogging = True
		L.logLevel = Configuration.get('logging.level')
		CSE.resetCSE()


	def openWebUI(self, key:str) -> None:
		"""	Open the web UI in the default web browser.
		"""
		webbrowser.open(CSE.httpServer.serverAddress)




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
	def getStatisticsRich(self, style:Style=Style()) -> Table:
		"""	Generate an overview about various resources and event counts.
		"""

		stats = CSE.statistics.getStats()

		if CSE.statistics.statisticsEnabled:
			resourceOps  =  '[underline]Resource Operations[/underline]\n'
			resourceOps += 	'\n'
			resourceOps +=  f'Created       : {stats[Statistics.createdResources]}\n'
			resourceOps +=  f'Updated       : {stats[Statistics.updatedResources]}\n'
			resourceOps +=  f'Deleted       : {stats[Statistics.deletedResources]}\n'
			resourceOps +=  f'Expired       : {stats[Statistics.expiredResources]}\n'
			resourceOps +=  f'Notifications : {stats[Statistics.notifications]}\n'

			httpReceived  = '[underline]HTTP Received[/underline]\n'
			httpReceived += 	'\n'
			httpReceived += f'RETRIEVE : {stats[Statistics.httpRetrieves]}\n'
			httpReceived += f'CREATE   : {stats[Statistics.httpCreates]}\n'
			httpReceived += f'UPDATE   : {stats[Statistics.httpUpdates]}\n'
			httpReceived += f'DELETE   : {stats[Statistics.httpDeletes]}\n'

			httpSent  = 	'[underline]HTTP Sent[/underline]\n'
			httpSent += 	'\n'
			httpSent += 	f'RETRIEVE : {stats[Statistics.httpSendRetrieves]}\n'
			httpSent += 	f'CREATE   : {stats[Statistics.httpSendCreates]}\n'
			httpSent += 	f'UPDATE   : {stats[Statistics.httpSendUpdates]}\n'
			httpSent += 	f'DELETE   : {stats[Statistics.httpSendDeletes]}\n'

			logs  = '[underline]Logs[/underline]\n'
			logs += '\n'
			logs += f'LogLevel : {str(L.logLevel)}\n'
			logs += f'Errors   : {stats[Statistics.logErrors]}\n'
			logs += f'Warnings : {stats[Statistics.logWarnings]}\n'

		else:
			resourceOps  = '\n[dim]statistics are disabled[/dim]\n'
			httpReceived = '\n[dim]statistics are disabled[/dim]\n'
			httpSent     = '\n[dim]statistics are disabled[/dim]\n'
			logs         = '\n[dim]statistics are disabled[/dim]\n'

		misc  = '[underline]Misc[/underline]\n'
		misc += '\n'
		misc += f'StartTime : {datetime.datetime.fromtimestamp(DateUtils.fromAbsRelTimestamp(cast(str, stats[Statistics.cseStartUpTime])))} (UTC)\n'
		misc += f'Uptime    : {stats[Statistics.cseUpTime]}\n'
		if hasattr(os, 'getloadavg'):
			load = os.getloadavg()
			misc += f'Load      : {load[0]:.2f} | {load[1]:.2f} | {load[2]:.2f}\n'
		else:
			misc += '\n'
		misc += f'Platform  : {sys.platform}\n'
		misc += f'Python    : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'

		# Adapt the following line when adding resources to keep formatting. 
		# It fills up the right columns to match the length of the left column.
		misc += '\n' * ( 3 if CSE.statistics.statisticsEnabled else 8)

		requestsGrid = Table.grid(expand=True)
		requestsGrid.add_column(ratio=33)
		requestsGrid.add_column(ratio=33)
		requestsGrid.add_column(ratio=33)
		requestsGrid.add_row(resourceOps, httpReceived, httpSent)

		infoGrid = Table.grid(expand=True)
		infoGrid.add_column(ratio=33)
		infoGrid.add_column(ratio=67)
		infoGrid.add_row(logs, misc)

		rightGrid = Table.grid(expand=True)
		rightGrid.add_column()
		rightGrid.add_row(Panel(requestsGrid))
		rightGrid.add_row(Panel(infoGrid))

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
		resourceTypes += f'TSI     : {CSE.dispatcher.countResources(T.TSI)}\n'
		resourceTypes += '\n'
		resourceTypes += f'[bold]Total[/bold]   : {int(stats[Statistics.resourceCount]) - CSE.dispatcher.countResources((T.CNT_LA, T.CNT_OL, T.FCNT_LA, T.FCNT_OL, T.TS_LA, T.TS_OL, T.GRP_FOPT, T.PCH_PCU))}\n'	# substract the virtual resources
		
		result = Table.grid(expand=True)
		result.style = style
		result.add_column(width=15)
		result.add_column()
		result.add_row(Panel(resourceTypes), rightGrid )

		return result


	def getResourceTreeRich(self, maxLevel:int=0, parent:str=None, style:Style=Style()) -> Tree:
		"""	This function will generate a Rich tree of a CSE's resource structure.
		"""

		#import resources.FCNT

		def info(res:Resource) -> str:

			# Determine extra infos
			extraInfo = ''
			if self.treeMode not in [ TreeMode.COMPACT, TreeMode.CONTENTONLY ]: 
				if res.ty == T.FCNT:
					extraInfo = f' ({res.cnd})'
				if res.ty in [ T.CIN, T.TS ]:
					extraInfo = f' ({res.cnf})' if res.cnf else ''
				elif res.ty == T.CSEBase:
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
				info = f'-> {res.__rtype__}{extraInfo} | ri={res.ri}'

			return f'{res.rn} [dim]{info}[/dim]'


		def getChildren(res:Resource, tree:Tree, level:int) -> None:
			""" Find and print the children in the tree structure. """
			if maxLevel > 0 and level == maxLevel:
				return
			chs = CSE.dispatcher.directChildResources(res.ri)
			for ch in chs:
				if ch.__isVirtual__:	# Ignore virual resources
					continue
				# Ignore resources/resource patterns 
				ri = ch.ri
				if len([ p for p in self.hideResources if helpers.TextTools.simpleMatch(p, ri) ]) > 0:
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
		tree = Tree(info(res), style=style, guide_style=style)
		getChildren(res, tree, 0)
		return tree


	def getResourceTreeText(self, maxLevel:int=0) -> str:
		"""	This function will generate a Text tree of a CSE's resource structure.
		"""
		from rich.console import Console as RichConsole

		console = RichConsole(color_system=None)
		console.begin_capture()
		console.print(self.getResourceTreeRich())
		return console.end_capture()
