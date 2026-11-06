#
#	handlers.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	HTTP request handlers for the DAS server
#
"""	HTTP request handlers for the DAS server. """

import logging
from typing import Optional
from aiohttp import web
from rich import inspect
from .Configuration import Configuration
from .Rules import Rules

log = logging.getLogger(__name__)

_config : Configuration = None
_rules : Rules = None

def _responseHeaders(request: web.Request, rsc: str, origin: str = 'Cunknown') -> dict:
	"""	Build a fresh response-headers dict for one authorize() response, with the
		"X-M2M-RSC" reflecting the actual outcome of this response.
	"""
	return {
		'X-M2M-RI': request.headers['X-M2M-RI'],
		'X-M2M-RVI': request.headers['X-M2M-RVI'],
		'X-M2M-RSC': rsc,
		'X-M2M-Origin': origin,
	}


async def authorize(request: web.Request) -> web.Response:
	"""	Handle a Dynamic Authorization Consultation request from a CSE.

	"""

	log.debug(f'Received dynamic authorization request from {request.remote} to {request.path}')
	log.debug(f'Request headers: {request.headers}')
	log.debug(f'Request body: {await request.text()}')

	# Get the orginator first.
	cseOriginator = request.headers.get('X-M2M-Origin', 'unknown')

	# Find the correct own Originator for the originator. _config.cses is a plain dict, so
	# .get() never raises KeyError - an unrecognized CSE originator must be checked explicitly.
	cseConfig = _config.cses.get(cseOriginator)
	if cseConfig is None:
		log.error(f'Unknown CSE originator "{cseOriginator}" in dynamic authorization request')
		# No "aeOriginator" exists for an unrecognized caller, so "X-M2M-Origin" stays the
		# 'Cunknown' placeholder here - this is an error response, not a dynamic authorization
		# decision, so there is nothing meaningful to report as the origin.
		return web.json_response({ 'dbg': f'Unknown CSE originator "{cseOriginator}"' },
								  headers=_responseHeaders(request, '4103'),
								  status=400)
	origin = cseConfig.get('aeOriginator', 'Cunknown')

	if request.content_type != 'application/json':
		log.error(f'Invalid content type "{request.content_type}" in dynamic authorization request')
		return web.json_response({ 'dbg': f'Invalid content type "{request.content_type}". Only "application/json" is supported.' },
									headers=_responseHeaders(request, '4000', origin),
									status=400)



	result = await _handleSecurityRequest(request, cseOriginator)
	if 'dbg' in result:
		log.error(f'Dynamic authorization request failed: {result["dbg"]}')
		return web.json_response(result,
								 headers=_responseHeaders(request, '4000', origin),
								 status=400)
	log.debug(f'Dynamic authorization request succeeded: {result}')
	return web.json_response(result,
							 headers=_responseHeaders(request, '2000', origin),
							 status=200)



def installRoutes(app: web.Application, authorizeEndpoint: str) -> None:
	"""	Install the DAS server's HTTP routes. """
	global _config, _rules

	# app contains the configuration and rules for the DAS server
	# Make them available as global variables for the handlers to use, because we
	# don't have access to the app object directly in the handler functions.
	_config = app['config']
	_rules = app['rules']

	app.router.add_post(authorizeEndpoint, authorize)
	app.router.add_post(f'{authorizeEndpoint}/{{resourceID:.*}}', authorize)


#############################################################################


async def _handleSecurityRequest(request: web.Request, cseOriginator: str) -> Optional[dict]:
	"""	Handle a security request. """

	# Get the JSON body of the request
	try:
		content = await request.json()
	except ValueError as e:
		log.error(f'Invalid JSON body in dynamic authorization request: {e}')
		return { 'dbg': f'Invalid JSON body: {e}' }

	# Check for the "m2m:seci" field in the request
	
	if not (seci := content.get('m2m:seci')):
		log.error('Missing "m2m:seci" in dynamic authorization request')
		return { 'dbg': 'Missing "m2m:seci" in request' }

	# Check for the "sit" field in the "m2m:seci" object and handle accordingly
	result: dict = {}
	match seci.get('sit'):
		case 1:	# Dynamic Authorization Request
			log.debug('Received a dynamic authorization request')

			if not (dreq := seci.get('dreq')):
				log.error('Missing "dreq" in dynamic authorization request')
				return { 'dbg': 'Missing "dreq" in request' }

			if (asi := dreq.get('asi')):
				log.warning(f'Dynamic Authorization Request: Received ASI: {asi} - Unsupported.')

			# Create a response with the required fields. For now, only support ACPInfos, NOT tokens
			result = {	'm2m:seci': { 
							'sit': 2, 
							'dai': {
								'gp': _getAcrsForRequest(dreq, cseOriginator)
							}
					} }	

			# Handle Proposed Privilegs Lifetime
			# For the moment, we just check and return the same valuue. But this could be used to limit the 
			# lifetime of the proposed privileges, e.g. to a maximum of 1 hour.
			if (ppl := dreq.get('ppl')):
				result['m2m:seci']['dai']['pl'] = ppl


		case 2:	# Dynamic Authorization Response
			log.error('Received a dynamic authorization response. This is unexpected, as the DAS server should only receive requests, not responses.')
			result = { 'dbg': 'Unexpected dynamic authorization response received' }
			
		case _:
			log.error(f'Invalid or unsupported "sit" value in dynamic authorization request: {seci.get("sit")}')
			result = { 'dbg': f'Invalid or unsupported "sit" value: {seci.get("sit")}' }
	

	return result


def _getAcrsForRequest(dreq: dict, cseOriginator: str) -> list[dict]:
	"""	Get the Access Control Rules (ACRs) for the given dynamic authorization request,
		by evaluating the configured rule files (see `Rules`).
	"""

	return _rules.getAcrs(cseId=cseOriginator,
						   originator=dreq.get('org'),
						   resourceId=dreq.get('trid'),
						   resourceType=dreq.get('trt'),
						   operation=dreq.get('op'))