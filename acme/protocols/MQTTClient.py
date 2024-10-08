#
#	MQTTClient.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Implementation of an MQTT Client for an MQTT Mcx binding implementation.
"""

from __future__ import annotations
from typing import Tuple, cast, Dict, Optional, Any

from urllib.parse import unquote

from ..etc.Types import Operation, CSERequest, ContentSerializationType, RequestType, ResourceTypes
from ..etc.Types import Result, ResponseStatusCode, ResourceTypes, ResponseType
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.RequestUtils import prepareResultForSending, createRequestResultFromURI
from ..etc.DateUtils import waitFor
from ..etc.IDUtils import getIdFromOriginator
from ..etc.Utils import renameThread
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.MQTTConnection import MQTTConnection, MQTTHandler, idToMQTT, idToMQTTClientID
from ..helpers import TextTools
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..runtime.Logging import Logging as L


class MQTTClientHandler(MQTTHandler):
	"""	Handler registering oneM2M topics and handling resceived requests.
	"""

	__slots__ = (
		'mqttClient',
		'topicPrefixCount',
		'operationEvents',
	)
	"""	Slots for the MQTTClientHandler. """

	def __init__(self, mqttClient:MQTTClient) -> None:
		"""	Initialize the MQTTClientHandler.

			Args:
				mqttClient: The MQTTClient instance using this handler.
		"""
		super().__init__()

		self.mqttClient = mqttClient
		""" The MQTTClient instance using this handler. """

		self.topicPrefixCount = len(Configuration.mqtt_topicPrefix.split('/'))	# Count the elements for the prefix
		""" Number of elements in the prefix. """

		self.operationEvents = {
			Operation.CREATE:		[CSE.event.mqttCreate, 'MQ_C'],		# type: ignore [attr-defined]
			Operation.RETRIEVE: 	[CSE.event.mqttRetrieve, 'MQ_R'],	# type: ignore [attr-defined]
			Operation.UPDATE:		[CSE.event.mqttUpdate, 'MQ_U'],		# type: ignore [attr-defined]
			Operation.DELETE:		[CSE.event.mqttDelete, 'MQ_D'],		# type: ignore [attr-defined]
			Operation.NOTIFY:		[CSE.event.mqttNotify, 'MQ_N'],		# type: ignore [attr-defined]
			Operation.DISCOVERY:	[CSE.event.mqttRetrieve, 'MQ_F'],	# type: ignore [attr-defined]
		}
		""" Operation events. """


	def onConnect(self, connection:MQTTConnection) -> bool:
		"""	When connected to a broker then register the topics the CSE listens to.
		"""
		super().onConnect(connection)
		L.isDebug and L.logDebug('Connected to MQTT broker')
		connection.subscribeTopic(f'{Configuration.mqtt_topicPrefix}/oneM2M/req/+/{idToMQTT(RC.cseCsi)}/#', self._requestCB)					# Subscribe to general requests
		connection.subscribeTopic(f'{Configuration.mqtt_topicPrefix}/oneM2M/resp/{idToMQTT(RC.cseCsi)}/+/#', self._responseCB)				# Subscribe to responses
		connection.subscribeTopic(f'{Configuration.mqtt_topicPrefix}/oneM2M/reg_req/+/{idToMQTT(RC.cseCsi)}/#', self._registrationRequestCB)	# Subscribe to registration requests
		return True


	def onDisconnect(self, connection:MQTTConnection) -> bool:
		"""	Callback when disconnecting from a broker.
		"""
		super().onDisconnect(connection)
		L.isDebug and L.logDebug('Disconnected from MQTT broker')
		return True


	def onSubscribed(self, connection:MQTTConnection, topic:str) -> bool:
		"""	Callback when successfully subscribed to a topic.
		"""
		super().onSubscribed(connection, topic)
		L.isDebug and L.logDebug(f'Topic successfully subscribed: {topic}')
		return True


	def onUnsubscribed(self, connection:MQTTConnection, topic:str) -> bool:
		"""	Callback when successfully unsubscribed from a topic.
		"""
		super().onUnsubscribed(connection, topic)
		L.isDebug and L.logDebug(f'Topic unsubscribed: {topic}')
		return True


	def onError(self, _:MQTTConnection, rc:Optional[int] = -1) -> bool:
		"""	Callback for error handlings.
		"""
		if rc in [5]:		# authorization error
			CSE.shutdown()
		if rc == -1: 	# unknown. probably connection error?
			CSE.shutdown()
		# ignore all others
		return True
	

	def logging(self, connection:Optional[MQTTConnection], level:int, message:str) -> bool:
		"""	Forwarding log events to the CSE's log system.
		"""
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


	def _responseCB(self, connection:MQTTConnection, topic:str, data:bytes) -> None:
		"""	Receive and handle a 'resp' message.
		"""
		ts = topic.split('/')

		# Check correct topic length
		if len(ts := topic.split('/')) != self.topicPrefixCount + 5:
			L.logErr(f'Received topic with incorrect length: {topic}', showStackTrace=False)
			# We can't do anything about a wrong topic. Actually, we should never have received this
			return
		
		# Dissect Body
		contentType:str = ts[-1]
		ct = ContentSerializationType.getType(contentType)
		try:
			dissectResult = CSE.request.dissectRequestFromBytes(data, ct, isResponse = True)
		except ResponseException as e:
			e.dbg = L.logWarn(f'Error receiving MQTT response: {e.dbg}')
			raise e
		
		# Add it to a response queue in the manager
		dissectResult.request.requestType = RequestType.RESPONSE
		CSE.request.addResponse(dissectResult, topic)
	

	def _handleIncommingRequest(self, connection:MQTTConnection, 
									  topic:str, 
									  data:bytes, 
									  responseTopicType:str, 
									  isRegistration:Optional[bool] = False) -> None:
		"""	Handling incoming requests is rather generic, since the special handling of some requests, like
			registration is done later anyway.
		"""

		def _sendResponse(result:Result, originalRequest:Optional[CSERequest] = None) -> None:
			"""	Send a response for a request.

				Args:
					result: The result to send.
					originalRequest: The original request.
			"""
			(_r, _data) = prepareResultForSending(result, isResponse = True, originalRequest = originalRequest)	# may throw an exception
			topic = f'{Configuration.mqtt_topicPrefix}/oneM2M/{responseTopicType}/{requestOriginator}/{requestReceiver}/{contentType}'
			logRequest(_r, _data, topic, isResponse=True, isIncoming=False)
			connection.publish(topic, _data)
			# if isinstance(data, bytes):
			# else:
			# 	connection.publish(topic, cast(str, data).encode())
		

		def _logRequest(result:Result) -> None:
			"""	Log request.
			"""
			if result.request.originalRequest:
				L.isDebug and L.logDebug(f'Operation: {result.request.originalRequest.get("op")}')
			if contentType == ContentSerializationType.JSON:
				L.isDebug and L.logDebug(f'Body: \n{cast(str, data.decode())}')
			else:
				L.isDebug and L.logDebug(f'Body: \n{TextTools.toHex(cast(bytes, data))}\n=>\n{result.request.originalRequest}')
					

		# SP relative of for : /cseid/aei
		L.isDebug and L.logDebug(f'==> MQTT Request: {topic}')

		# Check correct topic length
		if len(ts := topic.split('/')) != self.topicPrefixCount + 5:
			L.logErr(f'Received topic with incorrect length: {topic}', showStackTrace=False)
			# We can't do anything about a wrong topic. Actually, we should never have received this
			return

		# Dissect topic
		requestOriginator:str 	= ts[-3]
		requestReceiver:str   	= ts[-2]
		contentType:str   		= ts[-1]

		# Check supported contentTypes, and send an error message if not supported
		if contentType not in ContentSerializationType.supportedContentSerializationsSimple():
			L.logErr(f'Unsupported content serialization type: {contentType}, topic: {topic}', showStackTrace=False)
			# We cannot do much about an unsupported content serialization type since we cannot parse the request
			# sendResponse(Result(rsc=RC.badRequest, dbg=f'Unsupported content serialization type: {contentType}'))
			return

		# dissect and validate request (calls: fillAndValidateCSERequest())
		try:
			dissectResult = CSE.request.dissectRequestFromBytes(data, ContentSerializationType.getType(contentType))
			request = dissectResult.request
		except ResponseException as e:
			# something went wrong during dissection
			dissectResult = Result(rsc = e.rsc, dbg = e.dbg, request = e.data)
			CSE.request.recordRequest(dissectResult.request, dissectResult)
			_logRequest(dissectResult)
			_sendResponse(dissectResult)
			return

		if isRegistration:
			# Check access in case of a registration
			if Configuration.mqtt_security_allowedCredentialIDs:
				#L.logWarn(Configuration.mqtt_security_allowedCredentialIDs)
				# The requestOriginator is actually a Credential ID. Check whether it is allowed
				if not CSE.security.isAllowedOriginator(requestOriginator, Configuration.mqtt_security_allowedCredentialIDs):
					CSE.request.recordRequest(dissectResult.request, dissectResult)
					_logRequest(dissectResult)
					_sendResponse(Result(rsc = ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE, 
										 request = request, 
										 dbg = f'Invalid credential ID: {requestOriginator}'))
					return
			
			# TODO Is it necessary to check here the originator for None, empty, C, S?
			# TODO is the following necessary or isn't this been handled in the Registration Manager?

			if request.op != Operation.CREATE:
				# Registration must be a CREATE operation
				CSE.request.recordRequest(dissectResult.request, dissectResult)
				_logRequest(dissectResult)
				_sendResponse(Result(rsc = ResponseStatusCode.BAD_REQUEST,
									 request = request, 
									 dbg = L.logWarn(f'Invalid operation for registration: {request.op.name}')))
				return

			if request.ty not in [ ResourceTypes.AE, ResourceTypes.CSR]:
				# Registration type must be AE
				CSE.request.recordRequest(dissectResult.request, dissectResult)
				_logRequest(dissectResult)
				_sendResponse(Result(rsc = ResponseStatusCode.BAD_REQUEST,
									 request = request, 
									 dbg = L.logWarn(f'Invalid resource type for registration: {request.ty.name}')))
				return
			
		_logRequest(dissectResult)

		# server stopped
		if self.mqttClient.isStopped:
			_sendResponse(Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
								 request = dissectResult.request, 
								 dbg = 'mqtt server not running'))
			return

		# Handle the request

		# send events for the MQTT operations
		_t = self.operationEvents[request.op]
		_t[0]()	# Send event
		L.enableScreenLogging and renameThread(_t[1]) # rename threads

		try:
			responseResult = CSE.request.handleRequest(request)
		except Exception as e:
			responseResult = Result.exceptionToResult(e)
		
		# Don't send a response for "no response" requests
		if request.rt == ResponseType.noResponse:
			return

		# Send response

		# add, copy and update some fields from the original request
		# TODO Also change in http
		responseResult.prepareResultFromRequest(request)	

		#	Transform request to oneM2M request
		_sendResponse(responseResult, request)
	

##############################################################################


class MQTTClient(object):
	"""	The general MQTT manager for this CSE.
	"""
	# TODO doc

	__slots__ = (
		'mqttConnection',
		'isStopped',
		'mqttConnections',
		'receivedResponses',
		'receivedResponsesLock',
	)
	""" Slots for the MQTTClient. """

	# TODO move config handling to event handler

	def __init__(self) -> None:
		"""	Initialize the MQTT client.
		"""

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		self.isStopped = False
		""" Flag to indicate whether the MQTT client is stopped. """

		self.mqttConnections:Dict[Tuple[str, int], MQTTConnection]	= {}
		""" Dictionary of MQTT connections. """

		self.mqttConnection = self.connectToMqttBroker(address	= Configuration.mqtt_address,
													   port		= Configuration.mqtt_port,
													   useTLS	= Configuration.mqtt_security_useTLS,
													   username = Configuration.mqtt_security_username,
													   password	= Configuration.mqtt_security_password)
		""" The MQTT connection. """

		L.isInfo and L.log('MQTT Client initialized')
	

	def run(self) -> bool:
		"""	Initialize and run the MQTT client as a BackgroundWorker/Actor.
		"""
		if not Configuration.mqtt_enable or not self.mqttConnection:
			L.isInfo and L.log('MQTT: client NOT enabled')
			return True
		L.isInfo and L.log('Start MQTT client')
		self.mqttConnection.run()
		if not self.isFullySubscribed():	# This waits until the MQTT Client connects and fully subscribes (until a timeout)
			return False
		return True


	def shutdown(self) -> bool:
		"""	Shutdown the MQTTClient.
		"""
		L.isInfo and L.log('MQTT client shut down')
		self.isStopped = True
		for id in list(self.mqttConnections):
			self.disconnectFromMqttBroker(id[0], id[1])	# 0 = address, 1 = port
		self.mqttConnection = None
		return True
	

	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'mqtt.enable', 
						'mqtt.topicPrefix',
						'mqtt.timeout', 
						'mqtt.address',
						'mqtt.port',
						'mqtt.keepalive',
						'mqtt.listenIF',
						'mqtt.security.useTLS',
						'mqtt.security.verifyCertificate',
						'mqtt.security.caCertificateFile',
						'mqtt.security.username',
						'mqtt.security.password',
						'mqtt.security.allowedCredentialIDs' 
					  ]:
			return

		# possibly restart MQTT client
		self.shutdown()
		self.run()
		

	def pause(self) -> None:
		"""	Stop handling requests.
		"""
		L.isInfo and L.log('MqttClient paused')
		self.isStopped = True
		
	
	def unpause(self) -> None:
		"""	Continue handling requests.
		"""
		L.isInfo and L.log('MqttClient unpaused')
		self.isStopped = False


	#
	#	Additional methods
	#

	def isFullySubscribed(self) -> bool:
		"""	Check whether this mqttConnection is fully subscribed.
		"""
		return waitFor(Configuration.mqtt_timeout, lambda:self.mqttConnection.isConnected and self.mqttConnection.subscribedCount == 3)	# currently 3 topics


	def isConnected(self) -> bool:
		"""	Check whether the MQTT client is connected to a broker. Wait for a moment
			to take startup connection into account.
		"""
		return waitFor(Configuration.mqtt_timeout, lambda:self.mqttConnection.isConnected)


	def connectToMqttBroker(self, address:str, port:int, useTLS:bool, username:Optional[str], password:Optional[str]) -> Optional[MQTTConnection]:
		"""	Connect to a oneM2M MQTT Broker. The connection is cached and reused. The key for identifying the
			broker is a tupple (*address*, *port*). A new MQTTClientHandler() object be used for handling
			requests.
		"""
		if Configuration.mqtt_enable:
			if not (mqttConnect := self.mqttConnections.get( (address, port) )):
				mqttConnection = MQTTConnection(address				= address,
												port				= port,
												keepalive			= Configuration.mqtt_keepalive,
												interface			= Configuration.mqtt_listenIF,
												clientID			= idToMQTTClientID(RC.cseCsi),
												useTLS				= useTLS,
												caFile				= Configuration.mqtt_security_caCertificateFile,
												verifyCertificate	= Configuration.mqtt_security_verifyCertificate,
												username 			= username,
												password			= password,
												lowLevelLogging 	= L.enableBindingsLogging,
												messageHandler 		= MQTTClientHandler	(self))
				if mqttConnection:
					self.mqttConnections[(address, port)] = mqttConnection
			return mqttConnection
		return None

	
	def disconnectFromMqttBroker(self, address:str, port:int) -> None:
		"""	Remove the appropriate MQTTConnection for *address* and *port* from the 
			connection cache and also shut-down the connection.
		"""
		if (mqttConnection := self.getMqttBroker(address, port)):
			del self.mqttConnections[ (address, port) ]
			mqttConnection.shutdown()
	

	def getMqttBroker(self, address:str, port:int) -> MQTTConnection:
		"""	Return the MQTTConnection for the *address* and *port* from the internal
			connection cache.
		"""
		return self.mqttConnections.get( (address, port) )


	#########################################################################
	#
	#	Send MQTT requests
	#

	def sendMqttRequest(self, request:CSERequest, url:str, ignoreResponse:bool) -> Result:
		"""	Sending a request via MQTT.
		"""

		if self.isStopped:
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
						  dbg = 'MQTT client is not running')

		# deconstruct URL
		req, url, urlParsed = createRequestResultFromURI(request, url)
		# u = urlparse(url)

		mqttHost:Optional[str] = urlParsed.hostname
		mqttScheme = urlParsed.scheme.lower()
		mqttSecurity = mqttScheme == 'mqtts'	# TODO Is it necessary to do something special here?
		if not (mqttPort := urlParsed.port):
			mqttPort = 1883 if mqttScheme == 'mqtt' else 8883
		mqttUsername:Optional[str] = urlParsed.username
		mqttPassword:Optional[str] = urlParsed.password

		# Pack everything that is needed in a Result object as if this is a normal "response" (for MQTT this doesn't matter)
		# This seems to be a bit complicated, but we fill in the necessary values as if this is a normal "response"

		# req 					= Result(request = request)
		# req.request.id			= unquote(u.path[1:]) if u.path[1:] else req.request.to
		# req.resource			= req.request.pc
		# req.request.rqi			= uniqueRI()
		# if req.request.rvi != '1':
		# 	req.request.rvi		= req.request.rvi if req.request.rvi is not None else RC.releaseVersion
		# req.request.ot			= getResourceDate()
		# req.rsc					= ResponseStatusCode.UNKNOWN								# explicitly remove the provided OK because we don't want have any
		# req.request.ct			= req.request.ct if req.request.ct else CSE.defaultSerialization 	# get the serialization


		# construct the actual request and topic.
		# Some work is needed here because we take a normal URL for the address
		(preq, _data) = prepareResultForSending(req)
		topic = urlParsed.path	# We cannot unquote the path here, yet (s.b.)
		topicSplit = urlParsed.path.split('/')

		# Build the topic
		if not len(topic):
			# Miguel's proposal
			# topic = f'/oneM2M/req/{idToMQTT(RC.cseCsi)}/{idToMQTT(toSPRelative(req.request.to if req.request.to else req.request.originator))}/{req.request.ct.name.lower()}'
			#topic = f'/oneM2M/req/{idToMQTT(RC.cseCsi)}/{idToMQTT(toSPRelative(originator))}/{ct.name.lower()}'
			# topic = f'/oneM2M/req/{idToMQTT(RC.cseCsi)}/{idToMQTT(csiFromSPRelative(req.request.to))}/{req.request.ct.name.lower()}'

			topic = f'/oneM2M/req/{idToMQTT(RC.cseCsi)}/{idToMQTT(getIdFromOriginator(req.request.to))}/{req.request.ct.name.lower()}'
		elif topic.startswith('///'):
			topic = f'/oneM2M/req/{idToMQTT(RC.cseCsi)}/{idToMQTT(topicSplit[3])}/{req.request.ct.name.lower()}'		# TODO Investigate whether this needs to be SP-Relative as well
		elif topic.startswith('//'):
			topic = f'/oneM2M/req/{idToMQTT(RC.cseCsi)}/{idToMQTT(topicSplit[2])}/{req.request.ct.name.lower()}'		# TODO Investigate whether this needs to be SP-Relative as well
		elif not topic.startswith('/oneM2M/') and len(topic) > 0 and topic[0] == '/':	# remove leading "/" if not /oneM2M
			topic = topic[1:]
		else:
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
						  dbg = 'Cannot build topic')
		
		# Unquote the topic now, after the processing
		topic = unquote(topic)

		# Get the broker, or connect to a new MQTTBroker for this address
		if not (mqttConnection := self.getMqttBroker(mqttHost, mqttPort)):
			L.isDebug and L.logDebug(f'Creating a new connection for: {mqttHost}:{mqttPort}')
			mqttConnection = self.connectToMqttBroker(address = mqttHost,
													  port = mqttPort,
													  useTLS = mqttScheme == 'mqtts',
													  username = mqttUsername,
													  password = mqttPassword)

			# Wait a moment until we are connected.
			waitFor(Configuration.mqtt_timeout, lambda: mqttConnection is not None and mqttConnection.isConnected)

		# We are not connected, so -> fail
		if not mqttConnection or not mqttConnection.isConnected:
			return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, 
						  dbg = L.logWarn(f'Cannot connect to MQTT broker at: {mqttHost}:{mqttPort}'))

		# Publish the request and wait for the response.
		# Then return the response as result
		logRequest(preq, _data, topic, isResponse = False, isIncoming = False)
		# mqttConnection.publish(topic, cast(bytes, cast(Tuple, preq.data)[1]))
		mqttConnection.publish(topic, _data)

		# Don't wait for the response if the request is for a notification and a direct URL is used
		if ignoreResponse and req.request.op == Operation.NOTIFY:
			L.isDebug and L.logDebug('MQTT: Ignoring response to notification')
			return Result(rsc = ResponseStatusCode.OK)
		
		# Wait for the response
		response, responseTopic = CSE.request.waitForResponse(preq.request.rqi, Configuration.mqtt_timeout) # type: ignore
		logRequest(response, None, responseTopic, isResponse = True, isIncoming = True)
		return response


##############################################################################


def logRequest(reqResult:Result, 
			   data:bytes,
			   topic:str, 
			   isResponse:Optional[bool] = False, 
			   isIncoming:Optional[bool] = False) -> None:
	"""	Log a request. Make some adjustments, depending on the request or response type.
	"""
	if isIncoming:
		if isResponse:
			prefix = f'MQTT Response <== ({reqResult.rsc})'
		else:
			prefix = f'MQTT Request <=='
	else:
		if isResponse:
			prefix = f'<== MQTT Response ({reqResult.rsc})'
		else:
			prefix = f'MQTT Request ==>'

	body   = ''
	if reqResult.request:
		if reqResult.request.ct == ContentSerializationType.CBOR:
			if isResponse and reqResult.request.originalData:
				body = f'\nBody: \n{TextTools.toHex(reqResult.request.originalData)}\n=>\n{str(reqResult.request.originalRequest)}'
			else:
				body = f'\nBody: \n{TextTools.toHex(data)}\n=>\n{reqResult.data}'
		elif reqResult.request.ct == ContentSerializationType.JSON:

			if reqResult.data:
				bodyPrint = str(reqResult.data)
			else:
				bodyPrint = str(reqResult.request.originalRequest)

			body = f'\nBody: {bodyPrint}' 

	L.isDebug and L.logDebug(f'{prefix}: {topic}{body}', stackOffset = 1)
