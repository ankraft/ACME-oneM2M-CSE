#
#	LocationManager.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module implements location service and helper functions.
"""

from __future__ import annotations

from typing import Tuple, Optional, Literal
from dataclasses import dataclass
import json

from ..helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from ..etc.Types import LocationInformationType, LocationSource, GeofenceEventCriteria, ResourceTypes, GeometryType, GeoSpatialFunctionType
from ..etc.DateUtils import fromDuration
from ..etc.GeoTools import getGeoPoint, getGeoPolygon, isLocationInsidePolygon, geoWithin, geoContains, geoIntersects
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..resources.LCP import LCP
from ..resources.CIN import CIN
from ..resources import Factory
from ..resources.Resource import Resource

GeofencePositionType = Literal[GeofenceEventCriteria.Inside, GeofenceEventCriteria.Outside]
""" Type alias for the geofence position."""

LocationType = Tuple[float, float]
""" Type alias for the location type."""

@dataclass
class LocationInformation(object):
	"""	Location information for a location policy.
	"""
	worker:BackgroundWorker = None
	""" The worker for the location policy. """
	location:Optional[LocationType] = None
	""" The current location. """
	targetArea:Optional[list[LocationType]] = None
	""" The polygon. """
	geofencePosition:GeofencePositionType = GeofenceEventCriteria.Inside
	""" The current position type (inside, outside). """
	eventCriteria:GeofenceEventCriteria = GeofenceEventCriteria.Inside
	""" The event criteria. """
	locationContainerID:Optional[str] = None
	""" The location container resource ID. """


class LocationManager(object):
	"""	The LocationManager class implements the location service and helper functions.
	
		Attributes:
			locationPolicyWorkers: A dictionary of location policy workers
	"""

	__slots__ = (	
		'locationPolicyInfos',
		'deviceDefaultPosition'
	)


	def __init__(self) -> None:
		"""	Initialization of the LocationManager module.
		"""

		self.locationPolicyInfos:dict[str, LocationInformation] = {}
		
		self.deviceDefaultPosition:GeofencePositionType = GeofenceEventCriteria.Inside	# Default event criteria
		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore
		L.isInfo and L.log('LocationManager initialized')


# TODO rebuild the list of location policies when the CSE is reset or started. OR create a DB

	def shutdown(self) -> bool:
		"""	Shutdown the LocationManager.
		
			Returns:
				Boolean that indicates the success of the operation
		"""
		L.isInfo and L.log('LocationManager shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the LocationManager.
		"""
		L.isDebug and L.logDebug('LocationManager restarted')


	#########################################################################

	def addLocationPolicy(self, lcp:LCP) -> None:
		"""	Add a location policy.

			Args:
				lcp: The location policy to add.
		"""
		L.isDebug and L.logDebug('Adding location policy')
		lcpRi = lcp.ri
		gta = getGeoPolygon(lcp.gta)
		loi = lcp.loi

		# Remove first if already running
		if lcpRi in self.locationPolicyInfos:
			self.removeLocationPolicy(lcp)

		# Check whether the location source is device based (only one supported right now)
		if lcp.los != LocationSource.Device_based:
			L.isDebug and L.logDebug('Only device based location source supported')
			return	# Not supported

		# Add an empty entry first.
		self.locationPolicyInfos[lcpRi] = LocationInformation(targetArea = gta, 
						     								  geofencePosition = self.deviceDefaultPosition, 
															  eventCriteria = lcp.gec,
															  locationContainerID = loi)

		# Check if the location information type / position is fixed
		if (lit := lcp.lit) is None or lit == LocationInformationType.Position_fix:
			L.isDebug and L.logDebug('Location information type not set or position fix. Ignored.')
			return	# No updates needed
		
		# Get the periodicity
		if (lou := lcp.lou) is None or len(lou) == 0:	# locationUpdatePeriodicity
			L.isDebug and L.logDebug('Location update periodicity not set. Ignored.')
			return	# No updates needed. Checks are done when the location is requested via <latest>
		if (_lou := fromDuration(lou[0], False)) == 0.0:	# just take the first duration
			L.isDebug and L.logDebug('Location update periodicity is 0. Ignored.')
			return
		
		# Create a worker
		L.isDebug and L.logDebug(f'Starting location policy worker for: {lcpRi} Intervall: {_lou}')
		self.locationPolicyInfos[lcpRi] = LocationInformation(worker = BackgroundWorkerPool.newWorker(interval = _lou,
								  									workerCallback = self.locationWorker, 
																	name = f'lcp_{lcp.ri}', 
																	startWithDelay = True).start(lcpRi = lcpRi),
															targetArea = gta,
															geofencePosition = self.deviceDefaultPosition,
															eventCriteria = lcp.gec,
															locationContainerID = loi
														  )
		# # Immediately update the location
		# self.getNewLocation(lcpRi)
		

	
	def removeLocationPolicy(self, lcp:LCP) -> None:
		"""	Remove a location policy. This will stop the worker and remove the LCP from the internal list.	

			Args:
				lcp: The LCP to remove.
		"""
		L.isDebug and L.logDebug('Removing location policy')

		# Stopping the worker and remove the LCP from the internal list
		if (ri := lcp.ri) in self.locationPolicyInfos:
			L.isDebug and L.logDebug('Stopping location policy worker')
			if (worker := self.locationPolicyInfos[ri].worker) is not None:
				worker.stop()
			del self.locationPolicyInfos[ri]


	def updateLocationPolicy(self, lcp:LCP) -> None:
		"""	Update a location policy. This will remove the old location policy and add a new one.
		"""
		L.isDebug and L.logDebug('Updating location policy')
		self.removeLocationPolicy(lcp)
		self.addLocationPolicy(lcp)


	def handleLatestRetrieve(self, latest:CIN, lcpRi:str) -> None:
		"""	Handle a latest RETRIEVE request for a CNT with a location policy.

			Args:
				latest: The latest CIN
				lcpRi: The location policy resource ID
		"""
		if lcpRi is None:
			return
		
		# Check if the location policy is supported
		if (lcp := CSE.dispatcher.retrieveResource(lcpRi)) is not None:
			if lcp.los == LocationSource.Network_based and lcp.lou is not None and lcp.lou == 0:
				L.isDebug and L.logDebug(f'Handling latest RETRIEVE for CNT with locationID: {lcpRi}')
				# Handle Network based location source
				# NOT SUPPORTED YET
				L.isWarn and L.logWarn('Network-based location source not supported yet')
			
			if (lit := lcp.lit) is None or lit == LocationInformationType.Position_fix:
				L.isDebug and L.logDebug('Location information type not set or position fix. Ignored.')
				return	# No updates needed

		
		if (locations := self.getNewLocation(lcpRi, content = latest.con)) is None:
			return

		# check if the location is inside the polygon and update the location event
		self.updateLocationEvent(locations[0], locations[1], lcpRi)

		# TODO do something with the result


	def locationWorker(self, lcpRi:str) -> bool:
		"""	Worker function for location policies. This will be called periodically to update the location.

			Args:
				lcpRi: The resource ID of the location policy

			Returns:
				True if the worker should be continued, False otherwise.
		"""

		if (locations := self.getNewLocation(lcpRi)) is None:
			return True	# something went wrong, but still continue
		
		self.updateLocationEvent(locations[0], locations[1], lcpRi)

		return True
	



	#########################################################################



	def getNewLocation(self, lcpRi:str, content:Optional[str] = None) -> Optional[Tuple[LocationType, LocationType]]:
		"""	Get the new location for a location policy. Also, update the internal policy info if necessary.
		
			Args:
				lcpRi: The resource ID of the location policy
				content: The content of the latest CIN of the location policy's container resource
				
			Returns:
				The new and old locations as a tuple of (latitude, longitude), or None if the location is invalid or not found
		"""

		# Get the location policy info
		if (info := self.locationPolicyInfos.get(lcpRi)) is None:
			L.isWarn and L.logWarn(f'Internal location policy info for: {lcpRi} not found')
			return None

		# Get the content if not provided
		if not content:
			# Get the location from a location instance
			if not (cin := CSE.dispatcher.retrieveLatestOldestInstance(info.locationContainerID, ResourceTypes.CIN)):
				return None	# No resource found, still continue
			content = cin.con
		
		# Check whether the content is a valid location or an event
		if content in ('', '1', '2', '3', '4'):	# This could be done better...
			return None	# An event, so return 

		# From here on, content is a location
		if (newLocation := getGeoPoint(content)) is None:
			L.isWarn and L.logWarn(f'Invalid location: {content}. Must be a valid GeoPoint')

		# Check if the location has changed, or there was no location before
		oldLocation = info.location
		if oldLocation != newLocation:
			# Update the location in the location policy
			self.locationPolicyInfos[lcpRi].location = newLocation

		return (newLocation, oldLocation)
	

	def updateLocationEvent(self, newLocation:LocationType, oldLocation:LocationType, lcpRi:str) -> None:
		"""	Update the location event for a location policy if the location has changed and/or the event criteria is met.
		
			Args:
				newLocation: The new location
				oldLocation: The old location
				lcpRi: The resource ID of the location policy
		"""

		def addEventContentInstance(info:LocationInformation, eventType:GeofenceEventCriteria) -> None:
			"""	Add a new event content instance to the location policy's container resource.
			
				Args:
					info: The location policy info
					eventType: The type of the event
			"""
			L.isDebug and L.logDebug(f'Position: {eventType}')
			cnt = CSE.dispatcher.retrieveResource(info.locationContainerID)
			cin = Factory.resourceFromDict({ 'con': f'{eventType.value}' },
										   pi = info.locationContainerID, 
										   ty = ResourceTypes.CIN,
										   create = True,
										   originator = cnt.getOriginator())
			CSE.dispatcher.createLocalResource(cin, cnt)

		
		if (info := self.locationPolicyInfos.get(lcpRi)) is None:
			L.isWarn and L.logWarn(f'Internal location policy info for: {lcpRi} not found')
			return
		previousGeofencePosition = info.geofencePosition
		currentGeofencePosition = self.checkGeofence(lcpRi, newLocation)

		match currentGeofencePosition:
			case GeofenceEventCriteria.Inside if previousGeofencePosition == GeofenceEventCriteria.Outside and info.eventCriteria == GeofenceEventCriteria.Entering:
				# Entering
				addEventContentInstance(info, GeofenceEventCriteria.Entering)
			case GeofenceEventCriteria.Outside if previousGeofencePosition == GeofenceEventCriteria.Inside and info.eventCriteria == GeofenceEventCriteria.Leaving:
				# Leaving
				addEventContentInstance(info, GeofenceEventCriteria.Leaving)
			case GeofenceEventCriteria.Inside if previousGeofencePosition == GeofenceEventCriteria.Inside and info.eventCriteria == GeofenceEventCriteria.Inside:
				# Inside
				addEventContentInstance(info, GeofenceEventCriteria.Inside)
			case GeofenceEventCriteria.Outside if previousGeofencePosition == GeofenceEventCriteria.Outside and info.eventCriteria == GeofenceEventCriteria.Outside:
				# Outside
				addEventContentInstance(info, GeofenceEventCriteria.Outside)
			case _:
				# No event
				L.isDebug and L.logDebug(f'No event for: {previousGeofencePosition} -> {currentGeofencePosition} and event criteria: {GeofenceEventCriteria(info.eventCriteria)}')

		# update the geofence position
		info.geofencePosition = currentGeofencePosition
		info.location = newLocation


	def checkGeofence(self, lcpRi:str, location:tuple[float, float]) -> GeofencePositionType:
		"""	Check if a location is inside or outside the polygon of a location policy.
		
			Args:
				lcpRi: The resource ID of the location policy
				location: The location to check
				
			Returns:
				The geofence position of the location. Either *inside* or *outside*.
		"""
		result = GeofenceEventCriteria.Inside if isLocationInsidePolygon(self.locationPolicyInfos[lcpRi].targetArea, location) else GeofenceEventCriteria.Outside
		# L.isDebug and L.logDebug(f'Location is: {result}')
		return result	# type:ignore [return-value]


	#########################################################################
	#
	# 	GeoLocation and GeoQuery
	#

	def checkGeoLocation(self, r:Resource, gmty:GeometryType, geom:list, gsf:GeoSpatialFunctionType) -> bool:
		"""	Check if a resource's location confirms to a geo location.

			Args:
				r: The resource to check.
				gmty: The geometry type.
				geom: The geometry.
				gsf: The geo spatial function.

			Returns:
				True if the resource's location confirms to the geo location, False otherwise.
		"""
		if (rGeom := r.getLocationCoordinates()) is None:
			return False
		rTyp = r.loc.get('typ')
		
		try:
			match gsf:
				case GeoSpatialFunctionType.Within:
					return geoWithin(gmty, geom, rTyp, rGeom)
				case GeoSpatialFunctionType.Contains:
					return geoContains(gmty, geom, rTyp, rGeom)
				case GeoSpatialFunctionType.Intersects:
					return geoIntersects(gmty, geom, rTyp, rGeom)
				case _:
					raise ValueError(f'Invalid geo spatial function: {gsf}')
		except ValueError as e:
			raise BAD_REQUEST(L.logDebug(f'Invalid geometry: {e}'))
