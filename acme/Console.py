#
#	Console.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Console functions for ACME CSE
#

from typing import Dict, Union, cast
import datetime, os, sys, time
from Logging import Logging
from helpers.KeyHandler import loop, stopLoop, readline, waitForKeypress
from Constants import Constants as C
from Configuration import Configuration
from Types import CSEType, ResourceTypes as T
from resources.Resource import Resource

from helpers.BackgroundWorker import BackgroundWorkerPool
import Utils, CSE, Statistics
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree



_refreshTime = 2.0 # for continous display
# TODO refreshTime configurable?


class Console(object):

	def __init__(self) -> None:
		Logging.log('Console initialized')


	def shutdown(self) -> bool:
		Logging.log('Console shut down')
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
			'l'     : self.toggleLogging,
			'Q'		: self.shutdownCSE,		# See handler below
			'r'		: self.cseRegistrations,
			's'		: self.statistics,
			'\x13'	: self.continuesStatistics,
			't'		: self.resourceTree,
			'\x14'	: self.continuesTree,
			'T'		: self.childResourceTree,
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

	def help(self, key:str) -> None:
		"""	Print help for keyboard commands.
		"""
		Logging.console(f'\n[white][dim][[/dim][red][i]ACME[/i][/red][dim]] {C.version}', plain=True)
		Logging.console("""**Console Commands**  
- h, ?  - This help
- Q, ^C - Shutdown CSE
- c     - Show configuration
- C     - Clear the console screen
- D     - Delete resource
- i     - Inspect resource
- I     - Inspect resource and child resources
- l     - Toggle logging on/off
- r     - Show CSE registrations
- s     - Show statistics
- ^S    - Show statistics continuously
- t     - Show resource tree
- T     - Show child resource tree
- ^T    - Show resource tree continuously
- w     - Show worker threads status
- Z     - Reset the CSE
	""", extranl=True)


	def shutdownCSE(self, key:str) -> None:
		"""	Shutdown the CSE.
		"""
		if not CSE.isHeadless:
			Logging.console('Shutdown CSE')
		sys.exit()


	def toggleLogging(self, key:str) -> None:
		"""	Toggle through the log levels.
		"""
		Logging.enableScreenLogging = not Logging.enableScreenLogging
		Logging.console(f'Logging enabled -> **{Logging.enableScreenLogging}**')


	def workers(self, key:str) -> None:
		"""	Print the worker and actor threads.
		"""
		from rich.table import Table

		Logging.console('**Worker & Actor Threads**', extranl=True)
		table = Table()
		table.add_column('Name', no_wrap=True)
		table.add_column('Type', no_wrap=True)
		table.add_column('Interval', no_wrap=True)
		table.add_column('Runs', no_wrap=True)
		for w in BackgroundWorkerPool.backgroundWorkers.values():
			a = 'Actor' if w.count == 1 else 'Worker'
			table.add_row(w.name, a, str(w.interval), str(w.numberOfRuns))
		Logging.console(table, extranl=True)


	def configuration(self, key:str) -> None:
		"""	Print the configuration.
		"""
		from rich.table import Table

		Logging.console('**Configuration**', extranl=True)
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
		Logging.console(table, extranl=True)


	def clearScreen(self, key:str) -> None:
		"""	Clear the console screen.
		"""
		Logging.consoleClear()


	def resourceTree(self, key:str) -> None:
		"""	Render the CSE's resource tree.
		"""
		Logging.console('**Resource Tree**', extranl=True)
		Logging.console(self.getResourceTreeRich())
		Logging.console()


	def childResourceTree(self, key:str) -> None:
		"""	Render the CSE's resource tree, beginning with a child resource.
		"""
		Logging.console('**Child Resource Tree**', extranl=True)
		loggingOld = Logging.loggingEnabled
		Logging.loggingEnabled = False
		
		if (ri := readline('ri=')) is None:
			Logging.console()
		elif len(ri) > 0:
			if (tree := self.getResourceTreeRich(parent=ri)) is not None:
				Logging.console(tree)
			else:
				Logging.console('not found', isError=True)

		Logging.loggingEnabled = loggingOld


	def continuesTree(self, key:str) -> None:
		loggingOld = Logging.loggingEnabled
		Logging.loggingEnabled = False
		while True:
			self.clearScreen(key)
			self.resourceTree(key)
			Logging.console('**(Press any key to stop)**')
			if waitForKeypress(_refreshTime) is not None:
				break
		self.clearScreen(key)
		Logging.loggingEnabled = loggingOld


	def cseRegistrations(self, key:str) -> None:
		"""	Render CSE registrations.
		"""
		Logging.console('**CSE Registrations**', extranl=True)
		Logging.console(self.getCSERegistrationsRich())
		Logging.console()


	def statistics(self, key:str) -> None:
		""" Render various statistics & counts.
		"""
		Logging.console('**Statistics**', extranl=True)
		Logging.console(self.getStatisticsRich())
		Logging.console()

	
	def continuesStatistics(self, key:str) -> None:
		loggingOld = Logging.loggingEnabled
		Logging.loggingEnabled = False
		while True:
			self.clearScreen(key)
			self.statistics(key)
			# self.resourceTree(key)
			Logging.console('**(Press any key to stop)**')
			if waitForKeypress(_refreshTime) is not None:
				break
		self.clearScreen(key)
		Logging.loggingEnabled = loggingOld


	def deleteResource(self, key:str) -> None:
		"""	Delete a resource from the CSE.
		"""
		Logging.console('**Delete Resource**', extranl=True)
		loggingOld = Logging.loggingEnabled
		Logging.loggingEnabled = False

		if (ri := readline('ri=')) is None:
			Logging.console()
		elif len(ri) > 0:
			if (res := CSE.dispatcher.retrieveResource(ri)).resource is None:
				Logging.console(res.dbg, isError=True)
			else:
				if (res := CSE.dispatcher.deleteResource(res.resource, withDeregistration=True)).resource is None:
					Logging.console(res.dbg, isError=True)
				else:
					Logging.console('ok')

		Logging.loggingEnabled = loggingOld


	def inspectResource(self, key:str) -> None:
		"""	Show a resource.
		"""
		Logging.console('**Inspect Resource**', extranl=True)
		loggingOld = Logging.loggingEnabled
		Logging.loggingEnabled = False
		
		if (ri := readline('ri=')) is None:
			Logging.console()
		elif len(ri) > 0:
			if (res := CSE.dispatcher.retrieveResource(ri)).resource is None:
				Logging.console(res.dbg, isError=True)
			else:
				Logging.console(res.resource.asDict())
		Logging.loggingEnabled = loggingOld


	def inspectResourceChildren(self, key:str) -> None:
		"""	Show a resource and its children.
		"""
		Logging.console('**Inspect Resource and Children**', extranl=True)
		loggingOld = Logging.loggingEnabled
		Logging.loggingEnabled = False
		
		if (ri := readline('ri=')) is None:
			Logging.console()
		elif len(ri) > 0:
			if (res := CSE.dispatcher.retrieveResource(ri)).resource is None:
				Logging.console(res.dbg, isError=True)
			else: 
				if (resdis := CSE.dispatcher.discoverResources(ri, originator=CSE.cseOriginator)).lst is None:
					Logging.console(resdis.dbg, isError=True)
				else:
					CSE.dispatcher.resourceTreeDict(resdis.lst, res.resource)	# the function call add attributes to the target resource
					Logging.console(res.resource.asDict())
		Logging.loggingEnabled = loggingOld


	def resetCSE(self, key:str) -> None:
		"""	Reset the CSE. Remove all resources and do the importing again.
		"""
		Logging.console('**Resetting CSE**', extranl=True)
		Logging.enableScreenLogging = True
		CSE.resetCSE()


	#########################################################################
	#
	#	Generators for rich output
	#

	def getCSERegistrationsRich(self) -> str:
		"""	Return an overview in Rich format about the registrar, registrees, and
			descendant CSE's.
		"""

		result = ''
		if CSE.cseType != CSEType.IN and CSE.remote.remoteAddress is not None:
			registrarCSE = CSE.remote.registrarCSE
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE is not None else '???'
			result += f'- **Registrar CSE**  \n{CSE.remote.registrarCSI[1:]} ({registrarType}) @ {CSE.remote.remoteAddress}\n'

		if CSE.cseType != CSEType.ASN:
			#connections = {}
			if len(CSE.remote.descendantCSR) > 0:
				result += f'- **Registree CSEs**\n'
				for desc in CSE.remote.descendantCSR.keys():
					(csr, atCsi) = CSE.remote.descendantCSR[desc]
					if csr is not None:
						result += f'  - {desc[1:]} ({CSEType(csr.cst).name}) @ {csr.poa}\n'
						for desc2 in CSE.remote.descendantCSR.keys():
							(csr2, atCsi2) = CSE.remote.descendantCSR[desc2]
							if csr2 is None and atCsi2 == desc:
								result += f'    - {desc2[1:]}\n'
		
		return result if len(result) else 'None'
		

