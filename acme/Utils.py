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
import datetime, json, random, string, sys, re, threading
import traceback
import cbor2
from copy import deepcopy
import isodate
from typing import Any, List, Tuple, Union, Dict, cast

from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode
from Types import Result, Operation, RequestArguments, FilterUsage, DesiredIdentifierResultType
from Types import ResultContentType, ResponseType, FilterOperation
from Types import ContentSerializationType, JSON, Conditions
from Logging import Logging as L
from resources.Resource import Resource
import CSE
import cbor2


##############################################################################
#
#	Identifier and path related
#

def uniqueRI(prefix:str='') -> str:
	return noNamespace(prefix) + uniqueID()


def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))


def isUniqueRI(ri:str) -> bool:
	return len(CSE.storage.identifier(ri)) == 0


def uniqueRN(prefix:str='un') -> str:
	return f'{noNamespace(prefix)}_{_randomID()}'

def announcedRN(resource:Resource) -> str:
	""" Create the announced rn for a resource.
	"""
	return f'{resource.rn}_Annc'


# create a unique aei, M2M-SP type
def uniqueAEI(prefix:str='S') -> str:
	return f'{prefix}{_randomID()}'


def noNamespace(id:str) -> str:
	"""	Remove the namespace part of an identifier and return the remainder.

		Example: 'm2m:cnt' -> 'cnt'
	"""
	p = id.split(':')
	return p[1] if len(p) == 2 else p[0]


def _randomID() -> str:
	""" Generate an ID. Prevent certain patterns in the ID. """
	while True:
		result = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID
			return result


def fullRI(ri:str) -> str:
	return f'{CSE.cseCsi}/{ri}'


def isSPRelative(uri:str) -> bool:
	""" Check whether a URI is SP-Relative. """
	return uri is not None and len(uri) >= 2 and uri[0] == '/' and uri [1] != '/'


def isAbsolute(uri:str) -> bool:
	""" Check whether a URI is Absolute. """
	return uri is not None and uri.startswith('//')


def isCSERelative(uri:str) -> bool:
	""" Check whether a URI is CSE-Relative. """
	return uri is not None and uri[0] != '/'


def isStructured(uri:str) -> bool:
	if isCSERelative(uri):
		if '/' in uri:
			return True
	elif isSPRelative(uri):
		if uri.count('/') > 2:
			return True
	elif isAbsolute(uri):
		if uri.count('/') > 4:
			return True
	return False


def isVirtualResource(resource: Resource) -> bool:
	"""	Check whether the `resource` is a virtual resource. 
		The function returns `False` when the resource is not a virtual resource, or when it is `None`.
	"""
	if resource is None:
		return False
	result:bool = resource[resource._isVirtual]
	return result if result is not None else False
	# return (ty := r.ty) and ty in C.virtualResources


def isAnnouncedResource(resource:Resource) -> bool:
	"""	Check whether the `resource` is an announced resource. 
	"""
	result:bool = resource[resource._isAnnounced]
	return result if result is not None else False


def isValidID(id:str) -> bool:
	""" Check for valid ID. """
	#return len(id) > 0 and '/' not in id 	# pi might be ""
	return id is not None and '/' not in id


csiRx = re.compile('^/[^/\s]+') # Must start with a / and must not contain a further / or white space
def isValidCSI(csi:str) -> bool:
	"""	Check for valid CSE-ID format. """
	return re.fullmatch(csiRx, csi) is not None


def structuredPath(resource:Resource) -> str:
	""" Determine the structured path of a resource.
	"""
	rn:str = resource.rn
	if resource.ty == T.CSEBase: # if CSE
		return rn

	# retrieve identifier record of the parent
	if (pi := resource.pi) is None or len(pi) == 0:
		# L.logErr('PI is None')
		return rn
	rpi = CSE.storage.identifier(pi) 
	if len(rpi) == 1:
		return cast(str, rpi[0]['srn'] + '/' + rn)
	# L.logErr(traceback.format_stack())
	L.logErr(f'Parent {pi} not found in DB')
	return rn # fallback


def structuredPathFromRI(ri:str) -> str:
	""" Get the structured path of a resource by its ri. """
	if len((identifiers := CSE.storage.identifier(ri))) == 1:
		return cast(str, identifiers[0]['srn'])
	return None


