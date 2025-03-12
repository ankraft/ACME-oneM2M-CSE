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
from ..etc.Constants import RuntimeConstants as RC
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.CSEBase import getCSE
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..runtime.Logging import Logging as L


coRetrieves			= 'coqRet'
""" Attribute name for number of CoAP RETRIEVE requests. """
coCreates			= 'coCre'
""" Attribute name for number of CoAP CREATE requests. """
coUpdates			= 'coUpd'
""" Attribute name for number of CoAP UPDATE requests. """
coDeletes			= 'coDel'
""" Attribute name for number of CoAP DELETE requests. """
coNotifies			= 'coNot'
""" Attribute name for number of CoAP NOTIFY requests. """
coSendRetrieves		= 'coSRt'
""" Attribute name for number of CoAP SEND RETRIEVE requests. """
coSendCreates		= 'coSCr'
""" Attribute name for number of CoAP SEND CREATE requests. """
coSendUpdates		= 'coSUp'
""" Attribute name for number of CoAP SEND UPDATE requests. """
coSendDeletes		= 'coSDl'
""" Attribute name for number of CoAP SEND DELETE requests. """
coSendNotifies		= 'coSNo'
""" Attribute name for number of CoAP SEND NOTIFY requests. """
retrievedResources	= 'rRes'
""" Attribute name for number of retrieved resources in the storage. """
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
wsRetrieves			= 'wsqRet'
""" Attribute name for number of WS RETRIEVE requests. """
wsCreates			= 'wsCre'
""" Attribute name for number of WS CREATE requests. """
wsUpdates			= 'wsUpd'
""" Attribute name for number of WS UPDATE requests. """
wsDeletes			= 'wsDel'
""" Attribute name for number of WS DELETE requests. """
wsNotifies			= 'wsNot'
""" Attribute name for number of WS NOTIFY requests. """
wsSendRetrieves		= 'wsSRt'
""" Attribute name for number of WS SEND RETRIEVE requests. """
wsSendCreates		= 'wsSCr'
""" Attribute name for number of WS SEND CREATE requests. """
wsSendUpdates		= 'wsSUp'
""" Attribute name for number of WS SEND UPDATE requests. """
wsSendDeletes		= 'wsSDl'
""" Attribute name for number of WS SEND DELETE requests. """
wsSendNotifies		= 'wsSNo'
""" Attribute name for number of WS SEND NOTIFY requests. """
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
			statLock:				Internal lock for statistic handling.
			stats:					Statistics records
	"""

	__slots__ = (
		'statLock',
		'stats',
	)
	""" Slots of class attributes. """


	def __init__(self) -> None:

		# create lock
		self.statLock = Lock()

		# retrieve or create statistics record, even when statistics are disabled
		self.stats = self.setupStats()

		if Configuration.cse_statistics_enable:

			# Start background worker to handle writing to DB
			L.isInfo and L.log('Starting statistics DB thread')
			BackgroundWorkerPool.newWorker(Configuration.cse_statistics_writeInterval, self.statisticsDBWorker, 'statsDBWorker').start()

			# subscripe vto various events
			# mypy cannot handle dynamically created attributes
			CSE.event.addHandler(CSE.event.retrieveResource, lambda n, _: self._handleStatsEvent(retrievedResources))	# type: ignore
			CSE.event.addHandler(CSE.event.createResource, lambda n, _: self._handleStatsEvent(createdResources)) 		# type: ignore
			CSE.event.addHandler(CSE.event.updateResource, lambda n, _: self._handleStatsEvent(updatedResources))		# type: ignore
			CSE.event.addHandler(CSE.event.deleteResource, lambda n, _: self._handleStatsEvent(deletedResources))		# type: ignore
			CSE.event.addHandler(CSE.event.expireResource, lambda n, _: self._handleStatsEvent(expiredResources))		# type: ignore
			CSE.event.addHandler(CSE.event.coapRetrieve, lambda n: self._handleStatsEvent(coRetrieves))					# type: ignore
			CSE.event.addHandler(CSE.event.coapCreate, lambda n: self._handleStatsEvent(coCreates))						# type: ignore
			CSE.event.addHandler(CSE.event.coapUpdate, lambda n: self._handleStatsEvent(coUpdates))						# type: ignore
			CSE.event.addHandler(CSE.event.coapDelete, lambda n: self._handleStatsEvent(coDeletes))						# type: ignore
			CSE.event.addHandler(CSE.event.coapNotify, lambda n: self._handleStatsEvent(coNotifies))					# type: ignore
			CSE.event.addHandler(CSE.event.coapSendRetrieve, lambda n: self._handleStatsEvent(coSendRetrieves))			# type: ignore
			CSE.event.addHandler(CSE.event.coapSendCreate, lambda n: self._handleStatsEvent(coSendCreates))				# type: ignore
			CSE.event.addHandler(CSE.event.coapSendUpdate, lambda n: self._handleStatsEvent(coSendUpdates))				# type: ignore
			CSE.event.addHandler(CSE.event.coapSendDelete, lambda n: self._handleStatsEvent(coSendDeletes))				# type: ignore
			CSE.event.addHandler(CSE.event.coapSendNotify, lambda n: self._handleStatsEvent(coSendNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.httpRetrieve, lambda n: self._handleStatsEvent(httpRetrieves))				# type: ignore
			CSE.event.addHandler(CSE.event.httpCreate, lambda n: self._handleStatsEvent(httpCreates))					# type: ignore
			CSE.event.addHandler(CSE.event.httpUpdate, lambda n: self._handleStatsEvent(httpUpdates))					# type: ignore
			CSE.event.addHandler(CSE.event.httpDelete, lambda n: self._handleStatsEvent(httpDeletes))					# type: ignore
			CSE.event.addHandler(CSE.event.httpNotify, lambda n: self._handleStatsEvent(httpNotifies))					# type: ignore
			CSE.event.addHandler(CSE.event.httpSendRetrieve, lambda n: self._handleStatsEvent(httpSendRetrieves))		# type: ignore
			CSE.event.addHandler(CSE.event.httpSendCreate, lambda n: self._handleStatsEvent(httpSendCreates))			# type: ignore
			CSE.event.addHandler(CSE.event.httpSendUpdate, lambda n: self._handleStatsEvent(httpSendUpdates))			# type: ignore
			CSE.event.addHandler(CSE.event.httpSendDelete, lambda n: self._handleStatsEvent(httpSendDeletes))			# type: ignore
			CSE.event.addHandler(CSE.event.httpSendNotify, lambda n: self._handleStatsEvent(httpSendNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttRetrieve, lambda n: self._handleStatsEvent(mqttRetrieves))				# type: ignore
			CSE.event.addHandler(CSE.event.mqttCreate, lambda n: self._handleStatsEvent(mqttCreates))					# type: ignore
			CSE.event.addHandler(CSE.event.mqttUpdate, lambda n: self._handleStatsEvent(mqttUpdates))					# type: ignore
			CSE.event.addHandler(CSE.event.mqttDelete, lambda n: self._handleStatsEvent(mqttDeletes))					# type: ignore
			CSE.event.addHandler(CSE.event.mqttNotify, lambda n: self._handleStatsEvent(mqttNotifies))					# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendRetrieve, lambda n: self._handleStatsEvent(mqttSendRetrieves))		# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendCreate, lambda n: self._handleStatsEvent(mqttSendCreates))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendUpdate, lambda n: self._handleStatsEvent(mqttSendUpdates))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendDelete, lambda n: self._handleStatsEvent(mqttSendDeletes))			# type: ignore
			CSE.event.addHandler(CSE.event.mqttSendNotify, lambda n: self._handleStatsEvent(mqttSendNotifies))			# type: ignore
			CSE.event.addHandler(CSE.event.wsRetrieve, lambda n: self._handleStatsEvent(wsRetrieves))					# type: ignore
			CSE.event.addHandler(CSE.event.wsCreate, lambda n: self._handleStatsEvent(wsCreates))						# type: ignore
			CSE.event.addHandler(CSE.event.wsUpdate, lambda n: self._handleStatsEvent(wsUpdates))						# type: ignore
			CSE.event.addHandler(CSE.event.wsDelete, lambda n: self._handleStatsEvent(wsDeletes))						# type: ignore
			CSE.event.addHandler(CSE.event.wsNotify, lambda n: self._handleStatsEvent(wsNotifies))						# type: ignore
			CSE.event.addHandler(CSE.event.wsSendRetrieve, lambda n: self._handleStatsEvent(wsSendRetrieves))			# type: ignore
			CSE.event.addHandler(CSE.event.wsSendCreate, lambda n: self._handleStatsEvent(wsSendCreates))				# type: ignore
			CSE.event.addHandler(CSE.event.wsSendUpdate, lambda n: self._handleStatsEvent(wsSendUpdates))				# type: ignore
			CSE.event.addHandler(CSE.event.wsSendDelete, lambda n: self._handleStatsEvent(wsSendDeletes))				# type: ignore
			CSE.event.addHandler(CSE.event.wsSendNotify, lambda n: self._handleStatsEvent(wsSendNotifies))				# type: ignore
			CSE.event.addHandler(CSE.event.notification, lambda n: self._handleStatsEvent(notifications))				# type: ignore
			CSE.event.addHandler(CSE.event.cseStartup, self.handleCseStartup)											# type: ignore
			CSE.event.addHandler(CSE.event.logError, lambda n: self._handleStatsEvent(logErrors))						# type: ignore
			CSE.event.addHandler(CSE.event.logWarning, lambda n: self._handleStatsEvent(logWarnings))					# type: ignore

			# Also do some internal handling
			CSE.event.addHandler(CSE.event.cseReset, self.restart)														# type: ignore

		L.isInfo and L.log('Statistics initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the statistics service.

			Return:
				True if shutdown was successful, False otherwise.
		"""
		if Configuration.cse_statistics_enable:
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
			coRetrieves			: 0,
			coCreates			: 0,
			coUpdates 			: 0,
			coDeletes 			: 0,
			coNotifies 			: 0,
			coSendRetrieves		: 0,
			coSendCreates		: 0,
			coSendUpdates 		: 0,
			coSendDeletes 		: 0,
			coSendNotifies 		: 0,
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
			wsRetrieves			: 0,
			wsCreates			: 0,
			wsUpdates 			: 0,
			wsDeletes 			: 0,
			wsNotifies 			: 0,
			wsSendRetrieves		: 0,
			wsSendCreates		: 0,
			wsSendUpdates 		: 0,
			wsSendDeletes 		: 0,
			wsSendNotifies 		: 0,
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
				result += ' ' * 2 * level + f'|_ {ch.rn} <color:grey>< {ResourceTypes(ch.ty).typeShortname()} ></color>\n'
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
skinparam linetype ortho
"""

		# Own CSE node & http interface
		result += 'rectangle << CSE >> {\n'
		address = urlparse(Configuration.http_address)
		(ip, _) = tuple(address.netloc.split(':'))
		result += f'node CSE as "<color:green>{RC.cseCsi[1:]}</color> ({RC.cseType.name})\\n{ip}" #white\n'

		# Own http interface
		http = 'https' if Configuration.http_security_useTLS else 'http'
		result += f'interface "{http}\\n{Configuration.http_port}" as http_own #white\n'

		# MQTT broker connection
		if Configuration.mqtt_enable:
			mqtt = 'mqtts' if Configuration.mqtt_security_useTLS else 'mqtt'
			result += f'interface "{mqtt}\\n{mqtt}://{Configuration.mqtt_address}:{Configuration.mqtt_port}" as mqtt_own #white\n'
		
		# Own CoAP interface
		if Configuration.coap_enable:
			result += f'interface "coap\\n{Configuration.coap_port}" as coap_own #white\n'

		# Own WS interface
		if Configuration.websocket_enable:
			ws = 'wss' if Configuration.websocket_security_useTLS else 'ws'
			result += f'interface "{ws}\\n{Configuration.websocket_port}" as ws_own #white\n'

		# Build Resource Tree
		result += 'note left of CSE\n'
		result += '**Resource Tree**\n\n'
		cse = getCSE()
		result += f'{cse.rn}\n'
		result += getChildren(cse, 0)
		result += 'end note\n'

		# Build Own
		result += 'http_own -[norank]- [CSE] #lightblue\n'
		if Configuration.mqtt_enable:
			result += 'mqtt_own -[norank]- [CSE] #lightblue\n'
		if Configuration.coap_enable:
			result += 'coap_own -[norank]- [CSE] #lightblue\n'
		if Configuration.websocket_enable:
			result += 'ws_own -[norank]- [CSE] #lightblue\n'
		result += '}\n' # rectangle

		# Has parent Registrar CSE?
		if RC.cseType != CSEType.IN and Configuration.cse_registrar_address:
			registrarCSE = CSE.remote.registrarCSE
			bg = 'white' if registrarCSE else 'lightgrey'
			color = 'green' if registrarCSE else 'black'
			address = urlparse(Configuration.cse_registrar_address)
			(ip, port) = tuple(address.netloc.split(':'))
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
			result += f'cloud PARENT as "<color:{color}>{Configuration.cse_registrar_cseID[1:]}</color> ({registrarType})\\n{Configuration.cse_registrar_address}" #{bg}\n'
			result += 'CSE -UP- PARENT\n'

		
		# Has CSE descendants?
		if RC.cseType != CSEType.ASN:
			cnt = 0
			connections = {}
			for desc in CSE.remote.descendantCSR.keys():
				csi = desc[1:]
				(csr, atCsi) = CSE.remote.descendantCSR[desc]
				poa = f'\\n{csr.poa}' if csr else ''
				typeShortname = f' ({CSEType(csr.cst).name})' if csr and csr.cst else ''
				shape = 'node' if csr else 'rectangle'
				result += f'{shape} d{cnt} as "<color:green>{csi}</color>{typeShortname}{poa}" #white\n'
				connections[desc] = (cnt, atCsi)
				cnt += 1
			
			for key in connections.keys():
				connection = connections[key]
				nodeNr = connection[0]
				atCsi = connection[1]
				if atCsi == RC.cseCsi:
					result += f'd{nodeNr} -UP- CSE\n'
				else:
					if atCsi in connections:
						subcon = connections[atCsi]
						result += f'd{connection[0]} -UP- d{subcon[0]}\n'

		# end
		result += '@enduml'
		return result

