#
#	MQTTConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""MQTT Client configurations"""

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...helpers.NetworkTools import isValidPort


class MQTTConfiguration(ModuleConfiguration):
	"""MQTT Client configurations"""

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		#	MQTT Client
		config.mqtt_address = parser.get('mqtt', 'address', fallback='127.0.0.1')
		config.mqtt_enable = parser.getboolean('mqtt', 'enable', fallback=False)
		config.mqtt_keepalive = parser.getint('mqtt', 'keepalive', fallback=60)
		config.mqtt_listenIF = parser.get('mqtt', 'listenIF', fallback='0.0.0.0')
		config.mqtt_port = parser.getint('mqtt', 'port', fallback=None)			# Default will be determined later
		config.mqtt_timeout = parser.getfloat('mqtt', 'timeout', fallback=10.0)
		config.mqtt_topicPrefix = parser.get('mqtt', 'topicPrefix', fallback='')

		#	MQTT Client Security
		config.mqtt_security_allowedCredentialIDs = parser.getlist('mqtt.security', 'allowedCredentialIDs', fallback=[])	# type: ignore [attr-defined]
		config.mqtt_security_caCertificateFile = parser.get('mqtt.security', 'caCertificateFile', fallback=None)
		config.mqtt_security_password = parser.get('mqtt.security', 'password', fallback='')
		config.mqtt_security_username = parser.get('mqtt.security', 'username', fallback='')
		config.mqtt_security_useTLS = parser.getboolean('mqtt.security', 'useTLS', fallback=False)
		config.mqtt_security_verifyCertificate = parser.getboolean('mqtt.security', 'verifyCertificate', fallback=False)

		# MQTT Websocket Support
		config.mqtt_websocket_enable = parser.getboolean('mqtt.websocket', 'enable', fallback=False)
		config.mqtt_websocket_port = parser.getint('mqtt.websocket', 'port', fallback=8080)
		config.mqtt_websocket_path = parser.get('mqtt.websocket', 'path', fallback='')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool]=False) -> None:

		# override configuration with command line arguments
		if Configuration._args_mqttEnabled is not None:
			Configuration.mqtt_enable = Configuration._args_mqttEnabled

		#	MQTT client
		if not config.mqtt_port:	# set the default port depending on whether to use TLS
			config.mqtt_port = 8883 if config.mqtt_security_useTLS else 1883
		if not config.mqtt_security_username != (not config.mqtt_security_password):	# Hack: != -> either both are empty, or both are set
			raise ConfigurationError(fr'Configuration Error: Username or password missing for [i]\[mqtt.security][/i]')
	
		#	MQTT Websocket
		if isValidPort(config.mqtt_websocket_port) is False:
			raise ConfigurationError(fr'Configuration Error: Invalid port number {config.mqtt_websocket_port} for [i]\[mqtt.websocket].port[/i]')
		
		# remove empty cid from the list
		config.mqtt_security_allowedCredentialIDs = [ cid for cid in config.mqtt_security_allowedCredentialIDs if len(cid) ]