def riFromStructuredPath(srn: str) -> str:
	""" Get the ri from a resource by its structured path. """
	if len((paths := CSE.storage.structuredPath(srn))) == 1:
		return cast(str, paths[0]['ri'])
	return None


def srnFromHybrid(srn:str, id:str) -> Tuple[str, str]:
	""" Handle Hybrid ID. """
	if id is not None:
		ids = id.split('/')
		if srn is None and len(ids) > 1  and ids[-1] in C.virtualResourcesNames: # Hybrid
			if (srn := structuredPathFromRI('/'.join(ids[:-1]))) is not None:
				srn = '/'.join([srn, ids[-1]])
				id = riFromStructuredPath(srn) # id becomes the ri of the fopt
	return srn, id


def retrieveIDFromPath(id: str, csern: str, csecsi: str) -> Tuple[str, str, str]:
	""" Split a ful path e.g. from a http request into its component and return a local ri .
		Also handle retargeting paths.
		The return tupple is (RI, CSI, SRN).
	"""
	csi 		= None
	spi 		= None
	srn 		= None
	ri 			= None
	vrPresent	= None

	# Prepare. Remove leading / and split
	if id[0] == '/':
		id = id[1:]
	ids = id.split('/')
	csecsi = csecsi[1:]	# remove leading / from csi for our comparisons here

	if (idsLen := len(ids)) == 0:	# There must be something!
		return None, None, None

	# Remove virtual resource shortname if it is present
	if ids[-1] in C.virtualResourcesNames:
		vrPresent = ids.pop()	# remove and return last path element
		idsLen -= 1

	if ids[0] == '~' and idsLen > 1:			# SP-Relative
		# L.logDebug("SP-Relative")
		csi = ids[1]							# extract the csi
		if csi != csecsi:						# Not for this CSE? retargeting
			if vrPresent is not None:			# append last path element again
				ids.append(vrPresent)
			return f'/{"/".join(ids[1:])}', csi, srn		# Early return. ri is the remaining (un)structured path
		if idsLen > 2 and (ids[2] == csern or ids[2] == '-'):	# structured
			ids[2] = csern if ids[2] == '-' else ids[2]
			srn = '/'.join(ids[2:])
		elif idsLen == 3:						# unstructured
			ri = ids[2]
		else:
			return None, None, None

	elif ids[0] == '_' and idsLen >= 4:			# Absolute
		# L.logDebug("Absolute")
		spi = ids[1] 	#TODO Check whether it is same SPID, otherwise forward it throw mcc'
		csi = ids[2]
		if csi != csecsi:
			if vrPresent is not None:						# append last path element again
				ids.append(vrPresent)
			return f'/{"/".join(ids[2:])}', csi, srn	# Not for this CSE? retargeting
		if ids[3] == csern or ids[3] == '-':				# structured
			ids[3] = csern if ids[3] == '-' else ids[3]
			srn = '/'.join(ids[3:])
		elif idsLen == 4:						# unstructured
			ri = ids[3]
		else:
			return None, None, None

	else:										# CSE-Relative
		# L.logDebug("CSE-Relative")
		if idsLen == 1 and ((ids[0] != csern and ids[0] != '-') or ids[0] == csecsi):	# unstructured
			ri = ids[0]
		else:									# structured
			ids[0] = csern if ids[0] == '-' else ids[0]
			srn = '/'.join(ids)

	# Now either csi, ri or structured is set
	if ri is not None:
		if vrPresent is not None:
			ri = f'{ri}/{vrPresent}'
		return ri, csi, srn
	if srn is not None:
		# if '/fopt' in ids:	# special handling for fanout points
		# 	return srn, csi, srn
		if vrPresent is not None:
			srn = f'{srn}/{vrPresent}'
		return riFromStructuredPath(srn), csi, srn
	if csi is not None:
		return riFromCSI(f'/{csi}'), csi, srn
	# TODO do something with spi?
	return None, None, None


def riFromCSI(csi: str) -> str:
	""" Get the ri from an CSEBase resource by its csi. """
	if (res := resourceFromCSI(csi)) is None:
		return None
	return cast(str, res.ri)


