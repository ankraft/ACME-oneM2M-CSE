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
import threading, time, datetime
from threading import Lock

deletedResources	= 'rmRes'
createdresources	= 'crRes'
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

	def __init__(self):
		self.statisticsThread = None
		self.stopStatisticsThread = False
		self.dbWriteIntervall = Configuration.get('cse.statistics.writeIntervall')

		# create lock
		self.statLock = Lock()

		# retrieve or create statitics record
		self.stats = self.setupStats()

		# Start thread to handle writing to DB
		self.startDBHandling()

		# subscripe vto various events
		CSE.event.addHandler(CSE.event.createResource, self.handleCreateEvent)
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent)
		CSE.event.addHandler(CSE.event.httpRetrieve, self.handleHttpRetrieveEvent)
		CSE.event.addHandler(CSE.event.httpCreate, self.handleHttpCreateEvent)
		CSE.event.addHandler(CSE.event.httpUpdate, self.handleHttpUpdateEvent)
		CSE.event.addHandler(CSE.event.httpDelete, self.handleHttpDeleteEvent)
		CSE.event.addHandler(CSE.event.cseStartup, self.handleCseStartup)
		CSE.event.addHandler(CSE.event.logError, self.handleLogError)
		CSE.event.addHandler(CSE.event.logWarning, self.handleLogWarning)

		Logging.log('Statistics initialized')


	def shutdown(self):
		self.stopDBHandling()
		self.storeDBStatistics()
		Logging.log('Statistics shut down')


	def setupStats(self):
		result = self.retrieveDBStatistics()
		if result is not None:
			return result
		return {
			deletedResources	: 0,
			createdresources	: 0,
			httpRetrieves		: 0,
			httpCreates			: 0,
			httpUpdates 		: 0,
			httpDeletes 		: 0,
			cseStartUpTime		: 0.0,
			logErrors 			: 0,
			logWarnings 		: 0
		}

	# Return stats
	def getStats(self):
		s = self.stats.copy()

		# Calculate some stats
		s[cseUpTime] = str(datetime.timedelta(seconds=int(datetime.datetime.utcnow().timestamp() - s[cseStartUpTime])))
		s[cseStartUpTime] = Utils.toISO8601Date(s[cseStartUpTime])
		s[resourceCount] = s[createdresources] - s[deletedResources]
		return s


	#########################################################################
	#
	#	Event handlers
	#

	def handleCreateEvent(self, resource):
		with self.statLock:
			self.stats[createdresources] += 1
	

	def handleDeleteEvent(self, resource):
		with self.statLock:
			self.stats[deletedResources] += 1
	

	def handleHttpRetrieveEvent(self):
		with self.statLock:
			self.stats[httpRetrieves] += 1


	def handleHttpCreateEvent(self):
		with self.statLock:
			self.stats[httpCreates] += 1


	def handleHttpUpdateEvent(self):
		with self.statLock:
			self.stats[httpUpdates] += 1


	def handleHttpDeleteEvent(self):
		with self.statLock:
			self.stats[httpDeletes] += 1


	def handleCseStartup(self):
		with self.statLock:
			self.stats[cseStartUpTime] = datetime.datetime.utcnow().timestamp()


	def handleLogError(self):
		with self.statLock:
			self.stats[logErrors] += 1


	def handleLogWarning(self):
		with self.statLock:
			self.stats[logWarnings] += 1

	#########################################################################
	#
	#	Store statistics handling


	def startDBHandling(self):
		Logging.log('Starting statistics DB thread')
		self.stopStatisticsThread = False
		self.statisticsThread = threading.Thread(target=self.statisticsDBWorker)
		self.statisticsThread.setDaemon(True)	# Make the thread a daemon of the main thread
		self.statisticsThread.start()


	def stopDBHandling(self):
		Logging.log('Stopping statistics DB thread')

		# Stop the thread
		self.stopStatisticsThread = True
		if self.statisticsThread is not None:
			self.statisticsThread.join(self.dbWriteIntervall + 5) # wait a short time for the thread to terminate
			self.statisticsThread = None


	def statisticsDBWorker(self):
		Logging.logDebug('Statistics DB worker thread started')
		while not self.stopStatisticsThread:
			Logging.logDebug('Writing statistics DB')
			self._sleep(self.dbWriteIntervall)
			self.storeDBStatistics()
			try:
				self.storeDBStatistics()
			except Exception as e:
				Logging.logErr('Exception: %s' % e)


	def retrieveDBStatistics(self):
		with self.statLock:
			return CSE.storage.getStatistics()


	def storeDBStatistics(self):
		with self.statLock:
			return CSE.storage.updateStatistics(self.stats)
	

	# self-made sleep. Helps in speed-up shutdown etc
	def _sleep(self, t):
		for i in range(0,t):
			time.sleep(1)
			if self.stopStatisticsThread:
				break
