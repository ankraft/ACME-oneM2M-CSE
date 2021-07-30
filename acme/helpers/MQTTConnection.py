#
#	MQTTConnection.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of an MQTT Client helper class.
#

from __future__ import annotations
from abc import abstractmethod, ABC
import ssl, time
from dataclasses import dataclass
from typing import Callable, Any, Tuple
import logging

from .BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from .TextTools import simpleMatch

import paho.mqtt.client as mqtt

@dataclass
class MQTTTopic:
	"""	Structure that represents a subscribed-to topic.
	"""
	topic:str				= None
	mid:int					= None
	isSubscribed:bool		= False
	callback:MQTTCallback	= None
	callbackArgs:dict 		= None


class MQTTHandler(ABC):
	"""	This abstract base class defines the interface for an MQTT handler class. 
		The abstract methods defined here must be implemented by the implementing class.

		The implementing class acts as a handler for various callbacks when dealing with
		the MQTT handler. To receive messages a client implementation must register topics
		and the callbacks for them in the `onConnect()` method.
	"""

	@abstractmethod
	def onConnect(self, connection:MQTTConnection) -> None:
		"""	This method is called after the MQTT client connected to the MQTT broker. 
			Usually, an MQTT client should subscribe to topics and register the callback
			methods here.
		"""
		pass

	@abstractmethod
	def onDisconnect(self, connection:MQTTConnection) -> None:
		"""	This method is called after the MQTT client disconnected from the MQTT broker. 
		"""
		pass

	@abstractmethod
	def onError(self, connection:MQTTConnection, rc:int) -> None:
		"""	This method is called when receiving an error when communicating with the MQTT broker. 
		"""
		pass

	@abstractmethod
	def logging(self, connection:MQTTConnection, level:int, message:str) -> None:
		"""	This method is called when a log message should be handled. 
		"""
		pass


##############################################################################


