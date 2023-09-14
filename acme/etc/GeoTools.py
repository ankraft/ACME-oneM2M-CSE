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

from shapely import Point, Polygon, LineString, MultiPoint, MultiLineString, MultiPolygon
from shapely.geometry.base import BaseGeometry

from ..etc.Types import GeometryType


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


def geoWithin(aType:GeometryType, aShape:tuple|list, bType:GeometryType, bShape:tuple|list) -> bool:
	""" Check if a shape is within another shape.
	
		Args:
			aType: The type of the first shape.
			aShape: The shape of the first shape.
			bType: The type of the second shape.
			bShape: The shape of the second shape.
			
		Returns:
			True if the first shape is (fully) within the second shape, False otherwise.
	"""
	return getGeoShape(aType, aShape).within(getGeoShape(bType, bShape))


def geoContains(aType:GeometryType, aShape:tuple|list, bType:GeometryType, bShape:tuple|list) -> bool:
	""" Check if a shape contains another shape.

		Args:
			aType: The type of the first shape.
			aShape: The shape of the first shape.	
			bType: The type of the second shape.	
			bShape: The shape of the second shape.	
			
		Returns:
			True if the first shape (fully) contains the second shape, False otherwise.
	"""
	return getGeoShape(aType, aShape).contains(getGeoShape(bType, bShape))


def geoIntersects(aType:GeometryType, aShape:tuple|list, bType:GeometryType, bShape:tuple|list) -> bool:
	""" Check if a shape intersects another shape.

		Args:
			aType: The type of the first shape.
			aShape: The shape of the first shape.	
			bType: The type of the second shape.	
			bShape: The shape of the second shape.	
			
		Returns:
			True if the first shape intersects the second shape, False otherwise.
	"""
	return getGeoShape(aType, aShape).intersects(getGeoShape(bType, bShape))


def getGeoShape(typ:GeometryType, shape:tuple|list) -> BaseGeometry:
	""" Get a shapely geometry object from a geoJSON shape.

		Args:
			typ: The geometry type.
			shape: The geoJSON shape as a tuple or list.

		Returns:
			A shapely geometry object.
	"""
	try:
		match typ:
			case GeometryType.Point:
				return Point(shape)
			case GeometryType.LineString:
				return LineString(shape)
			case GeometryType.Polygon:
				return Polygon(shape)
			case GeometryType.MultiPoint:
				return MultiPoint(shape)
			case GeometryType.MultiLineString:
				return MultiLineString(shape)
			case GeometryType.MultiPolygon:
				# Convert to list to polygons. This is necessary because shapely does not support
				# passing a list of polygons to the MultiPolygon constructor. Those polygons must
				# contain "hole" definitions. So we need to create Polygons first and then
				# pass them to the MultiPolygon constructor. 
				ps:list[Polygon] = []
				for s in shape:
					if not isinstance(s, list):
						raise ValueError(f'Invalid geometry shape: {shape}')
					ps.append(Polygon(s))
				return MultiPolygon(ps)
	except TypeError as e:
		raise ValueError(f'Invalid geometry shape: {shape} ({e})')
