#
#	RequestUtils.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used to work with requests and responses
#


from __future__ import annotations
import threading
import cbor2, json
from typing import cast, Dict
from urllib.parse import urlparse, urlunparse, parse_qs, urlunparse, urlencode
from ..etc.DateUtils import waitFor

from .Types import CSERequest, ContentSerializationType, JSON
from .Constants import Constants as C
from ..services.Logging import Logging as L
from ..helpers import TextTools
from ..services import CSE


def serializeData(data:JSON, ct:ContentSerializationType) -> str|bytes|JSON:
	"""	Serialize a dictionary, depending on the serialization type.
	"""
	if ct == ContentSerializationType.PLAIN:
		return data
	encoder = json if ct == ContentSerializationType.JSON else cbor2 if ct == ContentSerializationType.CBOR else None
	if not encoder:
		return None
	return encoder.dumps(data)	# type:ignore[no-any-return]


def deserializeData(data:bytes, ct:ContentSerializationType) -> JSON:
	"""	Deserialize data into a dictionary, depending on the serialization type.
		If the len of the data is 0 then an empty dictionary is returned. 
	"""
	if len(data) == 0:
		return {}
	if ct == ContentSerializationType.JSON:
		return cast(JSON, json.loads(TextTools.removeCommentsFromJSON(data.decode('utf-8'))))
	elif ct == ContentSerializationType.CBOR:
		return cast(JSON, cbor2.loads(data))
	return None


def toHttpUrl(url:str) -> str:
	"""	Make the `url` a valid http URL (escape // and ///)
		and return it.
	"""
	u = list(urlparse(url))
	if u[2].startswith('///'):
		u[2] = f'/_{u[2][2:]}'
		url = urlunparse(u)
	elif u[2].startswith('//'):
		u[2] = f'/~{u[2][1:]}'
		url = urlunparse(u)
	return url


def determineSerialization(url:str, csz:list[str]=None,) -> ContentSerializationType:
	"""	Determine the type of serialization for a notification from either the `url`'s `ct` query parameter,
		or the given list of `csz`(contentSerializations, attribute of a target AE/CSE), or the CSE's default serialization.
	"""
	ct = None
	scheme = None

	# Dissect url and check whether ct is an argumemnt. If yes, then remove it
	# and store it to check later
	uu = list(urlparse(url))
	qs = parse_qs(uu[4], keep_blank_values=True)
	if ('ct' in qs):
		ct = qs.pop('ct')[0]	# remove the ct=
		uu[4] = urlencode(qs, doseq=True)
		url = urlunparse(uu)	# reconstruct url w/o ct
	scheme = uu[0]

	# Check scheme first
	# TODO should this really be in this function?
	if scheme not in C.supportedSchemes:
		L.isWarn and L.logWarn(f'URL scheme {scheme} not supported')
		return None	# Scheme not supported

	if ct:
		# if ct is given then check whether it is supported, 
		# otherwise ignore this url
		if ct not in C.supportedContentSerializationsSimple:
			return None	# Requested serialization not supported
		return ContentSerializationType.to(ct)

	elif csz:
		# if csz is given then build an intersection between the given list and
		# the list of supported serializations. Then take the first one
		# as the one to use.
		common = [x for x in csz if x in C.supportedContentSerializations]	# build intersection, keep the old sort order
		if len(common) == 0:
			return None
		return ContentSerializationType.to(common[0]) # take the first
	
	# Just use default serialization.
	return CSE.defaultSerialization

##############################################################################
#
#	Request/Response async sequence helpers
#

from threading import Lock
_requestLock = Lock()
_requests:Dict[str, CSERequest] = {}

def hasResponse(requestID:str) -> bool:
	"""	Callback for periodic check whether a response has arrived
	"""
	with _requestLock:
		return requestID in _requests and _requests[requestID] != None


def waitForResponse(requestID:str, timeout:float) -> CSERequest:
	# TODO doc + return

	with _requestLock:
		if requestID in _requests:						# Skip if it is already in the map
			return None
		_requests[requestID] = None						# Add the record to the map
	waitFor(timeout, lambda:hasResponse(requestID))		# Wait until timeout, or the response was set
	with _requestLock:
		return _requests.pop(requestID)					# Return whatever there is. 


def addResponse(response:CSERequest) -> bool:
	# TODO doc
	with _requestLock:
		if not (requestID := response.headers.requestIdentifier) in _requests:	# Check whether there is an entry
			return False														# This could also be None! Therefore the "in" test
		_requests[requestID] = response
		return True



threading.Thread(target=lambda:print(waitForResponse('12', 5.0))).start()


print("HUHUHUHU")
waitFor(2)
(resp := CSERequest()).headers.requestIdentifier = '132'
addResponse(resp)

