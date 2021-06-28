#
#	MQTTClient.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of an MQTT Client for an MQTT Mcx binding implementation.
#

from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from Logging import Logging as L
from Configuration import Configuration
from Constants import Constants as C
from helpers.MQTTConnection import MQTTConnection, MQTTHandler, idToMQTT, mqttToId
from Types import Operation, RequestHeaders, CSERequest, ContentSerializationType, Result, ResponseCode as RC, RequestHandler
import CSE, Utils


# TODO events

class MQTTClientHandler(MQTTHandler):

	def __init__(self, mqttClient:MQTTClient) -> None:
		super().__init__()
		self.mqttClient = mqttClient
		self.topicPrefix = mqttClient.topicPrefix
		self.topicPrefixCount = len(self.topicPrefix.split('/'))	# Count the elements for the prefix

		# TODO optimize - same table is in httpserver
		self._requestHandlers:RequestHandler = {
			Operation.RETRIEVE	: CSE.request.retrieveRequest,
			Operation.CREATE	: CSE.request.createRequest,
			Operation.UPDATE	: CSE.request.updateRequest,
			Operation.DELETE	: CSE.request.deleteRequest
		}


	def onConnect(self, connection:MQTTConnection) -> None:
		"""	When connected to a broker then register the topics the CSE listens to.
		"""
		# Subscribe to general requests
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/req/+/{connection.clientName}/#', self._requestCB)

		# Subscribe to responses
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/resp/+/{connection.clientName}/#', self._responseCB)

		# Subscribe to registration requests
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/reg_req/+/{connection.clientName}/#', self._registrationRequestCB)


	def onDisconnect(self, connection:MQTTConnection) -> None:
		pass




	# #
	# #	Various request, register and response callbacks
	# #



	def _requestCB(self, connection:MQTTConnection, topic:str, data:bytes) -> None:
		L.isDebug and L.logDebug(f'==> REQUEST {topic}, {str(data)}')# TODO hex output for cbor
		ts = topic.split('/')
		originator, _ = mqttToId(ts[self.topicPrefixCount + 2])
		receiver, _   = mqttToId(ts[self.topicPrefixCount + 3])
		contentType   = ts[self.topicPrefixCount + 4]

		if not (result := self.dissectMQTTRequest(data, contentType)).status:
			L.logWarn(str(result))

			return # TODO error

		responseResult = self._requestHandlers[result.request.op](result.request)
		# TODO real response
		L.logWarn(str(responseResult))
		L.logDebug(f'REQUEST originator:{originator}, receiver:{receiver}, type:{contentType}')
		connection.publish('test', f'{topic}, {str(responseResult)}'.encode())




	def _responseCB(self, connection:MQTTConnection, topic:str, data:str) -> None:
		ts = topic.split('/')
		L.logDebug(f'RESPONSE {topic}, {data}, {ts[-1]}')
		connection.publish('test', f'{topic}, {data}, {ts[-1]}'.encode())



	def _registrationRequestCB(self, connection:MQTTConnection, topic:str, data:str) -> None:
		ts = topic.split('/')
		L.logDebug(f'REGISTRATION {topic}, {data}, {ts[-1]}')
		connection.publish('test', f'{topic}, {data}, {ts[-1]}'.encode())
	

	def dissectMQTTRequest(self, data:bytes, contenType:str) -> Result:
		cseRequest = CSERequest()
		cseRequest.data = data
		cseRequest.headers = RequestHeaders()
		cseRequest.headers.contentType = contenType
		if contenType not in C.supportedContentSerializationsSimple:
			return Result(rsc=RC.unsupportedMediaType, request=cseRequest, dbg=f'Unsupported media type for content-type: {cseRequest.headers.contentType}', status=False)
		cseRequest.ct = ContentSerializationType.to(cseRequest.headers.contentType)

		# De-Serialize the content
		if cseRequest.data is not None and len(cseRequest.data) > 0:
			try:
				if (_d := Utils.deserializeData(cseRequest.data, cseRequest.ct)) is None:
					return Result(rsc=RC.unsupportedMediaType, request=cseRequest, dbg=f'Unsupported media type for content-type: {cseRequest.headers.contentType}', status=False)
			except Exception as e:
				L.isWarn and L.logWarn('Bad request (malformed content?)')
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'Malformed content? {str(e)}', status=False)
			
			# get request content
			if (pc := _d.get('pc')) is not None:
				cseRequest.dict = pc

			# get operation			
			if (op := _d.get('op')) is None:
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'operation is missing', status=False)
			if not (res := CSE.validator.validateAttribute('op', op)).status:
				return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
			if not Operation.isvalid(op):
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'operation has invalid value:{op}', status=False)
			cseRequest.op = Operation(op)

			# get originator / fr
			if (fr := _d.get('fr')) is None:
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'fr is missing', status=False)
			if not (res := CSE.validator.validateAttribute('fr', fr)).status:
				return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
			cseRequest.headers.originator = fr
			
			# get target / to
			if (to := _d.get('to')) is None:
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'to is missing', status=False)
			if not (res := CSE.validator.validateAttribute('to', to)).status:
				return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
			cseRequest.id, cseRequest.csi, cseRequest.srn = Utils.retrieveIDFromPath(to, CSE.cseRn, CSE.cseCsi)

			# get request ID
			if (rqi := _d.get('rqi')) is None:
				return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'rqi is missing', status=False)
			if not (res := CSE.validator.validateAttribute('rqi', rqi)).status:
				return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
			cseRequest.headers.requestIdentifier = rqi

			# get resource type (optional)
			if (ty := _d.get('ty')) is not None and not isinstance(ty, list):	# do not here if this is a list , eg. for discovery
				if not (res := CSE.validator.validateAttribute('ty', ty)).status:
					return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
				cseRequest.headers.resourceType = ty

			# get originating timestamp (optional)
			if (ot := _d.get('ot')) is not None:
				if not (res := CSE.validator.validateAttribute('ot', ot)).status:
					return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)
				cseRequest.headers.originatingTimestamp = ot

		 	# Extract request arguments
			try:
				# copy request arguments for greedy attributes checking
				args = deepcopy(_d) 	# type: ignore [no-untyped-call]
				for a in list(args.keys()):
					if a in ['op', 'fr', 'to', 'ot', 'rqi' ]:	# TODO make an ignoreArgsList
						del args[a]
				
				# TODO cseRequest.args, dbg = Utils.getRequestArguments(args, op)
				if cseRequest.args is None:
					return Result(rsc=RC.badRequest, request=cseRequest, dbg='#TODO', status=False)
			except Exception as e:
				 return Result(rsc=RC.invalidArguments, request=cseRequest, dbg=f'invalid arguments ({str(e)})', status=False)
			
		return Result(request=cseRequest, status=True)
		


		# rh.originator 					= self._requestHeaderField(request, C.hfOrigin)
		# rh.requestIdentifier			= self._requestHeaderField(request, C.hfRI)
		# rh.requestExpirationTimestamp 	= self._requestHeaderField(request, C.hfRET)
		# rh.responseExpirationTimestamp 	= self._requestHeaderField(request, C.hfRST)
		# rh.operationExecutionTime 		= self._requestHeaderField(request, C.hfOET)
		# rh.releaseVersionIndicator 		= self._requestHeaderField(request, C.hfRVI)
		# 	httpRequestResult = self._dissectHttpRequest(request, operation, Utils.retrieveIDFromPath(path, CSE.cseRn, CSE.cseCsi))


