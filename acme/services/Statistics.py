#
#	Statistics.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Statistics Module
#

from __future__ import annotations
from typing import Dict, Union, cast
import datetime
from urllib.parse import urlparse
from copy import deepcopy
from threading import Lock

from ..etc.Types import CSEType, ResourceTypes as T
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services import CSE as CSE
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..helpers.BackgroundWorker import BackgroundWorkerPool


deletedResources	= 'rmRes'
createdResources	= 'crRes'
updatedResources	= 'upRes'
expiredResources 	= 'exRes'
httpRetrieves		= 'htRet'
httpCreates			= 'htCre'
httpUpdates			= 'htUpd'
httpDeletes			= 'htDel'
httpNotifies		= 'htNot'
httpSendRetrieves	= 'htSRt'
httpSendCreates		= 'htSCr'
httpSendUpdates		= 'htSUp'
httpSendDeletes		= 'htSDl'
httpSendNotifies	= 'htSNo'
mqttRetrieves		= 'mqRet'
mqttCreates			= 'mqCre'
mqttUpdates			= 'mqUpd'
mqttDeletes			= 'mqDel'
mqttNotifies		= 'mqNot'
mqttSendRetrieves	= 'mqSRt'
mqttSendCreates		= 'mqSCr'
mqttSendUpdates		= 'mqSUp'
mqttSendDeletes		= 'mqSDl'
mqttSendNotifies	= 'mqSNo'
notifications		= 'notif'
logErrors			= 'lgErr'
logWarnings			= 'lgWrn'
cseStartUpTime		= 'cseSU'
cseUpTime			= 'cseUT'
resourceCount		= 'ctRes'

# TODO  restartcount, 

StatsT = Dict[str, Union[str, int, float]]

