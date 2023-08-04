#
#	GeoUtils.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various helpers for working with geo-coordinates, shapely, and geoJSON
#

""" Utility functions for geo-coordinates and geoJSON
"""

from typing import Union, Optional, cast
import json
from shapely import Point, Polygon


def getGeoPoint(jsn:Optional[Union[dict, str]]) -> Optional[tuple[float, float]]:
	""" Get the geo-point from a geoJSON object.

		Args:
			jsn: The geoJSON object as a dictionary or a string.

		Returns:
			A tuple of the geo-point (latitude, longitude). None if not found or invalid JSON.
	"""
	if jsn is None:
		return None
	if isinstance(jsn, str):
		try:
			jsn = json.loads(jsn)
		except ValueError:
			return None
	if cast(dict, jsn).get('type') != 'Point':
		return None
	if coordinates := cast(dict, jsn).get('coordinates'):
		return coordinates[0], coordinates[1]
	return None


def getGeoPolygon(jsn:Optional[Union[dict, str]]) -> Optional[list[tuple[float, float]]]:
	""" Get the geo-polygon from a geoJSON object.

		Args:
			jsn: The geoJSON object as a dictionary or a string.

		Returns:
			A list of tuples of the geo-polygon (latitude, longitude). None if not found or invalid JSON.
	"""
	if jsn is None:
		return None
	if isinstance(jsn, str):
		try:
			jsn = json.loads(jsn)
		except ValueError:
			return None
	if cast(dict, jsn).get('type') != 'Polygon':
		return None
	if coordinates := cast(dict, jsn).get('coordinates'):
		return coordinates[0]
	return None


def isLocationInsidePolygon(polygon:list[tuple[float, float]], location:tuple[float, float]) -> bool:
	""" Check if a location is inside a polygon.

		Args:
			polygon: The polygon as a list of tuples (latitude, longitude).
			location: The location as a tuple (latitude, longitude).

		Returns:
			True if the location is inside the polygon, False otherwise.
	"""
	return Polygon(polygon).contains(Point(location))

