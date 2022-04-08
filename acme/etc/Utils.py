#
#	Utils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

from __future__ import annotations
import random, string, sys, re, threading
import traceback
from typing import Any, Callable, Tuple, cast

from .Constants import Constants as C
from .Types import ResourceTypes as T, ResponseStatusCode
from .Types import Result, JSON
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.PCH_PCU import PCH_PCU
from ..services import CSE as CSE


##############################################################################
#
#	Identifier and path related
#

def uniqueRI(prefix:str = '') -> str:
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
def uniqueAEI(prefix:str = 'S') -> str:
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
		result = ''.join(random.choices(_randomIDCharSet, k = C.maxIDLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID	# TODO really necessary?
			return result


def spRelRI(ri:str) -> str:
	"""	Return a SP-relative resource ID for a resource ID.
	
		Args:
			ri: Resource ID
		Return:
			The SP-relative form of the provided resource ID
	"""
	return f'{CSE.cseCsi}/{ri}'


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


def isValidID(id:str, allowEmpty:bool = False) -> bool:
	""" Test for a valid ID. 

		Args:
			id: The ID to check
			allowedEmpty: Indicate whether an ID can be empty.
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


csiRx = re.compile('^/[^/\s]+') # Must start with a / and must not contain a further / or white space
def isValidCSI(csi:str) -> bool:
	"""	Test for valid CSE-ID format.

		Args:
			csi: The CSE-ID to check
		Return:
			Boolean
	"""
	return re.fullmatch(csiRx, csi) is not None


def csiFromSPRelative(ri:str) -> str:
	"""	Return the csi from a SP-relative resource ID. It is assumed that
		the passed `ri` is in SP-relative format.
		
		Args:
			ri: A SP-relative resource ID
		Return:
			The csi of the resource ID, or None
	"""
	ids = ri.split('/')
	# return f'/{ids[0]}' if len(ids) > 0 else None
	return f'/{ids[1]}' if len(ids) > 1 else None


def structuredPath(resource:Resource) -> str:
	""" Determine the structured path of a resource.

		Args:
			resource: The resource for which to get the structured path
		Return:
			Structured path or None
	"""
	rn:str = resource.rn
	if resource.ty == T.CSEBase: # if CSE
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


def structuredPathFromRI(ri:str) -> str:
	""" Get the structured path of a resource by its ri.
	
		Args:
			ri: Resource ID
		Return:
			Structured path
	"""
	try:
		return CSE.storage.identifier(ri)[0]['srn']
	except:
		return None


def riFromStructuredPath(srn: str) -> str:
	""" Get the resource ID from a resource by its structured path. 
		Makes a lookup to a table in the DB.

		Args:
			srn: structured path
		Return:
			Resource ID
	"""
	try:
		return CSE.storage.structuredIdentifier(srn)[0]['ri']
	except:
		return None


def srnFromHybrid(srn:str, id:str) -> Tuple[str, str]:
	""" Handle Hybrid ID. """
	if id:
		ids = id.split('/')
		if not srn and len(ids) > 1  and T.isVirtualResourceName(ids[-1]): # Hybrid
			if (srn := structuredPathFromRI('/'.join(ids[:-1]))):
				srn = '/'.join([srn, ids[-1]])
				id = riFromStructuredPath(srn) # id becomes the ri of the fopt
	return srn, id


def retrieveIDFromPath(id:str, csern:str, csecsi:str, SPID:str) -> Tuple[str, str, str, str]:
	""" Split a full path e.g. from a http request into its component and return a local ri .
		Also handle retargeting paths.
		The return tupple is (RI, CSI, SRN, debug message).
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
	csecsi = csecsi[1:]	# remove leading / from csi for our comparisons here

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
	if T.isVirtualResourceName(ids[-1]):
		vrPresent = ids.pop()	# remove and return last path element
		idsLen -= 1
	
	# CSE-Relative (first element is not /)
	if lvl == 0:								
		# L.logDebug("CSE-Relative")
		if idsLen == 1 and ((ids[0] != csern and ids[0] != '-') or ids[0] == csecsi):	# unstructured
			ri = ids[0]
		else:									# structured
			if ids[0] == '-':					# replace placeholder "-"
				ids[0] = csern
			srn = '/'.join(ids)
	
	# SP-Relative (first element is  /)
	elif lvl == 1:								
		# L.logDebug("SP-Relative")
		if idsLen < 1:
			return None, None, None, 'ID too short'
		csi = ids[0]							# extract the csi
		if csi != csecsi:						# Not for this CSE? retargeting
			if vrPresent:						# append last path element again
				ids.append(vrPresent)
			return id, csi, srn, None					# Early return. ri is the (un)structured path
		if idsLen == 1:
			ri = ids[0]
		elif idsLen > 1:
			if ids[1] == '-':						# replace placeholder "-"
				ids[1] = csern
			if ids[1] == csern:						# structured
				srn = '/'.join(ids[1:])				# remove the csi part
			elif idsLen == 2:						# unstructured
				ri = ids[1]
			else:
				return None, None, None, 'Too many "/" level'

	# Absolute (2 first elements are /)
	elif lvl == 2: 								
		# L.logDebug("Absolute")
		if idsLen < 2:
			return None, None, None, 'ID too short'
		spi = ids[0]
		csi = ids[1]
		if spi != SPID:							# Check for SP-ID
			return None, None, None, f'SP-ID: {SPID} does not match the request\'s target ID SP-ID: {spi}'
		if csi != csecsi:						# Check for CSE-ID
			if vrPresent:						# append virtual last path element again
				ids.append(vrPresent)
			return id, csi, srn, None	# Not for this CSE? retargeting
		if idsLen == 2:
			ri = ids[1]
		elif idsLen > 2:
			if ids[2] == '-':						# replace placeholder "-"
				ids[2] = csern
			if ids[2] == csern:						# structured
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


def riFromCSI(csi:str) -> str:
	""" Get the resource ID from any CSEBase or remoteCSE resource by its csi.
	
		Args:
			csi: The CSE-ID to search for
		Return:
			The resource ID of the resource with the `csi`, or None
	 """
	if not (res := resourceFromCSI(csi).resource):
		return None
	return cast(str, res.ri)


def getIdFromOriginator(originator: str, idOnly: bool = False) -> str:
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
			An originator.
		Return:
			A string in the format */<csi>/<originator*.
	"""
	if not isSPRelative(originator):
		return  f'{CSE.cseCsi}/{originator}'
	return originator


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
	ri1 = riFromStructuredPath(id1) if isStructured(id1) else id1
	ri2 = riFromStructuredPath(id2) if isStructured(id2) else id2
	return ri1 == ri2



##############################################################################
#
#	URL and Addressung related
#
urlregex = re.compile(
		r'^(?:http|ftp|mqtt)s?://|^(?:coap)://' 	# http://, https://, ftp://, ftps://, coap://, mqtt://, mqtts://
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
		r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9]))|' # localhost or single name w/o domain
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 		# ipv4
		r'(?::\d+)?' 								# optional port
		r'(?:/?|[/?]\S+)$', re.IGNORECASE			# optional path

		# Alternative version of the last line: match everything for the path and also remove the IGNORECASE
		# r'\S+' # re.IGNORECASE		 			# optional path

		)
def isURL(url: str) -> bool:
	""" Check whether a given string is a URL. """
	return url is not None and isinstance(url, str) and re.match(urlregex, url) is not None


def isHttpUrl(url:str) -> bool:
	"""	Test whether a URL is a http URL. 

		Args:
			url: URL to check
		Returns:
			Boolean True or False
	"""
	return url.startswith(('http', 'https'))


def isMQTTUrl(url:str) -> bool:
	"""	Test whether a URL is an mqtt URL. 

		Args:
			url: URL to check
		Returns:
			Boolean True or False
	"""
	return url.startswith(('mqtt', 'mqtts'))


def isAcmeUrl(url:str) -> bool:
	"""	Test whether a URL is an internal ACME event URL. 

		Args:
			url: URL to check
		Returns:
			Boolean True or False
	"""
	return url.startswith('acme')


def normalizeURL(url: str) -> str:
	""" Remove trailing / from the url. """
	if url:
		while len(url) > 0 and url[-1] == '/':
			url = url[:-1]
	return url


##############################################################################
#
#	Resource and content related
#

mgmtObjTPEs = 		[	T.FWR.tpe(), T.SWR.tpe(), T.MEM.tpe(), T.ANI.tpe(), T.ANDI.tpe(),
						T.BAT.tpe(), T.DVI.tpe(), T.DVC.tpe(), T.RBO.tpe(), T.EVL.tpe(),
			  		]

mgmtObjAnncTPEs = 	[	T.FWRAnnc.tpe(), T.SWRAnnc.tpe(), T.MEMAnnc.tpe(), T.ANIAnnc.tpe(),
						T.ANDIAnnc.tpe(), T.BATAnnc.tpe(), T.DVIAnnc.tpe(), T.DVCAnnc.tpe(),
						T.RBOAnnc.tpe(), T.EVLAnnc.tpe(),
			  		]


excludeFromRoot = [ 'pi' ]
pureResourceRegex = re.compile('[\w]+:[\w]')

def pureResource(dct:JSON) -> Tuple[JSON, str]:
	"""	Return the "pure" structure without "<domain>:xxx" resource specifier, and the oneM2M type identifier. 

		Args:
			dct: JSON dictionary with the resource attributes
		Return:
			Tupple with the inner JSON and the tpe
	"""
	rootKeys = list(dct.keys())
	# Try to determine the root identifier 
	if len(rootKeys) == 1 and (rk := rootKeys[0]) not in excludeFromRoot and re.match(pureResourceRegex, rk):
		return dct[rootKeys[0]], rootKeys[0]
	# Otherwise try to get the root identifier from the resource itself (stored as a private attribute)
	root = None
	if Resource._rtype in dct:
		root = dct[Resource._rtype]
	return dct, root


def deleteNoneValuesFromDict(dct:JSON, allowedNull:list[str]=[]) -> JSON:
	"""	Remove Null-values from a dictionary, but ignore the ones speciefed in 'allowedNull.
		Return a new dictionary.
	"""
	if not isinstance(dct, dict):
		return dct
	return { key:value for key,value in ((key, deleteNoneValuesFromDict(value)) for key,value in dct.items()) if value is not None or key in allowedNull }


decimalMatch = re.compile(r'{(\d+)}')
def findXPath(dct:JSON, key:str, default:Any=None) -> Any:
	""" Find a structured `key` in the dictionary `dct`. If `key` does not exists then
		`default` is returned.

		- It is possible to address a specific element in an array. This is done be
		specifying the element as `{n}`.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{0}')

		- If an element is specified as `{}` then all elements in that array are returned in
		an array.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{}') or findXPath(input, 'm2m:cnt/m2m:cin/{}/rn')

		- If an element is specified as `{_}` and is targeting a dictionary then a single random path is chosen.
		This can be used to skip, for example, unknown first elements in a structure.

		Example: findXPath(resource, '{_}/rn') 

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
		elif (m := decimalMatch.search(pathElement)) is not None:	# Match array index {i}
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

		elif pathElement == '{_}':
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


def setXPath(dct:JSON, key:str, value:Any, overwrite:bool=True) -> bool:
	"""	Set a structured `key` and `value` in the dictionary `dict`. 
		Create if necessary, and observe the `overwrite` option (True overwrites an
		existing key/value).
	"""
	paths = key.split("/")
	ln1 = len(paths)-1
	data = dct
	if ln1 > 0:	# Small optimization. don't check if there is no extended path
		for i in range(0, ln1):
			if (_p := paths[i]) not in data:
				data[_p] = {}
			data = data[_p]
	# if not isinstance(data, dict):
	# 	return False
	if not overwrite and paths[ln1] in data: # test overwrite first, it's faster
		return True # don't overwrite
	data[paths[ln1]] = value
	return True


def removeKeyFromDict(dct:dict, keys:list[str]) -> Any:
	"""	Recursively remove all occurences of `keys` from a dictionary `dct`.
	"""
	if not isinstance(dct, dict):
		return dct
	return {key:value for key, value in ((key, removeKeyFromDict(value, keys)) for key, value in dct.items()) if key not in keys}



def removeNoneValuesFromDict(dct:JSON, allowedNull:list[str]=[]) -> JSON:
	"""	Recursively remove Null-values from a dictionary, but ignore the ones speciefed in the `allowedNull` list.
		Return a new dictionary.
	"""
	if not isinstance(dct, dict):
		return dct
	return { key:value for key,value in ((key, removeNoneValuesFromDict(value)) for key,value in dct.items()) if value is not None or key in allowedNull }


def resourceDiff(old:Resource|JSON, new:Resource|JSON, modifiers:JSON=None) -> JSON:
	"""	Compare an old and a new resource. Keywords and values. Ignore internal __XYZ__ keys.
		Return a dictionary.
		If the modifier dict is given then it contains the changes that let from old to new.
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

	# ==> Old try to process Null attributes
	# if modifiers is not None:
	# 	for k,v in modifiers.items():
	# 		if v is None:
	# 			res[k] = v

	return res


def resourceModifiedAttributes(old:Resource|JSON, new:Resource|JSON, requestPC:JSON, modifiers:JSON=None) -> JSON:
	"""	Calculate the diff between a original resource and after it has been updated, and then remove the attributes
		that are part of the update request. In other words: Return a dictionary of those attributes that have been
		changed due in a CREATE or UPDATE request.
	"""
	return { k:v for k,v in resourceDiff(old, new, modifiers).items() if k not in requestPC or v != requestPC[k] }


def getCSE() -> Result:
	"""	Return the <CSEBase> resource.
	"""
	#return CSE.dispatcher.retrieveResource(CSE.cseRi)
	return resourceFromCSI(CSE.cseCsi)


def resourceFromCSI(csi:str) -> Result:
	""" Get the CSEBase resource by its csi. """
	return CSE.storage.retrieveResource(csi = csi)

	
def fanoutPointResource(id:str) -> Resource:
	"""	Check whether the target resource contains a fanoutPoint along its path,
		is a fanoutPoint itself.

		Args:
			id: the target's resource ID.
		Return:
			Return either the virtual fanoutPoint resource or None.
	"""
	# if not id:
	# 	return None
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
	# elif '/fopt/' in id:
	# 	(head, sep, tail) = id.partition('/fopt/')
	# 	nid = head + '/fopt'

	if nid and (result := CSE.dispatcher.retrieveResource(nid)).resource:
		return cast(Resource, result.resource)
	return None


def pollingChannelURIResource(id:str) -> PCH_PCU:
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
		if (result := CSE.dispatcher.retrieveResource(id)).resource and result.resource.ty == T.PCH_PCU:
			return cast(PCH_PCU, result.resource)
		# Fallthrough
	return None


def latestOldestResource(id:str) -> Resource:
	"""	Check whether the target is a latest or oldest virtual resource and return it.

		Args:
			id: Target resource ID
		Return:
			Return either the virtual resource or None.
	"""
	if not id:
		return None
	if id.endswith(('la', 'ol')):
		# Convert to srn
		if not isStructured(id):
			if not (id := structuredPathFromRI(id)):
				return None
		if (result := CSE.dispatcher.retrieveResource(id)).resource and result.resource.ty in [ T.CNT_LA, T.CNT_OL, T.FCNT_LA, T.FCNT_OL, T.TS_LA, T.TS_OL ]:
			return result.resource
		# Fallthrough
	return None

def getAttributeSize(attribute:Any) -> int:
	"""	Return a realistic size for the content of an attribute.
		Python does not really return good sizes for some of the data types.
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
	
	
def hasRegisteredAE(originator:str) -> bool:
	"""	Check wether an AE with `originator` is registered at the CSE.
	"""
	return len(CSE.storage.searchByFragment({'aei' : originator})) > 0


##############################################################################
#
#	Threads
#

# TODO Doc
def renameCurrentThread(name:str = None, thread:threading.Thread = None) -> None:
	thread = threading.current_thread() if not thread else thread
	thread.name = name if name else str(thread.native_id)


# TODO Doc
def runAsThread(task:Callable, *args:Any, **kwargs:Any) -> None:
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
