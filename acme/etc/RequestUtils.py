#
#	RequestUtils.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module contains various utilty functions that are used to work with requests and responses. """

from __future__ import annotations

import cbor2, json
from typing import Any, cast, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlunparse, urlencode, unquote, ParseResult

from .DateUtils import getResourceDate
from .Types import ContentSerializationType, JSON, RequestType, ResponseStatusCode
from .Types import Result, ResourceTypes, Operation, CSERequest
from ..etc.ResponseStatusCodes import BAD_REQUEST, UNSUPPORTED_MEDIA_TYPE
from .Constants import Constants
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration
from ..helpers import TextTools
from ..helpers.MultiDict import MultiDict
from ..etc.ResponseStatusCodes import ResponseStatusCode
from ..etc.Types import ReqResp
from ..etc.Constants import RuntimeConstants as RC
from .IDUtils import uniqueRI


def serializeData(data:JSON, ct:ContentSerializationType) -> Optional[str|bytes|JSON]:
	"""	Serialize a dictionary, depending on the serialization type.

		Args:
			data: The data to serialize.
			ct: The *data* content serialization format.
		
		Return:
			A data *str* or *byte* object with the serialized data, or *None*.
	"""
	if ct == ContentSerializationType.PLAIN:
		return data
	encoder = json if ct == ContentSerializationType.JSON else cbor2 if ct == ContentSerializationType.CBOR else None
	if not encoder:
		return None
	return encoder.dumps(data)	# type:ignore[no-any-return]


def deserializeData(data:bytes, ct:ContentSerializationType) -> Optional[JSON]:
	"""	Deserialize data into a dictionary, depending on the serialization type.

		Args:
			data: The data to deserialize.
			ct: The *data* content serialization format.
		
		Return:
			If the *data* is not *None*, but has a length of 0 then an empty dictionary is returned. If an unknown content serialization is specified then *None* is returned. Otherwise, a `JSON` object is returned.
	"""
	if len(data) == 0:
		return {}
	match ct:
		case ContentSerializationType.JSON:
			if isinstance(data, str):
				return cast(JSON, json.loads(TextTools.removeCommentsFromJSON(data)))	# String doesn't need to be decoded
			return cast(JSON, json.loads(TextTools.removeCommentsFromJSON(data.decode('utf-8'))))
		case ContentSerializationType.CBOR:
			return cast(JSON, cbor2.loads(data))
		case _:
			return None


def toHttpUrl(url:str) -> str:
	"""	Make the *url* a valid http URL (escape // and ///) and return it.

		Args:
			url: The URL to convert.
		
		Return:
			A valid URL with escaped special characters.
	"""
	u = list(urlparse(url))
	match u[2]:
		case x if '///' in x:
			u[2] = x.replace('///', '/_/')	# replace /// with /_/, also in the middle of the path
			url = urlunparse(u)
		case x if '//' in x:
			u[2] = x.replace('//', '/~/')	# replace // with /~/, also in the middle of the path
			url = urlunparse(u)
	return url


def fromHttpURL(path:str) -> str:
	"""	Make the *path* a valid oneM2M ID (unescape /~/ and /_/) and return it.
		This is valid of CoAP URL paths as well.

		Args:
			path: The path to convert.
		
		Return:
			A valid ID with unescaped special characters.
	"""
	# resolve http's /~ and /_ special prefixs
	match path[0]:
		case '~':
			return path[1:]			# ~/xxx -> /xxx
		case '_':
			return f'/{path[1:]}'	# _/xxx -> //xxx
		case _:
			return path
	

def toCoAPPath(path:str) -> str:
	"""	Make the *path* a valid CoAP URL path (escape / and //) and return it.

		Args:
			path: The path to convert.

		Return:
			A valid CoAP URL path with escaped special characters for oneM2M IDs
	"""
	if path.startswith('//'):
		return f'_{path[1:]}'	# //xxx -> _/xxx
	if path.startswith('/'):
		return f'~{path}'		# /xxx -> ~/xxx
	return path


