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
from typing import cast

from etc.Constants import Constants as C
from etc.Types import JSON, Operation, CSERequest, ContentSerializationType, ResourceTypes, Result, ResponseCode as RC
from services.Logging import Logging as L
from services.Configuration import Configuration
import services.CSE as CSE, etc.Utils as Utils, etc.DateUtils as DateUtils, etc.RequestUtils as RequestUtils
from helpers.MQTTConnection import MQTTConnection, MQTTHandler, idToMQTT, idToMQTTClientID
import helpers.TextTools


# TODO internal events
# TODO Docs
# TODO registration request handling
# TODO send request support
# TODO mqtt support for NotificationServer
# TODO notifications
# TODO select correct binding for requests (support mqtt / mqtts schemes)
# TODO Check allowed client id for registrations


class MQTTClientHandler(MQTTHandler):

	def __init__(self, mqttClient:MQTTClient) -> None:
		super().__init__()
		self.mqttClient  = mqttClient
		self.topicPrefix = mqttClient.topicPrefix
		self.topicPrefixCount = len(self.topicPrefix.split('/'))	# Count the elements for the prefix

	def onConnect(self, connection:MQTTConnection) -> bool:
		"""	When connected to a broker then register the topics the CSE listens to.
		"""
		L.isDebug and L.logDebug('Connected to MQTT broker')
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/req/+/{idToMQTT(CSE.cseCsi)}/#', self._requestCB)					# Subscribe to general requests
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/resp/{idToMQTT(CSE.cseCsi)}/+/#', self._responseCB)				# Subscribe to responses
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/reg_req/+/{idToMQTT(CSE.cseCsi)}/#', self._registrationRequestCB)	# Subscribe to registration requests
		return True


	def onDisconnect(self, _:MQTTConnection) -> bool:
		return L.isDebug and L.logDebug('Disconnected from MQTT broker')


	def onSubscribed(self, _: MQTTConnection, topic: str) -> bool:
		return L.isDebug and L.logDebug(f'Topic successfully subscribed: {topic}')


	def onUnsubscribed(self, _: MQTTConnection, topic: str) -> bool:
		return L.isDebug and L.logDebug(f'Topic unsubscribed: {topic}')


	def onError(self, _:MQTTConnection, rc:int=-1) -> bool:
		if rc in [5]:		# authorization error
			CSE.shutdown()
		if rc == -1: 	# unknown. probably connection error?
			CSE.shutdown()
		# ignore all others
		return True
	

	def logging(self, connection:MQTTConnection, level:int, message:str) -> bool:
		L.logWithLevel(level, message, stackOffset=4)	# Log the message, compensate to let the logger determine the correct file/linenumber
		return True

	#
	#	Various request, register and response callbacks
	#


	def _requestCB(self, connection:MQTTConnection, topic:str, data:bytes) -> None:
		"""	Handle a normal MQTT request.
		"""
		self._handleIncommingRequest(connection, topic, data, 'resp')


	def _registrationRequestCB(self, connection:MQTTConnection, topic:str, data:bytes) -> None:
		"""	handle an MQTT registration request.
		"""
		self._handleIncommingRequest(connection, topic, data, 'reg_resp', isRegistration=True)



	# TODO
	def _responseCB(self, connection:MQTTConnection, topic:str, data:bytes) -> None:
		"""	Receive and handle a 'resp' message.
		"""
		ts = topic.split('/')
		L.isDebug and L.logDebug(f'RESPONSE {topic}, {data.decode()}, {ts[-1]}')
		# TODO
		connection.publish('test', f'{topic}, {data:b}, {ts[-1]}'.encode())		# type: ignore [str-bytes-safe]


	def _handleIncommingRequest(self, connection:MQTTConnection, topic:str, data:bytes, responseTopicType:str, isRegistration:bool=False) -> None:
		"""	Handling incoming requests is rather generic, since the special handling of some requests, like
			registration is done later anyway.
		"""

		def _sendResponse(result:Result, request:CSERequest=None) -> None:
			"""	Actually send a response for a request. If `request` is given then
				set it for the response.
			"""
			if request:
				result.request = request
			if (response := self._prepareResponse(result)).status:
				connection.publish(f'{self.topicPrefix}/oneM2M/{responseTopicType}/{requestOriginator}/{requestReceiver}/{contentType}', response.data.encode())

		# SP relative of for : /cseid/aei
		L.isDebug and L.logDebug(f'==> MQTT-REQUEST: {topic}')

		# Check correct topic length
		if len(ts := topic.split('/')) != self.topicPrefixCount + 5:
			L.logErr(f'Received topic with incorrect length: {topic}', showStackTrace=False)
			# We can't do anything about a wrong topic. Actually, we should never have received this
			return

		# Dissect topic
		requestOriginator:str 	= ts[self.topicPrefixCount + 2]
		requestReceiver:str   	= ts[self.topicPrefixCount + 3]
		contentType:str   		= ts[self.topicPrefixCount + 4]


		# Check supported contentTypes, and send an error message if not supported
		if contentType not in C.supportedContentSerializationsSimple:
			L.logErr(f'Unsupported content serialization type: {contentType}, topic: {topic}', showStackTrace=False)
			# We cannot do much about an unsupported content serialization type since we cannot parse the request
			# sendResponse(Result(rsc=RC.badRequest, dbg=f'Unsupported content serialization type: {contentType}'))
			return

		# dissect and validate request
		if not (dissectResult := self._dissectMQTTRequest(data, contentType)).status:
			# something went wrong during dissection
			_sendResponse(dissectResult)
			return

		if isRegistration:
			# Check access in case of a registration
			if CSE.security.allowedCredentialIDsMqtt:
				L.logWarn(CSE.security.allowedCredentialIDsMqtt)
				# The requestOriginator is actually a Credential ID. Check whether it is allowed
				if not CSE.security.isAllowedOriginator(requestOriginator, CSE.security.allowedCredentialIDsMqtt):
					_sendResponse(Result(rsc=RC.originatorHasNoPrivilege, request=dissectResult.request, dbg=f'Invalid credential ID: {requestOriginator}'))
					return
			
			if dissectResult.request.op != Operation.CREATE:
				# Registration must be a CREATE operation
				L.logWarn(dbg := f'Invalid operation for registration: {dissectResult.request.op.name}')
				_sendResponse(Result(rsc=RC.badRequest, request=dissectResult.request, dbg=dbg))
				return

			if dissectResult.request.headers.resourceType != ResourceTypes.AE:
				# Registration type must be AE
				L.logWarn(dbg := f'Invalid resource type for registration: {dissectResult.request.headers.resourceType}')
				_sendResponse(Result(rsc=RC.badRequest, request=dissectResult.request, dbg=f'Invalid resource type for registration: {dissectResult.request.headers.resourceType.name}'))
				return
			
			# TODO Is it necessary to check here the originator for None, empty, C, S?


		# log request
		L.isDebug and L.logDebug(f'Operation: {dissectResult.request.op.name}')
		if contentType == ContentSerializationType.JSON:
			L.isDebug and L.logDebug(f'Body: \n{cast(str, data)}')
		else:
			L.isDebug and L.logDebug(f'Body: \n{helpers.TextTools.toHex(cast(bytes, data))}\n=>\n{dissectResult.request.dict}')

		# handle request
		if self.mqttClient.isStopped:
			_sendResponse(Result(rsc=RC.internalServerError, request=dissectResult.request, dbg='mqtt server not running', status=False))
			return
		try:
			responseResult = CSE.request.handleRequest(dissectResult.request)
		except Exception as e:
			responseResult = Utils.exceptionToResult(e)
		# Send response
		_sendResponse(responseResult, dissectResult.request)


	def _dissectMQTTRequest(self, data:bytes, contenType:str) -> Result:
		"""	Dissect an MQTT request. Return it in `Result.request` .
		"""
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
				#return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=res.status)
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
		resp['ot'] = DateUtils.getResourceDate()
		if result.request.headers.requestIdentifier is not None:
			resp['rqi'] = result.request.headers.requestIdentifier
		if result.request.headers.releaseVersionIndicator is not None:
			resp['rvi'] = result.request.headers.releaseVersionIndicator
		if result.request.headers.vendorInformation is not None:
			resp['vsi'] = result.request.headers.vendorInformation
		resp['pc'] = result.toData(ContentSerializationType.PLAIN)	# First, construct and serialize the data as JSON/dictionary. Encoding to JSON or CBOR is done later

		# serialize and log response
		response = Result(data=resp, request=result.request, status=True)
		if result.request.ct == ContentSerializationType.CBOR:		# Always us the ct from the request
			response.data = cast(bytes, RequestUtils.serializeData(response.data, ContentSerializationType.CBOR))
			L.isDebug and L.logDebug(f'<== MQTT-Response (RSC: {result.rsc:d}):\nBody: \n{helpers.TextTools.toHex(response.data)}\n=>\n{resp}')
		else:
			response.data = cast(bytes, RequestUtils.serializeData(response.data, ContentSerializationType.JSON))
			L.isDebug and L.logDebug(f'<== MQTT-Response (RSC: {result.rsc:d}):\nBody: {resp}')
		
		return response



##############################################################################

class MQTTClient(object):

	def __init__(self) -> None:
		self.enable			= Configuration.get('mqtt.enable')
		self.topicPrefix 	= Configuration.get('mqtt.topicPrefix')
		self.enableLogging 	= Configuration.get('mqtt.enableLogging')
		self.mqttConnection	= None
		self.isStopped		= False

		if self.enable:
			self.mqttConnection = MQTTConnection(address			= Configuration.get('mqtt.address'),
												 port				= Configuration.get('mqtt.port'),
												 keepalive			= Configuration.get('mqtt.keepalive'),
												 interface			= Configuration.get('mqtt.listenIF'),
												 clientID			= idToMQTTClientID(CSE.cseCsi),
												 useTLS				= CSE.security.useTlsMqtt,
												 caFile				= CSE.security.caCertificateFileMqtt,
												 verifyCertificate	= CSE.security.verifyCertificateMqtt,
												 username 			= CSE.security.usernameMqtt,
												 password			= CSE.security.passwordMqtt,
												 lowLevelLogging 	= L.enableBindingsLogging,
												 messageHandler 	= MQTTClientHandler	(self))
		L.isInfo and L.log('MQTT Client initialized')
	

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