def getIdFromOriginator(originator: str, idOnly: bool = False) -> str:
	""" Get AE-ID-Stem or CSE-ID from the originator (in case SP-relative or Absolute was used)
	"""
	if idOnly:
		return originator.split("/")[-1] if originator is not None  else originator
	else:
		return originator.split("/")[-1] if originator is not None and originator.startswith('/') else originator


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
		)
def isURL(url: str) -> bool:
	""" Check whether a given string is a URL. """
	return url is not None and isinstance(url, str) and re.match(urlregex, url) is not None


def isHttpUrl(url:str) -> bool:
	"""	Check whether a URL is a http URL. 
	"""
	return url.startswith(('http', 'https'))


def normalizeURL(url: str) -> str:
	""" Remove trailing / from the url. """
	if url is not None:
		while len(url) > 0 and url[-1] == '/':
			url = url[:-1]
	return url


##############################################################################
#
#	Time, Date, Timestamp related
#

def getResourceDate(delta:int=0) -> str:
	"""	Generate an UTC-relative ISO 8601 timestamp and return it.

		`delta` adds or substracts n seconds to the generated timestamp.
	"""
	return toISO8601Date(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=delta))


def toISO8601Date(ts:Union[float, datetime.datetime], isUTCtimestamp:bool=True) -> str:
	"""	Convert and return a UTC-relative float timestamp or datetime object to an ISO 8601 string.
	"""
	if isinstance(ts, float):
		if isUTCtimestamp:
			ts = datetime.datetime.fromtimestamp(ts)
		else:
			ts = datetime.datetime.utcfromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')


def fromAbsRelTimestamp(absRelTimestamp:str) -> float:
	"""	Parse a ISO 8601 string and return a UTC-relative timestamp as a float.
		If  `absRelTimestamp` in the string is a period (relatice) timestamp (e.g. PT2S), then this function
		tries to convert it and return an absolute timestamp as a float, based on the current UTC time.
		If the `absRelTimestamp` contains an integer then it is treated as a relative offset and a UTC-based
		timestamp is generated for this offset and returned.
	"""
	try:
		return isodate.parse_datetime(absRelTimestamp).timestamp()
		# return datetime.datetime.strptime(timestamp, '%Y%m%dT%H%M%S,%f').timestamp()
	except Exception as e:
		try:
			return utcTime() + fromDuration(absRelTimestamp)
		except:
			return 0.0
	return 0.0


def fromDuration(duration:str) -> float:
	"""	Convert a duration to a number of seconds (float). Input could be either an ISO period 
		or a number of ms.
	"""
	try:
		return isodate.parse_duration(duration).total_seconds()
	except Exception as e:
		try:
			# Last try: absRelTimestamp could be a relative offset in ms. Try to convert 
			# the string and return an absolute UTC-based duration
			return float(duration) / 1000.0
		except Exception as e:
			if L.isWarn: L.logWarn(f'Wrong format for duration: {duration}')
			raise e
	return 0.0


def utcTime() -> float:
	"""	Return the current time's timestamp, but relative to UTC.
	"""
	return datetime.datetime.utcnow().timestamp()


##############################################################################
#
#	Resource and content related
#

def resourceFromCSI(csi: str) -> Resource:
	""" Get the CSEBase resource by its csi. """
	return cast(Resource, CSE.storage.retrieveResource(csi=csi).resource)



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
	"""	Return the "pure" structure without the "m2m:xxx" or "<domain>:id" resource specifier, and the oneM2M type identifier. 
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


# def removeCommentsFromJSON(data:str) -> str:
# 	"""	Remove C-style comments from JSON.
# 	"""
# 	data = re.sub(r'^[\s]*//[^\n]*\n', '\n', data)		# Comment on first line
# 	data = re.sub(r'\n[\s]*//[^\n]*\n', '\n', data)	# Comments on some line in the middle
# 	data = re.sub(r'\n[\s]*//[^\n]*$', '\n', data)		# Comment on last line w/o newline at the end
# 	data = re.sub(r'/\\*.*?\\*/', '', data)
# 	return data


