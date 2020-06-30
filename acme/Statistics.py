#
#	Statistics.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Statistics Module
#

from Logging import Logging
from Configuration import Configuration
import CSE, Utils
import datetime
from threading import Lock
from helpers import BackgroundWorker
from resources.Resource import Resource



deletedResources	= 'rmRes'
createdResources	= 'crRes'
updatedResources	= 'upRes'
httpRetrieves		= 'htRet'
httpCreates			= 'htCre'
httpUpdates			= 'htUpd'
httpDeletes			= 'htDel'
logErrors			= 'lgErr'
logWarnings			= 'lgWrn'
cseStartUpTime		= 'cseSU'
cseUpTime			= 'cseUT'
resourceCount		= 'ctRes'

# TODO startup, uptime, restartcount, errors, warnings


class Statistics(object):

	def __init__(self) -> None:
		# create lock
		self.statLock = Lock()

		# retrieve or create statitics record
		self.stats = self.setupStats()

		# Start background worker to handle writing to DB
		Logging.log('Starting statistics DB thread')
		self.worker = BackgroundWorker.BackgroundWorker(Configuration.get('cse.statistics.writeIntervall'), self.statisticsDBWorker, 'statisticsDBWorker')
		self.worker.start()

		# subscripe vto various events
		# mypy cannot handle dynamically created attributes
		CSE.event.addHandler(CSE.event.createResource, self.handleCreateEvent) 		# type: ignore
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent)		# type: ignore
		CSE.event.addHandler(CSE.event.httpRetrieve, self.handleHttpRetrieveEvent)	# type: ignore
		CSE.event.addHandler(CSE.event.httpCreate, self.handleHttpCreateEvent)		# type: ignore
		CSE.event.addHandler(CSE.event.httpUpdate, self.handleHttpUpdateEvent)		# type: ignore
		CSE.event.addHandler(CSE.event.httpDelete, self.handleHttpDeleteEvent)		# type: ignore
		CSE.event.addHandler(CSE.event.cseStartup, self.handleCseStartup)			# type: ignore
		CSE.event.addHandler(CSE.event.logError, self.handleLogError)				# type: ignore
		CSE.event.addHandler(CSE.event.logWarning, self.handleLogWarning)			# type: ignore

		Logging.log('Statistics initialized')


	def shutdown(self) -> None:
		# Stop the worker
		Logging.log('Stopping statistics DB thread')
		self.worker.stop()

		# One final write
		self.storeDBStatistics()
		Logging.log('Statistics shut down')


	def setupStats(self) -> dict:
		result = self.retrieveDBStatistics()
		if result is not None:
			return result
		return {
			deletedResources	: 0,
			createdResources	: 0,
			updatedResources	: 0,
			httpRetrieves		: 0,
			httpCreates			: 0,
			httpUpdates 		: 0,
			httpDeletes 		: 0,
			cseStartUpTime		: 0.0,
			logErrors 			: 0,
			logWarnings 		: 0
		}

	# Return stats
	def getStats(self) -> dict:
		s = self.stats.copy()

		# Calculate some stats
		s[cseUpTime] = str(datetime.timedelta(seconds=int(datetime.datetime.utcnow().timestamp() - s[cseStartUpTime])))
		s[cseStartUpTime] = Utils.toISO8601Date(s[cseStartUpTime])
		s[resourceCount] = s[createdResources] - s[deletedResources]
		return s


	#########################################################################
	#
	#	Event handlers
	#

	def handleCreateEvent(self, resource: Resource) -> None:
		with self.statLock:
			self.stats[createdResources] += 1
	

	def handleDeleteEvent(self, resource: Resource) -> None:
		with self.statLock:
			self.stats[deletedResources] += 1
	
	def handleUpdateEvent(self, resource: Resource) -> None:
		with self.statLock:
			self.stats[updatedResources] += 1

	def handleHttpRetrieveEvent(self) -> None:
		with self.statLock:
			self.stats[httpRetrieves] += 1


	def handleHttpCreateEvent(self) -> None:
		with self.statLock:
			self.stats[httpCreates] += 1


	def handleHttpUpdateEvent(self) -> None:
		with self.statLock:
			self.stats[httpUpdates] += 1


	def handleHttpDeleteEvent(self) -> None:
		with self.statLock:
			self.stats[httpDeletes] += 1


	def handleCseStartup(self) -> None:
		with self.statLock:
			self.stats[cseStartUpTime] = datetime.datetime.utcnow().timestamp()


	def handleLogError(self) -> None:
		with self.statLock:
			self.stats[logErrors] += 1


	def handleLogWarning(self) -> None:
		with self.statLock:
			self.stats[logWarnings] += 1

	#########################################################################
	#
	#	Store statistics handling

	# Called by the background worker
	def statisticsDBWorker(self) -> bool:
		Logging.logDebug('Writing statistics DB')
		try:
			self.storeDBStatistics()
		except Exception as e:
			Logging.logErr('Exception: %s' % e)
			return False
		return True


	def retrieveDBStatistics(self) -> dict:
		with self.statLock:
			return CSE.storage.getStatistics()


	def storeDBStatistics(self) -> bool:
		with self.statLock:
			return CSE.storage.updateStatistics(self.stats)
	