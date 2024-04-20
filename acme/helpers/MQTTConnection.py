#
#	MQTTConnection.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of an MQTT Client helper class.
#
""" Implementation of an MQTT Client helper class. """

from __future__ import annotations
from typing import Callable, Any, Tuple, Optional, TypeAlias, cast

import ssl, time
from dataclasses import dataclass
import logging

from ..helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from ..helpers.TextTools import simpleMatch

import paho.mqtt.client as mqtt
import paho.mqtt.reasoncodes as mqtt_rc
import paho.mqtt.properties as mqtt_pr
import paho.mqtt.enums as mqtt_en


MQTTClient:TypeAlias = mqtt.Client
""" Type for an MQTT Client. """

@dataclass
class MQTTTopic:
	"""	Structure that represents a subscribed-to topic.
	"""
	topic:Optional[str]	= None
	""" The MQTT topic. """
	mid:Optional[int] = None
	""" The message ID of the MQTT subscription. """
	isSubscribed:bool = False
	""" Whether the topic is subscribed to. """
	callback:Optional[MQTTCallback] = None
	""" The callback function for the topic. """
	callbackArgs:Optional[dict] = None
	""" The callback arguments for the topic. """


class MQTTHandler(object):
	"""	This base class defines the interface for an MQTT handler class. 
		The abstract methods defined here must be implemented by the implementing class.

		The implementing class acts as a handler for various callbacks when dealing with
		the MQTT handler. To receive messages a client implementation must register topics
		and the callbacks for them in the `onConnect()` method.
	"""

	def onConnect(self, connection:MQTTConnection) -> bool:
		"""	This method is called after the MQTT client connected to the MQTT broker. 
			Usually, an MQTT client should subscribe to topics and register the callback
			methods here.

			Args:
				connection: The MQTT connection.

			Returns:
				True if successful, False otherwise.
		"""
		return True


	def onDisconnect(self, connection:MQTTConnection) -> bool:
		"""	This method is called after the MQTT client disconnected from the MQTT broker. 

			Args:
				connection: The MQTT connection.
			
			Returns:
				True if successful, False otherwise.
		"""
		return True


	def onSubscribed(self, connection:MQTTConnection, topic:str) -> bool:
		"""	This method is called after the MQTT client successfully subsribed to a topic. 

			Args:
				connection: The MQTT connection.
				topic: The topic that was subscribed to.
			
			Returns:
				True if successful, False otherwise.
		"""
		connection.subscribedCount += 1
		return True


	def onUnsubscribed(self, connection:MQTTConnection, topic:str) -> bool:
		"""	This method is called after the MQTT client successfully unsubsribed from a topic. 

			Args:
				connection: The MQTT connection.
				topic: The topic that was unsubscribed from.
			
			Returns:
				True if successful, False otherwise.
		"""
		connection.subscribedCount -= 1
		return True


	def onError(self, connection:MQTTConnection, rc:int) -> bool:
		"""	This method is called when receiving an error when communicating with the MQTT broker. 

			Args:
				connection: The MQTT connection.
				rc: The error code.
			
			Returns:
				True if successful, False otherwise.
		"""
		return True


	def logging(self, connection:Optional[MQTTConnection], level:int, message:str) -> bool:
		"""	This method is called when a log message should be handled. 

			Args:
				connection: The MQTT connection.
				level: The log level.
				message: The log message.
			
			Returns:
				True if successful, False otherwise.
		"""
		return True
	

	def onShutdown(self, connection:MQTTConnection) -> None:
		"""	This method is called after the ```connection``` was shut down.

			Args:
				connection: The MQTT connection.
		"""


##############################################################################


