#
#	ACMEUtils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

""" This module provides various utility functions. """

from __future__ import annotations

from typing import Any, Tuple, cast, Optional
import sys, re

from .Constants import Constants
from .Types import ResourceTypes
from .Types import JSON
from .IDUtils import isStructured, isCSERelative, toSPRelative
from ..runtime import CSE
from ..etc.Constants import RuntimeConstants as RC


# Optimize access (fewer look-up)
_attrType = Constants.attrRtype


def isUniqueRI(ri:str) -> bool:
	"""	Test whether a resource ID does not yet exists.
	
		Args:
			ri: Resource ID to check
		Return:
			Boolean indicating the result of the test
	"""
	return not CSE.storage.identifier(ri)


def structuredPathFromRI(ri:str) -> Optional[str]:
	""" Get the structured path of a resource by its ri.
	
		Args:
			ri: Resource ID.
		Return:
			Structured path, or None in case of an error.
	"""
	try:
		return CSE.storage.identifier(ri)[0]['srn']
	except:
		return None


def riFromStructuredPath(srn: str) -> Optional[str]:
	""" Get the resource ID from a resource by its structured path. 
		Makes a lookup to a table in the DB.

		Args:
			srn: structured path.
		Return:
			Resource ID, or None in case of an error.
	"""
	try:
		return CSE.storage.structuredIdentifier(srn)[0]['ri']
	except:
		return None


def srnFromHybrid(srn:str, id:str) -> Tuple[str, str]:
	""" Get the structured part of a hybrid resource ID, including the necessary handling of virtual
		resources in the path.

		Args:
			srn: Structured version of a resource ID. This part will be filled in when ommitted.
			id: Resource ID to check.
		Return:
			Tuple of the (possible new & filled) structured path and the resource ID.
	"""
	if id:
		ids = id.split('/')
		if not srn and len(ids) > 1  and ResourceTypes.isVirtualResourceName(ids[-1]): # Hybrid
			if (srn := structuredPathFromRI('/'.join(ids[:-1]))):
				srn = '/'.join([srn, ids[-1]])
				id = riFromStructuredPath(srn) # id becomes the ri of the fopt
	return srn, id


