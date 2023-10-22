#
#	Utils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

""" This module provides various utility functions. """

from __future__ import annotations

from typing import Any, Callable, Tuple, cast, Optional, Generator
import random, string, sys, re, threading
import traceback
from distutils.util import strtobool


from .Constants import Constants
from .Types import ResourceTypes, ResponseStatusCode
from .Types import Result, JSON
from ..services.Logging import Logging as L
from ..services import CSE as CSE

# Optimize access (fewer look-up)
_maxIDLength = Constants.maxIDLength
_attrType = Constants.attrRtype

##############################################################################
#
#	Identifier and path related
#

def uniqueRI(prefix:Optional[str] = '') -> str:
	"""	Generate a unique resource ID. Beside a random number it
		can have a prefix.
		
		Args:
			prefix: Prefix for the ID
		Return:
			String with the new ID
	"""
	return f'{noNamespace(prefix)}{uniqueID()}'


def uniqueID() -> str:
	"""	Generate a unique ID. This is for the moment just a large random number.
		NO check for uniqueness is done.
		
		Return:
			String with the identifier
	"""
	return str(random.randint(1,sys.maxsize))


def isUniqueRI(ri:str) -> bool:
	"""	Test whether a resource ID does not yet exists.
	
		Args:
			ri: Resource ID to check
		Return:
			Boolean indicating the result of the test
	"""
	return not CSE.storage.identifier(ri)


def uniqueRN(prefix:str) -> str:
	"""	Generate a unique resource name. A resource name has a prefix and 
		a random alpha-numeric string.

		Args:
			prefix: String prefix. If it contains a domain then that is removed
		Return:
			String with the resource name

	"""
	return f'{noNamespace(prefix)}_{_randomID()}'


# create a unique aei, M2M-SP type
def uniqueAEI(prefix:Optional[str] = 'S') -> str:
	"""	Create a new AE ID. An AE ID must always start with either "S" or "C".
	
		Args:
			prefix: "S" or "C"
		Return:
			String with the AE ID
	"""
	return f'{prefix}{_randomID()}'


def noNamespace(id:str) -> str:
	"""	Remove the namespace part of an identifier and return the remainder.

		Example: 
			'm2m:cnt' -> 'cnt'
		
		Args:
			id: String with the identifier. May be prefixed with a domain.
		Return:
			String that only contains the ID
	"""
	_, found, tail = id.partition(':')
	return tail if found else id


_randomIDCharSet = string.ascii_uppercase + string.digits + string.ascii_lowercase
"""	Character set for random IDs. """