class MQTTConnection(object):

	#
	#	Runtime methods
	#

	def __init__(self, address:str, port:int=None, keepalive:int=60, interface:str='0.0.0.0', 
					clientName:str=None, username:str=None, password:str=None,
					useTLS:bool=False, caFile:str=None, verifyCertificate:bool=False,
					messageHandler:MQTTHandler=None
				) -> None:
		self.brokerAddress							= address
		self.brokerPort								= port if port else 4883 if useTLS else 1883
		self.keepalive								= keepalive
		self.bindIF									= interface
		self.username:str							= username
		self.password:str 							= password
		self.useTLS:bool							= useTLS
		self.verifyCertificate						= verifyCertificate
		self.caFile									= caFile
		self.isStopped								= True
		self.isConnected							= False
		self.clientName								= clientName

		self.mqttClient:mqtt.Client 				= None
		self.messageHandler:MQTTHandler				= messageHandler
		self.actor:BackgroundWorker 				= None
		self.subscribedTopics:dict[str, MQTTTopic]	= {}

	
	def shutdown(self) -> bool:
		"""	Shutting down the MQTT client.
		"""
		self.isStopped = True
		if self.mqttClient and self.isConnected:
			# Unsubscribe from all topics
			for t in self.subscribedTopics.values():
				self.unsubscribeTopic(t)
			# wait a moment for all unsubscribe ACKs to arrive
			while len(self.subscribedTopics) > 0:
				time.sleep(0.1)
			# Then disconnect. The actor is stoped implicitly
			self.mqttClient.disconnect()
			self.actor = None

		self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.INFO, 'MQTT client shut down')
		return True


	def run(self) -> None:
		"""	Initialize and run the MQTT client as a BackgroundWorker/Actor.
		"""
		self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.DEBUG, f'MQTT: client name: {self.clientName}')
		self.mqttClient = mqtt.Client(client_id=self.clientName, clean_session=False)	# clean_session is defined by TS-0010

		# Enable SSL
		if self.useTLS:
			self.mqttClient.tls_set(ca_certs=self.caFile, cert_reqs=ssl.CERT_REQUIRED if self.verifyCertificate else ssl.CERT_NONE)

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
			self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.DEBUG, f'MQTT: connecting to host:{self.brokerAddress}, port:{self.brokerPort}, keepalive: {self.keepalive}, bind: {self.bindIF}')
			self.mqttClient.connect(host=self.brokerAddress, port=self.brokerPort, keepalive=self.keepalive, bind_address=self.bindIF)
		except Exception as e:
			if self.messageHandler:
				self.messageHandler.logging(self.mqttClient, logging.ERROR, f'MQTT: cannot connect to broker: {e}')
				self.messageHandler.onError(self, -1)

		# Actually start the actor to run the MQTT client as a thread
		self.actor = BackgroundWorkerPool.newActor(self._mqttActor, name='MQTTClient').start()


	def _mqttActor(self) -> bool:
		"""	Backgroundworker callback to run the actuall MQTT loop.
		"""
		self.isStopped = False
		self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.INFO, 'MQTT: client started')
		while not self.isStopped:
			self.mqttClient.loop_forever()	# Will return when disconnect() is called
		return True
	
	
	#
	#	MQTT/paho callbacks
	#

	def _onConnect(self, client:mqtt.Client, userdata:Any, flags:dict, rc:int) -> None:
		"""	Callback when the MQTT client connected to the broker.
		"""
		self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.DEBUG, f'MQTT: Connected with result code: {rc}')
		if rc == 0:
			self.isConnected = True
			self.messageHandler and self.messageHandler.onConnect(self)
		else:
			self.isConnected = False
			if self.messageHandler:
				self.messageHandler.logging(self.mqttClient, logging.ERROR, f'MQTT: Cannot connect to broker. Result code: {rc} ({mqtt.error_string(rc)})')
				self.messageHandler.onError(self, rc)


	def _onDisconnect(self, client:mqtt.Client, userdata:Any, rc:int) -> None:
		"""	Callback when the MQTT client disconnected from the broker.
		"""
		self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.DEBUG, f'MQTT: Disconnected with result code: {rc}')
		self.subscribedTopics.clear()
		if rc == 0:
			self.isConnected = False
			self.messageHandler and	self.messageHandler.onDisconnect(self)
		else:
			self.isConnected = False
			if self.messageHandler:
				self.messageHandler.logging(self.mqttClient, logging.ERROR, f'MQTT: Cannot disconnect from broker. Result code: {rc} ({mqtt.error_string(rc)})')
				self.messageHandler.onError(self, rc)


	def _onLog(self, client:mqtt.Client, userdata:Any, level:int, buf:str) -> None:
		"""	Mapping of the paho MQTT client's log to the logging system. Also handles different log-level scheme.
		"""
		self.messageHandler and self.messageHandler.logging(self.mqttClient, mqtt.LOGGING_LEVEL[level], f'MQTT: {buf}')
	

	def _onSubscribe(self, client:mqtt.Client, userdata:Any, mid:int, granted_qos:int) -> None:
		# TODO doc, error check when not connected, not subscribed
		for t in self.subscribedTopics.values():
			if t.mid == mid:
				t.isSubscribed = True
				break
	

	def _onUnsubscribe(self, client:mqtt.Client, userdata:Any, mid:int) -> None:
		# TODO doc, error check when not connected, not subscribed
		"""	Callback when the client successfulle unsubscribed from a topic. The topic
			is also removed from the internal list.
		"""
		for t in self.subscribedTopics.values():
			if t.mid == mid:
				del self.subscribedTopics[t.topic]
				break


	def _onMessage(self, client:mqtt.Client, userdata:Any, message:mqtt.MQTTMessage) -> None:
		"""	Handle a received message. Forward it to the apropriate handler callback (in a Thread)
		"""
		self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.DEBUG, f'MQTT: received topic:{message.topic}, payload:{message.payload}')
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

	def subscribeTopic(self, topic:str, callback:MQTTCallback=None, **kwargs:Any) -> None:
		"""	Add a MQTT topic to subscribe to. Add this topic afterwards
			to the list of subscribed-to topics.
		"""
		if not self.mqttClient or not self.isConnected:
			self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.ERROR, 'MQTT: Client missing or not initialized')
			return
		if topic in self.subscribedTopics:
			self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.WARNING, f'MQTT: topic already subscribed: {topic}')
			return

		if (r := self.mqttClient.subscribe(topic))[0] == 0:
			t = MQTTTopic(topic = topic, mid=r[1], callback=callback, callbackArgs=kwargs)
			self.subscribedTopics[topic] = t
		else:
			self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.ERROR, f'MQTT: cannot subscribe: {r[0]}')

	def unsubscribeTopic(self, topic:str|MQTTTopic) -> None:
		"""	Unsubscribe from a topic. `topic` is either an MQTTTopic structure with
			a previously subscribed to topic, or a topic name, in which case
			it is searched for in the list of MQTTTopics.
		"""
		if isinstance(topic, MQTTTopic):
			if topic.topic not in self.subscribedTopics:
				self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.WARNING, f'MQTT: unknown topic: {topic.topic}')
				return
			if (r := self.mqttClient.unsubscribe(topic.topic))[0] == 0:
				topic.mid = r[1]
			else:
				self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.ERROR, f'MQTT: cannot unsubscribe: {r[0]}')
				return

		else:	# if topic is just the name we need to subscribe to
			if topic not in self.subscribedTopics:
				self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.WARNING, f'MQTT: unknown topic: {topic}')
				return
			t = self.subscribedTopics[topic]
			if t.isSubscribed:
				if (r := self.mqttClient.unsubscribe(t.topic))[0] == 0:
					t.mid = r[1]
				else:
					self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.ERROR, f'MQTT: cannot unsubscribe: {r[0]}')
					return
			else:
				self.messageHandler and self.messageHandler.logging(self.mqttClient, logging.WARNING, f'MQTT: topic not subscribed: {topic}')

		# topic is removed in _onUnsubscribe() callback
	


	def publish(self, topic:str, data:bytes) -> None:
		"""	Publish the message `data` with the topic `topic` with the MQTT broker.
		"""
		self.mqttClient.publish(topic, data)



##############################################################################
#
#	Utility functions
#

def idToMQTT(id:str) -> str:
	"""	Convert a oneM2M ID to an MQTT compatible path element.
	"""
	return f'{id.lstrip("/").replace("/", ":")}'


def idToMQTTClientID(id:str, isCSE:bool=True) -> str:
	"""	Convert a oneM2M ID to an MQTT client ID.
	"""
	return f'{"C::" if isCSE else "A::"}{id.lstrip("/")}'

def mqttToId(mqttId:str, isCSE:bool=True) -> Tuple[str, bool]:
	"""	Convert an MQTT compatible path element to an ID.
	"""
	if mqttId.startswith('A:'):
		isCSE = False
	elif mqttId.startswith('C:'):
		isCSE = True
	else:
		return None, False
	return mqttId[2:].replace(':', '/'), isCSE


# Type for an MQTT Callback
MQTTCallback = Callable[[MQTTConnection, str, bytes], None]
