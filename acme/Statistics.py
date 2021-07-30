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
from Logging import Logging as L
from Configuration import Configuration
import CSE, Utils
import datetime
from urllib.parse import urlparse
from copy import deepcopy
from threading import Lock
from helpers.BackgroundWorker import BackgroundWorkerPool
from resources.Resource import Resource
from Types import CSEType, ResourceTypes as T


deletedResources	= 'rmRes'
createdResources	= 'crRes'
updatedResources	= 'upRes'
expiredResources 	= 'exRes'
httpRetrieves		= 'htRet'
httpCreates			= 'htCre'
httpUpdates			= 'htUpd'
httpDeletes			= 'htDel'
httpSendRetrieves	= 'htSRt'
httpSendCreates		= 'htSCr'
httpSendUpdates		= 'htSUp'
httpSendDeletes		= 'htSDl'
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
			CSE.event.addHandler(CSE.event.createResource, self.handleCreateEvent) 				# type: ignore
			CSE.event.addHandler(CSE.event.updateResource, self.handleUpdateEvent)				# type: ignore
			CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent)				# type: ignore
			CSE.event.addHandler(CSE.event.expireResource, self.handleExpireResource)			# type: ignore
			CSE.event.addHandler(CSE.event.httpRetrieve, self.handleHttpRetrieveEvent)			# type: ignore
			CSE.event.addHandler(CSE.event.httpCreate, self.handleHttpCreateEvent)				# type: ignore
			CSE.event.addHandler(CSE.event.httpUpdate, self.handleHttpUpdateEvent)				# type: ignore
			CSE.event.addHandler(CSE.event.httpDelete, self.handleHttpDeleteEvent)				# type: ignore
			CSE.event.addHandler(CSE.event.httpSendRetrieve, self.handleHttpSendRetrieveEvent)	# type: ignore
			CSE.event.addHandler(CSE.event.httpSendCreate, self.handleHttpSendCreateEvent)		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendUpdate, self.handleHttpSendUpdateEvent)		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendDelete, self.handleHttpSendDeleteEvent)		# type: ignore
			CSE.event.addHandler(CSE.event.notification, self.handleNotification)				# type: ignore
			CSE.event.addHandler(CSE.event.cseStartup, self.handleCseStartup)					# type: ignore
			CSE.event.addHandler(CSE.event.logError, self.handleLogError)						# type: ignore
			CSE.event.addHandler(CSE.event.logWarning, self.handleLogWarning)					# type: ignore

		L.isInfo and L.log('Statistics initialized')


	def shutdown(self) -> bool:
		if self.statisticsEnabled:
			# Stop the worker
			L.isInfo and L.log('Stopping statistics DB thread')
			BackgroundWorkerPool.stopWorkers('statsDBWorker')

			# One final write
			self.storeDBStatistics()

		L.isInfo and L.log('Statistics shut down')
		return True


	def setupStats(self) -> StatsT:
		result = self.retrieveDBStatistics()
		if result is not None:
			return result
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
			httpSendRetrieves	: 0,
			httpSendCreates		: 0,
			httpSendUpdates 	: 0,
			httpSendDeletes 	: 0,
			cseStartUpTime		: 0.0,
			logErrors 			: 0,
			logWarnings 		: 0
		}

	# Return stats
	def getStats(self) -> StatsT:			
		s = deepcopy(self.stats)

		# Calculate some stats
		s[cseUpTime] = str(datetime.timedelta(seconds=int(datetime.datetime.now(datetime.timezone.utc).timestamp() - int(s[cseStartUpTime]))))
		s[cseStartUpTime] = Utils.toISO8601Date(float(s[cseStartUpTime]))
		s[resourceCount] = int(s[createdResources]) - int(s[deletedResources])
		return s


	#########################################################################
	#
	#	Event handlers
	#

	def handleCreateEvent(self, resource:Resource) -> None:
		with self.statLock:
			self.stats[createdResources] += 1		# type: ignore
	

	def handleDeleteEvent(self, resource:Resource) -> None:
		with self.statLock:
			self.stats[deletedResources] += 1		# type: ignore
	

	def handleUpdateEvent(self, resource:Resource) -> None:
		with self.statLock:
			self.stats[updatedResources] += 1		# type: ignore


	def handleExpireResource(self, resource:Resource) -> None:
		with self.statLock:
			self.stats[expiredResources] += 1		# type: ignore


	def handleHttpRetrieveEvent(self) -> None:
		with self.statLock:
			self.stats[httpRetrieves] += 1		# type: ignore


	def handleHttpCreateEvent(self) -> None:
		with self.statLock:
			self.stats[httpCreates] += 1		# type: ignore


	def handleHttpUpdateEvent(self) -> None:
		with self.statLock:
			self.stats[httpUpdates] += 1		# type: ignore


	def handleHttpDeleteEvent(self) -> None:
		with self.statLock:
			self.stats[httpDeletes] += 1		# type: ignore


	def handleHttpSendRetrieveEvent(self) -> None:
		with self.statLock:
			self.stats[httpSendRetrieves] += 1	# type: ignore


	def handleHttpSendCreateEvent(self) -> None:
		with self.statLock:
			self.stats[httpSendCreates] += 1	# type: ignore


	def handleHttpSendUpdateEvent(self) -> None:
		with self.statLock:
			self.stats[httpSendUpdates] += 1	# type: ignore


	def handleHttpSendDeleteEvent(self) -> None:
		with self.statLock:
			self.stats[httpSendDeletes] += 1	# type: ignore


	def handleCseStartup(self) -> None:
		with self.statLock:
			self.stats[cseStartUpTime] = datetime.datetime.now(datetime.timezone.utc).timestamp()


	def handleLogError(self) -> None:
		with self.statLock:
			self.stats[logErrors] += 1	# type: ignore


	def handleLogWarning(self) -> None:
		with self.statLock:
			self.stats[logWarnings] += 1		# type: ignore


	def handleNotification(self) -> None:
		with self.statLock:
			self.stats[notifications] += 1		# type: ignore


	#########################################################################
	#
	#	Store statistics handling

	# Called by the background worker
	def statisticsDBWorker(self) -> bool:
		L.isDebug and L.logDebug('Writing statistics DB')
		try:
			self.storeDBStatistics()
		except Exception as e:
			L.isDebug and L.logErr(f'Exception: {str(e)}')
			return False
		return True


	def retrieveDBStatistics(self) -> StatsT:
		with self.statLock:
			return CSE.storage.getStatistics()


	def storeDBStatistics(self) -> bool:
		with self.statLock:
			return CSE.storage.updateStatistics(self.stats)
	
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
		if CSE.cseType != CSEType.IN and CSE.remote.remoteAddress is not None:
			registrarCSE = CSE.remote.registrarCSE
			bg = 'white' if registrarCSE is not None else 'lightgrey'
			color = 'green' if registrarCSE is not None else 'black'
			address = urlparse(CSE.remote.remoteAddress)
			(ip, port) = tuple(address.netloc.split(':'))
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE is not None else '???'
			result += f'cloud PARENT as "<color:{color}>{CSE.remote.registrarCSI[1:]}</color> ({registrarType})\\n{CSE.remote.remoteAddress}" #{bg}\n'
			result += 'CSE -UP- PARENT\n'

		
		# Has CSE descendants?
		if CSE.cseType != CSEType.ASN:
			cnt = 0
			connections = {}
			for desc in CSE.remote.descendantCSR.keys():
				csi = desc[1:]
				(csr, atCsi) = CSE.remote.descendantCSR[desc]
				address = f'\\n{csr.poa}' if csr is not None else ''
				tpe = f' ({CSEType(csr.cst).name})' if csr is not None else ''
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
