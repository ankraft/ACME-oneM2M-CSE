#
#	CoapBinding.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

from IBindingLayer import IBindingLayer

import json, requests, logging, os, sys, traceback, queue
from typing import Any, Callable, List, Tuple, Union
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result,  RequestHeaders, Operation, RequestArguments, FilterUsage, DesiredIdentifierResultType, ResultContentType, ResponseType, ResponseCode as RC, FilterOperation
from Types import CSERequest
import CSE, Utils
from Logging import Logging
from resources.Resource import Resource

from werkzeug.datastructures import MultiDict

from CoapDissector import CoapDissector, CoapMessage, CoapMessageRequest, CoapMessageResponse
import UdpServer

from urllib.parse import urlparse

class CoapBinding(IBindingLayer):

	def __init__(self) -> None:
		self.transport		= UdpServer.UdpServer(Configuration.get('coap.listenIF'), Configuration.get('coap.port'), self.process_incoming_data)
		self.rootPath		= Configuration.get('coap.root')
		self.useTLS 		= Configuration.get('cse.security.useTLS')
		self.serverID		= f'ACME {C.version}' 	# The server's ID for http response headers

		Logging.log('Registering CoAP server root at: {self.rootPath}}')
		if self.useTLS:
			Logging.log('TLS enabled. CoAP server serves via coaps.')

		# Keep some values for optimization
		self.csern = Configuration.get('cse.rn') 
		self.cseri = Configuration.get('cse.ri')

		# Register the endpoint for the web UI
		if Configuration.get('cse.webui.enable'):
			pass # FIXME How to start WebUI :(

	def run(self): # This does NOT return
		Logging.log('>>> CoapBinding.run')
		try:
			self.transport.listen(10)
		except KeyboardInterrupt:
			self.transport.close()
			# Return
		# End of run method

	def process_incoming_data(self, data, client_address, p_queue:queue):
		Logging.log('>>> CoapBinding.process_incoming_data: {str(client_address)}')
		coapMessage = CoapDissector.decode(p_data = data, p_source = client_address)
		Logging.log('CoapBinding.process_incoming_data: coapMessage = %s' % str(coapMessage))
		coapResponse = None
		if isinstance(coapMessage, CoapMessageRequest):
			if coapMessage.code == CoapDissector.GET.number:
				coapResponse = self.handleGET(coapMessage)
			elif coapMessage.code == CoapDissector.POST.number: 		
				coapResponse = self.handlePOST(coapMessage, client_address)
			elif coapMessage.code == CoapDissector.PUT.number: 		
				coapResponse = self.handlePUT(coapMessage)
			elif coapMessage.code == CoapDissector.DELETE.number: 		
				coapResponse = self.handleDELETE(coapMessage)
			else:
				raise Exception('CoapBinding.process_incoming_data: Unknown message type', '%s' % str(coapMessage))
		elif isinstance(coapMessage, CoapMessageResponse):
			pass
		else:
			pass
		if not coapResponse is None:
			p_queue.put((CoapDissector.encode(coapResponse), client_address))

	def handleGET(self, coapMessage:CoapMessageRequest) -> CoapMessageResponse:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Retrieve: /%s' % coapMessage.uri_path)	# path = request.path  w/o the root
		CSE.event.httpRetrieve() # type: ignore
		try:
			result = self.CoapMessage2Result(coapMessage, Operation.RETRIEVE, Utils.retrieveIDFromPath(coapMessage.uri_path, self.csern, self.cseri))
			if result.status:
				result = CSE.request.retrieveRequest(result.request)
		except Exception as e:
			result = self._prepareException(e)
		return self._prepareResponse(coapMessage, result)

	def handlePOST(self, coapMessage:CoapMessageRequest, client_address) -> CoapMessageResponse:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Create: /%s' % coapMessage.uri_path)	# path = request.path  w/o the root
		CSE.event.httpCreate()	# type: ignore
		try:
			result = self.CoapMessage2Result(coapMessage, Operation.CREATE, Utils.retrieveIDFromPath(coapMessage.uri_path, self.csern, self.cseri))
			if result.status:
				Logging.logDebug('Body: \n' + result.request.data)
				result = CSE.request.createRequest(result.request)
		except Exception as e:
			result = self._prepareException(e)
		return self._prepareResponse(coapMessage, result)

	def handlePUT(self, coapMessage:CoapMessageRequest) -> CoapMessageResponse:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Update: /%s' % coapMessage.uri_path)	# path = request.path  w/o the root\
		CSE.event.httpUpdate() # type: ignore
		try:
			result = self.CoapMessage2Result(coapMessage, Operation.UPDATE, Utils.retrieveIDFromPath(coapMessage.uri_path, self.csern, self.cseri))
			if result.status:
				result = CSE.request.updateRequest(result.request)
		except Exception as e:
			result = self._prepareException(e)
		return self._prepareResponse(coapMessage, result)

	def handleDELETE(self, coapMessage:CoapMessageRequest) -> CoapMessageResponse:
		Utils.renameCurrentThread()
		Logging.logDebug('==> Delete: /%s' % coapMessage.uri_path)	# path = request.path  w/o the root
		CSE.event.httpDelete() # type: ignore
		try:
			result = self.CoapMessage2Result(coapMessage, Operation.DELETE, Utils.retrieveIDFromPath(coapMessage.uri_path, self.csern, self.cseri))
			if result.status:
				result = CSE.request.deleteRequest(result.request)
		except Exception as e:
			result = self._prepareException(e)
		return self._prepareResponse(coapMessage, result)

	def sendRetrieveRequest(self, url:str, originator:str) -> Result:
		Logging.log('>>> CoapBinding.sendRetrieveRequest: %s - %s' % (url, originator))

	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, headers:dict=None) -> Result:
		Logging.log('>>> CoapBinding.sendCreateRequest: %s - %s' % (url, originator))

	def sendUpdateRequest(self, url:str, originator:str, data:Any) -> Result:
		Logging.log('>>> CoapBinding.sendUpdateRequest: %s - %s' % (url, originator))
		pass

	def sendDeleteRequest(self, url:str, originator:str) -> Result:
		Logging.log('>>> CoapBinding.sendDeleteRequest: %s - %s' % (url, originator))

	def sendRequest(self, method:Callable , url:str, originator:str, ty:T=None, data:Any=None, ct:str='application/json', headers:dict=None) -> Result:
		Logging.log('>>> CoapBinding.sendRequest: %s - %s' % (url, originator))

	def CoapMessage2Result(self, p_coapMessage:CoapMessageRequest, p_operation:Operation, _id:Tuple[str, str, str]) -> Result:
		cseRequest = CSERequest()		
		# get the data first. This marks the request as consumed 
		cseRequest.data = p_coapMessage.payload
		# handle ID's 
		cseRequest.id, cseRequest.csi, cseRequest.srn = _id
		# No ID, return immediately 
		if cseRequest.id is None and cseRequest.srn is None:
			return Result(rsc=RC.notFound, dbg='missing identifier', status=False)
		if (res := self.getRequestHeaders(p_coapMessage)).data is None:
			return Result(rsc=res.rsc, dbg=res.dbg, status=False)
		cseRequest.headers = res.data
		try:
			cseRequest.args, msg = self.getRequestArguments(p_coapMessage, p_operation)
			if cseRequest.args is None:
				return Result(rsc=RC.badRequest, dbg=msg, status=False)
		except Exception as e:
			return Result(rsc=RC.invalidArguments, dbg='invalid arguments (%s)' % str(e), status=False)
		cseRequest.originalArgs	= MultiDict([]) # FIXME request.args.copy()	#type: ignore
		if cseRequest.data is not None and len(cseRequest.data) > 0:
			try:
				cseRequest.json = json.loads(Utils.removeCommentsFromJSON(cseRequest.data))
			except Exception as e:
				Logging.logWarn('Bad request (malformed content?)')
				return Result(rsc=RC.badRequest, dbg=str(e), status=False)
		return Result(request=cseRequest, status=True)

	def getRequestHeaders(self, p_coapMessage:CoapMessageRequest) -> Result:
		rh 								= RequestHeaders()
		rh.originator 					= p_coapMessage.originator
		rh.requestIdentifier			= p_coapMessage.rqi
		rh.requestExpirationTimestamp 	= p_coapMessage.ot
		rh.responseExpirationTimestamp 	= p_coapMessage.rset
		rh.operationExecutionTime 		= p_coapMessage.oet
		rh.releaseVersionIndicator 		= p_coapMessage.rvi

		if (rtu := p_coapMessage.rturi) is not None: # handle rtu list
			rh.responseTypeNUs = rtu.split('&')

		# content-type
		value = p_coapMessage.content_type
		if value == 10000: # See TS-0008 Table 6.2.2.2-1: CoAP oneM2M Specific Content-Formats
			rh.contentType = 'application/vnd.onem2m-res+xml'
		elif value == 10001:
			rh.contentType = 'application/vnd.onem2m-res+json'
		else:
			rh.contentType = None
		if rh.contentType is not None:
			if not rh.contentType.startswith(tuple(C.supportedContentHeaderFormat)):
				rh.contentType 	= None
			else:
				if p_coapMessage.ty is not None:
					rh.resourceType = p_coapMessage.ty
					#else:
					#	return Result(rsc=RC.badRequest, dbg='Unknown resource type: %s' % t)
		return Result(data=rh, rsc=RC.OK)

	def getRequestArguments(self, p_coapMessage:CoapMessageRequest, p_operation:Operation) -> Tuple[RequestArguments, str]:
		result = RequestArguments(operation=p_operation, request=p_coapMessage)
		# copy for greedy attributes checking
		args = MultiDict([]) # FIXME request.args.copy()	 	# type: ignore
		return Utils.processRequestArguments(result, args, p_operation)

	def _prepareResponse(self, p_coapMessage:CoapMessageRequest, result:Result) -> CoapMessageResponse:
		# if isinstance(result.resource, Resource):
		# 	r = json.dumps(result.resource.asJSON())
		# elif result.dbg is not None:
		# 	r = '{ "m2m:dbg" : "%s" }' % result.dbg.replace('"', '\\"')
		# elif isinstance(result.resource, dict):
		# 	r = json.dumps(result.resource)
		# elif isinstance(result.resource, str):
		# 	r = result.resource
		# elif isinstance(result.jsn, dict):		# explicit json
		# 	r = json.dumps(result.jsn)
		# elif result.resource is None and result.jsn is None:
		# 	r = ''
		# else:
		# 	r = ''
		# 	result.rsc = RC.notFound

		response = CoapMessageResponse()
		response.version = p_coapMessage.version
		response.type = 2 #FIXME: CoapDissector.ACK
		response.mid = p_coapMessage.mid

		if result.rsc is not None:
			response.rsc = '%d' % result.rsc		# set the response status code
			if result.rsc == 2001:                  # TS-0008 Table 6.2.4-1: Mapping between oneM2M Response Status Code and CoAP Response Code
				response.code = 65					# Created
			elif result.rsc == 2002:
				response.code = 66					# Deleted
			elif result.rsc == 2003:
				response.code = 67					# Valid
			elif result.rsc == 2004:
				response.code = 68					# Changed
			elif result.rsc == 2005:
				response.code = 69					# Content
			elif result.rsc == 4105:
				response.code = 400					# Bad Request
			elif result.rsc == 4107:
				response.code = 500					# Server Internal Error
			elif result.rsc == 5000:
				response.code = 500					# Server Internal Error
			else:
				raise Exception('CoapBinding._prepareResponse', '%s' % str(result.rsc))
		response.rqi = p_coapMessage.rqi			# setheaders['X-M2M-RI']
		response.rvi = C.hfvRVI
		response.svi = C.hfvRVI
		# Content-type
		if C.hfvContentType.find('xml') != -1:
			response.content_type = 10000
		elif C.hfvContentType.find('json') != -1:
			response.content_type = 10001
			if result.resource is not None:
				response.location_path = result.resource.json.get('ri')
			response.payload = result.toString()

		Logging.logDebug('<== Response (RSC: %d):\n%s\n' % (result.rsc, str(response.payload)))
		return response

	def _prepareException(self, e: Exception) -> Result:
		Logging.logErr(traceback.format_exc())
		return Result(rsc=RC.internalServerError, dbg='encountered exception: %s' % traceback.format_exc().replace('"', '\\"').replace('\n', '\\n'))

	# End of class CoapBinding

# End of file