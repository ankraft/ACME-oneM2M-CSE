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

from typing import Any, Callable, Tuple, cast, Optional
import random, string, sys, re, threading, socket
import traceback
from distutils.util import strtobool


from .Constants import Constants
from .Types import ResourceTypes, ResponseStatusCode
from .Types import Result, JSON
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.PCH_PCU import PCH_PCU
from ..services import CSE as CSE


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


def announcedRN(resource:Resource) -> str:
	""" Create the announced resource name for a resource.

		Args:
			resource: The Resource for which to generate the announced resource name
		Return:
			String with the announced resource name
	"""
	return f'{resource.rn}_Annc'


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
def _randomID() -> str:
	""" Generate an ID. Prevent certain patterns in the ID.

		Return:
			String with a random ID
	"""
	while True:
		result = ''.join(random.choices(_randomIDCharSet, k = Constants.maxIDLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID	# TODO really necessary?
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


def isStructured(uri:str) -> bool:
	""" Test whether a URI is in structured format.
	
		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in structured format
	"""
	if isCSERelative(uri):
		return '/' in uri or uri == CSE.cseRn
	elif isSPRelative(uri):
		return uri.count('/') > 2
	elif isAbsolute(uri):
		return uri.count('/') > 4
	return False


def localResourceID(ri:str) -> Optional[str]:
	""" Test whether an ID is a resource ID of the local CSE.
	
		Args:
			ri: A resource ID in CSE-relative, SP-relative, or absolute notation.
		Return:
			If the ID targets a local resource then the CSE-relative form of the resource ID
			is returned, or None otherwise.
	"""
	if isAbsolute(ri):
		if ri.startswith(CSE.cseAbsoluteSlash):
			return ri[len(CSE.cseAbsoluteSlash):]
		return None
	elif isSPRelative(ri):
		if ri.startswith(CSE.cseCsiSlash):
			return ri[len(CSE.cseCsiSlash):]
		return None
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
def isValidCSI(csi:str) -> bool:
	"""	Test for valid CSE-ID format.

		Args:
			csi: The CSE-ID to check
		Return:
			Boolean
	"""
	return re.fullmatch(_csiRx, csi) is not None


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


def structuredPath(resource:Resource) -> Optional[str]:
	""" Determine the structured path of a resource.

		Args:
			resource: The resource for which to get the structured path
		Return:
			Structured path or None
	"""
	rn:str = resource.rn
	if resource.ty == ResourceTypes.CSEBase: # if CSE
		return rn

	# retrieve identifier record of the parent
	if not (pi := resource.pi):
		# L.logErr('PI is None')
		return rn
	if len(rpi := CSE.storage.identifier(pi)) == 1:
		return cast(str, f'{rpi[0]["srn"]}/{rn}')
	# L.logErr(traceback.format_stack())
	L.logErr(f'Parent {pi} not found in DB')
	return rn # fallback


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
	if isSPRelative(id):
		return ids[1], ids
	elif isAbsolute(id):
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
	
	# CSE-Relative (first element is not /)
	if lvl == 0:								
		# L.logDebug("CSE-Relative")
		if idsLen == 1 and ((ids[0] != CSE.cseRn and ids[0] != '-') or ids[0] == CSE.cseCsiSlashLess):	# unstructured
			ri = ids[0]
		else:									# structured
			if ids[0] == '-':					# replace placeholder "-"
				ids[0] = CSE.cseRn
			srn = '/'.join(ids)
	
	# SP-Relative (first element is  /)
	elif lvl == 1:								
		# L.logDebug("SP-Relative")
		if idsLen < 2:
			return None, None, None, 'ID too short. Must be /<cseid>/<structured|unstructured>.'
		csi = ids[0]							# extract the csi
		if csi != CSE.cseCsiSlashLess:			# Not for this CSE? retargeting
			if vrPresent:						# append last path element again
				ids.append(vrPresent)
			return id, csi, srn, None					# Early return. ri is the (un)structured path
		# if idsLen == 1:
		# 	# ri = ids[0]
		# 	return None, None, None, 'ID too short'
		#elif idsLen > 1:
		if ids[1] == '-':						# replace placeholder "-"
			ids[1] = CSE.cseRn
		if ids[1] == CSE.cseRn:					# structured
			srn = '/'.join(ids[1:])				# remove the csi part
		elif idsLen == 2:						# unstructured
			ri = ids[1]
		else:
			return None, None, None, 'Too many "/" level'

	# Absolute (2 first elements are /)
	elif lvl == 2: 								
		# L.logDebug("Absolute")
		if idsLen < 3:
			return None, None, None, 'ID too short. Must be //<spid>/<cseid>/<structured|unstructured>.'
		spi = ids[0]
		csi = ids[1]
		if spi != CSE.cseSpid:					# Check for SP-ID
			return None, None, None, f'SP-ID: {CSE.cseSpid} does not match the request\'s target ID SP-ID: {spi}'
		if csi != CSE.cseCsiSlashLess:			# Check for CSE-ID
			if vrPresent:						# append virtual last path element again
				ids.append(vrPresent)
			return id, csi, srn, None	# Not for this CSE? retargeting
		# if idsLen == 2:
		# 	ri = ids[1]
		# elif idsLen > 2:
		if ids[2] == '-':						# replace placeholder "-"
			ids[2] = CSE.cseRn
		if ids[2] == CSE.cseRn:					# structured
			srn = '/'.join(ids[2:])
		elif idsLen == 3:						# unstructured
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
	if not (res := resourceFromCSI(csi).resource):
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

	ri1 = riFromStructuredPath(id1) if isStructured(id1) else id1
	ri2 = riFromStructuredPath(id2) if isStructured(id2) else id2
	return ri1 == ri2



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
_pureResourceRegex = re.compile('[\w]+:[\w]')

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
	root = None
	if Resource._rtype in dct:
		root = dct[Resource._rtype]
	return dct, root, rootKeys[0] if lrk > 0 else None



_decimalMatch = re.compile(r'{(\d+)}')
def findXPath(dct:JSON, key:str, default:Optional[Any] = None) -> Optional[Any]:
	""" Find a structured *key* in the dictionary *dct*. If *key* does not exists then
		*default* is returned.

		- It is possible to address a specific element in a list. This is done be
			specifying the element as "{n}".

		Example: 
			findXPath(resource, 'm2m:cin/{1}/lbl/{0}')

		- If an element is specified as "{}" then all elements in that list are returned in
			a list.

		Example: 
			findXPath(resource, 'm2m:cin/{1}/lbl/{}') or findXPath(input, 'm2m:cnt/m2m:cin/{}/rn')

		- If an element is specified as "{*}" and is targeting a dictionary then a single unknown key is
			jumped over. This can be used to skip, for example, unknown first elements in a structure. 
			This is similar but not the same as "{0}" that works on lists.

		Example: 
			findXPath(resource, '{*}/rn') 
		
		Args:
			dct: Dictionary to search.
			key: Key with path to an attribute.
			default: Optional return value if *key* is not found in *dct*
		
		Return:
			Any found value for the key path, or *None* resp. the provided *default* value.
	"""

	if not key or not dct:
		return default
	if key in dct:
		return dct[key]

	paths = key.split("/")
	data:Any = dct
	for i in range(0,len(paths)):
		if not data:
			return default
		pathElement = paths[i]
		if len(pathElement) == 0:	# return if there is an empty path element
			return default
		elif (m := _decimalMatch.search(pathElement)) is not None:	# Match array index {i}
			idx = int(m.group(1))
			if not isinstance(data, (list,dict)) or idx >= len(data):	# Check idx within range of list
				return default
			if isinstance(data, dict):
				data = data[list(data)[i]]
			else:
				data = data[idx]

		elif pathElement == '{}':	# Match an array in general
			if not isinstance(data, (list,dict)):	# not a list, return the default
				return default
			if i == len(paths)-1:	# if this is the last element and it is a list then return the data
				return data
			return [ findXPath(d, '/'.join(paths[i+1:]), default) for d in data  ]	# recursively build an array with remnainder of the selector

		elif pathElement == '{*}':
			if isinstance(data, dict):
				if keys := list(data.keys()):
					data = data[keys[0]]
				else:
					return default
			else:
				return default

		elif pathElement not in data:	# if key not in dict
			return default
		else:
			data = data[pathElement]	# found data for the next level down
	return data



def setXPath(dct:JSON, 
			 key:str, 
			 value:Optional[Any] = None, 
			 overwrite:Optional[bool] = True, 
			 delete:Optional[bool] = False) -> bool:
	"""	Set a structured *key* and *value* in the dictionary *dict*.

		Create the attribute if necessary, and observe the *overwrite* option (True overwrites an
		existing key/value).

		When the *delete* argument is set to *True* then the *key* attribute is deleted from the dictionary.

		Examples:
			setXPath(aDict, 'a/b/c', 'aValue)

			setXPath(aDict, 'a/{2}/c', 'aValue)

		Args:
			dct: A dictionary in which to set or add the *key* and *value*.
			key: The attribute's name to set in *dct*. This could by a path in *dct*, where the separator is a slash character (/). To address an element in a list, one can use the *{n}* operator in the path.
			value: The value to set for the attribute. Could be left out when deleting an attribute or value.
			overwrite: If True that overwrite an already existing value, otherwise skip.
			delete: If True then remove the atribute or list attribute *key* from the dictionary.
		
		Retun:
			Boolean indicating the success of the operation.
	"""

	paths = key.split("/")
	ln1 = len(paths)-1
	data = dct
	if ln1 > 0:	# Small optimization. don't check if there is no extended path
		for i in range(0, ln1):
			_p = paths[i]
			if isinstance(data, list):
				if (m := _decimalMatch.search(_p)) is not None:
					data = data[int(m.group(1))]
			else:
				if _p not in data:
					data[_p] = {}
				data = data[_p]
	if isinstance(data, list):
		if (m := _decimalMatch.search(paths[ln1])) is not None:
			idx = int(m.group(1))
			if not overwrite and idx < len(data): # test overwrite first, it's faster
				return True # don't overwrite
			if delete :
				if idx < len(data):
					del data[idx]
				return True
			else:
				data[idx] = value
			return True
		return False
	else:
		if not overwrite and paths[ln1] in data: # test overwrite first, it's faster
			return True # don't overwrite
		if delete:
			del data[paths[ln1]]
			return True
		data[paths[ln1]] = value
	return True


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


def getCSE() -> Result:
	"""	Return the <CSEBase> resource.

		Return:
			<CSEBase> resource.
	"""
	#return CSE.dispatcher.retrieveResource(CSE.cseRi)
	return resourceFromCSI(CSE.cseCsi)


def resourceFromCSI(csi:str) -> Result:
	""" Get A CSEBase resource by its csi. This might be a different <CSEBase> resource then the hosting CSE.

		Args:
			csi: *CSE-ID* of the <CSEBase> resource to retrieve.
		Return:
			<CSEBase> resource.
	"""
	return CSE.storage.retrieveResource(csi = csi)

	
def fanoutPointResource(id:str) -> Optional[Resource]:
	"""	Check whether the target resource contains a fanoutPoint along its path is a fanoutPoint.

		Args:
			id: the target's resource ID.
		Return:
			Return either the virtual fanoutPoint resource, or None in case of an error.
	"""
	# Convert to srn
	if not isStructured(id):
		if not (id := structuredPathFromRI(id)):
			return None
	# from here on id is a srn
	nid = None
	if id.endswith('/fopt'):
		nid = id
	else:
		(head, found, _) = id.partition('/fopt/')
		if found:
			nid = head + '/fopt'

	if nid and (result := CSE.dispatcher.retrieveResource(nid)).resource:
		return cast(Resource, result.resource)
	return None


def pollingChannelURIResource(id:str) -> Optional[PCH_PCU]:
	"""	Check whether the target is a PollingChannelURI resource and return it.

		Args:
			id: Target resource ID
		Return:
			Return either the virtual PollingChannelURI resource or None.
	"""
	if not id:
		return None
	if id.endswith('pcu'):
		# Convert to srn
		if not isStructured(id):
			if not (id := structuredPathFromRI(id)):
				return None
		if (result := CSE.dispatcher.retrieveResource(id)).resource and result.resource.ty == ResourceTypes.PCH_PCU:
			return cast(PCH_PCU, result.resource)
		# Fallthrough
	return None


def latestOldestResource(id:str) -> Optional[Resource]:
	"""	Check whether the target is a latest or oldest virtual resource and return it.

		Args:
			id: Target resource ID
		Return:
			Return either the virtual resource, or None in case of an error.
	"""
	if not id:
		return None
	if id.endswith(('la', 'ol')):
		# Convert to srn
		if not isStructured(id):
			if not (id := structuredPathFromRI(id)):
				return None
		if (result := CSE.dispatcher.retrieveResource(id)).resource and ResourceTypes.isLatestOldestResource(result.resource.ty):
			return result.resource
		# Fallthrough
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
	if isinstance(attribute, str):
		size = len(attribute)
	elif isinstance(attribute, int):
		size = 4
	elif isinstance(attribute, float):
		size = 8
	elif isinstance(attribute, bool):
		size = 1
	elif isinstance(attribute, list):	# recurse a list
		for e in attribute:
			size += getAttributeSize(e)
	elif isinstance(attribute, dict):	# recurse a dictionary
		for _,v in attribute:
			size += getAttributeSize(v)
	else:
		size = sys.getsizeof(attribute)	# fallback for not handled types
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

def renameThread(name:Optional[str] = None,
				 thread:Optional[threading.Thread] = None,
				 prefix:Optional[str] = None) -> None:
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
#	Network


def getIPAddress(hostname:Optional[str] = None) -> str:
	"""	Lookup and return the IP address for a host name.
	
		Args:
			hostname: The host name to look-up. If none is given, the own host name is tried.
		Return:
			IP address, or 127.0.0.1 as a last resort. *None* is returned in case of an error.
	"""
	if not hostname:
		hostname = socket.gethostname()
	
	try:
		ip = socket.gethostbyname(hostname)

		#	Try to resolve a local address. For example, sometimes raspbian
		#	need to add a 'local' ir 'lan' postfix, depending on the local 
		#	device configuration
		if ip.startswith('127.'):	# All local host addresses
			for ext in ['.local', '.lan']:
				try:
					ip = socket.gethostbyname(hostname + ext)
				except:
					pass
		return ip
	except Exception:
		return ''

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
	return Result(rsc = ResponseStatusCode.internalServerError, dbg = f'encountered exception: {tbs}')



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