# TODO Similar function like getRequestArguments. Not muuch to do here, but add meaningful defaults.



##############################################################################

class MQTTClient(object):

	def __init__(self) -> None:
		self.enable	= Configuration.get('mqtt.enable')
		self.mqttConnection	= None
		self.topicPrefix 	= ''	# TODO

		if self.enable:
			self.mqttConnection = MQTTConnection(address			= Configuration.get('mqtt.address'),
												 port				= Configuration.get('mqtt.port'),
												 keepalive			= Configuration.get('mqtt.keepalive'),
												 interface			= Configuration.get('mqtt.bindIF'),
												 clientName			= idToMQTT(CSE.cseCsi),
												 useTLS				= CSE.security.useTLS,
												 sslContext			= CSE.security.getSSLContext(),
												 messageHandler 	= MQTTClientHandler	(self)
												 # username =		# TODO
												 # password=		# TODO
			)
										

	def run(self) -> None:
		"""	Initialize and run the MQTT client as a BackgroundWorker/Actor.
		"""
		if not self.enable or self.mqttConnection is None:
			L.isInfo and L.log('MQTT: client NOT enabled')
			return
		self.mqttConnection.run()
	

	def shutdown(self) -> bool:
		"""	Shutdown the MQTTClient.
		"""
		if self.mqttConnection is not None:
			return self.mqttConnection.shutdown()
		return True

