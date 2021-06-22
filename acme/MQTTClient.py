#
#	MQTTClient.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of an MQTT Client for an MQTT Mcx binding implementation.
#

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Callable
from Logging import Logging as L
from Configuration import Configuration
from Types import ContentSerializationType
from helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
import CSE, Utils

import paho.mqtt.client as mqtt

@dataclass
class MQTTTopic:
	"""	Structure that represents a subscribed-to topic.
	"""
	topic:str			= None
	mid:int				= None
	isSubscribed:bool	= False
	callback:Callable	= None
	callbackArgs:dict 	= None


# TODO split MQTThandler stuff. Only two callbacks for connected and disconnected to handle subscriptions.

class MQTTHandler(object):

	def onConnect(self, mqttClient:MQTTClient):
		# Subscribe to general requests
		mqttClient.subscribeTopic(f'{mqttClient.topicPrefix}/oneM2M/req/+/{mqttClient.clientName}/cbor', self._requestCallback, serialization=ContentSerializationType.CBOR)
		mqttClient.subscribeTopic(f'{mqttClient.topicPrefix}/oneM2M/req/+/{mqttClient.clientName}/json', self._requestCallback, serialization=ContentSerializationType.JSON)

		# TODO Subscribe to register requests

		# TODO Subscribe to responses

	def onDisconnect(self, mqttClient:MQTTClient):
		pass

	#
	#	Various request, register and response callbacks
	#

	def _requestCallback(self, mqttClient:MQTTClient, topic:str, data:str, args):
		L.logDebug(f'REQUEST {topic}, {data}, {args}')
		mqttClient.publish('test', f'{topic}, {data}, {args}')



##############################################################################