class MQTTConnection(object):
	"""	This class implements an MQTT client. It is a wrapper around the paho MQTT client.
		It is implemented as a BackgroundWorker/Actor, so it runs in its own thread.
	"""

	__slots__ = (
		'address',
		'port',
		'keepalive',
		'bindIF',
		'username',
		'password',
		'useTLS',
		'verifyCertificate',
		'caFile',
		'mqttsCertfile',
		'mqttsKeyfile',
		'clientID',
		'lowLevelLogging',
		'isStopped',
		'isConnected',
		'subscribedCount',
		'mqttClient',
		'messageHandler',
		'actor',
		'subscribedTopics',
	)
	"""	Slots of the class. """

	#
	#	Runtime methods
	#

	def __init__(self, address:str, 
					   port:Optional[int] = None,
					   keepalive:int = 60,
					   interface:str = '0.0.0.0', 
					   clientID:Optional[str] = None,
					   username:Optional[str] = None,
					   password:Optional[str] = None,
					   useTLS:bool = False, 
					   caFile:Optional[str] = None, 
					   verifyCertificate:bool = False,
					   certfile:Optional[str] = None, 
					   keyfile:Optional[str] = None,
					   lowLevelLogging:bool = True,
					   messageHandler:Optional[MQTTHandler] = None
				) -> None:
		"""	Constructor. Initialize the MQTT client.

			Args:
				address: The address of the MQTT broker.
				port: The port of the MQTT broker.
				keepalive: The keepalive time for the MQTT connection.
				interface: The interface to bind to.
				clientID: The client ID for the MQTT client.
				username: The username for the MQTT broker.
				password: The password for the MQTT broker.
				useTLS: Whether to use TLS for the MQTT connection.
				caFile: The CA file for the MQTT broker's certificate.
				verifyCertificate: Indicator whether to verify the MQTT broker's certificate.
				certfile: The certificate file for the MQTT client.
				keyfile: The key file for the MQTT client.
				lowLevelLogging: Indicator whether to log MQTT messages.
				messageHandler: The message handler.
		"""
		
		self.address								= address
		""" The address of the MQTT broker. """
		self.port									= port if port else 8883 if useTLS else 1883
		""" The port of the MQTT broker. """
		self.keepalive								= keepalive
		""" The keepalive time for the MQTT connection. """
		self.bindIF									= interface
		""" The interface to bind to. """
		self.username:Optional[str]					= username
		""" The username for the MQTT broker. """
		self.password:Optional[str]					= password
		""" The password for the MQTT broker. """
		self.useTLS:bool							= useTLS
		""" Whether to use TLS for the MQTT connection. """
		self.verifyCertificate						= verifyCertificate
		""" Indicator whether to verify the MQTT broker's certificate. """
		self.caFile									= caFile
		""" The CA file for the MQTT broker's certificate. """
		self.mqttsCertfile 							= certfile
		""" The certificate file for the MQTT client. """
		self.mqttsKeyfile 							= keyfile
		""" The key file for the MQTT client. """
		self.clientID								= clientID
		""" The client ID for the MQTT client. """
		self.lowLevelLogging						= lowLevelLogging
		""" Indicator whether to log MQTT messages. """

		self.isStopped								= True
		""" Indicator whether the MQTT client is stopped."""
		self.isConnected							= False
		""" Indicator whether the MQTT client is connected."""
		self.subscribedCount 						= 0
		""" The number of subscribed-to topics. """


		self.mqttClient:Optional[MQTTClient]		= None
		""" The MQTT client. """
		self.messageHandler:Optional[MQTTHandler]	= messageHandler
		""" The message handler. """
		self.actor:Optional[BackgroundWorker]		= None
		""" The actor for the MQTT client. """
		self.subscribedTopics:dict[str, MQTTTopic]	= {}
		""" The list of subscribed-to topics. """

	
	def shutdown(self) -> bool:
		"""	Shutting down the MQTT client.

			Returns:
				True if successful, False otherwise.
		"""

		self.isStopped = True
		if self.mqttClient:
		# if self.mqttClient and self.isConnected:
			# Unsubscribe from all topics
			for t in list(self.subscribedTopics.values()):
				self.unsubscribeTopic(t)
			# wait a moment for all unsubscribe ACKs to arrive
			while len(self.subscribedTopics) > 0:
				time.sleep(0.1)
			# Then disconnect. The actor is stoped implicitly
			self.mqttClient.disconnect()
			self.actor = None

		self.messageHandler and self.messageHandler.logging(self, logging.INFO, 'MQTT client shut down')
		return True


	def run(self) -> None:
		"""	Initialize and run the MQTT client as a BackgroundWorker/Actor.
		"""
		self.messageHandler and self.messageHandler.logging(self, logging.DEBUG, f'MQTT: client name: {self.clientID}')
		self.mqttClient = MQTTClient(callback_api_version = mqtt.CallbackAPIVersion.VERSION2,
							   		 client_id = self.clientID, 
									 clean_session = False if self.clientID else True)	# clean_session=False is defined by TS-0010

		# Enable SSL see: https://pypi.org/project/paho-mqtt/
		if self.useTLS:
			self.mqttClient.tls_set(ca_certs = self.caFile, 
									certfile = self.mqttsCertfile, 
									keyfile = self.mqttsKeyfile, 
									cert_reqs = ssl.CERT_REQUIRED, 
									tls_version = ssl.PROTOCOL_TLS, 
									ciphers = None)
			# If tls_insecure_set is set to True, it is impossible to guarantee that the host you are connecting to is not impersonating your server. This can be useful in initial server testing, but makes it possible for a malicious third party to impersonate your server through DNS spoofing, for example.
			self.mqttClient.tls_insecure_set(True)
			
		# Set username/password
		if self.username and self.password:
			self.mqttClient.username_pw_set(self.username, self.password)
		
		self.mqttClient.on_connect 		= self._onConnect
		self.mqttClient.on_disconnect	= self._onDisconnect
		self.mqttClient.on_log			= self._onLog
		self.mqttClient.on_subscribe	= self._onSubscribe
		self.mqttClient.on_unsubscribe	= self._onUnsubscribe
		self.mqttClient.on_message		= self._onMessage

		try:
			self.messageHandler and self.messageHandler.logging(self, logging.DEBUG, f'MQTT: connecting to host:{self.address}, port:{self.port}, keepalive: {self.keepalive}, bind: {self.bindIF}')
			self.mqttClient.connect(host = self.address, port = self.port, keepalive = self.keepalive, bind_address = self.bindIF)
		except Exception as e:
			if self.messageHandler:
				self.messageHandler.logging(self, logging.ERROR, f'MQTT: cannot connect to broker: {e}')
				self.messageHandler.onError(self, -1)
				return

		# Actually start the actor to run the MQTT client as a thread
		self.actor = BackgroundWorkerPool.newActor(self._mqttActor, name='MQTTClient').start()


	def _mqttActor(self) -> bool:
		"""	BackgroundWorker callback to run the actuall MQTT loop.

			Returns:
				Always True.
		"""
		self.isStopped = False
		self.messageHandler and self.messageHandler.logging(self, logging.INFO, 'MQTT: client started')
		while not self.isStopped:
			self.mqttClient.loop_forever()	# Will return when disconnect() is called
		if self.messageHandler:
			self.messageHandler.onShutdown(self)
		return True
	
	
	#
	#	MQTT/paho callbacks
	#

	def _onConnect(self, client:MQTTClient, userdata:Any, flags:dict, reason_code:mqtt_rc.ReasonCode, properties:mqtt_pr.Properties) -> None:
		"""	Callback when the MQTT client connected to the broker.

			Args:
				client: The MQTT client.
				userdata: User data.
				flags: Flags.
				reason_code: Reason code
				properties : Properties (MQTTv5 Only)
		"""
		self.messageHandler and self.messageHandler.logging(self, logging.DEBUG, f'MQTT: Connected with reason code: {reason_code} ({str(reason_code)})')
		if reason_code == 0:
			self.isConnected = True
			self.messageHandler and self.messageHandler.onConnect(self)
		else:
			self.isConnected = False
			if self.messageHandler:
				self.messageHandler.logging(self, logging.ERROR, f'MQTT: Cannot connect to broker. Reason code: {reason_code} ({str(reason_code)})')
				self.messageHandler.onError(self, reason_code.value)


	def _onDisconnect(self, client:MQTTClient, userdata:Any, disconnect_flags:mqtt.DisconnectFlags ,reason_code:mqtt_rc.ReasonCode, properties:mqtt_pr.Properties) -> None:
		"""	Callback when the MQTT client disconnected from the broker.

			Args:
				client: The MQTT client.
				userdata: User data.
				reason_code: Reason code
				properties : Properties (MQTTv5 Only)
		"""
		self.messageHandler and self.messageHandler.logging(self, logging.DEBUG, f'MQTT: Disconnected with reason code: {reason_code} ({str(reason_code)})')
		self.subscribedTopics.clear()

		match reason_code:
			case 0:
				self.isConnected = False
				self.messageHandler and	self.messageHandler.onDisconnect(self)
			case 7:
				self.isConnected = False
				self.messageHandler.logging(self, logging.ERROR, f'MQTT: Cannot disconnect from broker. Reason code: {reason_code} ({str(reason_code)})')
				self.messageHandler.logging(self, logging.ERROR, f'MQTT: Did another client connected with the same ID ({self.clientID})?')
				self.messageHandler and	self.messageHandler.onDisconnect(self)
			case _:
				self.isConnected = False
				if self.messageHandler:
					self.messageHandler.logging(self, logging.ERROR, f'MQTT: Cannot disconnect from broker. Reason code: {reason_code} ({str(reason_code)})')
					self.messageHandler.onDisconnect(self)
					self.messageHandler.onError(self, reason_code.value)


	def _onLog(self, client:MQTTClient, userdata:Any, level:int, buf:str) -> None:
		"""	Mapping of the paho MQTT client's log to the logging system. 
			Also handles different log-level scheme.

			Args:
				client: The MQTT client.
				userdata: User data.
				level: Log level.
				buf: Log message.
		"""
		self.lowLevelLogging and self.messageHandler and self.messageHandler.logging(self, mqtt.LOGGING_LEVEL[cast(mqtt_en.LogLevel, level)], f'MQTT: {buf}')
	

	def _onSubscribe(self, client:MQTTClient, userdata:Any, mid:int, reason_codes:list[mqtt_rc.ReasonCode], properties:mqtt_pr.Properties) -> None:
		"""	Callback when the client successfulle subscribed to a topic. The topic
			is also added to the internal topic list.

			Args:
				client: The MQTT client.
				userdata: User data.
				mid: The message ID.
				reason_codes: Reason codes received from the broker for each subscription
				properties : Properties (MQTTv5 Only)
		"""
		# TODO doc, error check when not connected, not subscribed
		for t in self.subscribedTopics.values():
			if t.mid == mid:
				t.isSubscribed = True
				self.messageHandler and self.messageHandler.onSubscribed(self, t.topic)
				break
	

	def _onUnsubscribe(self, client:MQTTClient, userdata:Any, mid:int, reason_codes:list[mqtt_rc.ReasonCode], properties:mqtt_pr.Properties) -> None:
		"""	Callback when the client successfulle unsubscribed from a topic. The topic
			is also removed from the internal topic list.
			"""
		# TODO doc, error check when not connected, not subscribed
		"""	Callback when the client successfulle unsubscribed from a topic. The topic
			is also removed from the internal list.

			Args:
				client: The MQTT client.
				userdata: User data.
				mid: The message ID.
				reason_codes: Reason codes received from the broker for each subscription
				properties : Properties (MQTTv5 Only)
		"""
		for t in self.subscribedTopics.values():
			if t.mid == mid:
				del self.subscribedTopics[t.topic]
				self.messageHandler and self.messageHandler.onUnsubscribed(self, t.topic)
				break


	def _onMessage(self, client:MQTTClient, userdata:Any, message:mqtt.MQTTMessage) -> None:
		"""	Handle a received message. Forward it to the apropriate handler callback
		 	(in another Thread).
			 
			Args:
				client: The MQTT client.
				userdata: User data.
				message: The received message.
		"""
		self.lowLevelLogging and self.messageHandler and self.messageHandler.logging(self, logging.DEBUG, f'MQTT: received topic:{message.topic}, payload:{message.payload!r}')
		for t in self.subscribedTopics.keys():
			if simpleMatch(message.topic, t, star='#'):
				if (topic := self.subscribedTopics[t]).callback:
					# Run actual request handling in a thread
					# For some reasons mid is not initialized in the on on_message callback, so we use the timestamp for the actor name
					BackgroundWorkerPool.newActor(topic.callback, name=f'mid_{message.timestamp}').start(	connection=self,
																											topic=message.topic,
																											data=message.payload, 
																											**topic.callbackArgs)
					break	# break at first occurence


	#
	#	MQTT messaging methods
	#

	def subscribeTopic(self, topic:str|list[str], callback:Optional[MQTTCallback] = None, **kwargs:Any) -> None:
		"""	Add one or more MQTT topics to subscribe to. Add the topic(s) afterwards
			to the list of subscribed-to topics.

			Args:
				topic: The topic(s) to subscribe to. Either a single topic or a list of topics.
				callback: The callback function to call when a message is received for the topic.
				kwargs: Additional arguments for the callback function.
		"""
		def _subscribe(topic:str) -> None:
			"""	Handle subscription of a single topic.
			"""
			if topic in self.subscribedTopics:
				self.messageHandler and self.messageHandler.logging(self, logging.WARNING, f'MQTT: topic already subscribed: {topic}')
				return
			if (r := self.mqttClient.subscribe(topic))[0] == 0:
				t = MQTTTopic(topic = topic, mid=r[1], callback=callback, callbackArgs=kwargs)
				self.subscribedTopics[topic] = t
			else:
				self.messageHandler and self.messageHandler.logging(self, logging.ERROR, f'MQTT: cannot subscribe: {r[0]}')

		if not self.mqttClient or not self.isConnected:
			self.messageHandler and self.messageHandler.logging(self, logging.ERROR, 'MQTT: Client missing or not initialized')
			return

		# either subscribe a list of topics or a single topic
		list(map(_subscribe, topic if isinstance(topic, list) else [topic]))


	def unsubscribeTopic(self, topic:str|MQTTTopic) -> None:
		"""	Unsubscribe from a topic. `topic` is either an MQTTTopic structure with
			a previously subscribed to topic, or a topic name, in which case
			it is searched for in the list of MQTTTopics.

			Args:
				topic: The topic to unsubscribe from.
		"""
		if isinstance(topic, MQTTTopic):
			if topic.topic not in self.subscribedTopics:
				self.messageHandler and self.messageHandler.logging(self, logging.WARNING, f'MQTT: unknown topic: {topic.topic}')
				return
			if (r := self.mqttClient.unsubscribe(topic.topic))[0] == 0:
				topic.mid = r[1]
			else:
				self.messageHandler and self.messageHandler.logging(self, logging.ERROR, f'MQTT: cannot unsubscribe: {r[0]}')
				return

		else:	# if topic is just the name we need to subscribe to
			if topic not in self.subscribedTopics:
				self.messageHandler and self.messageHandler.logging(self, logging.WARNING, f'MQTT: unknown topic: {topic}')
				return
			t = self.subscribedTopics[topic]
			if t.isSubscribed:
				if (r := self.mqttClient.unsubscribe(t.topic))[0] == 0:
					t.mid = r[1]
				else:
					self.messageHandler and self.messageHandler.logging(self, logging.ERROR, f'MQTT: cannot unsubscribe: {r[0]}')
					return
			else:
				self.messageHandler and self.messageHandler.logging(self, logging.WARNING, f'MQTT: topic not subscribed: {topic}')

		# topic is removed in _onUnsubscribe() callback


	def isFullySubscribed(self) -> bool:
		"""	Check whether the number managed subscriptions matches the number of
			currently subscribed-to topics.

			Return:
				True if fully subscribed, False otherwise.
		"""
		return self.subscribedCount == len(self.subscribedTopics)


	def publish(self, topic:str, data:bytes) -> None:
		"""	Publish the message *data* with the topic *topic* with the MQTT broker.
		
			Args:
				topic: The topic to publish to.
				data: The data to publish.
		"""
		self.mqttClient.publish(topic, data)



