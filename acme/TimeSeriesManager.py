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
		self.workerName 				= 'timeSeriesMonitor'
		self.currentMonitoringInterval 	= 0.0

		# Check monitoring after a CSE restart
		self.setMonitorInterval(CSE.storage.getTimeSeriesShortestMdt())

		Logging.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		self.stopMonitoring()
		Logging.log('TimeSeriesManager shut down')
		return True


	def startMonitoring(self, interval:float) -> None:
		"""	Start a background worker to monitor the timeSeries ingress. 
		"""
		if len(BackgroundWorkerPool.findWorkers(self.workerName)) > 0:	# Stop existing workers
			self.stopMonitoring()
		if interval > 0.0:
			BackgroundWorkerPool.newWorker(interval, self.timeSeriesMonitor, self.workerName).start()
			self.currentMonitoringInterval = interval


	def stopMonitoring(self) -> None:
		"""	Stop the background worker that monitores the timeSeries ingress. 
		"""
		BackgroundWorkerPool.stopWorkers(self.workerName)
		self.currentMonitoringInterval = 0.0
	
	
	def setMonitorInterval(self, mdt:float) -> None:
		"""	Set the monitoring interval according the given `mdt` (missingDataTime) value.

			This value will be divided by 2 to follow the Nyquist–Shannon sampling theorem.

			A value of 0.0 ends monitoring alltogether.
		"""
		interval = mdt / 2.0	# see Nyquist–Shannon sampling theorem...
		if interval == self.currentMonitoringInterval:
			return
		if interval == 0.0:
			Logging().logDebug('Stop TS monitoring')
			self.stopMonitoring()
			return
		Logging().logDebug(f'(Re)Start TS monitoring with interval: {interval}s')
		self.startMonitoring(interval)	# implicit stop


	def _addToMdlt(self, tsRes:Resource, dgt:str) -> None:
		tsRes.mdlt.append(Utils.toISO8601Date(dgt))	# Add missing dataGenerationTime to TS.missingDataList
		if (tsMdn := tsRes.mdn) is not None:		# mdn may not be set. Then this list grows forever
			if len(tsRes.mdlt) > tsMdn:				# If missingDataList is bigger then missingDataMaxNr allows
				tsRes['mdlt'] = tsRes.mdlt[1:]		# Reduce the missingDataList
			tsRes['mdc'] = len(tsRes.mdlt)			# set the missingDataCurrentNr
			tsRes.dbUpdate()						# Update in DB


	def timeSeriesMonitor(self) -> bool:
		"""	Callback for the monitor. Checking regularly whether there are timeSeries instances
			after a period, and where the ingress period has expired.
		"""
		Logging.logDebug('Looking for missing timeSeriesInstances')
		if len(ets := CSE.storage.getPastPeriodTimeSeries()) == 0:		# Nothing to process
			return True

		for ts in ets:
			ri  = ts['ri']
			Logging.logDebug(f'Period and missingDataTime expired for TS: {ri}')

			# Add the assumed mdt timestamp to the mdlt list of the original TS resource
			if (tsRes := CSE.dispatcher.retrieveResource(ri).resource) is None:
				Logging.logErr(f'Cannot retrieve original TS resource: {ri}')
				continue
			
			dgt = ts['ndgt']	# expected dgt
			# #Logging.logDebug(f'Expected DGT: {dgt}')
			pei = ts['pei']		# periodic interval

			self._addToMdlt(tsRes, dgt)

			# TODO handle subscription stuff

			# This ts info has been handled.
			ts['npei'] = (npei := ts['npei'] + pei)	# Next periodTime timestamp
			ts['nmdt'] = npei + (tsRes.mdt / 1000)	# Next mdt timestamp :  pt + mdt . mdt might change in the TS resource
			ts['ndgt'] = dgt + pei					# Next expected dgt timestamp: old dgt + pei
			CSE.storage.updateTimeSeries(ts)
		return True


	def updateTimeSeries(self, timeSeries:Resource, instance:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started only when a first TSI is added for a TS.
		"""
		Logging.logDebug(f'New TSI for TS: {timeSeries.ri}')
		pei = timeSeries.pei / 1000.0 # ms -> s
		mdt = timeSeries.mdt / 1000.0 # ms -> s
		if (dgt := Utils.fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			Logging.logWarn(f'Error parsing TSI.dgt: {dgt}')
			return
		isNewTS = False
		time_ 	= Utils.utcTime()
		if ( l:= len(lst := CSE.storage.getTimeSeries(tsri := timeSeries.ri))) == 0:	# new timeSeries
			Logging.logDebug(f'Start monitoring TSI: {timeSeries.ri}')
			CSE.storage.addTimeSeries(	timeSeries.ri, 
										periodicInterval=pei,
										missingDataTime=mdt,
										nextPeriodTime=time_ + pei, 
										nextMissingDataTime=time_ + pei + mdt,
										nextDgt=dgt+pei)
			isNewTS = True
		elif l > 1:
			Logging.logErr(f'Multiple DB entries for TSI: {tsri}')
		else:
			tse = lst[0]					# the only one
			tse['npei'] = time_ + pei		# next period = now + TS.pei
			tse['nmdt'] = time_ + pei + mdt	# next missingDataTime = now + TS.pei + TS.mdt
			CSE.storage.updateTimeSeries(tse)

			# TODO Check whether dgt is in periodic interval delta
			# TODO Bob: but expected DGT or dgt from TSI in mdlt?
			# TODO don't put DGT twince in mdlt



		# Only need to recalculate and set a new monitoring interval when a TS starts to receive TSI
		# Or when TS.mdt was changed, but then monitoring was stopped, so this is regarded as a new monitoring anyway
		if isNewTS:
			self.setMonitorInterval(CSE.storage.getTimeSeriesShortestMdt())



	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored. """
		return len(CSE.storage.getTimeSeries(ri)) == 1


	def stopMonitoringTimeSeries(self, timeSeries:Resource) -> bool:
		"""	Remove a timeSeries from monitoring.
		"""
		Logging.logDebug(f'Remove TS from monitoring: {timeSeries.ri}')
		result = CSE.storage.removeTimeSeries(timeSeries.ri)
		# re-calculate and set the monitoring interval
		if self.currentMonitoringInterval > 0.0:	# Only need to stop when monitoring
			self.setMonitorInterval(CSE.storage.getTimeSeriesShortestMdt())
		return result

