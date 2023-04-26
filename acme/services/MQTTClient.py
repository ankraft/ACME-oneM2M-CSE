#
#	MQTTClient.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Implementation of an MQTT Client for an MQTT Mcx binding implementation.
"""

from __future__ import annotations
from typing import Tuple, cast, Dict, Optional, Any, Union

from urllib.parse import urlparse
from threading import Lock

from ..etc.Types import JSON, Operation, CSERequest, ContentSerializationType, RequestType, ResourceTypes, Result, ResponseStatusCode, ResourceTypes
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.RequestUtils import requestFromResult, serializeData
from ..etc.DateUtils import getResourceDate, waitFor
from ..etc.Utils import exceptionToResult, uniqueRI, toSPRelative, renameThread, csiFromSPRelative, getIdFromOriginator
from ..helpers.MQTTConnection import MQTTConnection, MQTTHandler, idToMQTT, idToMQTTClientID
from ..helpers import TextTools
from ..services.Configuration import Configuration
from ..services import CSE
from ..services.Logging import Logging as L


class MQTTClientHandler(MQTTHandler):
	"""	Handler registering oneM2M topics and handling resceived requests.

		Attributes:
			mqttClient: The using MQTTClient instance for this handler.
			topicPrefix: The used topic prefix to recognize requests for this handler.
			topicPrefixCont: Count of elements in the prefix.
	"""

	__slots__ = (
		'mqttClient',
		'topicPrefix',
		'topicPrefixCount',
		'operationEvents',

		'_eventMqttCreate',
		'_eventMqttRetrieve',
		'_eventMqttUpdate',
		'_eventMqttDelete',
		'_eventMqttNotify',
	)

	def __init__(self, mqttClient:MQTTClient) -> None:
		super().__init__()
		self.mqttClient  = mqttClient
		self.topicPrefix = mqttClient.topicPrefix
		self.topicPrefixCount = len(self.topicPrefix.split('/'))	# Count the elements for the prefix

		# Optimize event handling
		self._eventMqttCreate =  CSE.event.mqttCreate				# type: ignore [attr-defined]
		self._eventMqttRetrieve =  CSE.event.mqttRetrieve			# type: ignore [attr-defined]
		self._eventMqttUpdate =  CSE.event.mqttUpdate				# type: ignore [attr-defined]
		self._eventMqttDelete =  CSE.event.mqttDelete				# type: ignore [attr-defined]
		self._eventMqttNotify =  CSE.event.mqttNotify				# type: ignore [attr-defined]

		self.operationEvents = {
			Operation.CREATE:		[self._eventMqttCreate, 'MQCR'],
			Operation.RETRIEVE: 	[self._eventMqttRetrieve, 'MQRE'],
			Operation.UPDATE:		[self._eventMqttUpdate, 'MQUP'],
			Operation.DELETE:		[self._eventMqttDelete, 'MQDE'],
			Operation.NOTIFY:		[self._eventMqttNotify, 'MQNO'],
			Operation.DISCOVERY:	[self._eventMqttRetrieve, 'MQDI'],
		}


	def onConnect(self, connection:MQTTConnection) -> bool:
		"""	When connected to a broker then register the topics the CSE listens to.
		"""
		super().onConnect(connection)
		L.isDebug and L.logDebug('Connected to MQTT broker')
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/req/+/{idToMQTT(CSE.cseCsi)}/#', self._requestCB)					# Subscribe to general requests
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/resp/{idToMQTT(CSE.cseCsi)}/+/#', self._responseCB)				# Subscribe to responses
		connection.subscribeTopic(f'{self.topicPrefix}/oneM2M/reg_req/+/{idToMQTT(CSE.cseCsi)}/#', self._registrationRequestCB)	# Subscribe to registration requests
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
	

	def logging(self, connection:MQTTConnection, level:int, message:str) -> bool:
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
		try:
			dissectResult = CSE.request.dissectRequestFromBytes(data, contentType, isResponse = True)
		except ResponseException as e:
			e.dbg = L.logWarn(f'Error receiving MQTT response: {e.dbg}')
			raise e
		
		# Add it to a response queue in the manager
		dissectResult.request.requestType = RequestType.RESPONSE
		self.mqttClient.addResponse(dissectResult, topic)
	

	def _handleIncommingRequest(self, connection:MQTTConnection, 
									  topic:str, 
									  data:bytes, 
									  responseTopicType:str, 
									  isRegistration:Optional[bool] = False) -> None:
		"""	Handling incoming requests is rather generic, since the special handling of some requests, like
			registration is done later anyway.
		"""

		def _sendResponse(result:Result) -> None:
			"""	Send a response for a request.
			"""
			response = prepareMqttRequest(result, isResponse = True)	# may throw an exception
			topic = f'{self.topicPrefix}/oneM2M/{responseTopicType}/{requestOriginator}/{requestReceiver}/{contentType}'
			logRequest(response, topic, isResponse=True, isIncoming=False)
			if isinstance(cast(Tuple, response.data)[1], bytes):
				connection.publish(topic, cast(Tuple, response.data)[1])
			else:
				connection.publish(topic, cast(str, cast(Tuple, response.data)[1]).encode())
		

		def _logRequest(result:Result) -> None:
			"""	Log request.
			"""
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
			dissectResult = CSE.request.dissectRequestFromBytes(data, contentType)
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
			if CSE.security.allowedCredentialIDsMqtt:
				#L.logWarn(CSE.security.allowedCredentialIDsMqtt)
				# The requestOriginator is actually a Credential ID. Check whether it is allowed
				if not CSE.security.isAllowedOriginator(requestOriginator, CSE.security.allowedCredentialIDsMqtt):
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
		_t[0]()
		
		# rename threads
		renameThread(_t[1])

		try:
			responseResult = CSE.request.handleRequest(request)
		except Exception as e:
			responseResult = exceptionToResult(e)
		# Send response

		# TODO Also change in http
		responseResult.prepareResultFromRequest(request)	# Add and change some fields from the original request
		#Overwrite some attributes
		responseResult.request.rqi = request.rqi

		# Add Originating Timestamp if present in request
		if request.ot:
			responseResult.request.ot = getResourceDate()
		
		#	Transform request to oneM2M request
		_sendResponse(responseResult)
	

##############################################################################


class MQTTClient(object):
	"""	The general MQTT manager for this CSE.
	"""
	# TODO doc

	__slots__ = (
		'mqttConnection',
		'isStopped',
		'topicsCount',
		'mqttConnections',
		'receivedResponses',
		'receivedResponsesLock',

		'enable',
		'topicPrefix',
		'requestTimeout',
	)

	# TODO move config handling to event handler

	def __init__(self) -> None:

		# Get the configuration settings
		self._assignConfig()

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		self.isStopped												= False
		self.topicsCount											= 0
		self.mqttConnections:Dict[Tuple[str, int], MQTTConnection]	= {}
		self.receivedResponses:Dict[str, Tuple[Result, str]]		= {}
		self.receivedResponsesLock									= Lock()


		self.mqttConnection = self.connectToMqttBroker(address	= Configuration.get('mqtt.address'),
													   port		= Configuration.get('mqtt.port'),
													   useTLS	= CSE.security.useTlsMqtt,
													   username = CSE.security.usernameMqtt,
													   password	= CSE.security.passwordMqtt)
		L.isInfo and L.log('MQTT Client initialized')
	

	def run(self) -> bool:
		"""	Initialize and run the MQTT client as a BackgroundWorker/Actor.
		"""
		if not self.enable or not self.mqttConnection:
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
		L.isInfo and L.log('Shutdown MQTT client')
		self.isStopped = True
		for id in list(self.mqttConnections):
			self.disconnectFromMqttBroker(id[0], id[1])	# 0 = address, 1 = port
		self.mqttConnection = None
		return True
	

	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.enable = Configuration.get('mqtt.enable')
		self.topicPrefix = Configuration.get('mqtt.topicPrefix')
		self.requestTimeout = Configuration.get('mqtt.timeout')


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
					  ]:
			return

		# assign new values
		self._assignConfig()

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
		return waitFor(self.requestTimeout, lambda:self.mqttConnection.isConnected and self.mqttConnection.subscribedCount == 3)	# currently 3 topics


	def isConnected(self) -> bool:
		"""	Check whether the MQTT client is connected to a broker. Wait for a moment
			to take startup connection into account.
		"""
		return waitFor(self.requestTimeout, lambda:self.mqttConnection.isConnected)


	def connectToMqttBroker(self, address:str, port:int, useTLS:bool, username:str, password:str) -> Optional[MQTTConnection]:
		"""	Connect to a oneM2M MQTT Broker. The connection is cached and reused. The key for identifying the
			broker is a tupple (*address*, *port*). A new MQTTClientHandler() object be used for handling
			requests.
		"""
		if self.enable:
			if not (mqttConnect := self.mqttConnections.get( (address, port) )):
				mqttConnection = MQTTConnection(address				= address,
												port				= port,
												keepalive			= Configuration.get('mqtt.keepalive'),
												interface			= Configuration.get('mqtt.listenIF'),
												clientID			= idToMQTTClientID(CSE.cseCsi),
												useTLS				= useTLS,
												caFile				= CSE.security.caCertificateFileMqtt,
												verifyCertificate	= CSE.security.verifyCertificateMqtt,
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

	def sendMqttRequest(self, request:CSERequest, url:str) -> Result:
		"""	Sending a request via MQTT.
		"""

		if self.isStopped:
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
						  dbg = 'MQTT client is not running')

		# deconstruct URL
		u = urlparse(url)
		mqttHost = u.hostname
		mqttScheme = u.scheme.lower()
		mqttSecurity = mqttScheme == 'mqtts'	# TODO Is it necessary to do something special here?
		if not (mqttPort := u.port):
			mqttPort = 1883 if mqttScheme == 'mqtt' else 8883
		mqttUsername = u.username
		mqttPassword = u.password

		# Pack everything that is needed in a Result object as if this is a normal "response" (for MQTT this doesn't matter)
		# This seems to be a bit complicated, but we fill in the necessary values as if this is a normal "response"

		req 					= Result(request = request)
		req.request.id			= u.path[1:] if u.path[1:] else req.request.to
		req.resource			= req.request.pc
		req.request.rqi			= uniqueRI()
		if req.request.rvi != '1':
			req.request.rvi		= req.request.rvi if req.request.rvi is not None else CSE.releaseVersion
		req.request.ot			= getResourceDate()
		req.rsc					= ResponseStatusCode.UNKNOWN								# explicitly remove the provided OK because we don't want have any
		req.request.ct			= req.request.ct if req.request.ct else CSE.defaultSerialization 	# get the serialization

		# construct the actual request and topic.
		# Some work is needed here because we take a normal URL for the address
		preq = prepareMqttRequest(req)
		topic = u.path
		pathSplit = u.path.split('/')

		# Build the topic
		if not len(topic):
			# Miguel's proposal
			# topic = f'/oneM2M/req/{idToMQTT(CSE.cseCsi)}/{idToMQTT(toSPRelative(req.request.to if req.request.to else req.request.originator))}/{req.request.ct.name.lower()}'
			#topic = f'/oneM2M/req/{idToMQTT(CSE.cseCsi)}/{idToMQTT(toSPRelative(originator))}/{ct.name.lower()}'
			
			topic = f'/oneM2M/req/{idToMQTT(CSE.cseCsi)}/{idToMQTT(csiFromSPRelative(req.request.to))}/{req.request.ct.name.lower()}'
		elif topic.startswith('///'):
			topic = f'/oneM2M/req/{idToMQTT(CSE.cseCsi)}/{idToMQTT(pathSplit[3])}/{req.request.ct.name.lower()}'		# TODO Investigate whether this needs to be SP-Relative as well
		elif topic.startswith('//'):
			topic = f'/oneM2M/req/{idToMQTT(CSE.cseCsi)}/{idToMQTT(pathSplit[2])}/{req.request.ct.name.lower()}'		# TODO Investigate whether this needs to be SP-Relative as well
		elif not topic.startswith('/oneM2M/') and len(topic) > 0 and topic[0] == '/':	# remove leading "/" if not /oneM2M
			topic = topic[1:]
		else:
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, 
						  dbg = 'Cannot build topic')

		# Get the broker, or connect to a new MQTTBroker for this address
		if not (mqttConnection := self.getMqttBroker(mqttHost, mqttPort)):
			L.isDebug and L.logDebug(f'Creating a new connection for: {mqttHost}:{mqttPort}')
			mqttConnection = self.connectToMqttBroker(address = mqttHost,
													  port = mqttPort,
													  useTLS = mqttScheme == 'mqtts',
													  username = mqttUsername,
													  password = mqttPassword)

			# Wait a moment until we are connected.
			waitFor(self.requestTimeout, lambda: mqttConnection is not None and mqttConnection.isConnected)

		# We are not connected, so -> fail
		if not mqttConnection or not mqttConnection.isConnected:
			return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, 
						  dbg = L.logWarn(f'Cannot connect to MQTT broker at: {mqttHost}:{mqttPort}'))

		# Publish the request and wait for the response.
		# Then return the response as result
		logRequest(preq, topic, isResponse=False, isIncoming=False)
		mqttConnection.publish(topic, cast(bytes, cast(Tuple, preq.data)[1]))
		response, responseTopic = self.waitForResponse(preq.request.rqi, self.requestTimeout)
		logRequest(response, responseTopic, isResponse = True, isIncoming = True)
		return response


	def addResponse(self, response:Result, topic:str) -> None:
		"""	Add a response and topic to the response dictionary. The key is the *rqi* (requestIdentifier) of
			the response. 
		"""
		if (rqi := response.request.rqi):
			with self.receivedResponsesLock:
				self.receivedResponses[rqi] = (response, topic)


	def waitForResponse(self, rqi:str, timeOut:float) -> Tuple[ Result, str ]:
		"""	Wait for a response with a specific requestIdentifier *rqi*.
		"""
		resp = None
		topic = None

		def _receivedResponse() -> bool:
			nonlocal resp, topic
			with self.receivedResponsesLock:
				if not self.receivedResponses:
					return False
				if rqi in self.receivedResponses:
					resp, topic = self.receivedResponses.pop(rqi)	# return the response (in a Result object), and remove it from the dict.
					return True
			return False
			
		if not waitFor(timeOut, _receivedResponse):
			return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, 
						  dbg = 'Target not reachable or timeout'), None
		resp.data = resp.request.pc					# Add the pc to the data, since components excepct this. 
													# TODO perhaps unify the use of response values throughout the CSE
		CSE.event.responseReceived(resp.request)	# type:ignore [attr-defined]
		return resp, topic


##############################################################################


# TODO check whether this still needs to be this complicated after we refactored request sending
def prepareMqttRequest(inResult:Result, 
					   isResponse:Optional[bool] = False,) -> Result:
	"""	Prepare a new request for MQTT. 
	
		Attention:
			Remember, a response is actually just a new request. This takes care of the fact that in MQTT
			a response is very similar to a response.
	
		Args:
			inResult: A `Result` object, that contains a request in its *request* attribute.
			isResponse: Indicater whether the `Result` object is actually a response or a request.

		Return:
			The constructed and serialized content is returned in a tuple in the `Result.data` attribute:
		    the content as a dictionary and the serialized content.
	"""
	# result = requestFromResult(inResult, originator, ty, op = op, isResponse = isResponse)
	result = requestFromResult(inResult, isResponse = isResponse)
	result.data = (result.data, cast(bytes, serializeData(cast(JSON, result.data), result.request.ct)))
	return result


def logRequest(reqResult:Result, 
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
		if reqResult.request.mediaType == ContentSerializationType.CBOR or reqResult.request.ct == ContentSerializationType.CBOR:
			if isResponse and reqResult.request.originalData:
				body = f'\nBody: \n{TextTools.toHex(reqResult.request.originalData)}\n=>\n{str(reqResult.request.originalRequest)}'
			else:
				body = f'\nBody: \n{TextTools.toHex(cast(bytes, cast(Tuple, reqResult.data)[1]))}\n=>\n{cast(Tuple, reqResult.data)[0]}'
		elif reqResult.request.mediaType == ContentSerializationType.JSON or reqResult.request.ct == ContentSerializationType.JSON:

			if reqResult.data:
				if isinstance(reqResult.data, tuple):
					bodyPrint = str(cast(Tuple, reqResult.data)[0])
				else:
					bodyPrint = str(reqResult.data)
			else:
				bodyPrint = str(reqResult.request.originalRequest)

			body = f'\nBody: {bodyPrint}' 

	L.isDebug and L.logDebug(f'{prefix}: {topic}{body}', stackOffset = 1)
