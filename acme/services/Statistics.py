#
#	Statistics.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Statistics Module
#

"""	Statistics Module for internal statistics.
"""
from __future__ import annotations
from typing import Dict, Union, Optional

import datetime
from urllib.parse import urlparse
from copy import deepcopy
from threading import Lock

from ..etc.Types import CSEType, ResourceTypes
from ..etc.DateUtils import utcTime, toISO8601Date
from ..services import CSE
from ..services.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.CSEBase import getCSE
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..services.Logging import Logging as L


deletedResources	= 'rmRes'
""" Attribute name for number of deleted resources in the storage. """
createdResources	= 'crRes'
""" Attribute name for number of created resources in the storage. """
updatedResources	= 'upRes'
""" Attribute name for number of updated resources in the storage. """
expiredResources 	= 'exRes'
""" Attribute name for number of expired resources in the storage. """
httpRetrieves		= 'htRet'
""" Attribute name for number of HTTP RETRIEVE requests. """
httpCreates			= 'htCre'
""" Attribute name for number of HTTP CREATE requests. """
httpUpdates			= 'htUpd'
""" Attribute name for number of HTTP UPDATE requests. """
httpDeletes			= 'htDel'
""" Attribute name for number of HTTP DELETE requests. """
httpNotifies		= 'htNot'
""" Attribute name for number of HTTP NOTIFY requests. """
httpSendRetrieves	= 'htSRt'
""" Attribute name for number of HTTP SEND RETRIEVE requests. """
httpSendCreates		= 'htSCr'
""" Attribute name for number of HTTP SEND CREATE requests. """
httpSendUpdates		= 'htSUp'
""" Attribute name for number of HTTP SEND UPDATE requests. """
httpSendDeletes		= 'htSDl'
""" Attribute name for number of HTTP SEND DELETE requests. """
httpSendNotifies	= 'htSNo'
""" Attribute name for number of HTTP SEND NOTIFY requests. """
mqttRetrieves		= 'mqRet'
""" Attribute name for number of MQTT RETRIEVE requests. """
mqttCreates			= 'mqCre'
""" Attribute name for number of MQTT CREATE requests. """
mqttUpdates			= 'mqUpd'
""" Attribute name for number of MQTT UPDATE requests. """
mqttDeletes			= 'mqDel'
""" Attribute name for number of MQTT DELETE requests. """
mqttNotifies		= 'mqNot'
""" Attribute name for number of MQTT NOTIFY requests. """
mqttSendRetrieves	= 'mqSRt'
""" Attribute name for number of MQTT SEND RETRIEVE requests. """
mqttSendCreates		= 'mqSCr'
""" Attribute name for number of MQTT SEND CREATE requests. """
mqttSendUpdates		= 'mqSUp'
""" Attribute name for number of MQTT SEND UPDATE requests. """
mqttSendDeletes		= 'mqSDl'
""" Attribute name for number of MQTT SEND DELETE requests. """
mqttSendNotifies	= 'mqSNo'
""" Attribute name for number of MQTT SEND NOTIFY requests. """
notifications		= 'notif'
""" Attribute name for number of notifications. """
logErrors			= 'lgErr'
""" Attribute name for number of log errors. """
logWarnings			= 'lgWrn'
""" Attribute name for number of log warnings. """
cseStartUpTime		= 'cseSU'
""" Attribute name for CSE startup time. """
cseUpTime			= 'cseUT'
""" Attribute name for CSE uptime. """
resourceCount		= 'ctRes'
""" Attribute name for number of resources in the storage. """

# TODO  restartcount, 

StatsT = Dict[str, Union[str, int, float]]
""" Type for statistics records. """

