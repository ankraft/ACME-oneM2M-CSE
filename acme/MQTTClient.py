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
from Logging import Logging as L
from Configuration import Configuration
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

class MQTTClient(object):

	def __init__(self) -> None:
		self.mqttClient:mqtt.Client 			= None
		self.actor:BackgroundWorker 			= None
		self.enable								= Configuration.get('mqtt.enable')
		self.brokerAddress						= Configuration.get('mqtt.address')
		self.brokerPort							= Configuration.get('mqtt.port')
		self.keepalive							= Configuration.get('mqtt.keepalive')
		self.bindIF								= Configuration.get('mqtt.bindIF')
		self.isStopped							= True
		self.isConnected						= False
		self.subscribedTopics:list[MQTTTopic]	= []
		self.clientName							= f'C::{Utils.getIdFromOriginator(CSE.cseCsi)}'
		L.isInfo and  L.log('MQTT client initialized')


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

		# Actually start the actor to sun the MQTT client as a thread
		self.actor = BackgroundWorkerPool.newActor(self._mqttActor, name='MQTTClient')
		self.actor.start()


	def _mqttActor(self) -> bool:
		"""	Backgroundworker callback to run the actuall MQTT loop.
		"""
		self.isStopped = False	
		if L.isInfo: L.log('MQTT: client started')
		self.mqttClient.loop_forever()	# Will return when disconnect() is called
		return True
	

	def shutdown(self) -> bool:
		"""	Shutting down the MQTT client.
		"""
		if self.enable and self.mqttClient is not None:
			if self.isConnected:
				# Unsubscribe from all topics
				for t in self.subscribedTopics:
					self.unsubscribeTopic(t)
				# wait a moment for all unsubscribe ACKs to arrive
				while len(self.subscribedTopics) > 0:
					time.sleep(0.1)
				# Then disconnect. The actor is stoped implicitly
				self.mqttClient.disconnect()
				self.actor = None

		self.isStopped = True
		L.isInfo and L.log('MQTT client shut down')
		return True
	

	def subscribeTopic(self, topic:str) -> None:
		"""	Add a MQTT topic to subscribe to. Add this topic afterwards
			to the list of subscribed to topics.
		"""
		if self.mqttClient is None or not self.isConnected:
			L.logErr('MQTT: Client missing or not initialized')
			return
		if (r := self.mqttClient.subscribe(topic))[0] == 0:
			t = MQTTTopic(topic = topic, mid=r[1])
			self.subscribedTopics.append(t)
		else:
			L.logErr(f'MQTT: cannot subscribe: {r[0]}')
			pass
	

	def unsubscribeTopic(self, topic:str|MQTTTopic) -> None:
		"""	Unsubscribe from a topic. `topic` is either an MQTTTopic structure with
			a previously subscribed to topic, or a topic name, in which case
			it is searched for in the list of MQTTTopics.
		"""
		if isinstance(topic, MQTTTopic):
			if (r := self.mqttClient.unsubscribe(topic.topic))[0] == 0:
				topic.mid = r[1]
			else:
				L.logErr(f'MQTT: cannot unsubscribe: {r[0]}')
				return

		else:	# if topic is just the name we need to se
			for t in self.subscribedTopics:
				if t.topic == topic and t.isSubscribed:
					if (r := self.mqttClient.unsubscribe(t.topic))[0] == 0:
						t.mid = r[1]
					else:
						L.logErr(f'MQTT: cannot unsubscribe: {r[0]}')
						return
		# topic is removed in _onUnsubscribe() callback


	#
	#	MQTT callbacks
	#

	def _onConnect(self, client, userdata, flags, rc):
		"""	Callback when the MQTT client connected to the broker.
		"""
		L.isDebug and L.logDebug(f'MQTT: Connected with result code: {rc}')
		if rc == 0:
			self.isConnected = True
			self.subscribeTopic('test')
			self.subscribeTopic('test2')
		else:
			CSE.shutdown()


	def _onDisconnect(self, client, userdata, rc):
		"""	Callback when the MQTT client disconnected from the broker.
		"""
		L.isDebug and L.logDebug(f'MQTT: Disconnected with result code: {rc}')
		if rc == 0:
			self.isConnected = False
			self.subscribedTopics.clear()


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
		L.isDebug and L.logDebug(f'{client}, {userdata}, {mid}, {granted_qos}')
		for t in self.subscribedTopics:
			if t.mid == mid:
				t.isSubscribed = True
				break
	

	def _onUnsubscribe(self, client, userdata, mid):
		# TODO doc, error check when not connected, not subscribed
		L.isDebug and L.logDebug(f'{client}, {userdata}, {mid}')
		for t in list(self.subscribedTopics):
			if t.mid == mid:
				self.subscribedTopics.remove(t)
				break


	def _onMessage(self, client, userdata, message:mqtt.MQTTMessage):
		# TODO doc, error check when not connected, not subscribed

		L.isDebug and L.logDebug(f'{client}, {userdata}, {message.topic}, {message.payload}')
		self.mqttClient.publish('bla', str(Utils.utcTime()))