##############################################################################
#
#	Utility functions
#

def idToMQTT(id:str) -> str:
	"""	Convert a oneM2M ID to an MQTT compatible path element.

		Args:
			id: The oneM2M ID to convert.

		Returns:
			The MQTT compatible path element.
	"""
	return f'{id.lstrip("/").replace("/", ":")}'


def idToMQTTClientID(id:str, isCSE:Optional[bool] = True) -> str:
	"""	Convert a oneM2M ID to an MQTT client ID.

		Args:
			id: The oneM2M ID to convert.
			isCSE: Whether the ID is a CSE-ID or an AE-ID.

		Returns:
			The MQTT client ID.
	"""
	return f'{"C::" if isCSE else "A::"}{id.lstrip("/")}'


def mqttToId(mqttId:str, isCSE:Optional[bool] = True) -> Tuple[str, bool]:
	"""	Convert an MQTT compatible path element to an ID.

		Args:
			mqttId: The MQTT compatible path element to convert.
			isCSE: Whether the ID is a CSE-ID or an AE-ID.

		Returns:
			The ID and whether it is a CSE-ID or an AE-ID.
	"""
	match mqttId:
		case x if x.startswith('A:'):
			isCSE = False
		case x if x.startswith('C:'):
			isCSE = True
		case _:
			return None, False
	return mqttId[2:].replace(':', '/'), isCSE


MQTTCallback = Callable[[MQTTConnection, str, bytes], None]
""" Type for an MQTT Callback. """
