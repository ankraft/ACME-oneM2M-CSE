#
#	TimeSeriesManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Manager for TimeSeries handlings
#
from __future__ import annotations
import time
from Logging import Logging
import CSE, Utils
from Configuration import Configuration
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool


class TimeSeriesManager(object):

	def __init__(self) -> None:
		self.startMonitoring()
		Logging.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		self.stopMonitoring()
		Logging.log('TimeSeriesManager shut down')
		return True


	def startMonitoring(self) -> None:
		"""	Start a background worker to monitor the timeSeries ingress. 
		"""
		if (interval := Configuration.get('cse.checkTimeSeriesInterval')) > 0:
			BackgroundWorkerPool.newWorker(interval, self.timeSeriesMonitor, 'timeSeriesMonitor').start()


	def stopMonitoring(self) -> None:
		"""	Stop the background worker that monitores the timeSeries ingress. 
		"""
		BackgroundWorkerPool.stopWorkers('timeSeriesMonitor')


	def timeSeriesMonitor(self) -> bool:
		"""	Callback for the monitor. Checking regularly whether there are timeSeries instances
			after a period, and where the ingress period has expired.
		"""
		Logging.logDebug('Looking for missing timeSeriesInstances')
		if len(ets := CSE.storage.getPastPeriodTimeSeries()) == 0:		# Nothing to process
			return True

		time_ = time.time()
		for ts in ets:
			#Logging.log(f'time: {time_}, mdt: {ts["mdt"]}')
			if time_ > (mdt := ts['mdt']):
				ri = ts['ri']
				Logging.log(f'MissingDataDetectTimer reached for TS: {ri}')

				# Add the current mdt timestamp to the mdlt list of the original TS resource
				if (tsRes := CSE.dispatcher.retrieveResource(ri).resource) is None:
					Logging.logErr(f'Cannot retrieve original TS resource: {ri}')
					continue
				tsRes.mdlt.append(Utils.toISO8601Date(mdt))	# Add missing dataGenerationTime to TS.missingDataList
				if (tsMdn := tsRes.mdn) is not None:		# mdn may not be set. Then this list grows forever
					if len(tsRes.mdlt) > tsMdn:				# If missingDataList is bigger then missingDataMaxNr allows
						tsRes['mdlt'] = tsRes.mdlt[1:]		# Reduce the missingDataList
					tsRes['mdc'] = len(tsRes.mdlt)			# set the missingDataCurrentNr
					tsRes.dbUpdate()						# Update in DB
				
				# TODO handle subscription stuff

				# This ts info has been handled.
				# Set a new missingDataDetectTime. now + the TS's mdt
				ts['mdt'] = time_ + (tsRes.mdt / 1000)	

			# Update ts info to the next period timeSeries timestamp
			ts['pt'] += ts['pei']
			CSE.storage.updateTimeSeries(ts)
		return True


	def updateTimeSeries(self, timeSeries:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started only when a first TSI is added.
		"""
		Logging.logDebug(f'New TSI for TS: {timeSeries.ri}')
		pei = timeSeries.pei / 1000 # ms
		mdt = timeSeries.mdt / 1000 # ms
		time_ = time.time()
		if ( l:= len(lst := CSE.storage.getTimeSeries(tsri := timeSeries.ri))) == 0:	# new timeSeries
			CSE.storage.addTimeSeries(timeSeries.ri, periodicInterval=pei, periodTime=time_ + pei, missingDataTime=time_ + mdt)
		elif l > 1:
			Logging.logErr(f'Multiple DB entries for TSI: {tsri}')
		else:
			tse = lst[0]					# the only one
			tse['pt']  = time_ + pei		# next period = now + TS.pei
			tse['mdt'] = time_ + mdt		# missingDataTime = now + TS.missingDataTime
			CSE.storage.updateTimeSeries(tse)	


	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored. """
		return len(CSE.storage.getTimeSeries(ri)) == 1


	def stopMonitoringTimeSeries(self, timeSeries:Resource) -> bool:
		"""	Remove a timeSeries from monitoring.
		"""
		Logging.logDebug(f'Remove timeSeries from monitoring: {timeSeries.ri}')
		return CSE.storage.removeTimeSeries(timeSeries.ri)