class Statistics(object):
	"""	Statistics class. Handles all internal statistics.

		Attributes:
			statisticsEnabled:		Flag whether statistics are enabled.
			statLock:				Internal lock for statistic handling.
			stats:					Statistics records
	"""

	__slots__ = (
		'statisticsEnabled',
		'statLock',
		'stats',
	)
	""" Slots of class attributes. """


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
			CSE.event.addHandler(CSE.event.createResource, lambda n, _: self._handleStatsEvent(createdResources)) 	# type: ignore
			CSE.event.addHandler(CSE.event.updateResource, lambda n, _: self._handleStatsEvent(updatedResources))	# type: ignore
			CSE.event.addHandler(CSE.event.deleteResource, lambda n, _: self._handleStatsEvent(deletedResources))	# type: ignore
			CSE.event.addHandler(CSE.event.expireResource, lambda n, _: self._handleStatsEvent(expiredResources))	# type: ignore
			CSE.event.addHandler(CSE.event.httpRetrieve, lambda n: self._handleStatsEvent(httpRetrieves))			# type: ignore
			CSE.event.addHandler(CSE.event.httpCreate, lambda n: self._handleStatsEvent(httpCreates))				# type: ignore
			CSE.event.addHandler(CSE.event.httpUpdate, lambda n: self._handleStatsEvent(httpUpdates))				# type: ignore
			CSE.event.addHandler(CSE.event.httpDelete, lambda n: self._handleStatsEvent(httpDeletes))				# type: ignore
			CSE.event.addHandler(CSE.event.httpNotify, lambda n: self._handleStatsEvent(httpNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.httpSendRetrieve, lambda n: self._handleStatsEvent(httpSendRetrieves))	# type: ignore
			CSE.event.addHandler(CSE.event.httpSendCreate, lambda n: self._handleStatsEvent(httpSendCreates))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendUpdate, lambda n: self._handleStatsEvent(httpSendUpdates))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendDelete, lambda n: self._handleStatsEvent(httpSendDeletes))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendNotify, lambda n: self._handleStatsEvent(httpSendNotifies))	# type: ignore
			CSE.event.addHandler(CSE.event.mqttRetrieve, lambda n: self._handleStatsEvent(mqttRetrieves))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttCreate, lambda n: self._handleStatsEvent(mqttCreates))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttUpdate, lambda n: self._handleStatsEvent(mqttUpdates))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttDelete, lambda n: self._handleStatsEvent(mqttDeletes))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttNotify, lambda n: self._handleStatsEvent(mqttNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendRetrieve, lambda n: self._handleStatsEvent(mqttSendRetrieves))	# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendCreate, lambda n: self._handleStatsEvent(mqttSendCreates))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendUpdate, lambda n: self._handleStatsEvent(mqttSendUpdates))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendDelete, lambda n: self._handleStatsEvent(mqttSendDeletes))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendNotify, lambda n: self._handleStatsEvent(mqttSendNotifies))	# type: ignore
			CSE.event.addHandler(CSE.event.notification, lambda n: self._handleStatsEvent(notifications))			# type: ignore
			CSE.event.addHandler(CSE.event.cseStartup, self.handleCseStartup)									# type: ignore
			CSE.event.addHandler(CSE.event.logError, lambda n: self._handleStatsEvent(logErrors))					# type: ignore
			CSE.event.addHandler(CSE.event.logWarning, lambda n: self._handleStatsEvent(logWarnings))				# type: ignore

			# Also do some internal handling
			CSE.event.addHandler(CSE.event.cseReset, self.restart)												# type: ignore

		L.isInfo and L.log('Statistics initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the statistics service.

			Return:
				True if shutdown was successful, False otherwise.
		"""
		if self.statisticsEnabled:
			# Stop the worker
			L.isInfo and L.log('Stopping statistics DB thread')
			BackgroundWorkerPool.stopWorkers('statsDBWorker')

			# One final write
			self.storeDBStatistics()

		L.isInfo and L.log('Statistics shut down')
		return True
	
	
	def restart(self, name:str) -> None:
		"""	Restart the statistics service.

			Args:
				name:	The name of the event that triggered the restart.
		"""
		self.purgeDBStatistics()
		self.stats = self.setupStats()
		self.handleCseStartup(None)
		L.isDebug and L.logDebug('Statistics restarted')


	def setupStats(self) -> StatsT:
		"""	Setup the statistics dictionary.

			Return:
				The statistics dictionary.
		"""
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
		"""	Return the current statistics.

			Return:
				The statistics dictionary.
		"""
		s = deepcopy(self.stats)

		# Calculate some stats
		# s[cseUpTime] = str(datetime.timedelta(seconds=int(datetime.datetime.now(datetime.timezone.utc).timestamp() - int(s[cseStartUpTime]))))
		s[cseUpTime] = str(datetime.timedelta(seconds=int(utcTime() - int(s[cseStartUpTime]))))
		s[cseStartUpTime] = toISO8601Date(float(s[cseStartUpTime]))
		s[resourceCount] = int(s[createdResources]) - int(s[deletedResources])
		return s


	#########################################################################
	#
	#	Event handlers
	#

	def _handleStatsEvent(self, eventType:str) -> None:
		"""	Generic handling of statist events.

			Args:
				eventType:	The type of event that occurred.
		"""
		try:
			with self.statLock:
				self.stats[eventType] += 1		# type: ignore
		except KeyError:
			# In case there is a version update and a new event was added,
			# the we might just add this event as the first entry
			with self.statLock:
				self.stats[eventType] = 1		# type: ignore


	def handleCseStartup(self, name:str) -> None:
		"""	Assign the CSE's startup time.

			Args:
				name:	The name of the event that triggered function.
		"""
		with self.statLock:
			# self.stats[cseStartUpTime] = datetime.datetime.now(datetime.timezone.utc).timestamp()
			self.stats[cseStartUpTime] = utcTime()


	#########################################################################
	#
	#	Store statistics handling

	# Called by the background worker
	def statisticsDBWorker(self) -> bool:
		"""	Background worker to write statistics to the database.

			Return:
				True if the statistics were written successfully, False otherwise. True continous the worker.
		"""
		# L.isDebug and L.logDebug('Writing statistics DB')
		try:
			self.storeDBStatistics()
		except Exception as e:
			L.logErr(f'Error while writing statistics DB Exception: {str(e)}', exc = e)
			return False
		return True


	def retrieveDBStatistics(self) -> StatsT:
		"""	Retrieve statistics data.

			Return:
				The retrieved statistics dictionary.
		"""
		
		with self.statLock:
			return CSE.storage.getStatistics()


	def storeDBStatistics(self) -> bool:
		"""	Store statistics data.

			Return:
				True if the statistics were stored successfully, False otherwise.
		"""
		with self.statLock:
			return CSE.storage.updateStatistics(self.stats)
	

	def purgeDBStatistics(self) -> None:
		"""	Purge statistics data.
		"""
		with self.statLock:
			CSE.storage.purgeStatistics()

	
	#########################################################################
	#
	#	CSE Structure handling

	def getStructurePuml(self, maxLevel:Optional[int] = 0) -> str:
		"""	This function will generate a PlanUML graph of a CSE's structure, including:
				- The CSE, Type, http, port
				- The CSE's resource tree
				- The Registrar CSE (if any)
				- A list of descendant CSE's (if any)
			
			This function calls itself recursively to generate the tree structure.
			
			Args:
				maxLevel:	The maximum level of the tree to print. 0 means all levels.
			
			Return:
				The PlanUML graph as a string.
		"""

		def getChildren(res:Resource, level:int) -> str:
			""" Find and print the children in the tree structure. """
			result = ''
			if maxLevel > 0 and level == maxLevel:
				return result
			chs = CSE.dispatcher.retrieveDirectChildResources(res.ri)
			for ch in chs:
				result += ' ' * 2 * level + f'|_ {ch.rn} <color:grey>< {ResourceTypes(ch.ty).tpe()} ></color>\n'
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
		cse = getCSE()
		result += f'{cse.rn}\n'
		result += getChildren(cse, 0)
		result += 'end note\n'

		# Build Own
		result += 'http_own - [CSE] : \\t\n'
		result += '}\n' # rectangle

		# Has parent Registrar CSE?
		if CSE.cseType != CSEType.IN and CSE.remote.registrarAddress:
			registrarCSE = CSE.remote.registrarCSE
			bg = 'white' if registrarCSE else 'lightgrey'
			color = 'green' if registrarCSE else 'black'
			address = urlparse(CSE.remote.registrarAddress)
			(ip, port) = tuple(address.netloc.split(':'))
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
			result += f'cloud PARENT as "<color:{color}>{CSE.remote.registrarCSI[1:]}</color> ({registrarType})\\n{CSE.remote.registrarAddress}" #{bg}\n'
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
