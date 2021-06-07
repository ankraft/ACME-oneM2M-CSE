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

from dataclasses import dataclass

@dataclass
class LastTSInstance:
	"""	Defines a data class for a single TS's latest and next expected TSI/dgt. """
	lastSeenDgt:float
	arrivedAt:float
	nextExpectedDgt:float


runningTimeserieses:dict[str, LastTSInstance] = {}	# Holds and maps the active TS and their LastTSInstance objects

class TimeSeriesManager(object):

	def __init__(self) -> None:
		Logging.log('TimeSeriesManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the TimeSeriesManager. Stop all the active workers.
		"""
		self.stopMonitoring()
		Logging.log('TimeSeriesManager shut down')
		return True


	def stopMonitoring(self) -> None:
		"""	Stop the background worker that monitores the timeSeries ingress. 
		"""
		for tsRi in runningTimeserieses.keys():
			self.stopMonitoringTimeSeries(tsRi)
	
	
	def timeSeriesMonitor(self, tsRi:str, pei:float, mdt:float, runtime:float) -> bool:
		"""	This method is called when the period + mdt has passed. It checks whether a TSI is missing by
			looking at the latest arrived dgt.
		"""
		# TODO Bob: put expected DGT or dgt from TSI in mdlt?
		# TODO Same in Monitor. What happens if dgt is suddenly in the past. what happens to nextExpected? This currently leads to creating lots of actors that are executed immedieately. Try to catch up with next expected?


		# Check TSI arrival for this TS
		if (rts := runningTimeserieses.get(tsRi)) is None:
			Logging.logErr(f'No LastTSInstance for TimeSeries: {tsRi}')
			return False
		peid = 200/1000 # TODO
		ontime = runtime-mdt

		# Check if there is a dgt in the expected time frame
		if not ( (ontime < rts.arrivedAt < runtime) and (ontime-peid < rts.lastSeenDgt < ontime+peid) ):
			# If not, then add the expected arrival time as the dgt to the parent's mdlt list.
			# Logging.logWarn(f'No TSI within time period or DGT outside peid. onTime:{ontime} < arrivedAt:{rts.arrivedAt} < runtime:{runtime} or ontime-peid:{ontime-peid} < lastSeenDGT:{rts.lastSeenDgt} < ontime+peid:{ontime+peid}')
			Logging.logWarn(f'No TSI within time period or DGT outside peid. runTime: {runtime} onTime: {ontime} mdt: {mdt} nextExpectedDGT:{rts.nextExpectedDgt} lastSeenDGT: {rts.lastSeenDgt}')
			if (tsRes := CSE.dispatcher.retrieveResource(tsRi).resource) is None:
				Logging.logErr(f'Cannot retrieve original TS resource: {tsRi}')
			tsRes.setAttribute('mdlt', [], overwrite=False)				# Add missingDataList, just in case it hasn't created before
			tsRes.mdlt.append(Utils.toISO8601Date(rts.nextExpectedDgt))	# Add missing dataGenerationTime to TS.missingDataList
			if (tsMdn := tsRes.mdn) is not None:						# mdn may not be set. Then this list grows forever
				if len(tsRes.mdlt) > tsMdn:								# If missingDataList is bigger then missingDataMaxNr allows
					tsRes['mdlt'] = tsRes.mdlt[1:]						# Reduce the missingDataList
				tsRes['mdc'] = len(tsRes.mdlt)							# set the missingDataCurrentNr
			tsRes.dbUpdate()											# Update in DB
			Logging.logWarn(tsRes.mdlt)
		rts.nextExpectedDgt = rts.lastSeenDgt + pei					# Set the next expected DGT. Will be overwritten when a real one arrives

		# Schedule the next actor runtime
		actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=runtime+pei, name=f'tsMonitor_{tsRi}_{runtime+pei}')
		Logging.logDebug(f'tsRi={tsRi}, pei={pei}, mdt={mdt}, runtime={runtime+pei}')
		actor.start(tsRi=tsRi, pei=pei, mdt=mdt, runtime=runtime+pei)		

		return True


	def updateTimeSeries(self, timeSeries:Resource, instance:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started only when a first TSI is added for a TS.
		"""

		# TODO check whether dgt is way in the past (gdt < now - peid?) Then what? Ignore?

		now_ 	= Utils.utcTime()
		Logging.logDebug(f'New TSI for TS: {timeSeries.ri}')
		pei = timeSeries.pei / 1000.0 # ms -> s
		mdt = timeSeries.mdt / 1000.0 # ms -> s
		if (dgt := Utils.fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			Logging.logWarn(f'Error parsing TSI.dgt: {dgt}')
			return
		if dgt > now_:
			Logging.logWarn(f'TDI.get is in the future: {dgt}')
			return
		tsRi = timeSeries.ri
		Logging.logDebug(f'New TSI at: {now_} dgt: {dgt}')

		if runningTimeserieses.get(tsRi) is None:		# is new timeSeries
			Logging.logDebug(f'Start monitoring TSI: {tsRi}')
			runtime = dgt+pei+mdt
			actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=runtime, name=f'tsMonitor_{tsRi}_{runtime}')
			actor.start(tsRi=tsRi, pei=pei, mdt=mdt, runtime=dgt+pei+mdt)		

		# Add/Update runningTimeserieses map
		runningTimeserieses[tsRi] = LastTSInstance(lastSeenDgt=dgt, arrivedAt=now_, nextExpectedDgt=dgt+pei)


	def isMonitored(self, ri:str) -> bool:
		"""	Check whether a resource is been monitored. """
		return runningTimeserieses.get(ri) is not None


	def stopMonitoringTimeSeries(self, tsRi:str) -> bool:
		"""	Remove a timeSeries from monitoring.
		"""
		Logging.logDebug(f'Remove TS from monitoring: {tsRi}')
		BackgroundWorkerPool.stopWorkers(name=f'tsMonitor_{tsRi}_*')
		if tsRi in runningTimeserieses:
			del runningTimeserieses[tsRi]
		return True
