#
#	WebSocketConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	WebSocket Binding configurations
#

from __future__ import annotations
from typing import Optional, cast

import configparser, os

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...etc.Types import LogLevel
from ...etc.Utils import normalizeURL
from ...helpers.NetworkTools import isValidPort, isValidateIpAddress, isValidateHostname


class WebSocketConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		"""	Read the configuration from the configuration file.

			Args:
				parser: The configuration parser.
				config: The configuration object.
		"""

		# Basic configs
		config.websocket_enable = parser.getboolean('websocket', 'enable', fallback = False)
		config.websocket_listenIF = parser.get('websocket', 'listenIF', fallback = '0.0.0.0')
		config.websocket_port = parser.getint('websocket', 'port', fallback = 8180)
		config.websocket_address = parser.get('websocket', 'address', fallback = 'ws://127.0.0.1:8180')
		config.websocket_loglevel = parser.get('websocket', 'loglevel', fallback = 'debug')
		config.websocket_timeout = parser.getfloat('websocket', 'timeout', fallback = 10.0)

		# Security configs
		config.websocket_security_caCertificateFile = parser.get('websocket.security', 'caCertificateFile', fallback = None)
		config.websocket_security_caPrivateKeyFile = parser.get('websocket.security', 'caPrivateKeyFile', fallback = None)
		config.websocket_security_tlsVersion = parser.get('websocket.security', 'tlsVersion', fallback ='auto')
		config.websocket_security_useTLS = parser.getboolean('websocket.security', 'useTLS', fallback = False)
		config.websocket_security_verifyCertificate = parser.getboolean('websocket.security', 'verifyCertificate', fallback = False)
		config.websocket_security_enableBasicAuth = parser.getboolean('websocket.security', 'enableBasicAuth', fallback = False)
		config.websocket_security_enableTokenAuth = parser.getboolean('websocket.security', 'enableTokenAuth', fallback = False)
		config.websocket_security_basicAuthFile = parser.get('websocket.security', 'basicAuthFile', fallback = './certs/ws_basic_auth.txt')
		config.websocket_security_tokenAuthFile = parser	.get('websocket.security', 'tokenAuthFile', fallback = './certs/ws_token_auth.txt')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		"""	Validate the configuration.

			Args:
				config: The configuration object.
				initial: Flag whether this is the initial validation.
		"""
		config.websocket_address = normalizeURL(config.websocket_address)

		# override configuration with command line arguments
		if Configuration._args_wsEnabled is not None:
			Configuration.websocket_enable = Configuration._args_wsEnabled

		if config.websocket_security_useTLS:
			if (val := config.websocket_address).startswith('ws:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "ws" to "wss" in [i]\[websocket]:address[/i]')
				config.websocket_address = val.replace('ws:', 'wss:')
			# registrar might still be accessible via another protocol
		else: 
			if (val := config.websocket_address).startswith('wss:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "wss" to "ws" in [i]\[websocket]:address[/i]')
				config.websocket_address = val.replace('wss:', 'ws:')
			# registrar might still be accessible via another protocol

		if not isValidPort(config.websocket_port):
			raise ConfigurationError(fr'Configuration Error: Invalid port number for [i]\[websocket]:port[/i]: {config.websocket_port}')
		if not (isValidateHostname(config.websocket_listenIF) or isValidateIpAddress(config.websocket_listenIF)):
			raise ConfigurationError(fr'Configuration Error: Invalid hostname or IP address for [i]\[websocket]:listenIF[/i]: {config.websocket_listenIF}')

		# Override loglevel with command line argument
		logLevel = Configuration._args_loglevel if Configuration._args_loglevel else config.websocket_loglevel
		logLevel = cast(LogLevel, logLevel).name if isinstance(logLevel, LogLevel) else logLevel
		if isinstance(logLevel, str):
			if (ll := LogLevel.toLogLevel(logLevel)) is None:
				raise ConfigurationError(fr'Configuration Error: Unsupported \[websocket]:loglevel: {logLevel}')
			config.websocket_loglevel = ll
		else:
			raise ConfigurationError(fr'Configuration Error: Unsupported \[websocket]:loglevel: {logLevel}')

		# WebSocket TLS & certificates
		if not config.websocket_security_useTLS:	# clear certificates configuration if not in use
			config.websocket_security_verifyCertificate = False
			config.websocket_security_tlsVersion = 'auto'
			config.websocket_security_caCertificateFile = ''
			config.websocket_security_caPrivateKeyFile = ''
		else:
			config.websocket_security_tlsVersion = config.websocket_security_tlsVersion.lower()
			if not (val := config.websocket_security_tlsVersion) in [ 'tls1.1', 'tls1.2', 'auto' ]:
				raise ConfigurationError(fr'Configuration Error: Unknown value for [i]\[websocket.security]:tlsVersion[/i]: {val}')
			
			if not (val := config.websocket_security_caCertificateFile):
				raise ConfigurationError(r'Configuration Error: [i]\[websocket.security]:caCertificateFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'Configuration Error: [i]\[websocket.security]:caCertificateFile[/i] does not exists or is not accessible: {val}')
			
			if not (val := config.websocket_security_caPrivateKeyFile):
				raise ConfigurationError(r'Configuration Error: [i]\[websocket.security]:caPrivateKeyFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'Configuration Error: [i]\[websocket.security]:caPrivateKeyFile[/i] does not exists or is not accessible: {val}')


		# WebSocket authentication
		if config.websocket_security_enableBasicAuth and not config.websocket_security_basicAuthFile:
			raise ConfigurationError(r'Configuration Error: [i]\[websocket.security]:basicAuthFile[/i] must be set when WebSocket Basic Auth is enabled')
		if config.websocket_security_enableTokenAuth and not config.websocket_security_tokenAuthFile:
			raise ConfigurationError(r'Configuration Error: [i]\[http.security]:tokenAuthFile[/i] must be set when WebSocket Token Auth is enabled')