def determineSerialization(url:str, csz:list[str], defaultSerialization:ContentSerializationType) -> Optional[ContentSerializationType]:
	"""	Determine the type of serialization for a notification from either the *url*'s *ct* query parameter,
		or the given list of *csz* (contentSerializations, attribute of a target AE/CSE), or the CSE's default serialization.

		As a side effect this function also validates the allowed URL scheme.

		Args:
			url: The *URL* to parse.
			csz: The fallback content serialization.
			defaultSerialization: The CSE's defaults serialization.
		
		Return:
			The determined content serialization, or *None* if none could be determined.
	"""
	ct = None
	scheme = None

	# Dissect url and check whether ct is an argumemnt. If yes, then remove it
	# and store it to check later
	uu = list(urlparse(url))
	qs = parse_qs(uu[4], keep_blank_values = True)
	if ('ct' in qs):
		ct = qs.pop('ct')[0]	# remove the ct=
		uu[4] = urlencode(qs, doseq=True)
		url = urlunparse(uu)	# reconstruct url w/o ct
	scheme = uu[0]

	# Check scheme first
	# TODO should this really be in this function?
	if scheme not in Constants.supportedSchemes:
		L.isWarn and L.logWarn(f'URL scheme {scheme} not supported')
		return None	# Scheme not supported

	if ct:
		# if ct is given then check whether it is supported, 
		# otherwise ignore this url
		if ct not in ContentSerializationType.supportedContentSerializationsSimple():
			return None	# Requested serialization not supported
		return ContentSerializationType.getType(ct)

	elif csz:
		# if csz is given then build an intersection between the given list and
		# the list of supported serializations. Then take the first one
		# as the one to use.
		common = [x for x in csz if x in ContentSerializationType.supportedContentSerializations()]	# build intersection, keep the old sort order
		if len(common) == 0:
			return None
		return ContentSerializationType.getType(common[0]) # take the first
	
	# Just use default serialization.
	return defaultSerialization


def contentAsString(content:bytes|str|Any, ct:ContentSerializationType) -> str:
	"""	Convert a content to a string. 
		If the content is a string, it is returned as is.
		If the content is a byte array, it is decoded to a string.
		If the content is neither a string nor a byte array, it is converted to a hex string.

		Args:
			content: The content to convert.
			ct: The content serialization type.
		
		Return:
			The content as a string.
	"""
	if not content:	return ''
	if isinstance(content, str): return content
	return content.decode('utf-8') if ct == ContentSerializationType.JSON else TextTools.toHex(content)