def getIDFromPath(id:str) -> Tuple[str, str, str, str]:
	""" Split a full path e.g. from a http request into its component and return a CSE local ri .
		Also handle retargeting paths.

		Args:
			id: A resource ID to process. This could be a structured or unstructured, and in CSE-relative, SP-relative or Absolute format.
		Return:
			The return tupple is (RI, CSI of the resource ID, structured path of the ID, debug message or None).
	"""

	if not id:
		return None, None, None, 'ID must not be empty'
	
	csi 		= None
	spi 		= None
	srn 		= None
	ri 			= None
	vrPresent	= None

	# split path
	idsLen = len(ids := id.split('/'))

	# # Test for empty ID
	# if (idsLen := len(ids)) == 0:	# There must be something!
	# 	return None, None, None, 'ID must not be empty'

	# Remove the empty elements in the beginnig of the list (they result from a single "/")
	# and calculate from that the "level", which indicates CSE relative,
	# SP relative or absolute
	lvl = 0
	while not ids[0]:
		ids.pop(0)
		lvl += 1
		idsLen -= 1
	if lvl > 2:						# not more than 2 * / in front
		return None, None, None, 'Too many "/" level'

	# Remove virtual resource shortname if it is present
	if ResourceTypes.isVirtualResourceName(ids[-1]):
		vrPresent = ids.pop()	# remove and return last path element
		idsLen -= 1
	
	match lvl:

		# CSE-Relative (first element is not /)
		case 0:
			if idsLen == 1 and ((ids[0] != RC.cseRn and ids[0] != '-') or ids[0] == RC.cseCsiSlashLess):	# unstructured
				ri = ids[0]
			else:							# structured
				if ids[0] == '-':			# replace placeholder "-". Always convert in CSE-relative
					ids[0] = RC.cseRn
				srn = '/'.join(ids)
			csi = RC.cseCsi

		# SP-Relative (first element is /)
		case 1:
			# L.logDebug("SP-Relative")
			if idsLen < 2:
				return None, None, None, f'ID too short: {id}. Must be /<cseid>/<structured|unstructured>.'
			csi = ids[0]					# extract the csi
			if csi != RC.cseCsiSlashLess:	# Not for this CSE? retargeting
				if vrPresent:				# append last path element again
					ids.append(vrPresent)
				return id, csi, srn, None	# Early return. ri is the (un)structured path
			# replace placeholder "-", convert in CSE-relative when the target is this CSE
			if ids[1] == '-' and ids[0] == RC.cseCsiSlashLess:	
				ids[1] = RC.cseRn
			if ids[1] == RC.cseRn:			# structured
				srn = '/'.join(ids[1:])		# remove the csi part
			elif idsLen == 2:				# unstructured
				ri = ids[1]
			else:
				return None, None, None, 'Too many "/" level'


		# Absolute (2 first elements are /)
		case 2:
			# L.logDebug("Absolute")
			if idsLen < 3:
				return None, None, None, 'ID too short. Must be //<spid>/<cseid>/<structured|unstructured>.'
			spi = ids[0]
			csi = ids[1]
			if spi != RC.cseSpid:			# Check for SP-ID
				return None, None, None, f'SP-ID: {RC.cseSpid} does not match the request\'s target ID SP-ID: {spi}'
			if csi != RC.cseCsiSlashLess:	# Check for CSE-ID
				if vrPresent:				# append virtual last path element again
					ids.append(vrPresent)
				return id, csi, srn, None	# Not for this CSE? retargeting

			# replace placeholder "-", convert in absolute when the target is this CSE
			if ids[2] == '-' and ids[1] == RC.cseCsiSlashLess:	
				ids[2] = RC.cseRn
			if ids[2] == RC.cseRn:			# structured
				srn = '/'.join(ids[2:])
			elif idsLen == 3:				# unstructured
				ri = ids[2]
			else:
				return None, None, None, 'Too many "/" level'

	# Now either csi, ri or structured srn is set
	if ri:
		if vrPresent:
			ri = f'{ri}/{vrPresent}'
		return ri, csi, srn, None
	if srn:
		if vrPresent:
			srn = f'{srn}/{vrPresent}'
		return riFromStructuredPath(srn), csi, srn, None
	if csi:
		return riFromCSI(f'/{csi}'), csi, srn, None
	# TODO do something with spi?
	return None, None, None, 'Unsupported ID'


def riFromCSI(csi:str) -> Optional[str]:
	""" Get the resource ID from any CSEBase or remoteCSE resource by its csi.
	
		Args:
			csi: The CSE-ID to search for.
		Return:
			The resource ID of the resource with the *csi*, or None in case of an error.
	 """
	if not (res := resourceFromCSI(csi)):
		return None
	return cast(str, res.ri)


def compareIDs(id1:str, id2:str) -> bool:
	"""	Compare two resource IDs.

		Both IDs can be either unstructured or structured resource IDs. They match
		if they point to the same resource.

		Args:
			id1: First ID for the comparison.
			id2: Second ID for the comparison
		Return:
			True if both IDs point to the same resource, False otherwise.
	"""

	# Compare two unstrutured IDs
	if not isStructured(id1) and not isStructured(id2):
		ri1 = id1
		ri2 = id2
		if isCSERelative(id1):
			ri1 = toSPRelative(id1)
		if isCSERelative(id2):
			ri2 = toSPRelative(id2)
		return ri1 == ri2

	return riFromID(id1) == riFromID(id2)
	# ri1 = riFromStructuredPath(id1) if isStructured(id1) else id1
	# ri2 = riFromStructuredPath(id2) if isStructured(id2) else id2
	# return ri1 == ri2


def riFromID(id:str) -> str:
	"""	Return the unstructured resource ID from either an unstructured or structured resource ID.

		Args:
			id: Structured or unstructured Resource ID.
		Return:
			Unstructured resource ID.
	"""
	return riFromStructuredPath(id) if isStructured(id) else id


##############################################################################
#
#	Resource and content related
#

_excludeFromRoot = [ 'pi' ]
"""	Attributes that are excluded from the root of a resource tree. """

