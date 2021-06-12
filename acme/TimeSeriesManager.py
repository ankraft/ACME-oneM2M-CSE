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
from Logging import Logging as L
import CSE, Utils
from Configuration import Configuration
from resources.Resource import Resource
from helpers.BackgroundWorker import BackgroundWorkerPool

from dataclasses import dataclass

@dataclass
class LastTSInstance:
	"""	Defines a data class for a single TS's latest and next expected TSI/dgt, and other information """
	lastSeenDgt:float
	tsiArrivedAt:float
	nextExpectedDgt:float
	nextRuntime:float

	# <TS> attribues
	pei:float
	mdt:float
	peid:float


# TODO: Subscriptions: Add the missing instances window list to LastTSInstance, also the time

runningTimeserieses:dict[str, LastTSInstance] = {}	# Holds and maps the active TS and their LastTSInstance objects

class TimeSeriesManager(object):

	def __init__(self) -> None:
		L.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeSeriesManager. Stop all the active workers.
		"""
		self.stopMonitoring()
		L.log('TimeSeriesManager shut down')
		return True


	def stopMonitoring(self) -> None:
		"""	Stop the background worker that monitores the timeSeries ingress. 
		"""
		for tsRi in runningTimeserieses.keys():
			self.stopMonitoringTimeSeries(tsRi)
	
	
	def timeSeriesMonitor(self, tsRi:str) -> bool:
		"""	This method is called when the period + mdt has passed. It checks whether a TSI is missing by
			looking at the latest arrived dgt.

			`tsRi` - resourceID of the respective <TS> resource. Can be used to retrieve infos from 'runningTimeserieses' dict.
			`runtime` - The timestamp of the runtime of this function for tsRI 
		"""

		# Check TSI arrival for this TS
		if (rts := runningTimeserieses.get(tsRi)) is None:
			L.logErr(f'No last TSI for TS: {tsRi}')
			return False # stop monitoring
		
		ontime = rts.nextRuntime-rts.mdt	# Expected (minimum) timestamp of the last <TSI>.

		# Check if there was a <TSI> in the expected time frame (between ontime and now)
		# Also check if the <TSI>'s dgt is between ontime-delta and onetime+delta
		if L.isDebug: L.logDebug(f'TSI Monitor runTime:{rts.nextRuntime} onTime:{ontime} pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt} tsiArrivedAt:{rts.tsiArrivedAt}, nextExpectedDGT:{rts.nextExpectedDgt} lastSeenDGT:{rts.lastSeenDgt}')
		if not ( (ontime <= rts.tsiArrivedAt <= rts.nextRuntime) and (ontime-rts.peid <= rts.lastSeenDgt <= ontime+rts.peid) ):

			# If not, then add the expected arrival time as the dgt to the parent's mdlt list.
			if L.isWarn: L.logWarn(f'No TSI within time period or DGT outside peid')
			if (tsRes := CSE.dispatcher.retrieveResource(tsRi).resource) is None:
				L.logErr(f'Cannot retrieve original TS resource: {tsRi}')
				return False	# stop monitoring
			tsRes.addDgtToMdlt(rts.nextExpectedDgt)

		rts.nextExpectedDgt += rts.pei									# Set the next expected DGT. Will be overwritten when a real one arrives
		rts.nextRuntime += rts.pei

		# Schedule the next actor runtime
		actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=rts.nextRuntime, name=f'tsMonitor_{tsRi}_{rts.nextRuntime}')
		if L.isDebug: L.logDebug(f'tsRi:{tsRi}, pei:{rts.pei}, peid:{rts.peid}, mdt:{rts.mdt}, nextRuntime:{rts.nextRuntime}, nextExpectedDgt:{rts.nextExpectedDgt}')
		actor.start(tsRi=tsRi) 				# Next running is in now+interval
		return True


	def updateTimeSeries(self, timeSeries:Resource, instance:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started only when a first TSI is added for a TS.
		"""

		now  = Utils.utcTime()
		if L.isDebug: L.logDebug(f'New TSI for TS: {timeSeries.ri}')
		pei  = timeSeries.pei / 1000.0  # ms -> s
		peid = timeSeries.peid / 1000.0 # ms -> s
		mdt  = timeSeries.mdt / 1000.0  # ms -> s
		tsRi = timeSeries.ri
		if (dgt := Utils.fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			if L.isWarn: L.logWarn(f'Error parsing TSI.dgt: {dgt}')
			return
		if L.isDebug: L.logDebug(f'New TSI at: {now} dgt: {dgt}')
		runtime = dgt+pei+mdt

		if runningTimeserieses.get(tsRi) is None:		# is new timeSeries

			if runtime < now:
				# Don't start a monitor if the next runtime for that monitor would be in the past anyway.
				if L.isDebug: L.logDebug(f'First TSI for this TS: {tsRi} but way back in the past. NO monitoring for this TS.')
			
			else:
				if L.isDebug: L.logDebug(f'First TSI for this TS: {tsRi} Starting monitoring')
				actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=runtime, name=f'tsMonitor_{tsRi}_{runtime}')
				actor.start(tsRi=tsRi)		

		else:
			if runtime < now:
				# If the next runtime is too way back in the past then we don't start a monitor for that but add THIS TSI's dgt
				timeSeries.addDgtToMdlt(dgt)


		# Add/Update runningTimeserieses map. All TS get an entry, even when there is no running monitor, e.g. for past TSI
		if (rts := runningTimeserieses.get(tsRi)) is None:
			runningTimeserieses[tsRi] = (rts := LastTSInstance(lastSeenDgt=dgt, tsiArrivedAt=now, nextExpectedDgt=dgt+pei, nextRuntime=runtime, pei=pei, mdt=mdt, peid=peid))
		else:
			rts.lastSeenDgt  = dgt
			rts.tsiArrivedAt = now
			# rts.nextExpectedDgt = dgt+pei
		if L.isDebug: L.logDebug(f'tsRi:{tsRi}, pei:{rts.pei}, mdt:{rts.mdt}, runtime:{rts.nextRuntime}, lastSeenDgt:{rts.lastSeenDgt}, nextExpectedDgt:{rts.nextExpectedDgt}')


	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored. """
		return runningTimeserieses.get(ri) is not None


	def stopMonitoringTimeSeries(self, tsRi:str) -> bool:
		"""	Remove a timeSeries from monitoring.
		"""
		if L.isDebug: L.logDebug(f'Remove TS from monitoring: {tsRi}')
		BackgroundWorkerPool.stopWorkers(name=f'tsMonitor_{tsRi}_*')
		if tsRi in runningTimeserieses:
			del runningTimeserieses[tsRi]
		return True