def _randomID() -> str:
	""" Generate an ID. Prevent certain patterns in the ID.

		Return:
			String with a random ID
	"""
	while True:
		result = ''.join(random.choices(_randomIDCharSet, k = _maxIDLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID
			return result


def isSPRelative(uri:str) -> bool:
	""" Test whether a URI is SP-Relative. 

		Args:
			uri: The URI to check
		Return:
			Boolean
	"""
	return uri is not None and len(uri) >= 2 and uri[0] == '/' and uri [1] != '/'


def isAbsolute(uri:str) -> bool:
	""" Test whether a URI is in absolute format.
	
		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in absolute format
	"""
	return uri is not None and uri.startswith('//')


def isCSERelative(uri:str) -> bool:
	""" Test whether a URI is in CSE-relative format.

		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in CSE-relative format
	"""
	return uri is not None and not uri.startswith('/')


def isStructured(uri:str) -> bool: # type: ignore[return]
	""" Test whether a URI is in structured format.
	
		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in structured format
	"""
	match uri:
		case x if isCSERelative(uri):
			return '/' in uri or uri == CSE.cseRn
		case x if isSPRelative(uri):
			return uri.count('/') > 2
		case x if isAbsolute(uri):
			return uri.count('/') > 4
		case _:
			return False


def localResourceID(ri:str) -> Optional[str]: # type: ignore[return]
	""" Test whether an ID is a resource ID of the local CSE.
	
		Args:
			ri: A resource ID in CSE-relative, SP-relative, or absolute notation.
		Return:
			If the ID targets a local resource then the CSE-relative form of the resource ID
			is returned, or None otherwise.
	"""
	
	def _checkDash(ri:str) -> str:
		"""	Handle the special case of '-'.

			Args:
				ri: The resource ID to check
			
			Return:
				The resource ID with the special case handled.
		"""
		if ri.startswith('-/'):
			return f'{CSE.cseRn}{ri[1:]}'
		if ri == '-':
			return CSE.cseRn
		return ri


	if ri == CSE.cseCsi:
		return CSE.cseRn
	
	match ri:
		case x if isAbsolute(x):
			if ri.startswith(CSE.cseAbsoluteSlash):
				return _checkDash(ri[len(CSE.cseAbsoluteSlash):])
			return None
		case x if isSPRelative(x):
			if ri.startswith(CSE.cseCsiSlash):
				return _checkDash(ri[len(CSE.cseCsiSlash):])
			return None
		case _:
			return ri


def isValidID(id:str, allowEmpty:Optional[bool] = False) -> bool:
	""" Test for a valid ID. 

		Args:
			id: The ID to check
			allowEmpty: Indicate whether an ID can be empty.
		Returns:
			Boolean
	"""
	if allowEmpty:
		return id is not None and '/' not in id	# pi might be ""
	return id is not None and len(id) > 0 and hasOnlyUnreserved(id)


_unreserved = re.compile(r'^[\w\-.~]*$')
"""	Regular expression to test for unreserved characters. """

def hasOnlyUnreserved(id:str) -> bool:
	"""	Test that an ID only contains characters from the unreserved character set of 
		RFC 3986.
		
		Args:
			id: the ID to check.
		Returns:
			Boolean
	"""
	return re.match(_unreserved, id) is not None


_csiRx = re.compile('^/[^/\s]+') # Must start with a / and must not contain a further / or white space
"""	Regular expression to test for valid CSE-ID format. """

def isValidCSI(csi:str) -> bool:
	"""	Test for valid CSE-ID format.

		Args:
			csi: The CSE-ID to check
		Return:
			Boolean
	"""
	return re.fullmatch(_csiRx, csi) is not None


_aeRx = re.compile('^[^/\s]+') # Must not start with a / and must not contain a further / or white space
"""	Regular expression to test for valid AE-ID format. """

def isValidAEI(aei:str) -> bool:
	"""	Test for valid AE-ID format. 

		It takes SP-Relative AEI's into account.

		Args:
			aei: The AE-ID to check
		Return:
			Boolean
	"""
	if isSPRelative(aei):
		ids = aei.split('/')
		aei = ids[-1]

	return re.fullmatch(_aeRx, aei) is not None


def csiFromSPRelative(ri:str) -> Optional[str]:
	"""	Return the csi from a SP-relative resource ID. It is assumed that
		the passed *ri* is in SP-relative format.
		
		Args:
			ri: A SP-relative resource ID
		Return:
			The csi of the resource ID, or None
	"""
	ids = ri.split('/')
	# return f'/{ids[0]}' if len(ids) > 0 else None
	return f'/{ids[1]}' if len(ids) > 1 else None


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


def csiFromRelativeAbsoluteUnstructured(id:str) -> Tuple[str, list[str]]:
	"""	Get the csi from an unstructured CSE-relative, SP-relative, or
		absolute ID.
		
		Args:
			id: unstructured ID.
		Return:
			Tuple (CSE ID (no leading slashes) without any SP-ID or CSE-ID, list of path elements)
		"""
	ids = id.split('/')
	match id:
		case x if isSPRelative(x):
			return ids[1], ids
		case x if isAbsolute(x):
			return ids[3], ids
	return id, ids


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


def retrieveIDFromPath(id:str) -> Tuple[str, str, str, str]:
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
			if idsLen == 1 and ((ids[0] != CSE.cseRn and ids[0] != '-') or ids[0] == CSE.cseCsiSlashLess):	# unstructured
				ri = ids[0]
			else:							# structured
				if ids[0] == '-':			# replace placeholder "-". Always convert in CSE-relative
					ids[0] = CSE.cseRn
				srn = '/'.join(ids)

		# SP-Relative (first element is /)
		case 1:
			# L.logDebug("SP-Relative")
			if idsLen < 2:
				return None, None, None, f'ID too short: {id}. Must be /<cseid>/<structured|unstructured>.'
			csi = ids[0]					# extract the csi
			if csi != CSE.cseCsiSlashLess:	# Not for this CSE? retargeting
				if vrPresent:				# append last path element again
					ids.append(vrPresent)
				return id, csi, srn, None	# Early return. ri is the (un)structured path
		
			# replace placeholder "-", convert in CSE-relative when the target is this CSE
			if ids[1] == '-' and ids[0] == CSE.cseCsiSlashLess:	
				ids[1] = CSE.cseRn
			if ids[1] == CSE.cseRn:			# structured
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
			if spi != CSE.cseSpid:			# Check for SP-ID
				return None, None, None, f'SP-ID: {CSE.cseSpid} does not match the request\'s target ID SP-ID: {spi}'
			if csi != CSE.cseCsiSlashLess:	# Check for CSE-ID
				if vrPresent:				# append virtual last path element again
					ids.append(vrPresent)
				return id, csi, srn, None	# Not for this CSE? retargeting

			# replace placeholder "-", convert in absolute when the target is this CSE
			if ids[2] == '-' and ids[1] == CSE.cseCsiSlashLess:	
				ids[2] = CSE.cseRn
			if ids[2] == CSE.cseRn:			# structured
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


def getIdFromOriginator(originator: str, idOnly:Optional[bool] = False) -> str:
	""" Get AE-ID-Stem or CSE-ID from the originator (in case SP-relative or Absolute was used).

		Args:
			originator: An originator.
			idOnly: Indicator that only the CSE-local resource ID is provided.
		Returns:
			Resource ID.
	"""
	if idOnly:
		return originator.split("/")[-1] if originator else originator
	else:
		return originator.split("/")[-1] if originator and originator.startswith('/') else originator


def toSPRelative(originator:str) -> str:
	"""	Add the CSI to an originator (if not already present).

		Args:
			originator: A string with the originator to convert.
		Return:
			A string in the format */<csi>/<originato>*.
	"""
	if not isSPRelative(originator):
		return  f'{CSE.cseCsi}/{originator}'
	return originator


def toCSERelative(id:str) -> str:
	"""	Convert an id to CSE-Relative format.

		Args:
			id: 	An ID in SP-relative or absolute format.
		Return:
			An ID in CSE-Relative format.
	"""
	_e = id.split('/')
	if isSPRelative(id):
		return '/'.join(_e[2:])
	elif isAbsolute(id):
		return '/'.join(_e[3:])
	return id


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
#	URL and Addressung related
#
_urlregex = re.compile(
		r'^(?:http|ftp|mqtt)s?://|^(?:coap|acme)://' 	# http://, https://, ftp://, ftps://, coap://, mqtt://, mqtts://
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
		r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9]))|' # localhost or single name w/o domain
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 		# ipv4
		r'(?::\d+)?' 								# optional port
		r'(?:/?|[/?]\S+)$', re.IGNORECASE			# optional path

		# Alternative version of the last line: match everything for the path and also remove the IGNORECASE
		# r'\S+' # re.IGNORECASE		 			# optional path

		)