def requestFromResult(inResult:Result, 
					  originator:Optional[str] = None, 
					  ty:Optional[ResourceTypes] = None, 
					  op:Optional[Operation] = None, 
					  isResponse:Optional[bool] = False,
					  originalRequest:Optional[CSERequest] = None) -> Result:
	"""	Convert a response request to a new *Result* object and create a new dictionary in *Result.data*
		with the full Response structure. Recursively do this if the *embeddedRequest* is also
		a full Request or Response.

		Args:
			inResult: The input `Result` object.
			originator: The request originator.
			ty: Optional resource type.
			op: Optional request operation type
			isResponse: Whether the result is actually a response, and not a request.
		
		Return:
			`Result` object with the response. The request or response is in *data*.

		See Also:
			`responseFromResult`
	"""
	from ..runtime import CSE

	req:JSON = {}

	# Assign the From and to of the request. An assigned originator has priority for this
	# TO and FROM are optional in a response. So, don't put them in by default.
	if not isResponse or (isResponse and CSE.request.sendToFromInResponses):
		if originator:
			req['fr'] = RC.cseCsi if isResponse else originator
			req['to'] = inResult.request.id if inResult.request.id else originator
		elif inResult.request and inResult.request.originator:
			req['fr'] = RC.cseCsi if isResponse else inResult.request.originator
			req['to'] = inResult.request.originator if isResponse else inResult.request.id
		else:
			req['fr'] = RC.cseCsi
			req['to'] = inResult.request.id if inResult.request.id else RC.cseCsi


	# Originating Timestamp
	if inResult.request.ot:
			req['ot'] = inResult.request.ot
	else:
		# Always add the OT in a response if not already present
		if isResponse:
			req['ot'] = getResourceDate()
	
	# Response Status Code
	if inResult.rsc and inResult.rsc != ResponseStatusCode.UNKNOWN:
		req['rsc'] = int(inResult.rsc)
	
	# Operation
	if not isResponse:
		if op:
			req['op'] = int(op)
		elif inResult.request.op:
			req['op'] = int(inResult.request.op)

	# Type
	if ty:
		req['ty'] = int(ty)
	elif inResult.request.ty:
		req['ty'] = int(inResult.request.ty)
	
	# Request Identifier 
	if inResult.request.rqi:					# copy from the original request
		req['rqi'] = inResult.request.rqi
	
	# Release Version Indicator
	# TODO handle version 1 correctly
	if inResult.request.rvi:			# copy from the original request
		req['rvi'] = inResult.request.rvi
	
	# Vendor Information
	if inResult.request.vsi:					# copy from the original request
		req['vsi'] = inResult.request.vsi
	
	# Event Category
	if inResult.request.ec:
		req['ec'] = int(inResult.request.ec)
	
	# Result Content
	if inResult.request.rcn:
		req['rcn'] = int(inResult.request.rcn)

	# Result Content
	if inResult.request.drt:
		req['drt'] = int(inResult.request.drt)
	
	# Result Expiration Timestamp
	if inResult.request.rset is not None:
		req['rset'] = inResult.request.rset


	# If the response contains a request (ie. for polling), then add that request to the pc
	pc = None
	# L.isDebug and L.logDebug(inResult)

	if inResult.embeddedRequest:
		if inResult.embeddedRequest.originalRequest:
			pc = inResult.embeddedRequest.originalRequest
		else:
			pc = cast(JSON, requestFromResult(Result(request = inResult.embeddedRequest)).data)
		# L.isDebug and L.logDebug(pc)

	else:
		# construct and serialize the data as JSON/dictionary. Encoding to JSON or CBOR is done later
		pc = inResult.toData(ContentSerializationType.PLAIN)	#  type:ignore[assignment]
	
	if pc:
		# If the request has selected attributes, then the pc content must be filtered
		if originalRequest and originalRequest.selectedAttributes:
			_typeShortname = list(pc.keys())[0]
			pc = { _typeShortname : filterAttributes(pc[_typeShortname], originalRequest.selectedAttributes) }


		# if the request/result is actually an incoming request targeted to the receiver, then the
		# whole request must be embeded as a "m2m:rqp" request.
		if inResult.embeddedRequest and inResult.embeddedRequest.requestType == RequestType.REQUEST:
			req['pc'] = { 'm2m:rqp' : pc }
		else:
			req['pc'] = pc

	# Filter Criteria attributes
	if inResult.request.fc:
		fcAttributes:JSON = {}
		inResult.request.fc.mapAttributes(lambda k,v: fcAttributes.update({k:v}), False)
		if fcAttributes:
			req['fc'] = fcAttributes


	
	return Result(data = req, 
				  resource = inResult.resource, 
				  request = inResult.request, 
				  embeddedRequest = inResult.embeddedRequest, 
				  rsc = inResult.rsc)


def prepareResultForSending(inResult:Result, 
					   		isResponse:Optional[bool] = False,
							originalRequest:Optional[CSERequest] = None) -> Tuple[Result, bytes]:
	"""	Prepare a new request for MQTT or WebSocket sending. 
	
		Attention:
			Remember, a response is actually just a new request. This takes care of the fact that in MQTT or WebSockets
			a response is very similar to a response.
	
		Args:
			inResult: A `Result` object, that contains a request in its *request* attribute.
			isResponse: Indicator whether the `Result` object is actually a response or a request.
			originalRequest: The original request that was received.

		Return:
			A tuple with an updated `Result` object and the serialized content.
	"""
	result = requestFromResult(inResult, isResponse = isResponse, originalRequest = originalRequest)
	return (result, cast(bytes, serializeData(cast(JSON, result.data), result.request.ct)))


