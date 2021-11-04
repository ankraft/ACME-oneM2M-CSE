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
		L.isInfo and L.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeSeriesManager. Stop all the active workers.
		"""
		self.stopMonitoring()
		L.isInfo and L.log('TimeSeriesManager shut down')
		return True

	#
	#	Monitor handling
	#

	def stopMonitoring(self) -> None:
		"""	Stop the background worker that monitores the timeSeries ingress. 
		"""
		for tsRi in list(runningTimeserieses.keys()):	# dict changes during processing, therefore make a list out of it
			self.stopMonitoringTimeSeries(tsRi)
	
	
	def timeSeriesMonitor(self, tsRi:str) -> bool:
		"""	This method is called when the period + mdt has passed. It checks whether a TSI is missing by
			looking at the latest arrived dgt.

			`tsRi` - resourceID of the respective <TS> resource. Can be used to retrieve infos from 'runningTimeserieses' dict.
			`runtime` - The timestamp of the runtime of this function for tsRI 
		"""

		# Check TSI arrival for this TS
		if not (rts := runningTimeserieses.get(tsRi)):
			# This might happen when the monitoring has been stopped in between.
			L.logWarn(f'No last <tsi> for <ts>: {tsRi}')
			return False # stop monitoring

		# First handle every possible time window for missingData subscriptions that might have expired
		# during the previous period.
		for (subRi, md) in rts.missingData.items():
			if md.timeWindowEndTimestamp and md.timeWindowEndTimestamp <= rts.nextRuntime:	# nextRuntime is the time when this monitor is executed
				# Just clear the data structures. The timeWindow might be set again further below
				md.clear()
		
		ontime = rts.nextRuntime-rts.mdt	# Expected (minimum) timestamp of the last <TSI>.

		# Check if there was a <TSI> in the expected time frame (between ontime and now)
		# Also check if the <TSI>'s dgt is between ontime-delta and onetime+delta
		L.isDebug and L.logDebug(f'<tsi> monitor runTime:{rts.nextRuntime} onTime:{ontime} pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt} tsiArrivedAt:{rts.tsiArrivedAt}, nextExpectedDGT:{rts.nextExpectedDgt} lastSeenDGT:{rts.lastSeenDgt}')
		if not ( (ontime <= rts.tsiArrivedAt <= rts.nextRuntime) and (ontime-rts.peid <= rts.lastSeenDgt <= ontime+rts.peid) ):
			L.isWarn and L.logWarn(f'No <tsi> within time period or DGT outside peid: ontime:{ontime} <= rts.tsiArrivedAt:{rts.tsiArrivedAt} <= rts.nextRuntime:{rts.nextRuntime} and ontime-rts.peid:{ontime-rts.peid} <= rts.lastSeenDgt:{rts.lastSeenDgt} <= ontime+rts.peid:{ontime+rts.peid}')
			
			# If not, then add the expected arrival time as the dgt to the parent's mdlt list.
			if not (tsRes := CSE.dispatcher.retrieveResource(tsRi).resource):
				L.logErr(f'Cannot retrieve original <ts> resource: {tsRi}', showStackTrace=False)			# might (very rarely) happen when this monitor runs while the <ts> was deleted in another request
				return False	# stop monitoring (actor not restarted)
			tsRes.addDgtToMdlt(rts.nextExpectedDgt)

			# Add the dgt to the missing data of the subscriptions
			for (subRi, md) in rts.missingData.items():
				md.missingDataList.append(DateUtils.toISO8601Date(rts.nextExpectedDgt))
				md.missingDataCurrentNr += 1
				if md.missingDataCurrentNr == 1:	# If it is the first missing data point in this run, then start an actor to react on the end of specified time window
					md.timeWindowEndTimestamp = rts.nextRuntime + md.missingDataDuration

			# Check for sending the missing data subscriptions in  general
			CSE.notification.checkSubscriptions(None, NET.reportOnGeneratedMissingDataPoints, ri=tsRi, missingData=rts.missingData, now=rts.nextRuntime)

		rts.nextExpectedDgt += rts.pei									# Set the next expected DGT. Will be overwritten when a real one arrives
		rts.nextRuntime += rts.pei

		# Schedule the next actor runtime
		L.isDebug and L.logDebug(f'tsRi:{tsRi}, pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt}, nextRuntime:{rts.nextRuntime}, nextExpectedDgt:{rts.nextExpectedDgt}')
		rts.actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=rts.nextRuntime, name=f'tsMonitor_{tsRi}_{rts.nextRuntime}')
		rts.actor.start(tsRi=tsRi) 				# Next running is in now+interval

		return True


	#
	#	TS handling
	#

	def updateTimeSeries(self, timeSeries:Resource, instance:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started only when a first TSI is added for a <TS>.
		"""

		now  = DateUtils.utcTime()
		pei  = timeSeries.pei / 1000.0  # ms -> s
		peid = timeSeries.peid / 1000.0 # ms -> s
		mdt  = timeSeries.mdt / 1000.0  # ms -> s
		tsRi = timeSeries.ri
		if (dgt := DateUtils.fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			L.isWarn and L.logWarn(f'Error parsing <tsi>.dgt: {dgt}')
			return
		L.isDebug and L.logDebug(f'New <tsi> for <ts>:{timeSeries.ri} dgt:{dgt}')
		runtime = dgt+pei+mdt

		if not (rts := runningTimeserieses.get(tsRi)) or not rts.running:		# is new timeSeries
			if runtime < now:
				# Don't start a monitor if the next runtime for that monitor would be in the past anyway.
				L.isDebug and L.logDebug(f'First <tsi> for this <ts>: {tsRi} but way back in the past. NO monitoring.')
			
			else:
				L.isDebug and L.logDebug(f'First <tsi> for this <ts>: {tsRi} Starting monitoring. Next runtime:{runtime}')
				actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=runtime, name=f'tsMonitor_{tsRi}_{runtime}')
				actor.start(tsRi=tsRi)
			
			#	rts could have been created earlier (or not), eg. by adding a subscription earlier, but is not running yet
			#	It still needs to be filled
			if not rts:
				runningTimeserieses[tsRi] = (rts := LastTSInstance())
			rts.lastSeenDgt		= dgt
			rts.tsiArrivedAt	= now
			rts.nextExpectedDgt	= dgt+pei
			rts.nextRuntime		= runtime
			rts.pei				= pei
			rts.mdt				= mdt
			rts.peid 			= peid
			rts.actor 			= actor
			rts.running 		= True

		else:
			if runtime < now:
				# If the next runtime is too way back in the past then we don't start a monitor for that but add THIS TSI's dgt
				timeSeries.addDgtToMdlt(dgt)

			# Add or update runningTimeserieses map.
			rts.lastSeenDgt  = dgt
			rts.tsiArrivedAt = now

		L.isDebug and L.logDebug(f'tsRi:{tsRi}, pei:{rts.pei}, mdt:{rts.mdt}, runtime:{rts.nextRuntime}, lastSeenDgt:{rts.lastSeenDgt}, nextExpectedDgt:{rts.nextExpectedDgt}')


	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored. """
		return runningTimeserieses.get(ri) is not None  # if any


	def stopMonitoringTimeSeries(self, tsRi:str) -> bool:
		"""	Remove a timeSeries from monitoring.
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
			rts.missingData[subscription.ri] = MissingData(	subscriptionRi=subscription.ri, 
															missingDataDuration=DateUtils.fromDuration(subscription['enc/md/dur']),
															missingDataNumber=subscription['enc/md/num'])


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