"""	Regular expression to test for a valid URL. """

def isURL(url:str) -> bool:
	""" Check whether a given string is a URL. 

		Args:
			url: String to check for URL-ness.
		Return:
			Boolean indicating whether the argument is a valid URL.
	"""
	return isinstance(url, str) and re.match(_urlregex, url) is not None


def isHttpUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL, and indicates an http or https scheme.

		Args:
			url: String to check.
		Returns:
			True if the argument is a URL, and is an http or https scheme.
	"""
	return isURL(url) and url.startswith(('http', 'https'))


def isMQTTUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL, and indicates an mqtt URL. 

		Args:
			url: String to check.
		Returns:
			True if the argument is a URL, and is an mqtt or mqtts scheme.
	"""
	return isURL(url) and url.startswith(('mqtt', 'mqtts'))


def isAcmeUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL and an internal ACME event URL. 

		Args:
			url: URL to check.
		Returns:
			True if the argument is a URL, and is an internal ACME scheme.
	"""
	return isURL(url) and url.startswith('acme')


def normalizeURL(url:str) -> str:
	""" Remove trailing / from a url. 

		Args:
			url: URL to remove trailing /'s from.
		Returns:
			URL without trailing /'s.
	"""
	if url:
		while len(url) > 0 and url[-1] == '/':
			url = url[:-1]
	return url


##############################################################################
#
#	Resource and content related
#

_excludeFromRoot = [ 'pi' ]
"""	Attributes that are excluded from the root of a resource tree. """

_pureResourceRegex = re.compile('[\w]+:[\w]')
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
	rootKeys = list(dct.keys())
	# Try to determine the root identifier 
	if (lrk := len(rootKeys)) == 1 and (rk := rootKeys[0]) not in _excludeFromRoot and re.match(_pureResourceRegex, rk):
		return dct[rootKeys[0]], rootKeys[0], rootKeys[0]
	# Otherwise try to get the root identifier from the resource itself (stored as a private attribute)
	return dct, dct.get(_attrType), rootKeys[0] if lrk > 0 else None


# def removeKeyFromDict(jsn:dict, keys:list[str]) -> Any:
# 	"""	Recursively remove all occurences of *keys* from a dictionary *dct*.
# 	"""
# 	if not isinstance(jsn, dict):
# 		return jsn
# 	return {key:value for key, value in ((key, removeKeyFromDict(value, keys)) for key, value in jsn.items()) if key not in keys}
#
#
# def removeNoneValuesFromDict(jsn:JSON, allowedNull:list[str]=[]) -> JSON:
# 	"""	Recursively remove Null-values from a dictionary, but ignore the ones speciefed in the `allowedNull` list.
# 		Return a new dictionary.
# 	"""
# 	if not isinstance(jsn, dict):
# 		return jsn
# 	return { key:value for key,value in ((key, removeNoneValuesFromDict(value)) for key,value in jsn.items()) if value is not None or key in allowedNull }

