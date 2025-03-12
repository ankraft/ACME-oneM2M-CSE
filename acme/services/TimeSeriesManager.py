#
#	TimeSeriesManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Manager for TimeSeries handlings"""

from __future__ import annotations

from ..etc.Types import NotificationEventType, MissingData, LastTSInstance, ResourceTypes
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.DateUtils import toISO8601Date, fromAbsRelTimestamp, fromDuration
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..runtime.Logging import Logging as L


runningTimeserieses:dict[str, LastTSInstance] = {}	# Holds and maps the active TS and their LastTSInstance objects
"""	Active TimeSeries instances. Maps the resourceID of the <TS> resource to the LastTSInstance object. """

class TimeSeriesManager(object):
	""" Manager for TimeSeries handlings
	"""

	def __init__(self) -> None:
		"""	Initialize the TimeSeriesManager. Register event handlers.
		"""
		self._restoreTimeSeriesStructures()	# Restore structures after a complete restart
		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore
		L.isInfo and L.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeSeriesManager. Stop all the active workers.

			Return:
				True if the shutdown was successful.
		"""
		self.stopMonitoring()
		L.isInfo and L.log('TimeSeriesManager shut down')
		return True

	
	def restart(self, name:str) -> None:
		"""	Restart the TimeSeriesManager service.

			Args:
				name: The name of the event.
		"""
		self.stopMonitoring()
		runningTimeserieses.clear()
		L.isDebug and L.logDebug('TimeSeriesManager restarted')


	def _restoreTimeSeriesStructures(self) -> bool:
		"""	Restore the necessary internal in-memory structures when (re)starting
			a CSE.

			Return:
				True if the structures have been restored.
		"""
		for each in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.SUB):
			if NotificationEventType.reportOnGeneratedMissingDataPoints in each.attribute('enc/net', []): # enc/net might be empty
				L.isDebug and L.logDebug(f'Restoring structures for TSI subscription: {each.ri}')
				self.addSubscription(each.retrieveParentResource(), each)
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
		"""	This method is called when the expectedDgtRange has passed. It checks whether a TSI is missing by
			looking at the latest arrived dgt.

			Args:
				tsRi: resourceID of the respective <TS> resource. 
					Can be used to retrieve infos from `runningTimeserieses` dict.
			
			Return:
				True if the monitor should continue, False if the monitor should stop.
		"""
		L.isDebug and L.logDebug(f'Running DGT-monitor for TS: {tsRi}')

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

		tsRes = None
		# Iterate over all arrived dgt's till the last run of the monitor
		dgt = rts.nextDgt()
		while True:
			dgt = -1 if dgt is None else dgt 

			min = rts.expectedDgt - rts.peid
			max = rts.expectedDgt + rts.peid
			L.isDebug and L.logDebug(f'Expected dataGenerationTimeRange: {min} < dgt:{dgt} <= {max}')
			if not (min < dgt <= max):
				L.isDebug and L.logDebug(f'rts.expectedDgt: {rts.expectedDgt}, rts.peid: {rts.peid}')
				L.isWarn and L.logWarn(f'<tsi> NOT within expected dataGenerationTimeRange: {min} < dgt:{dgt} <= {max}')

				# If not, then add the expected arrival time as the dgt to the parent's mdlt list.
				if tsRes is None:
					if not (tsRes := CSE.dispatcher.retrieveResource(tsRi)):
						L.logErr(f'Cannot retrieve original <ts> resource: {tsRi}', showStackTrace = False)			# might (very rarely) happen when this monitor runs while the <ts> was deleted in another request
						return False	# stop monitoring (actor not restarted)
				tsRes.addDgtToMdlt(rts.expectedDgt)

				# Add the dgt to the missing data of the subscriptions
				for (subRi, md) in rts.missingData.items():
					md.missingDataList.append(toISO8601Date(rts.expectedDgt))
					md.missingDataCurrentNr += 1
					if md.missingDataCurrentNr == 1:	
						md.timeWindowEndTimestamp = rts.missingDataDetectionTime + md.missingDataDuration
				
				# L.logDebug(rts.missingData)
				# Check for sending the missing data subscriptions in  general
				CSE.notification.checkSubscriptions(None, 
													NotificationEventType.reportOnGeneratedMissingDataPoints, 
													None,
													ri = tsRi, 
													missingData = rts.missingData)
			else:
				L.isDebug and L.logDebug(f'<tsi> with dgt:{dgt} within expected dataGenerationTimeRange')

			# Prepare for the next DGT
			# This increments the expected times etc
			rts.prepareNextDgt()
			if (dgt := rts.nextDgt()) == None:
				break

		# Schedule the next actor runtime
		rts.prepareNextRun()
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

			Args:
				timeSeries: The <TS> resource.
				instance: The <TSI> resource.
		"""

		arrivedAt = fromAbsRelTimestamp(instance.ct)
		pei  = timeSeries.pei / 1000.0  # ms -> s
		peid = timeSeries.peid / 1000.0 # ms -> s
		mdt  = timeSeries.mdt / 1000.0  # ms -> s
		tsRi = timeSeries.ri
		if (dgt := fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			L.isWarn and L.logWarn(f'Error parsing <tsi>.dgt: {dgt}')
			return
		L.isDebug and L.logDebug(f'New <tsi> for <ts>:{timeSeries.ri} dgt:{dgt}')
		#now = utcTime()
		missingDataDetectionTime = dgt + pei + mdt # next runtime of the check

		if not (rts := runningTimeserieses.get(tsRi)) or not rts.running:		# it is a new timeSeries
			actor = None
			if missingDataDetectionTime < arrivedAt:
				# Don't start a monitor if the next runtime for that monitor would be in the past anyway.
				L.isDebug and L.logDebug(f'First <tsi> for this <ts>: {tsRi} but way back in the past. NOT monitoring.')
			
			else:
				# Create and start monitoring worker 
				L.isDebug and L.logDebug(f'First <tsi> for this <ts>: {tsRi}. Starting monitoring. Next runtime:{missingDataDetectionTime}')
				actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at = missingDataDetectionTime, name = f'tsMonitor_{tsRi}_{missingDataDetectionTime}').start(tsRi = tsRi)
			
			#	runningTimeserieses structure could have been created earlier (or not), eg. by adding a subscription earlier, but is not running yet
			#	It still needs to be filled
			if not rts:
				# L.logWarn(f'Adding new instance for {tsRi}')
				runningTimeserieses[tsRi] = (rts := LastTSInstance())
			else:
				L.isDebug and L.logDebug(f'Re-using existing LastTSInstance monitor')

			# Prepare runningTS structure after receiving a first TSI
			# No dgt is added for the first tsi
			rts.clearDgt()
			rts.expectedDgt					= dgt + pei		# will be set in the monitor from hereon
			rts.missingDataDetectionTime	= rts.expectedDgt + mdt
			rts.pei							= pei
			rts.mdt							= mdt
			rts.peid 						= peid
			rts.actor 						= actor
			rts.running 					= True

		else:
			L.isDebug and L.logDebug(f'Using existing LastTSInstance monitor')
			if missingDataDetectionTime < arrivedAt:
				# If the next runtime is too way back in the past then we don't start a monitor for that but add THIS TSI's dgt
				timeSeries.addDgtToMdlt(dgt)

			# Add or update runningTimeserieses map.
			rts.addDgt(dgt)

		L.isDebug and L.logDebug(f'tsRi:{tsRi}, pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt}, missingDataDetectionTime:{rts.missingDataDetectionTime}, dgt:{dgt}, expectedDgt:{rts.expectedDgt}')


	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored.

			Args:
				ri: ResourceID of the TimeSeries resource.

			Return:
				Boolean indicating whether the resource is monitored.
		"""
		return runningTimeserieses.get(ri) is not None  # if any


	def stopMonitoringTimeSeries(self, tsRi:str) -> bool:
		"""	Remove a <TS> resource from monitoring. No other attributes are updated.

			Args:
				tsRi: ResourceID of the TimeSeries resource.
			Return:
				Boolean indicating success.
		"""
		L.isDebug and L.logDebug(f'Remove <ts> from monitoring: {tsRi}')
		if tsRi in runningTimeserieses:
			rts = runningTimeserieses.pop(tsRi)	# removes (!) it also from the dict
			if rts.actor:
				rts.actor.stop()
		return True

	
	def pauseMonitoringTimeSeries(self, tsRi:str) -> bool:
		"""	Pause the monitoring of a <TS> resource.

			Args:
				tsRi: ResourceID of the TimeSeries resource.
			Return:
				Boolean indicating success.
		"""
		if tsRi in runningTimeserieses:
			rts = runningTimeserieses.get(tsRi)
			rts.running = False
			if rts.actor:
				rts.actor.stop()
		return True


	#
	#	Subscriptions
	#

	def addSubscription(self, timeSeries:Resource, subscription:Resource) -> None:
		"""	Add a subscription for the <TS> resource. Setup the internal structures.

			Args:
				timeSeries: The <TS> resource.
				subscription: The <sub
		"""
		if (net := subscription['enc/net']) is not None and NotificationEventType.reportOnGeneratedMissingDataPoints in net:
			L.isDebug and L.logDebug(f'Adding missing-data <sub>: {subscription.ri}. Not started yet.')
			tsRi = timeSeries.ri
			if not (rts := runningTimeserieses.get(timeSeries.ri)):
				runningTimeserieses[tsRi] = (rts := LastTSInstance())
			rts.missingData[subscription.ri] = MissingData(	subscriptionRi = subscription.ri, 
															missingDataDuration = fromDuration(subscription['enc/md/dur']),
															missingDataNumber = subscription['enc/md/num'])


	def updateSubscription(self, timeSeries:Resource, subscription:Resource) -> None:
		""" Update an existing missing data subscription.

			Args:
				timeSeries: The <TS> resource.
				subscription: The <sub> resource.
		"""
		if (net := subscription['enc/net']) is not None and NotificationEventType.reportOnGeneratedMissingDataPoints in net:
			L.isDebug and L.logDebug(f'Updating missing data <sub>: {subscription.ri}')
			if (rts := runningTimeserieses.get(timeSeries.ri)) and (md := rts.missingData.get(subscription.ri)):
				md.missingDataDuration = fromDuration(subscription['enc/md/dur'])
				md.missingDataNumber = subscription['enc/md/num']


	def removeSubscription(self, timeSeries:Resource, subscription:Resource) -> None:
		"""	Remove a subcription from a <TS> resource. Remove the internal structures.

			Args:
				timeSeries: The <TS> resource.
				subscription: The <sub> resource.
		"""
		if (net := subscription['enc/net']) is not None and NotificationEventType.reportOnGeneratedMissingDataPoints in net:
			L.isDebug and L.logDebug(f'Removing missing data <sub>: {subscription.ri}')
			if (rts := runningTimeserieses.get(timeSeries.ri)) and subscription.ri in rts.missingData:
				del rts.missingData[subscription.ri]
