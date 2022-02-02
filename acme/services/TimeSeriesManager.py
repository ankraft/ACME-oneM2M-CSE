#
#	TimeSeriesManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Manager for TimeSeries handlings
#
from __future__ import annotations
from dataclasses import dataclass

from ..etc.Types import NotificationEventType as NET, MissingData, LastTSInstance
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..services import CSE as CSE
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..helpers.BackgroundWorker import BackgroundWorkerPool


runningTimeserieses:dict[str, LastTSInstance] = {}	# Holds and maps the active TS and their LastTSInstance objects

class TimeSeriesManager(object):

	def __init__(self) -> None:
		global runningTimeserieses
		runningTimeserieses = {}	# Initialize or clear
		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore
		L.isInfo and L.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeSeriesManager. Stop all the active workers.
		"""
		self.stopMonitoring()
		L.isInfo and L.log('TimeSeriesManager shut down')
		return True

	
	def restart(self) -> None:
		"""	Restart the TimeSeriesManager service.
		"""
		global runningTimeserieses
		self.stopMonitoring()
		runningTimeserieses.clear()
		L.isDebug and L.logDebug('TimeSeriesManager restarted')


	#
	#	Monitor handling
	#

	def stopMonitoring(self) -> None:
		"""	Stop the background worker that monitores the timeSeries ingress. 
		"""
		for tsRi in list(runningTimeserieses.keys()):	# dict changes during processing, therefore make a list out of it
			self.stopMonitoringTimeSeries(tsRi)
	
	
	def timeSeriesMonitor(self, tsRi:str) -> bool:
		"""	This method is called when the expectedDgtRange has passed. It checks whether a TSI is missing by
			looking at the latest arrived dgt.

			`tsRi` - resourceID of the respective <TS> resource. Can be used to retrieve infos from 'runningTimeserieses' dict.
			`runtime` - The timestamp of the runtime of this function for tsRI 
		"""

		# Check TSI arrival for this TS
		if not (rts := runningTimeserieses.get(tsRi)):
			# This might happen when the monitoring has been stoped in between.
			L.logWarn(f'No last <tsi> for <ts>: {tsRi}')
			return False # stop monitoring

		# First handle every possible time window for missingData subscriptions that might have expired
		# during the previous period.
		for (subRi, md) in rts.missingData.items():
			if md.timeWindowEndTimestamp and md.timeWindowEndTimestamp <= rts.missingDataDetectionTime:	# nextRuntime is the time when this monitor is executed
				# Just clear the data structures. The timeWindow might be set again further below
				md.clear()

		if not ((rts.expectedDgt - rts.peid) < rts.dgt <= (rts.expectedDgt + rts.peid)):
			L.isDebug and L.logDebug(f'rts.expectedDgt: {rts.expectedDgt}, rts.peid: {rts.peid}')
			L.isWarn and L.logWarn(f'<tsi> not within expected dataGenerationTimeRange: {rts.expectedDgt - rts.peid} < rts.dgt:{rts.dgt} <= {rts.expectedDgt + rts.peid}')

			# If not, then add the expected arrival time as the dgt to the parent's mdlt list.
			if not (tsRes := CSE.dispatcher.retrieveResource(tsRi).resource):
				L.logErr(f'Cannot retrieve original <ts> resource: {tsRi}', showStackTrace = False)			# might (very rarely) happen when this monitor runs while the <ts> was deleted in another request
				return False	# stop monitoring (actor not restarted)
			tsRes.addDgtToMdlt(rts.expectedDgt)

			# Add the dgt to the missing data of the subscriptions
			for (subRi, md) in rts.missingData.items():
				md.missingDataList.append(DateUtils.toISO8601Date(rts.expectedDgt))
				md.missingDataCurrentNr += 1
				if md.missingDataCurrentNr == 1:	# If it is the first missing data point in this run, then start an actor to react on the end of specified time window
					md.timeWindowEndTimestamp = rts.missingDataDetectionTime + md.missingDataDuration

			# Check for sending the missing data subscriptions in  general
			CSE.notification.checkSubscriptions(None, NET.reportOnGeneratedMissingDataPoints, ri = tsRi, missingData = rts.missingData, now = rts.missingDataDetectionTime)
		else:
			L.isDebug and L.logDebug(f'<tsi> with dgt:{rts.dgt} within expected dataGenerationTimeRange')

		# Prepare for the next DGT
		rts.prepareNextRun()

		# Schedule the next actor runtime
		L.isDebug and L.logDebug(f'Next expected tsRi:{tsRi}, pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt}, missingDataDetectionTime:{rts.missingDataDetectionTime}, expectedDgt:{rts.expectedDgt}')
		rts.actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at = rts.missingDataDetectionTime, name = f'tsMonitor_{tsRi}_{rts.missingDataDetectionTime}')
		rts.actor.start(tsRi = tsRi) 				# Next running is in now+interval

		return True


	#
	#	TS handling
	#

	def updateTimeSeries(self, timeSeries:Resource, instance:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started  when a first TSI is added for a <TS>.
		"""

		arrivedAt = DateUtils.fromAbsRelTimestamp(instance.ct)
		pei  = timeSeries.pei / 1000.0  # ms -> s
		peid = timeSeries.peid / 1000.0 # ms -> s
		mdt  = timeSeries.mdt / 1000.0  # ms -> s
		tsRi = timeSeries.ri
		if (dgt := DateUtils.fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			L.isWarn and L.logWarn(f'Error parsing <tsi>.dgt: {dgt}')
			return
		L.isDebug and L.logDebug(f'New <tsi> for <ts>:{timeSeries.ri} dgt:{dgt}')
		missingDataDetectionTime = dgt + pei + mdt # next runtime of the check

		if not (rts := runningTimeserieses.get(tsRi)) or not rts.running:		# it is a new timeSeries
			actor = None
			if missingDataDetectionTime < arrivedAt:
				# Don't start a monitor if the next runtime for that monitor would be in the past anyway.
				L.isDebug and L.logDebug(f'First <tsi> for this <ts>: {tsRi} but way back in the past. NOT monitoring.')
			
			else:
				# Create and start monitoring worker 
				L.isDebug and L.logDebug(f'First <tsi> for this <ts>: {tsRi} Starting monitoring. Next runtime:{missingDataDetectionTime}')
				actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at = missingDataDetectionTime, name = f'tsMonitor_{tsRi}_{missingDataDetectionTime}').start(tsRi = tsRi)
			
			#	runningTimeserieses structure could have been created earlier (or not), eg. by adding a subscription earlier, but is not running yet
			#	It still needs to be filled
			if not rts:
				runningTimeserieses[tsRi] = (rts := LastTSInstance())
			rts.dgt							= dgt
			rts.arrivedAt					= arrivedAt
			rts.expectedDgt					= dgt + pei		# will be set in the monitor from hereon
			rts.missingDataDetectionTime	= rts.expectedDgt + mdt
			rts.pei							= pei
			rts.mdt							= mdt
			rts.peid 						= peid
			rts.actor 						= actor
			rts.running 					= True

		else:
			if missingDataDetectionTime < arrivedAt:
				# If the next runtime is too way back in the past then we don't start a monitor for that but add THIS TSI's dgt
				timeSeries.addDgtToMdlt(dgt)

			# Add or update runningTimeserieses map.
			rts.dgt = dgt
			rts.arrivedAt = arrivedAt

		L.isDebug and L.logDebug(f'tsRi:{tsRi}, pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt}, missingDataDetectionTime:{rts.missingDataDetectionTime}, dgt:{rts.dgt}, expectedDgt:{rts.expectedDgt}')


	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored. """
		return runningTimeserieses.get(ri) is not None  # if any


	def stopMonitoringTimeSeries(self, tsRi:str) -> bool:
		"""	Remove a timeSeries from monitoring. No other attributes are updated.
		"""
		L.isDebug and L.logDebug(f'Remove <ts> from monitoring: {tsRi}')
		if tsRi in runningTimeserieses:
			lastTsi = runningTimeserieses.pop(tsRi)	# removes it also from the dict
			if lastTsi.actor:
				lastTsi.actor.stop()
		return True


	#
	#	Subscriptions
	#

	def addSubscription(self, timeSeries:Resource, subscription:Resource) -> None:
		"""	Add a subscription for the <TS> resource. Setup the internal structures.
		"""
		if NET.reportOnGeneratedMissingDataPoints in subscription['enc/net']:
			L.isDebug and L.logDebug(f'Adding missing data <sub>: {subscription.ri}')
			tsRi = timeSeries.ri
			if not (rts := runningTimeserieses.get(timeSeries.ri)):
				runningTimeserieses[tsRi] = (rts := LastTSInstance())
			rts.missingData[subscription.ri] = MissingData(	subscriptionRi = subscription.ri, 
															missingDataDuration = DateUtils.fromDuration(subscription['enc/md/dur']),
															missingDataNumber = subscription['enc/md/num'])


	def updateSubscription(self, timeSeries:Resource, subscription:Resource) -> None:
		""" Update an existing missing data subscription.
		"""
		if NET.reportOnGeneratedMissingDataPoints in subscription['enc/net']:
			L.isDebug and L.logDebug(f'Updating missing data <sub>: {subscription.ri}')
			if (rts := runningTimeserieses.get(timeSeries.ri)) and (md := rts.missingData.get(subscription.ri)):
				md.missingDataDuration = DateUtils.fromDuration(subscription['enc/md/dur'])
				md.missingDataNumber = subscription['enc/md/num']


	def removeSubscription(self, timeSeries:Resource, subscription:Resource) -> None:
		"""	Remove a subcription from a <TS> resource. Remove the internal structures.
		"""
		if NET.reportOnGeneratedMissingDataPoints in subscription['enc/net']:
			L.isDebug and L.logDebug(f'Removing missing data <sub>: {subscription.ri}')
			if (rts := runningTimeserieses.get(timeSeries.ri)) and subscription.ri in rts.missingData:
				del rts.missingData[subscription.ri]