class Statistics(object):

	def __init__(self) -> None:
		self.statisticsEnabled = Configuration.get('cse.statistics.enable')

		# create lock
		self.statLock = Lock()

		# retrieve or create statistics record, even when statistics are disabled
		self.stats = self.setupStats()

		if self.statisticsEnabled:

			# Start background worker to handle writing to DB
			L.isInfo and L.log('Starting statistics DB thread')
			BackgroundWorkerPool.newWorker(Configuration.get('cse.statistics.writeInterval'), self.statisticsDBWorker, 'statsDBWorker').start()

			# subscripe vto various events
			# mypy cannot handle dynamically created attributes
			CSE.event.addHandler(CSE.event.createResource, lambda _: self._handleStatsEvent(createdResources)) 	# type: ignore
			CSE.event.addHandler(CSE.event.updateResource, lambda _: self._handleStatsEvent(updatedResources))	# type: ignore
			CSE.event.addHandler(CSE.event.deleteResource, lambda _: self._handleStatsEvent(deletedResources))	# type: ignore
			CSE.event.addHandler(CSE.event.expireResource, lambda _: self._handleStatsEvent(expiredResources))	# type: ignore
			CSE.event.addHandler(CSE.event.httpRetrieve, lambda: self._handleStatsEvent(httpRetrieves))			# type: ignore
			CSE.event.addHandler(CSE.event.httpCreate, lambda: self._handleStatsEvent(httpCreates))				# type: ignore
			CSE.event.addHandler(CSE.event.httpUpdate, lambda: self._handleStatsEvent(httpUpdates))				# type: ignore
			CSE.event.addHandler(CSE.event.httpDelete, lambda: self._handleStatsEvent(httpDeletes))				# type: ignore
			CSE.event.addHandler(CSE.event.httpNotify, lambda: self._handleStatsEvent(httpNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.httpSendRetrieve, lambda: self._handleStatsEvent(httpSendRetrieves))	# type: ignore
			CSE.event.addHandler(CSE.event.httpSendCreate, lambda: self._handleStatsEvent(httpSendCreates))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendUpdate, lambda: self._handleStatsEvent(httpSendUpdates))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendDelete, lambda: self._handleStatsEvent(httpSendDeletes))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendNotify, lambda: self._handleStatsEvent(httpSendNotifies))	# type: ignore
			CSE.event.addHandler(CSE.event.mqttRetrieve, lambda: self._handleStatsEvent(mqttRetrieves))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttCreate, lambda: self._handleStatsEvent(mqttCreates))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttUpdate, lambda: self._handleStatsEvent(mqttUpdates))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttDelete, lambda: self._handleStatsEvent(mqttDeletes))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttNotify, lambda: self._handleStatsEvent(mqttNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendRetrieve, lambda: self._handleStatsEvent(mqttSendRetrieves))	# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendCreate, lambda: self._handleStatsEvent(mqttSendCreates))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendUpdate, lambda: self._handleStatsEvent(mqttSendUpdates))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendDelete, lambda: self._handleStatsEvent(mqttSendDeletes))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendNotify, lambda: self._handleStatsEvent(mqttSendNotifies))	# type: ignore
			CSE.event.addHandler(CSE.event.notification, lambda: self._handleStatsEvent(notifications))			# type: ignore
			CSE.event.addHandler(CSE.event.cseStartup, self.handleCseStartup)									# type: ignore
			CSE.event.addHandler(CSE.event.logError, lambda: self._handleStatsEvent(logErrors))					# type: ignore
			CSE.event.addHandler(CSE.event.logWarning, lambda: self._handleStatsEvent(logWarnings))				# type: ignore

			# Also do some internal handling
			CSE.event.addHandler(CSE.event.cseReset, self.restart)												# type: ignore

		L.isInfo and L.log('Statistics initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the statistics service.
		"""
		if self.statisticsEnabled:
			# Stop the worker
			L.isInfo and L.log('Stopping statistics DB thread')
			BackgroundWorkerPool.stopWorkers('statsDBWorker')

			# One final write
			self.storeDBStatistics()

		L.isInfo and L.log('Statistics shut down')
		return True
	
	
	def restart(self) -> None:
		"""	Restart the statistics service.
		"""
		self.purgeDBStatistics()
		self.stats = self.setupStats()
		self.handleCseStartup()
		L.isDebug and L.logDebug('Statistics restarted')


	def setupStats(self) -> StatsT:
		if (stats := self.retrieveDBStatistics()):
			return stats
		return {
			deletedResources	: 0,
			createdResources	: 0,
			updatedResources	: 0,
			expiredResources 	: 0,
			notifications		: 0,
			httpRetrieves		: 0,
			httpCreates			: 0,
			httpUpdates 		: 0,
			httpDeletes 		: 0,
			httpNotifies 		: 0,
			httpSendRetrieves	: 0,
			httpSendCreates		: 0,
			httpSendUpdates 	: 0,
			httpSendDeletes 	: 0,
			httpSendNotifies 	: 0,
			mqttRetrieves		: 0,
			mqttCreates			: 0,
			mqttUpdates 		: 0,
			mqttDeletes 		: 0,
			mqttNotifies 		: 0,
			mqttSendRetrieves	: 0,
			mqttSendCreates		: 0,
			mqttSendUpdates 	: 0,
			mqttSendDeletes 	: 0,
			mqttSendNotifies 	: 0,

			cseStartUpTime		: 0.0,
			logErrors 			: 0,
			logWarnings 		: 0
		}

	# Return stats
	def getStats(self) -> StatsT:			
		s = deepcopy(self.stats)

		# Calculate some stats
		# s[cseUpTime] = str(datetime.timedelta(seconds=int(datetime.datetime.now(datetime.timezone.utc).timestamp() - int(s[cseStartUpTime]))))
		s[cseUpTime] = str(datetime.timedelta(seconds=int(DateUtils.utcTime() - int(s[cseStartUpTime]))))
		s[cseStartUpTime] = DateUtils.toISO8601Date(float(s[cseStartUpTime]))
		s[resourceCount] = int(s[createdResources]) - int(s[deletedResources])
		return s


	#########################################################################
	#
	#	Event handlers
	#

	def _handleStatsEvent(self, eventType:str) -> None:
		"""	Generic handling of statist events.
		"""
		try:
			with self.statLock:
				self.stats[eventType] += 1		# type: ignore
		except KeyError:
			# In case there is a version update and a new event was added,
			# the we might just add this event as the first entry
			with self.statLock:
				self.stats[eventType] = 1		# type: ignore


	def handleCseStartup(self) -> None:
		"""	Assign the CSE's startup time.
		"""
		with self.statLock:
			# self.stats[cseStartUpTime] = datetime.datetime.now(datetime.timezone.utc).timestamp()
			self.stats[cseStartUpTime] = DateUtils.utcTime()


	#########################################################################
	#
	#	Store statistics handling

	# Called by the background worker
	def statisticsDBWorker(self) -> bool:
		# L.isDebug and L.logDebug('Writing statistics DB')
		try:
			self.storeDBStatistics()
		except Exception as e:
			L.logErr(f'Error while writing statistics DB Exception: {str(e)}', exc = e)
			return False
		return True


	def retrieveDBStatistics(self) -> StatsT:
		with self.statLock:
			return CSE.storage.getStatistics()


	def storeDBStatistics(self) -> bool:
		"""	Store statistics data"""
		with self.statLock:
			return CSE.storage.updateStatistics(self.stats)
	

	def purgeDBStatistics(self) -> None:
		with self.statLock:
			CSE.storage.purgeStatistics()

	
	#########################################################################
	#
	#	CSE Structure handling

	def getStructurePuml(self, maxLevel:int=0) -> str:
		"""	This function will generate a PlanUML graph of a CSE's structure, including:
				- The CSE, Type, http, port
				- The CSE's resource tree
				- The Registrar CSE (if any)
				- A list of descendant CSE's (if any)
		"""

		def getChildren(res:Resource, level:int) -> str:
			""" Find and print the children in the tree structure. """
			result = ''
			if maxLevel > 0 and level == maxLevel:
				return result
			chs = CSE.dispatcher.directChildResources(res.ri)
			for ch in chs:
				result += ' ' * 2 * level + f'|_ {ch.rn} <color:grey>< {T(ch.ty).tpe()} ></color>\n'
				result += getChildren(ch, level+1)
			return result

		result = """@startuml
!define lightgrey eeeeee
skinparam defaultTextAlignment center
skinparam note {
    BorderColor grey
    backgroundColor lightgrey
    RoundCorner 25
    TextAlignment left
    FontSize 10
}
skinparam rectangle {
	Shadowing<< CSE >> false
	bordercolor<< CSE >> #cccccc
}
"""

		# Own CSE node & http interface
		result += 'rectangle << CSE >> {\n'
		address = urlparse(CSE.httpServer.serverAddress)
		(ip, _) = tuple(address.netloc.split(':'))
		result += f'node CSE as "<color:green>{CSE.cseCsi[1:]}</color> ({CSE.cseType.name})\\n{ip}" #white\n'

		# Own http interface
		http = 'https' if CSE.security.useTLSHttp else 'http'
		result += f'interface "{http}\\n{CSE.httpServer.port}" as http_own #white\n'

		# Build Resource Tree
		result += 'note right of CSE\n'
		result += '**Resource Tree**\n\n'
		cse = Utils.getCSE().resource
		result += f'{cse.rn}\n'
		result += getChildren(cse, 0)
		result += 'end note\n'

		# Build Own
		result += 'http_own - [CSE] : \\t\n'
		result += '}\n' # rectangle

		# Has parent Registrar CSE?
		if CSE.cseType != CSEType.IN and CSE.remote.remoteAddress:
			registrarCSE = CSE.remote.registrarCSE
			bg = 'white' if registrarCSE else 'lightgrey'
			color = 'green' if registrarCSE else 'black'
			address = urlparse(CSE.remote.remoteAddress)
			(ip, port) = tuple(address.netloc.split(':'))
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
			result += f'cloud PARENT as "<color:{color}>{CSE.remote.registrarCSI[1:]}</color> ({registrarType})\\n{CSE.remote.remoteAddress}" #{bg}\n'
			result += 'CSE -UP- PARENT\n'

		
		# Has CSE descendants?
		if CSE.cseType != CSEType.ASN:
			cnt = 0
			connections = {}
			for desc in CSE.remote.descendantCSR.keys():
				csi = desc[1:]
				(csr, atCsi) = CSE.remote.descendantCSR[desc]
				address = f'\\n{csr.poa}' if csr else ''
				tpe = f' ({CSEType(csr.cst).name})' if csr and csr.cst else ''
				shape = 'node' if csr else 'rectangle'
				result += f'{shape} d{cnt} as "<color:green>{csi}</color>{tpe}{address}" #white\n'
				connections[desc] = (cnt, atCsi)
				cnt += 1
			
			for key in connections.keys():
				connection = connections[key]
				nodeNr = connection[0]
				atCsi = connection[1]
				if atCsi == CSE.cseCsi:
					result += f'd{nodeNr} -UP- CSE\n'
				else:
					if atCsi in connections:
						subcon = connections[atCsi]
						result += f'd{connection[0]} -UP- d{subcon[0]}\n'

		# end
		result += '@enduml'
		return result