# TODO events transit requests
	def getStatisticsRich(self) -> Table:
		"""	Generate an overview about various resources and event counts.
		"""

		stats = CSE.statistics.getStats()

		if CSE.statistics.statisticsEnabled:
			resourceOps  =  '[bold][underline]Resource Operations[/underline][/bold]\n'
			resourceOps += 	'\n'
			resourceOps +=  f'Created       : {stats[Statistics.createdResources]}\n'
			resourceOps +=  f'Updated       : {stats[Statistics.updatedResources]}\n'
			resourceOps +=  f'Deleted       : {stats[Statistics.deletedResources]}\n'
			resourceOps +=  f'Expired       : {stats[Statistics.expiredResources]}\n'
			resourceOps +=  f'Notifications : {stats[Statistics.notifications]}\n'

			httpReceived  = '[bold][underline]HTTP Received[/underline][/bold]\n'
			httpReceived += 	'\n'
			httpReceived += f'RETRIEVE : {stats[Statistics.httpRetrieves]}\n'
			httpReceived += f'CREATE   : {stats[Statistics.httpCreates]}\n'
			httpReceived += f'UPDATE   : {stats[Statistics.httpUpdates]}\n'
			httpReceived += f'DELETE   : {stats[Statistics.httpDeletes]}\n'

			httpSent  = 	'[bold][underline]HTTP Sent[/underline][/bold]\n'
			httpSent += 	'\n'
			httpSent += 	f'RETRIEVE : {stats[Statistics.httpSendRetrieves]}\n'
			httpSent += 	f'CREATE   : {stats[Statistics.httpSendCreates]}\n'
			httpSent += 	f'UPDATE   : {stats[Statistics.httpSendUpdates]}\n'
			httpSent += 	f'DELETE   : {stats[Statistics.httpSendDeletes]}\n'

			logs  = '[bold][underline]Logs[/underline][/bold]\n'
			logs += '\n'
			logs += f'Errors   : {stats[Statistics.logErrors]}\n'
			logs += f'Warnings : {stats[Statistics.logWarnings]}\n'

		else:
			resourceOps  = '\n[dim]statistics are disabled[/dim]\n'
			httpReceived = '\n[dim]statistics are disabled[/dim]\n'
			httpSent     = '\n[dim]statistics are disabled[/dim]\n'
			logs         = '\n[dim]statistics are disabled[/dim]\n'

		misc  = '[bold][underline]Misc[/underline][/bold]\n'
		misc += '\n'
		misc += f'StartTime : {datetime.datetime.fromtimestamp(Utils.fromISO8601Date(cast(str, stats[Statistics.cseStartUpTime])))} (UTC)\n'
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

		resourceTypes = '[bold][underline]Resource Types[/underline][/bold]\n'
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
		result.add_column(width=12, min_width=12)
		result.add_column()
		result.add_row(Panel(resourceTypes), rightGrid )

		return result


	def getResourceTreeRich(self, maxLevel:int=0, parent:str=None) -> Tree:
		"""	This function will generate a Rich tree of a CSE's resource structure.
		"""

		def info(res:Resource) -> str:
			if res.ty == T.FCNT:
				return f'{res.rn} [dim]-> {res.__rtype__} ({res.cnd}) | ri={res.ri}[/dim]'
			if res.ty == T.CSEBase:
				return f'{res.rn} [dim]-> {res.__rtype__} | ri={res.ri} | csi={res.csi}[/dim]'
			# if res.__isVirtual__:
			# 	return f'{res.rn}'
			return f'{res.rn} [dim]-> {res.__rtype__} | ri={res.ri}[/dim]'

		def getChildren(res:Resource, tree:Tree, level:int) -> None:
			""" Find and print the children in the tree structure. """
			if maxLevel > 0 and level == maxLevel:
				return
			chs = CSE.dispatcher.directChildResources(res.ri)
			for ch in chs:
				if ch.__isVirtual__:
					continue
				branch = tree.add(info(ch))
				getChildren(ch, branch, level+1)

		if parent is not None:
			if (res := CSE.dispatcher.retrieveResource(parent).resource) is None:
				return None
		else:
			res = Utils.getCSE().resource
		if res is None:
			return None
		tree = Tree(info(res))
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

