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

import json, requests, logging, os, sys, traceback, threading
from typing import Any, Callable, List, Tuple, Union
from Configuration import Configuration
from Constants import Constants as C
from Types import ResourceTypes as T, Result,  RequestHeaders, Operation, RequestArguments, FilterUsage, DesiredIdentifierResultType, ResultContentType, ResponseType, ResponseCode as RC, FilterOperation, Parameters, ContentSerializationType
from Types import CSERequest
import CSE, Utils
from Logging import Logging
from resources.Resource import Resource

from werkzeug.datastructures import MultiDict

from CoapDissector import CoapDissector, CoapMessage, CoapMessageRequest, CoapMessageResponse
import UdpServer

from urllib.parse import urlparse

sync_ack_lock	= threading.Event()
sync_ack		= dict()

class CoapBinding(IBindingLayer):

	def __init__(self) -> None:
		Logging.log('>>> CoapBinding.__init__')
		self.transport		= UdpServer.UdpServer(Configuration.get('coap.listenIF'), Configuration.get('coap.port'), self.process_incoming_data)
		self.rootPath		= Configuration.get('coap.root')
		self.serverAddress      = Configuration.get('coap.server.address')
		self.useTLS 		= Configuration.get('cse.security.useTLS')

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

	def process_incoming_data(self, data, client_address):
		global sync_ack, sync_ack_lock
		Logging.log(f'>>> CoapBinding.process_incoming_data: {str(client_address)}')
		coapMessage = CoapDissector.decode(p_data = data, p_source = client_address)
		Logging.log(f'CoapBinding.process_incoming_data: coapMessage = {str(coapMessage)}')
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
				raise Exception(f'CoapBinding.process_incoming_data: Unknown message type', f'{str(coapMessage)}')
			self.transport.sendTo((coapResponse, client_address))
		elif isinstance(coapMessage, CoapMessageResponse):
			Logging.log(f'>>> CoapBinding.process_incoming_data: {str(client_address)}')
			if len(sync_ack) != 0:
				if str(coapMessage.mid) in sync_ack:
					sync_ack[str(coapMessage.mid)] = coapMessage
					# Set lock
					sync_ack_lock.set()
				else:
					raise Exception(f'CoapBinding.process_incoming_data: Unbalamnced ACK received for {str(coapMessage.mid)}', f'{str(coapMessage)}')
		else:
			pass

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
		return self.sendRequest(requests.get, url, originator)

	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, headers:dict=None) -> Result:
		return self.sendRequest(requests.post, url, originator, ty, data, headers=headers)

	def sendUpdateRequest(self, url:str, originator:str, data:Any) -> Result:
		return self.sendRequest(requests.put, url, originator, data=data)

	def sendDeleteRequest(self, url:str, originator:str) -> Result:
		return self.sendRequest(requests.delete, url, originator)

	def sendRequest(self, method:Callable , url:str, originator:str, ty:T=None, data:Any=None, parameters:Parameters=None, ct:ContentSerializationType=None, targetResource:Resource=None, headers:dict=None) -> Result: # TODO Check if headers is required
		global sync_ack, sync_ack_lock
		Logging.log(f'>>> CoapBinding.sendRequest: url:{url} - from:{originator} - ty:{ty} - ct:{ct} - headers:{headers}')
		ct = CSE.defaultSerialization if ct is None else ct

		request = CoapMessageRequest()
		request.type = 0 # CON
		request.token = None
		request.mid = int(Utils.uniqueID()) % 32768 # Only positive signed short value

		o = urlparse(url)
		request.uri_host = o.hostname
		request.uri_port = int(o.port)
		if o.path[0] == '/':
			request.uri_path = o.path[1:]
		else:
			request.uri_path = o.path
		Logging.log(f'CoapBinding.sendRequest: host:{request.uri_host} - port:{request.uri_port} - path:{request.uri_path}')

		# Set basic headers
		request.ty = int(ty) if ty is not None else ''
		Logging.log(f'CoapBinding.sendRequest: ty:{request.ty}')
		if ct == ContentSerializationType.XML: # See TS-0008 Table 6.2.2.2-1: CoAP oneM2M Specific Content-Formats
			request.content_type = 41
		elif ct == ContentSerializationType.Json:
			request.content_type = 10001
		else:
			request.content_type = None # FIXME: Think about serialization CBOR & TEXT as default
			raise Exception('CoapBinding.sendRequest', 'To be implemented')
		request.accept = request.content_type

		request.originator = originator
		request.rqi = Utils.uniqueRI()
		request.rvi = C.hfvRVI

		# Add additional headers
		if headers is not None:
			if C.hfcEC in headers:				# Event Category
				request.ec = headers[C.hfcEC]

		# Set HTTP method
		s = method.__name__.upper()
		if s == 'GET':
			request.code = CoapDissector.GET.number
		elif s == 'POST':
			request.code = CoapDissector.POST.number
		elif s == 'PUT':
			request.code = CoapDissector.PUT.number
		elif s == 'DELETE':
			request.code = CoapDissector.DELETE.number
		else:
			raise Exception(f'CoapBinding.sendRequest: Invalid code: {s}')
		
		# Set HTTP message
		request.payload = str(data) if data is not None else None

		# Send CoAP message and wait the response
		try:
			data = CoapDissector.encode(request)
			Logging.logDebug(f'Sending request: method:{s} dest:{url}')
			Logging.logDebug(f'Request ==>:\n{str(data) if data is not None else ""}\n')
			self.transport.sendTo((data, (o.hostname, o.port)))
			sync_ack[str(request.mid)] = None
			Logging.logDebug(f'CoapBinding.sendRequest: Wait ACK for {str(request.mid)}')
			while not sync_ack_lock.is_set():
				sync_ack_lock.wait(1)
			response = sync_ack[str(request.mid)]
			sync_ack.pop(str(request.mid))
			sync_ack_lock.clear()
			Logging.logDebug(f'CoapBinding.sendRequest: Got ACK for {str(request.mid)} - response:{response}')
		except Exception as e:
			Logging.logWarn(f'CoapBinding.sendRequest: Failed to send request: {str(e)}')
			return Result(rsc=RC.targetNotReachable, dbg='target not reachable')
		rsc = None
		if response.code == 69:					# TS-0008 Table 6.2.4-1: Mapping between oneM2M Response Status Code and CoAP Response Code
			rsc = 2000							# OK
		elif response.code == 65:				# TS-0008 Table 6.2.4-1: Mapping between oneM2M Response Status Code and CoAP Response Code
			rsc = 2001							# Created
		elif response.code == 66:
			rsc = 2002							# Deleted
		elif response.code == 67:
			rsc = 2003							# Valid
		elif response.code == 68:
			rsc = 2004							# Changed
		elif response.code == 128:
			rsc = 4000							# Bad Request
		elif response.code == 131:
			rsc = 4003							# Forbidden
		elif response.code == 132:
			rsc = 4004							# Not Found
		elif response.code == 160:
			rsc = 5000							# Server Internal Error
		else:
			Logging.logErr(f'CoapBinding.sendRequest: {str(response.code)}')
		Logging.logDebug(f'CoapBinding.sendRequest: rsc={rsc}')
		rc = RC(rsc if not rsc is None else RC.internalServerError)
		jsn = None
		if not response.payload is None:
			jsn = json.loads(response.payload)
		Logging.logDebug(f'CoapBinding.sendRequest: jsn={jsn}')
		return Result(jsn=jsn, rsc=rc)
	# End of method sendRequest

	def shutdown(self) -> bool:
		Logging.log('CoapBinding shut down')
		self.transport.close()
		return True
	# End of method shutdown

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
		if value == 41 or value == 10002 or value == 10006 or value == 10008 or value == 10014: # See TS-0008 Table 6.2.2.2-1: CoAP oneM2M Specific Content-Formats
			rh.contentType = 'application/vnd.onem2m-res+xml'
		elif value == 50 or value == 10001 or value == 10003 or value == 10007 or value == 10000:
			rh.contentType = 'application/vnd.onem2m-res+json'
		else:
			rh.contentType = None # FIXME: Think about serialization XML, CBOR & TEXT
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

	def _prepareResponse(self, p_coapMessage:CoapMessageRequest, result:Result):
		response = CoapMessageResponse()
		response.version = p_coapMessage.version
		response.type = 2 #FIXME: CoapDissector.ACK
		response.mid = p_coapMessage.mid

		if result.rsc is not None:
			response.rsc = '%d' % result.rsc				# set the response status code
			if result.rsc == 2000:                  		# TS-0008 Table 6.2.4-1: Mapping between oneM2M Response Status Code and CoAP Response Code
				response.code = 69							# OK
			elif result.rsc == 1000 or result.rsc == 2001:	# TS-0008 Table 6.2.4-1: Mapping between oneM2M Response Status Code and CoAP Response Code
				response.code = 65							# Created
			elif result.rsc == 2002:
				response.code = 66							# Deleted
			elif result.rsc == 2003:
				response.code = 67							# Valid
			elif result.rsc == 2004:
				response.code = 68							# Changed
			elif result.rsc == 2005:
				response.code = 69							# Content
			elif result.rsc == 4000 or result.rsc == 4001 or result.rsc == 4002 or result.rsc == 4004 or result.rsc == 4110:
				response.code = 128							# Bad Request
			elif result.rsc == 4003 or result.rsc == 4101 or result.rsc == 4103 or result.rsc == 4105 or result.rsc == 4106 or result.rsc == 4107 or result.rsc == 4109 or result.rsc == 4109:
				response.code = 131							# Forbidden
			elif result.rsc == 4004 or result.rsc == 4008:
				response.code = 132							# Not Found
			elif result.rsc == 5000:
				response.code = 160							# Server Internal Error
			else:
				raise Exception('CoapBinding._prepareResponse', '%s' % str(result.rsc))
		response.rqi = p_coapMessage.rqi			# setheaders['X-M2M-RI']
		response.rvi = C.hfvRVI
		response.svi = C.hfvRVI
		# Content-type
		if C.hfvContentType.find('xml') != -1: # FIXME: Think about serialization XML, CBOR & TEXT
			response.content_type = 41
		elif C.hfvContentType.find('json') != -1:
			response.content_type = 10001
		if result.resource is not None:
			response.rqi = result.resource.json.get('ri')
		response.payload = result.toString()

		Logging.logDebug('<== Response (RSC: %d):\n%s\n' % (result.rsc, str(response.payload)))
		return CoapDissector.encode(response)

	def _prepareException(self, e: Exception) -> Result:
		Logging.logErr(traceback.format_exc())
		return Result(rsc=RC.internalServerError, dbg='encountered exception: %s' % traceback.format_exc().replace('"', '\\"').replace('\n', '\\n'))

	# End of class CoapBinding

# End of file
