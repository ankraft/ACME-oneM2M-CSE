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
from typing import Tuple, cast
from Logging import Logging as L
from Configuration import Configuration
from Constants import Constants as C
from helpers.MQTTConnection import MQTTConnection, MQTTHandler, idToMQTT, idToMQTTClientID, mqttToId
from Types import JSON, Operation, RequestHeaders, CSERequest, ContentSerializationType, Result, ResponseCode as RC, RequestHandler
import CSE, Utils


# TODO internal events
# TODO Docs

class MQTTClientHandler(MQTTHandler):

	def __init__(self, mqttClient:MQTTClient) -> None:
		super().__init__()
		self.mqttClient = mqttClient
		self.topicPrefix = mqttClient.topicPrefix
		self.topicPrefixCount = len(self.topicPrefix.split('/'))	# Count the elements for the prefix

	def onConnect(self, connection:MQTTConnection) -> None:
		"""	When connected to a broker then register the topics the CSE listens to.
		"""
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/req/+/{idToMQTT(CSE.cseCsi)}/#', self._requestCB)					# Subscribe to general requests
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/resp/{idToMQTT(CSE.cseCsi)}/+/#', self._responseCB)				# Subscribe to responses
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/reg_req/+/{idToMQTT(CSE.cseCsi)}/#', self._registrationRequestCB)	# Subscribe to registration requests


	def onDisconnect(self, _:MQTTConnection) -> None:
		pass

	
	def onError(self, _:MQTTConnection, rc:int=-1) -> None:
		if rc == 5:		# authentication error
			CSE.shutdown()
		if rc == -1: 	# unknown. probably connection error?
			CSE.shutdown()


	#
	#	Various request, register and response callbacks
	#

	def _requestCB(self, connection:MQTTConnection, topic:str, data:bytes) -> None:

		# SP relative of fr : /cseid/aei
		# TODO reg_resp diferent

		ts = topic.split('/')
		requestTopicType	= ts[self.topicPrefixCount + 1]
		responseTopicType	= 'resp' if requestTopicType == 'req' else 'reg_resp'
		requestOriginator 	= ts[self.topicPrefixCount + 2]
		requestReceiver   	= ts[self.topicPrefixCount + 3]
		contentType   		= ts[self.topicPrefixCount + 4]
		L.isDebug and L.logDebug(f'==> MQTT-REQUEST {topic} originator:{requestOriginator}, receiver:{requestReceiver}, type:{contentType}')

		# dissect and validate request
		if not (dissectResult := self._dissectMQTTRequest(data, contentType)).status:
			if (response := self._prepareResponse(dissectResult)).status:
				connection.publish(f'{self.topicPrefix}/oneM2M/{responseTopicType}/{requestOriginator}/{requestReceiver}/{contentType}', response.data.encode())
			return

		# log request
		if contentType == ContentSerializationType.JSON:
			L.isDebug and L.logDebug(f'Body: \n{cast(str, data)}')
		else:
			L.isDebug and L.logDebug(f'Body: \n{Utils.toHex(cast(bytes, data))}\n=>\n{dissectResult.request.dict}')

		# handle request
		if self.mqttClient.isStopped:
			responseResult = Result(rsc=RC.internalServerError, dbg='mqtt server not running', status=False)
		else:
			try:
				if dissectResult.status:
					if dissectResult.request.op in [ Operation.CREATE, Operation.UPDATE ]:
						if dissectResult.request.ct == ContentSerializationType.CBOR:
							L.isDebug and L.logDebug(f'Data: \n{Utils.toHex(cast(bytes, dissectResult.request.data))}\n=>\n{dissectResult.request.dict}')
						else:
							L.isDebug and L.logDebug(f'Data: \n{str(dissectResult.request.data)}')
					responseResult = CSE.request.handleRequest(dissectResult.request)
				else:
					responseResult = dissectResult
			except Exception as e:
				responseResult = Utils.exceptionToResult(e)
		responseResult.request = dissectResult.request
		if (response := self._prepareResponse(responseResult)).status:
			connection.publish(f'{self.topicPrefix}/oneM2M/{responseTopicType}/{requestOriginator}/{requestReceiver}/{contentType}', response.data.encode())


	def _responseCB(self, connection:MQTTConnection, topic:str, data:str) -> None:
		"""	Receive and handle a 'resp' message.
		"""
		ts = topic.split('/')
		L.isDebug and L.logDebug(f'RESPONSE {topic}, {data}, {ts[-1]}')
		connection.publish('test', f'{topic}, {data}, {ts[-1]}'.encode())



	def _registrationRequestCB(self, connection:MQTTConnection, topic:str, data:str) -> None:
		ts = topic.split('/')
		L.logDebug(f'REGISTRATION {topic}, {data}, {ts[-1]}')
		# TODO 
		connection.publish('test', f'{topic}, {data}, {ts[-1]}'.encode())
	

	def _dissectMQTTRequest(self, data:bytes, contenType:str) -> Result:
		# TODO doc
		cseRequest = CSERequest()
		cseRequest.data = data
		cseRequest.headers.contentType = contenType.lower()

		# De-Serialize the content
		if not (contentResult := CSE.request.deserializeContent(cseRequest.data, cseRequest.headers.contentType)).status:
			return Result(rsc=contentResult.rsc, request=cseRequest, dbg=contentResult.dbg, status=False)
		cseRequest.req, cseRequest.ct = contentResult.data

		# Validate the request
		try:
			if not (res := CSE.request.fillAndValidateCSERequest(cseRequest)).status:
				return res
		except Exception as e:
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=f'invalid arguments/attributes ({str(e)})', status=False)
			
		return Result(request=cseRequest, status=True)
	

	def _prepareResponse(self, result:Result) -> Result:
		"""	Prepare the response for MQTT.
		
			The constructed and encoded content is returned in `Result.data`.
		"""
		content:str|bytes = ''
		resp:JSON = {}

		# Build response attributes
		resp['fr'] = CSE.cseCsi
		resp['to'] 	= result.request.headers.originator
		resp['rsc'] = int(result.rsc)
		resp['ot'] = Utils.getResourceDate()
		if result.request.headers.requestIdentifier is not None:
			resp['ri'] = result.request.headers.requestIdentifier
		if result.request.headers.releaseVersionIndicator is not None:
			resp['rvi'] = result.request.headers.releaseVersionIndicator
		resp['pc'] = result.toData(ContentSerializationType.JSON)	# First, serialize the data as JSON/dictionary

		# serialize and log response
		response = Result(data=resp, status=True)
		if result.request.ct == ContentSerializationType.CBOR:		# Always us the ct from the request
			response.data = cast(bytes, Utils.serializeData(response.data, ContentSerializationType.CBOR))
			L.isDebug and L.logDebug(f'<== MQTT-Response (RSC: {result.rsc:d}):\nBody: \n{Utils.toHex(response.data)}\n=>\n{resp}')
			#response.data = bytearray(response.data)
		else:
			response.data = str(response.data)
			L.isDebug and L.logDebug(f'<== MQTT-Response (RSC: {result.rsc:d}):\nBody: {resp}')
		
		return response



##############################################################################

class MQTTClient(object):

	def __init__(self) -> None:
		self.enable			= Configuration.get('mqtt.enable')
		self.username		= Configuration.get('mqtt.username')
		self.password		= Configuration.get('mqtt.password')
		self.mqttConnection	= None
		self.topicPrefix 	= ''	# TODO

		if self.enable:
			self.mqttConnection = MQTTConnection(address			= Configuration.get('mqtt.address'),
												 port				= Configuration.get('mqtt.port'),
												 keepalive			= Configuration.get('mqtt.keepalive'),
												 interface			= Configuration.get('mqtt.bindIF'),
												 clientName			= idToMQTTClientID(CSE.cseCsi),
												 useTLS				= CSE.security.useTLS,
												 sslContext			= CSE.security.getSSLContext(),
												 messageHandler 	= MQTTClientHandler	(self),
												 username 			= self.username,
												 password			= self.password)
		self.isStopped = False
										

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
		self.isStopped = True
		if self.mqttConnection is not None:
			return self.mqttConnection.shutdown()
		return True

