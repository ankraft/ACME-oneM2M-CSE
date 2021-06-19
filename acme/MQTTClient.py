#
#	MQTTClient.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of an MQTT Client for an MQTT Mcx binding implementation.
#

from __future__ import annotations
from Logging import Logging as L
from Configuration import Configuration
from helpers.BackgroundWorker import BackgroundWorkerPool
import CSE, Utils

import paho.mqtt.client as mqtt


class MQTTClient(object):
	mqttClient = None

	def __init__(self) -> None:
		self.enable				= Configuration.get('mqtt.enable')
		self.brokerAddress		= Configuration.get('mqtt.address')
		self.brokerPort			= Configuration.get('mqtt.port')
		self.keepalive			= Configuration.get('mqtt.keepalive')
		self.bindIF				= Configuration.get('mqtt.bindIF')
		self.isStopped			= True
		self.isConnected		= False
		self.clientName			= f'C::{Utils.getIdFromOriginator(CSE.cseCsi)}'
		L.isInfo and  L.log('MQTT client initialized')


	def run(self) -> None:
		"""	Run the MQTT client in a separate thread.
		"""
		if not self.enable:
			L.isInfo and L.log('MQTT: client NOT enabled')
			return
		L.isDebug and L.logDebug(f'MQTT: client name: {self.clientName}')
		self.mqttClient = mqtt.Client(client_id=self.clientName, clean_session=False)	# clean_session is defined by TS-0010
		if CSE.security.useTLS:
			self.mqttClient.tls_set_context(CSE.security.getSSLContext())
		
		self.mqttClient.on_connect = self._onConnect
		self.mqttClient.on_disconnect = self._onDisconnect
		self.mqttClient.on_log = self._onLog
		
		# TODO optional username/password, also in config. self.mqttClient.username_pw_set()

		try:
			self.mqttClient.connect(host=self.brokerAddress, port=self.brokerPort, keepalive=self.keepalive, bind_address=self.bindIF)
		except Exception as e:
			L.logErr(f'MQTT: cannot connect to broker: {e}', showStackTrace=False)
			CSE.shutdown()
			return


		# TODO put into an actor worker, even when this is not necessary. But it then shows in the list of workers

		self.mqttClient.loop_start()
		self.isStopped = False	
		if L.isInfo: L.log('MQTT: client started')


	def shutdown(self) -> bool:
		"""	Shutting down the MQTT client.
		"""
		if self.enable:
			if self.mqttClient:
				self.mqttClient.loop_stop()
				self.mqttClient.disconnect()	# -> in disconnect?
		L.isInfo and L.log('MQTT client shut down')
		self.isStopped = True
		return True
	

	#
	#	MQTT callbacks
	#
	
	def _onConnect(self, client, userdata, flags, rc):
		"""	Callback when the MQTT client connected to the broker.
		"""
		L.isDebug and L.logDebug(f'MQTT: Connected with result code: {rc}')
		if rc == 0:
			self.isConnected = True
		else:
			CSE.shutdown()

	def _onDisconnect(self, client, userdata, rc):
		"""	Callback when the MQTT client disconnected from the broker.
		"""
		L.isDebug and L.logDebug(f'MQTT: Disconnected with result code: {rc}')
		if rc == 0:
			self.isConnected = False


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