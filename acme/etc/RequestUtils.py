#
#	RequestUtils.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module contains various utilty functions that are used to work with requests and responses. """

from __future__ import annotations

import cbor2, json
from typing import Any, cast, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlunparse, urlencode

from .DateUtils import getResourceDate
from .Types import ContentSerializationType, JSON, RequestType, ResponseStatusCode, Result, ResourceTypes, Operation
from .Constants import Constants
from ..services.Logging import Logging as L
from ..helpers import TextTools
from ..etc.ResponseStatusCodes import ResponseStatusCode


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
		case x if x.startswith('///'):
			u[2] = f'/_{u[2][2:]}'
			url = urlunparse(u)
		case x if x.startswith('//'):
			u[2] = f'/~{u[2][1:]}'
			url = urlunparse(u)

	return url


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
		return ContentSerializationType.toContentSerialization(ct)

	elif csz:
		# if csz is given then build an intersection between the given list and
		# the list of supported serializations. Then take the first one
		# as the one to use.
		common = [x for x in csz if x in ContentSerializationType.supportedContentSerializations()]	# build intersection, keep the old sort order
		if len(common) == 0:
			return None
		return ContentSerializationType.toContentSerialization(common[0]) # take the first
	
	# Just use default serialization.
	return defaultSerialization


def requestFromResult(inResult:Result, 
					  originator:Optional[str] = None, 
					  ty:Optional[ResourceTypes] = None, 
					  op:Optional[Operation] = None, 
					  isResponse:Optional[bool] = False) -> Result:
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
			`Result` object with the response.

		See Also:
			`responseFromResult`
	"""
	from ..services import CSE

	req:JSON = {}

	# Assign the From and to of the request. An assigned originator has priority for this
	# TO and FROM are optional in a response. So, don't put them in by default.
	if not isResponse or (isResponse and CSE.request.sendToFromInResponses):
		if originator:
			req['fr'] = CSE.cseCsi if isResponse else originator
			req['to'] = inResult.request.id if inResult.request.id else originator
		elif inResult.request and inResult.request.originator:
			req['fr'] = CSE.cseCsi if isResponse else inResult.request.originator
			req['to'] = inResult.request.originator if isResponse else inResult.request.id
		else:
			req['fr'] = CSE.cseCsi
			req['to'] = inResult.request.id if inResult.request.id else CSE.cseCsi


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
	if inResult.request.rset:
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
	from ..services import CSE 
	from ..etc.Utils import uniqueRI	# Leave it here to avoid circular init

	r = {	'fr': CSE.cseCsi,
			'rqi': uniqueRI(),
			'rvi': CSE.releaseVersion,
		}
	r.update(kwargs)
	return r