class MQTTClient(object):

	def __init__(self, mqttHandler:MQTTHandler=MQTTHandler()) -> None:
		self.mqttHandler:MQTTHandler				= mqttHandler
		self.mqttClient:mqtt.Client 				= None
		self.actor:BackgroundWorker 				= None
		self.enable									= Configuration.get('mqtt.enable')
		self.brokerAddress							= Configuration.get('mqtt.address')
		self.brokerPort								= Configuration.get('mqtt.port')
		self.keepalive								= Configuration.get('mqtt.keepalive')
		self.bindIF									= Configuration.get('mqtt.bindIF')
		self.username:str							= None  # TODO config
		self.password:str 							= None  # TODO config
		self.isStopped								= True
		self.isConnected							= False
		self.clientName								= idToMQTT(CSE.cseCsi)
		self.topicPrefix:str						= ''	# TODO config value
		self.subscribedTopics:dict[str, MQTTTopic]	= {}
		L.isInfo and  L.log('MQTT client initialized')

	
	def shutdown(self) -> bool:
		"""	Shutting down the MQTT client.
		"""
		self.isStopped = True
		if self.enable and self.mqttClient is not None:
			if self.isConnected:
				# Unsubscribe from all topics
				for t in self.subscribedTopics.values():
					self.unsubscribeTopic(t)
				# wait a moment for all unsubscribe ACKs to arrive
				while len(self.subscribedTopics) > 0:
					time.sleep(0.1)
				# Then disconnect. The actor is stoped implicitly
				self.mqttClient.disconnect()
				self.actor = None

		L.isInfo and L.log('MQTT client shut down')
		return True


	def run(self) -> None:
		"""	Initialize and run the MQTT client as a BackgroundWorker/Actor.
		"""
		if not self.enable:
			L.isInfo and L.log('MQTT: client NOT enabled')
			return
		L.isDebug and L.logDebug(f'MQTT: client name: {self.clientName}')
		self.mqttClient = mqtt.Client(client_id=self.clientName, clean_session=False)	# clean_session is defined by TS-0010
		if CSE.security.useTLS:
			self.mqttClient.tls_set_context(CSE.security.getSSLContext())
		
		self.mqttClient.on_connect 		= self._onConnect
		self.mqttClient.on_disconnect	= self._onDisconnect
		self.mqttClient.on_log			= self._onLog
		self.mqttClient.on_subscribe	= self._onSubscribe
		self.mqttClient.on_unsubscribe	= self._onUnsubscribe
		self.mqttClient.on_message		= self._onMessage

		# TODO optional username/password, also in config. self.mqttClient.username_pw_set()

		try:
			self.mqttClient.connect(host=self.brokerAddress, port=self.brokerPort, keepalive=self.keepalive, bind_address=self.bindIF)
		except Exception as e:
			L.logErr(f'MQTT: cannot connect to broker: {e}', showStackTrace=False)
			CSE.shutdown()
			return

		# Actually start the actor to run the MQTT client as a thread
		self.actor = BackgroundWorkerPool.newActor(self._mqttActor, name='MQTTClient').start()


	def _mqttActor(self) -> bool:
		"""	Backgroundworker callback to run the actuall MQTT loop.
		"""
		self.isStopped = False	
		if L.isInfo: L.log('MQTT: client started')
		while not self.isStopped:
			self.mqttClient.loop_forever()	# Will return when disconnect() is called
		return True
	

	def subscribeTopic(self, topic:str, callback:Callable=None, **kwargs) -> None:
		"""	Add a MQTT topic to subscribe to. Add this topic afterwards
			to the list of subscribed to topics.
		"""
		if self.mqttClient is None or not self.isConnected:
			L.logErr('MQTT: Client missing or not initialized')
			return
		if topic in self.subscribedTopics:
			L.isWarn and L.logWarn(f'MQTT: topic already subscribed: {topic}')
			return

		if (r := self.mqttClient.subscribe(topic))[0] == 0:
			t = MQTTTopic(topic = topic, mid=r[1], callback=callback, callbackArgs=kwargs)
			self.subscribedTopics[topic] = t
		else:
			L.logErr(f'MQTT: cannot subscribe: {r[0]}')
			pass
	

	def unsubscribeTopic(self, topic:str|MQTTTopic) -> None:
		"""	Unsubscribe from a topic. `topic` is either an MQTTTopic structure with
			a previously subscribed to topic, or a topic name, in which case
			it is searched for in the list of MQTTTopics.
		"""
		if isinstance(topic, MQTTTopic):
			if topic.topic not in self.subscribedTopics:
				L.isWarn and L.logWarn(f'MQTT: unknown topic: {topic.topic}')
				return
			if (r := self.mqttClient.unsubscribe(topic.topic))[0] == 0:
				topic.mid = r[1]
			else:
				L.logErr(f'MQTT: cannot unsubscribe: {r[0]}')
				return

		else:	# if topic is just the name we need to subscribe to
			if topic not in self.subscribedTopics:
				L.isWarn and L.logWarn(f'MQTT: unknown topic: {topic}')
				return
			t = self.subscribedTopics[topic]
			if t.isSubscribed:
				if (r := self.mqttClient.unsubscribe(t.topic))[0] == 0:
					t.mid = r[1]
				else:
					L.logErr(f'MQTT: cannot unsubscribe: {r[0]}')
					return
			else:
				L.isWarn and L.logWarn(f'MQTT: topic not subscribed: {topic}')

		# topic is removed in _onUnsubscribe() callback
	


	def publish(self, topic:str, data:bytes):
		# TODO doc
		self.mqttClient.publish(topic, data)


	#
	#	MQTT/paho callbacks
	#

	def _onConnect(self, client, userdata, flags, rc):
		"""	Callback when the MQTT client connected to the broker.
		"""
		L.isDebug and L.logDebug(f'MQTT: Connected with result code: {rc}')
		if rc == 0:
			self.isConnected = True
			if self.mqttHandler is not None:
				self.mqttHandler.onConnect(self)
		else:
			CSE.shutdown()


	def _onDisconnect(self, client, userdata, rc):
		"""	Callback when the MQTT client disconnected from the broker.
		"""
		L.isDebug and L.logDebug(f'MQTT: Disconnected with result code: {rc}')
		if rc == 0:
			self.isConnected = False
			self.subscribedTopics.clear()
			if self.mqttHandler is not None:
				self.mqttHandler.onDisconnect(self)


	def _onLog(self, client, userdata, level, buf):
		"""	Mapping of the paho MQTT client's log to the CSE's logging system.
		"""
		if level == mqtt.MQTT_LOG_DEBUG and L.isDebug:
			L.logDebug(f'MQTT: {buf}')
		elif (level == mqtt.MQTT_LOG_INFO or level == mqtt.mqtt.MQTT_LOG_NOTICE) and L.isInfo:
			L.log(f'MQTT: {buf}')
		elif level == mqtt.MQTT_LOG_WARNING and L.isWarn:
			L.logWarn(f'MQTT: {buf}')
		elif level == mqtt.MQTT_LOG_ERR:
			L.logErr(f'MQTT: {buf}', showStackTrace=False)
	

	def _onSubscribe(self, client, userdata, mid, granted_qos):
		# TODO doc, error check when not connected, not subscribed
		for t in self.subscribedTopics.values():
			if t.mid == mid:
				t.isSubscribed = True
				break
	

	def _onUnsubscribe(self, client, userdata, mid):
		# TODO doc, error check when not connected, not subscribed
		for t in self.subscribedTopics.values():
			if t.mid == mid:
				del self.subscribedTopics[t.topic]
				break


	def _onMessage(self, client, userdata, message:mqtt.MQTTMessage):
		"""	Handle a received message. Forward it to the apropriate handler callback (in a Thread)
		"""
		L.isDebug and L.logDebug(f'MQTT: received topic:{message.topic}, payload:{message.payload}')
		for t in self.subscribedTopics.keys():
			if Utils.simpleMatch(message.topic, t):
				topic = self.subscribedTopics[t]
				if topic.callback is not None:
					# Run actual request handling in a thread
					BackgroundWorkerPool.newActor(topic.callback, name=f'mid_{message.mid}').start(	mqttClient=self,
																									topic=message.topic,
																									data=message.payload, 
																									args=topic.callbackArgs)
				break




##############################################################################
#
#	Utility functions
#

def idToMQTT(id:str, isCSE:bool=True) -> id:
	return f'{"C:" if isCSE else "A:"}{id.replace("/", ":")}'