def responseFromResult(inResult:Result, originator:Optional[str] = None) -> Result:
	"""	Shortcut for `requestFromResult` to create a response object.
	
		Args:
			inResult: Result that contains the response.
			originator: Originator for the response.
		
		Return:
			`Result` object with the response.
	"""
	return requestFromResult(inResult, originator, isResponse = True)


def createRawRequest(**kwargs:Any) -> JSON:
	"""	Create a dictionary with a couple of pre-initialized fields. No validation is done.
	
		Args:
			kwargs: individual attributes to set in the request.
		
		Return:
			JSON dictionary with the request.
	"""

	r = {	'fr': RC.cseCsi,
			'rqi': uniqueRI(),
			'rvi': RC.releaseVersion,
		}
	r.update(kwargs)
	return r


def createPositiveResponseResult() -> Result:
	"""	Create a positive `Result` object with a request.
	
		Return:
			A `Result` object with a positive response.
	"""
	return Result(rsc = ResponseStatusCode.OK, request = CSERequest(requestType = RequestType.RESPONSE,
																 	rsc = ResponseStatusCode.OK))
			   

def createRequestResultFromURI(request:CSERequest, url:str) -> Tuple[Result, str, ParseResult]:
	"""	Create a `Result` object from a URI. The URI is unquoted, parsed and the request is created.
	
		Args:
			request: The request to create.
			url: The URL to parse.
		
		Return:
			A tuple with the `Result` object, the URL and the parsed URL.
	"""

	url = unquote(url)
	u = urlparse(url)
	req 					= Result(request = request)
	req.request.id			= u.path[1:] if u.path[1:] else req.request.to
	req.resource			= req.request.pc
	req.request.rqi			= uniqueRI()
	if req.request.rvi != '1':
		req.request.rvi		= req.request.rvi if req.request.rvi is not None else RC.releaseVersion
	req.request.ot			= getResourceDate()
	req.rsc					= ResponseStatusCode.UNKNOWN								# explicitly remove the provided OK because we don't want have any
	req.request.ct			= req.request.ct if req.request.ct else RC.defaultSerialization 	# get the serialization

	return req, url, u


def filterAttributes(dct:JSON, attributesToInclude:list[str]) -> JSON:
	"""	Filter a dictionary by a list of attributes to include.
	
		Args:
			dct: Dictionary to filter.
			attributesToInclude: List of attributes to include.
			
		Return:
	"""
	return { k: v 
			 for k, v in dct.items() 
			 if k in attributesToInclude }
			 

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



