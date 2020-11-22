#
#	HttpDissector.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

import json
from typing import Any, List, Tuple, Union, Dict

from Constants_ import Constants_ as C
from Types import ResourceTypes as T, ResponseCode as RC
from Types import Result,  RequestHeaders, Operation, RequestArguments, FilterUsage, DesiredIdentifierResultType, ResultContentType, ResponseType, FilterOperation
from Types import CSERequest
from Configuration import Configuration
from Logging import Logging
from flask import Request
import Utils
import CSE

#
#	HTTP request helper functions
#

def dissectHttpRequest(request:Request, operation:Operation, _id:Tuple[str, str, str]) -> Result:
	cseRequest = CSERequest()

	# get the data first. This marks the request as consumed 
	cseRequest.data = request.get_data(as_text=True)	# alternative: request.data.decode("utf-8")
	
	# handle ID's 
	cseRequest.id, cseRequest.csi, cseRequest.srn = _id

	# No ID, return immediately 
	if cseRequest.id is None and cseRequest.srn is None:
		return Result(rsc=RC.notFound, dbg='missing identifier', status=False)

	if (res := Utils.getRequestHeaders(request)).data is None:
		return Result(rsc=res.rsc, dbg=res.dbg, status=False)
	cseRequest.headers = res.data
	
	try:
		cseRequest.args, msg = Utils.getRequestArguments(request, operation)
		if cseRequest.args is None:
			return Result(rsc=RC.badRequest, dbg=msg, status=False)
	except Exception as e:
		return Result(rsc=RC.invalidArguments, dbg='invalid arguments (%s)' % str(e), status=False)
	cseRequest.originalArgs	= request.args.copy()	#type: ignore
	if cseRequest.data is not None and len(cseRequest.data) > 0:
		try:
			cseRequest.json = json.loads(Utils.removeCommentsFromJSON(cseRequest.data))
		except Exception as e:
			Logging.logWarn('Bad request (malformed content?)')
			return Result(rsc=RC.badRequest, dbg=str(e), status=False)
	return Result(request=cseRequest, status=True)