_pureResourceRegex = re.compile(r'[\w]+:[\w]')
"""	Regular expression to test for a pure resource name. """

def pureResource(dct:JSON) -> Tuple[JSON, str, str]:
	"""	Return the "pure" structure without the "<domain>:xxx" resource type name, and the oneM2M type identifier. 

		Args:
			dct: JSON dictionary with the resource attributes.
		Return:
			Tupple with the inner JSON, the resource type name, and the found key.
			If the resource type name is not in the correct format, eg the domain is missing, it is *None*.
			The third element always contains the found outer attribute name.
	"""
	try:
		rootKeys = list(dct.keys())
		# Try to determine the root identifier 
		if (lrk := len(rootKeys)) == 1 and (rk := rootKeys[0]) not in _excludeFromRoot and re.match(_pureResourceRegex, rk):
			return dct[rootKeys[0]], rootKeys[0], rootKeys[0]
		# Otherwise try to get the root identifier from the resource itself (stored as a private attribute)
		return dct, dct.get(_attrType), rootKeys[0] if lrk > 0 else None
	except Exception:
		raise


def resourceDiff(old:JSON, new:JSON, modifiers:Optional[JSON] = None) -> JSON:
	"""	Compare an old and a new resource. A comparison happens for keywords and values.
		Attributes which names start and end with "__" (ie internal attributes) are ignored.

		Args:
			old: Old resource dictionary to compare.
			new: New resource dictionary to compare.
			modifiers: A dictionary. If this dictionary is given then it contains the changes that let from old to new. This is used to determine if attributes were just updated with the same values.
		Return:	
			Return a dictionary of identified changes.
	"""
	res = {}
	for k, v in new.items():
		if k.startswith('__'):	# ignore all internal attributes
			continue
		if not k in old:		# Key not in old
			res[k] = v
		elif v != old[k]:		# Value different
			res[k] = v
		elif modifiers and k in modifiers:	# this means the attribute is overwritten by the same value. But still modified
			res[k] = v

	# Process deleted attributes. This is necessary since attributes can be
	# explicitly set to None/Nulls.
	for k, v in old.items():
		if k not in new:
			res[k] = None

	return res



def resourceModifiedAttributes(old:JSON, new:JSON, requestPC:JSON, modifiers:Optional[JSON] = None) -> JSON:
	"""	Calculate the difference between an original resource and after it has been updated, and then remove the attributes
		that are part of the update request.

		Args:
			old: Old resource dictionary to compare.
			new: New resource dictionary to compare.
			modifiers: A dictionary. If this dictionary is given then it contains the changes that let from old to new. This is used to determine if attributes were just updated with the same values.
		Return:	
			Return a dictionary of those attributes that have been changed in a CREATE or UPDATE request.	
	"""
	return { k:v for k,v in resourceDiff(old, new, modifiers).items() if k not in requestPC or v != requestPC[k] }


def resourceFromCSI(csi:str) -> Optional[Any]:	# Actual a Resource object
	""" Get A CSEBase resource by its csi. This might be a different <CSEBase> resource then the hosting CSE.

		Args:
			csi: *CSE-ID* of the <CSEBase> resource to retrieve.
		
		Return:
			<CSEBase> resource or None if not found.
	"""
	try:
		return CSE.storage.retrieveResource(csi = csi)
	except Exception as e:
		import traceback
		traceback.print_exc()
		return None


def getAttributeSize(attribute:Any) -> int:
	"""	Return a realistic size for the content of an attribute.
		Python does not really return good sizes for some of the data types.

		Args:
			attribute: An attribute's content of any of the suppported types.
		Return:
			Byte size of the attribute's value.
	"""
	size = 0

	match attribute:
		case str():
			return len(attribute)
		case int():
			return 4
		case float():
			return 8
		case bool():
			return 1
		case list():	# recurse a list
			for e in attribute:
				size += getAttributeSize(e)
			return size
		case dict():	# recurse a dictionary
			for _,v in attribute.items():
				size += getAttributeSize(v)
			return size
		case None:	# e.g. when attribute is not present
			return 0
		case _:		# fallback for not handled types
			return sys.getsizeof(attribute)

