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

	# <TS> attribues
	pei:float
	mdt:float
	peid:float

runningTimeserieses:dict[str, LastTSInstance] = {}	# Holds and maps the active TS and their LastTSInstance objects

# TODO What shoul happen when first DGT is already in the past, so that dgt-peid < now?

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
	
	
	def timeSeriesMonitor(self, tsRi:str, runtime:float) -> bool:
		"""	This method is called when the period + mdt has passed. It checks whether a TSI is missing by
			looking at the latest arrived dgt.

			`tsRi` - resourceID of the respective <TS> resource. Can be used to retrieve infos from 'runningTimeserieses' dict.
			`runtime` - The timestamp of the runtime of this function for tsRI 
		"""

		# Check TSI arrival for this TS
		if (rts := runningTimeserieses.get(tsRi)) is None:
			if L.isWarn: L.logWarn(f'No last TSInstance for TimeSeries: {tsRi}')
			return False
		
		ontime = runtime-rts.mdt	# Expected timestamp of the last <TSI>.

		# Check if there was a <TSI> in the expected time frame (between ontime and now)
		# Also check if the <TSI>'s dgt is between ontime-delta and onetime+delta
		if L.isDebug: L.logDebug(f'TSI Monitor runTime: {runtime} onTime: {ontime} mdt: {rts.mdt} nextExpectedDGT:{rts.nextExpectedDgt} lastSeenDGT: {rts.lastSeenDgt}')
		if not ( (ontime <= rts.tsiArrivedAt <= runtime) and (ontime-rts.peid <= rts.lastSeenDgt <= ontime+rts.peid) ):

			# If not, then add the expected arrival time as the dgt to the parent's mdlt list.
			if L.isWarn: L.logWarn(f'No TSI within time period or DGT outside peid')
			if (tsRes := CSE.dispatcher.retrieveResource(tsRi).resource) is None:
				L.logErr(f'Cannot retrieve original TS resource: {tsRi}')
			tsRes.setAttribute('mdlt', [], overwrite=False)				# Add missingDataList, just in case it hasn't created before
			tsRes.mdlt.append(Utils.toISO8601Date(rts.nextExpectedDgt))	# Add missing dataGenerationTime to TS.missingDataList
			if (tsMdn := tsRes.mdn) is not None:						# mdn may not be set. Then this list grows forever
				if len(tsRes.mdlt) > tsMdn:								# If missingDataList is bigger then missingDataMaxNr allows
					tsRes['mdlt'] = tsRes.mdlt[1:]						# Reduce the missingDataList
				tsRes['mdc'] = len(tsRes.mdlt)							# set the missingDataCurrentNr
			tsRes.dbUpdate()											# Update in DB
			# if L.isWarn: L.logWarn(tsRes.mdlt)
		rts.nextExpectedDgt += rts.pei									# Set the next expected DGT. Will be overwritten when a real one arrives

		# Schedule the next actor runtime
		actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=runtime+rts.pei, name=f'tsMonitor_{tsRi}_{runtime+rts.pei}')
		if L.isDebug: L.logDebug(f'tsRi={tsRi}, pei={rts.pei}, mdt={rts.mdt}, runtime={runtime+rts.pei}')
		actor.start(tsRi=tsRi, runtime=runtime+rts.pei) 				# Next running is in now+interval

		return True


	def updateTimeSeries(self, timeSeries:Resource, instance:Resource) -> None:
		"""	Add or update to the internal monitor DB.
			The monitoring is started only when a first TSI is added for a TS.
		"""

		# TODO check whether dgt is way in the past (gdt < now - peid?) Then what? Ignore?

		now_ 	= Utils.utcTime()
		if L.isDebug: L.logDebug(f'New TSI for TS: {timeSeries.ri}')
		pei  = timeSeries.pei / 1000.0  # ms -> s
		peid = timeSeries.peid / 1000.0 # ms -> s
		mdt  = timeSeries.mdt / 1000.0  # ms -> s
		if (dgt := Utils.fromAbsRelTimestamp(instance.dgt)) == 0.0:	# error
			if L.isWarn: L.logWarn(f'Error parsing TSI.dgt: {dgt}')
			return
		if dgt > now_:
			if L.isWarn: L.logWarn(f'TDI.get is in the future: {dgt}')	# TODO
			return
		tsRi = timeSeries.ri
		if L.isDebug: L.logDebug(f'New TSI at: {now_} dgt: {dgt}')

		if runningTimeserieses.get(tsRi) is None:		# is new timeSeries
			if L.isDebug: L.logDebug(f'Start monitoring TSI: {tsRi}')
			runtime = dgt+pei+mdt
			actor = BackgroundWorkerPool.newActor(self.timeSeriesMonitor, at=runtime, name=f'tsMonitor_{tsRi}_{runtime}')
			actor.start(tsRi=tsRi, runtime=dgt+pei+mdt)		

			# TODO check whether a first TSI's DGT is also with the limits!!!!


		# Add/Update runningTimeserieses map
		runningTimeserieses[tsRi] = LastTSInstance(lastSeenDgt=dgt, tsiArrivedAt=now_, nextExpectedDgt=dgt+pei, pei=pei, mdt=mdt, peid=peid)


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