def removeNoneValuesFromDict(jsn:JSON, allowedNull:Optional[list[str]] = []) -> JSON:
	"""	Remove Null/None-values from a dictionary, but ignore the ones specified in *allowedNull*.

		Args:
			jsn: JSON dictionary.
			allowedNull: Optional list of attribute names to ignore.
		Return:
			Return a new dictionary with None-value attributes removed.
	"""
	if not isinstance(jsn, dict):
		return jsn
	return { key:value for key,value in ((key, removeNoneValuesFromDict(value)) for key,value in jsn.items()) if value is not None or key in allowedNull }



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


def filterAttributes(dct:JSON, attributesToInclude:JSON) -> JSON:
	"""	Filter a dictionary by a list of attributes to include.
	
		Args:
			dct: Dictionary to filter.
			attributesToInclude: List of attributes to include.
			
		Return:
			Filtered dictionary.
	"""
	return { k: v 
			 for k, v in dct.items() 
			 if k in attributesToInclude }
			 

def resourceFromCSI(csi:str) -> Any:	# Actual a Resource object
	""" Get A CSEBase resource by its csi. This might be a different <CSEBase> resource then the hosting CSE.

		Args:
			csi: *CSE-ID* of the <CSEBase> resource to retrieve.
		
		Return:
			<CSEBase> resource.
	"""
	return CSE.storage.retrieveResource(csi = csi)


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
			size = len(attribute)
		case int():
			size = 4
		case float():
			size = 8
		case bool():
			size = 1
		case list():	# recurse a list
			for e in attribute:
				size += getAttributeSize(e)
		case dict():	# recurse a dictionary
			for _,v in attribute.items():
				size += getAttributeSize(v)
		case _:		# fallback for not handled types
			size = sys.getsizeof(attribute)

	return size
	

def strToBool(value:str) -> bool:
	"""	Convert a string value to a boolean.
	
		Args:
			value: Any string value that looks like a boolean *true* or *false*.
		Return:
			The boolean value.
	"""
	return bool(strtobool(str(value)))


##############################################################################
#
#	Threads
#

def renameThread(prefix:Optional[str] = None,
				 name:Optional[str] = None,
				 thread:Optional[threading.Thread] = None) -> None:
	"""	Rename a thread.

		If *name* is provided then the thread is renamed to that name.
		If *name* is not provided, but *prefix* is, then the thread is renamed to the prefix + its thread ID.
		If neither *name* nor *prefix* is provided, then the thread is renamed to its own ID.
	
		Args:
			name: New name for a thread. 
			thread: The Thread to rename. If none is provided then the current thread is renamed.
			prefix: Used for "prefix + ID" procedure explained above.
		"""
	thread = threading.current_thread() if not thread else thread
	if name is not None:
		thread.name = name 
	elif prefix is not None:
		thread.name = f'{prefix}_{thread.native_id}'
	else:
		thread.name = str(thread.native_id)


def runAsThread(task:Callable, *args:Any, **kwargs:Any) -> None:
	"""	Helper function to run a function as a thread.

		Args:
			task: Function to run in a thread.
			args: Positional function arguments for *task*.
			kwargs: Keyword function arguments for *task*.
	"""
	thread = threading.Thread(target = task, args = args, kwargs = kwargs)
	thread.setDaemon(True)		# Make the thread a daemon of the main thread
	thread.start()
	thread.name = str(thread.native_id)



##############################################################################
#
#	Various

def exceptionToResult(e:Exception) -> Result:
	"""	Transform a Python exception to a result.
	
		Args:
			e: Exception
		Return:
			Result object, with "rsc" set to internal server error, and "dbg" to the exception message.
	"""
	tb = traceback.format_exc()
	L.logErr(tb, exc=e)
	tbs = tb.replace('"', '\\"').replace('\n', '\\n')
	return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, dbg = f'encountered exception: {tbs}')



def runsInIPython() -> bool:
	"""	Check whether the current runtime environment is IPython or not.

		This is a hack!

		Return:
			True if run in IPython, otherwise False.
	"""
	import traceback
	for each in traceback.extract_stack():
		if each.filename.startswith('<ipython'):
			return True
	return False


def reverseEnumerate(data:list) -> Generator[Tuple[int, Any], None, None]:
	"""	Reverse enumerate a list.

		Args:
			data: List to enumerate.
		Return:
			Generator that yields a tuple with the index and the value of the list.
	"""
	for i in range(len(data)-1, -1, -1):
		yield (i, data[i])