#commentPattern = r'(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)'
#commentPattern = r'(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*$)'	# recognized escaped comments
commentPattern = r'(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*$|#[^\r\n]*$)'	# recognized escaped comments
# first group captures quoted strings (double or single)
# second group captures comments (//single-line or /* multi-line */)
commentRegex = re.compile(commentPattern, re.MULTILINE|re.DOTALL)

def removeCommentsFromJSON(data:str) -> str:
	"""	This WILL remove:
			/* multi-line comments */
			// single-line comments
			# single-line comments
		
		Will NOT remove:
			String var1 = "this is /* not a comment. */";
			char *var2 = "this is // not a comment, either.";
			url = 'http://not.comment.com';
	"""
	def _replacer(match):	# type: ignore
		# if the 2nd group (capturing comments) is not None,
		# it means we have captured a non-quoted (real) comment string.
		if match.group(2) is not None:
			return "" # so we will return empty to remove the comment
		else: # otherwise, we will return the 1st group
			return match.group(1) # captured quoted-string
	return commentRegex.sub(_replacer, data)


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

		It is possible to address a specific element in an array. This is done be
		specifying the element as `{n}`.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{0}')

		If an element if specified as '{}' then all elements in that array are returned in
		an array.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{}') or findXPath(input, 'm2m:cnt/m2m:cin/{}/rn')

	"""

	if key is None or dct is None:
		return default

	paths = key.split("/")
	data:Any = dct
	for i in range(0,len(paths)):
		if data is None:
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
		for i in range(0,ln1):
			if paths[i] not in data:
				data[paths[i]] = {}
			data = data[paths[i]]
	if paths[ln1] in data is not None and not overwrite:
		return True # don't overwrite
	if not isinstance(data, dict):
		return False
	data[paths[ln1]] = value
	return True


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
		elif modifiers is not None and k in modifiers:	# this means the attribute is overwritten by the same value. But still modified
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


def getCSE() -> Result:
	"""	Return the <CSEBase> resource.
	"""
	return CSE.dispatcher.retrieveResource(CSE.cseRi)

	
def fanoutPointResource(id: str) -> Resource:
	"""	Check whether the target contains a fanoutPoint in between or as the target.

		Return either the virtual fanoutPoint resource or None.
	"""
	if id is None:
		return None
	# retrieve srn
	if not isStructured(id):
		id = structuredPathFromRI(id)
	if id is None:
		return None
	nid = None
	if id.endswith('/fopt'):
		nid = id
	elif '/fopt/' in id:
		(head, sep, tail) = id.partition('/fopt/')
		nid = head + '/fopt'
	if nid is not None:
		if (result := CSE.dispatcher.retrieveResource(nid)).resource is not None:
			return cast(Resource, result.resource)
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
	
	

##############################################################################
#
#	Threads
#

def renameCurrentThread(name:str = None, thread:threading.Thread = None) -> None:
	thread = threading.current_thread() if thread is None else thread
	thread.name = name if name is not None else str(thread.native_id)


##############################################################################
#
#	Text formattings and search
#

def toHex(bts:bytes, toBinary:bool=False, withLength:bool=False) -> str:
	"""	Print bts as hex output, similar to the 'od' command.
	"""
	if len(bts) == 0 and not withLength: return ''
	result = ''
	n = 0
	b = bts[n:n+16]

	while b and len(b) > 0:

		if toBinary:
			s1 = ' '.join([f'{i:08b}' for i in b])
			s1 = f'{s1[0:71]} {s1[71:]}'
			width = 144
		else:
			s1 = ' '.join([f'{i:02x}' for i in b])
			s1 = f'{s1[0:23]} {s1[23:]}'
			width = 48

		s2 = ''.join([chr(i) if 32 <= i <= 127 else '.' for i in b])
		s2 = f'{s2[0:8]} {s2[8:]}'
		result += f'0x{n:08x}  {s1:<{width}}  | {s2}\n'

		n += 16
		b = bts[n:n+16]
	result += f'0x{len(bts):08x}'

	return result


def simpleMatch(st:str, pattern:str, star:str='*') -> bool:
	"""	Simple string match function. 
		This class supports the following expression operators:

	
		- '?' : any single character
		- '*' _ zero or more characters
		- '+' _ one or more characters
		- '\\' - Escape an expression operator

		Examples: 
			"hello" - "h?llo" -> True
	 		"hello" - "h?lo" -> False
	 		"hello" - "h*lo" -> True
			"hello" - "h*" -> True
			"hello" - "*lo" -> True
			"hello" - "*l?" -> True

		Parameter:
			- st : string to test
			- pattern : the pattern string
			- star : optionally specify a different character as the star character
	"""

	def _simpleMatchStar(st:str, pattern:str) -> bool:
		""" Recursively eat up a string when the pattern is a star at the beginning
			or middle of a pattern.
		"""
		stLen	= len(st)
		stIndex	= 0
		while not _simpleMatch(st[stIndex:], pattern):
			stIndex += 1
			if stIndex >= stLen:
				return False
		return True
	

	def _simpleMatchPlus(st:str, pattern:str) -> bool:
		""" Recursively eat up a string when the pattern is a plus at the beginning
			or middle of a pattern.
		"""
		stLen	= len(st)
		stIndex	= 1
		if len(st) == 0:
			return False
		while not _simpleMatch(st[stIndex:], pattern):
			stIndex += 1
			if stIndex >= stLen:
				return False
		return True

	def _simpleMatch(st:str, pattern:str) -> bool:
		last:int		= 0
		matched:bool	= False
		reverse:bool	= False
		stLen			= len(st)
		patternLen 		= len(pattern)

		# We later increment these indexes first in the loop below, therefore they need to be initialized with -1
		stIndex			= -1
		patternIndex 	= -1

		while patternIndex < patternLen-1:

			stIndex 		+= 1
			patternIndex 	+= 1
			p 				= pattern[patternIndex]

			if stIndex > stLen:
				return False

			# Match exactly one character, if there is one left
			if p == '?':
				if stIndex >= stLen:
					return False
				continue
			
			# Match zero or more characters
			if p == star:
				patternIndex += 1
				if patternIndex == patternLen:	# * is the last char in the pattern: this is a match
					return True
				return _simpleMatchStar(st[stIndex:], pattern[patternIndex:])	# Match recursively the remainder of the string

			if p == '+':
				patternIndex += 1
				if patternIndex == patternLen and len(st[stIndex:]) > 0:	# + is the last char in the pattern and there is enough string remaining: this is a match
					return True
				return _simpleMatchPlus(st[stIndex:], pattern[patternIndex:])	# Match recursively the remainder of the string

			# Literal match with the following character
			if p == '\\':
				patternIndex += 1
				p = pattern[patternIndex]
				# Fall-through
			
			# Literall match 
			if stIndex < stLen:
				if p != st[stIndex]:
					return False
		
		# End of matches
		return stIndex == stLen-1
	
	return _simpleMatch(st, pattern)


def serializeData(data:JSON, ct:ContentSerializationType) -> str|bytes|JSON:
	"""	Serialize a dictionary, depending on the serialization type.
	"""
	if ct == ContentSerializationType.PLAIN:
		return data
	encoder = json if ct == ContentSerializationType.JSON else cbor2 if ct == ContentSerializationType.CBOR else None
	if encoder is None:
		return None
	return encoder.dumps(data)	# type:ignore[no-any-return]


def deserializeData(data:bytes, ct:ContentSerializationType) -> JSON:
	"""	Deserialize data into a dictionary, depending on the serialization type.
		If the len of the data is 0 then an empty dictionary is returned. 
	"""
	if len(data) == 0:
		return {}
	if ct == ContentSerializationType.JSON:
		return cast(JSON, json.loads(removeCommentsFromJSON(data.decode("utf-8"))))
	elif ct == ContentSerializationType.CBOR:
		return cast(JSON, cbor2.loads(data))
	# except Exception as e:
	# 	L.logErr(f'Deserialization error: {str(e)}')
	return None


##############################################################################
#
#	Various

def exceptionToResult(e:Exception) -> Result:
	tb = traceback.format_exc()
	L.logErr(tb, exc=e)
	tbs = tb.replace('"', '\\"').replace('\n', '\\n')
	return Result(rsc=ResponseCode.internalServerError, dbg=f'encountered exception: {tbs}')