def fillRequestWithArguments(arguments:MultiDict, dct:JSON, cseRequest:CSERequest, sep:Optional[str] = None) -> CSERequest:
	"""	Fill a request with arguments from a `MultiDict`. The `MultiDict` contains the arguments from a request.

		Args:
			arguments: The `MultiDict` with the arguments.
			dct: The dictionary to fill.
			cseRequest: The `CSERequest` object to fill.
			sep: The separator for the attribute list.

		Return:
			The filled `CSERequest` object.
	"""

	# The Filter Criteria and attribute lists
	filterCriteria:ReqResp = {}
	attributeList:list[str] = []

	for arg in list(arguments.keys()):
		match arg:
			# Actually, the following attributes are filterCriteria attributes, but are
			# stored in the CSERequest object as request attributes
			case 'rcn' | 'rp' | 'drt' | 'sqi':
				dct[arg] = arguments.getOne(arg, greedy = True)

			case 'rt':
				if not (rt := cast(JSON, dct.get('rt'))):	# if not yet in the req
					rt = {}
				rt['rtv'] = arguments.getOne(arg, greedy = True)	# type: ignore [assignment]
				dct['rt'] = rt

			case 'atrl':
				# the attribute list could appear multiple times in the query, or have multiple values separated by '+'
				while (_a := arguments.getOne(arg, greedy = True)) is not None:
					attributeList.extend(_a.split(sep))
				# If there is only one attribute, add it to the to field instead of the atrl in the CONTENT
				if len(attributeList) == 1:
					dct['to'] = f'{dct["to"]}#{attributeList[0]}'
					attributeList = []

			# Maxage
			# TODO make this a propper request attribute later when accepted for the spec. Also for http
			case 'ma':
				cseRequest.ma = arguments.getOne(arg, greedy = True)

			# Some filter criteria attributes are stored as lists, and can appear multiple times
			# in the query. A single entry could also have multiple values separated by "+"
			# The goal is to store them as a single list in the filterCriteria
			case 'ty' | 'lbl' | 'cty':
				filterCriteria[arg] = []
				while (_a := arguments.getOne(arg, greedy = True)) is not None:
					filterCriteria[arg].extend(_a.split(sep))	# type: ignore [union-attr]
				
			# Extract further request arguments from the coaprequest
			# add all the args to the filterCriteria
			# Some args are lists, so keep them as lists from the multi-dict
			case _:
				filterCriteria[arg] = arguments.get(arg, flatten = True, greedy = True)

	# Add the filterCriteria to the request
	if len(filterCriteria) > 0:
		dct['fc'] = filterCriteria

	if attributeList:
		dct['pc'] = { 'm2m:atrl': attributeList }
		cseRequest.ct = RC.defaultSerialization
	else:
		# De-Serialize the content
		pc = deserializeContent(cseRequest.originalData, cseRequest.ct) # may throw an exception
		
		# Remove 'None' fields *before* adding the pc, because the pc may contain 'None' fields that need to be preserved
		dct = removeNoneValuesFromDict(dct)

		# Add the primitive content and 
		dct['pc'] = pc		# The actual content

	cseRequest.originalRequest	= dct	# finally store the oneM2M request object in the cseRequest

	return cseRequest


def deserializeContent(data:bytes, contentType:ContentSerializationType) -> JSON:
	"""	Deserialize a data structure.
		Supported media serialization types are JSON and cbor.

		Args:
			data: The data to deserialize.
			contentType: The content type of the data.
		
		Return:
			The deserialized data structure.

		Raises:
			*UNSUPPORTED_MEDIA_TYPE* if the content type is not supported.
			*BAD_REQUEST* if the data is malformed.
	"""
	dct = None
	# ct = ContentSerializationType.getType(contentType, default = CSE.defaultSerialization)
	if data:
		try:
			if (dct := deserializeData(data, contentType)) is None:
				raise UNSUPPORTED_MEDIA_TYPE(f'Unsupported media type for content-type: {contentType.name}', data = None)
		except UNSUPPORTED_MEDIA_TYPE as e:
			raise
		except Exception as e:
			raise BAD_REQUEST(L.logWarn(f'Malformed request/content? {str(e)}'), data = None)
	
	return dct


def curlFromRequest(request:JSON) -> str:
	"""	Create a cURL command from a request.
	
		Args:
			request: The request to create the cURL command from.
		
		Return:
			A cURL command.
	"""
	if not request:
		return 'No request available'

	curl = f"""\
curl -X {[None, 'POST', 'GET', 'PUT', 'DELETE', 'POST' ][request['op']]} '{Configuration.http_address}{Configuration.http_root}/{request['to']}' \\
  -H 'X-M2M-Origin: {request['fr']}' \\
  -H 'X-M2M-RVI: {request['rvi']}' \\
  -H 'X-M2M-RI: {request['rqi']}'"""
	
	if (ot := request.get('ot')):
		curl += f" \\\n  -H 'X-M2M-OT: {ot}'"
	if (pc := request.get('pc')):
		curl += f" \\\n  -H 'Content-Type: {request['csz']}{';ty=' + str(request['ty']) if 'ty' in request else ''}'"
		curl += f" \\\n  -d '{json.dumps(pc)}'"
	
	return curl
