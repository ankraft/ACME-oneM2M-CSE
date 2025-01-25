#
#	CoAPServerConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" CoAP Server Binding configurations """

from __future__ import annotations
from typing import Optional

import configparser, os

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...helpers.NetworkTools import isValidPort, isValidateHostname, isValidateIpAddress


class CoAPServerConfiguration(ModuleConfiguration):
	""" CoAP Server Binding configurations.
	"""

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		""" Read the CoAP configuration from the configuration file.

			Args:
				parser: The configuration parser.
				config: The configuration object.
		"""

		# override configuration with command line arguments
		if Configuration._args_coapEnabled is not None:
			Configuration.websocket_enable = Configuration._args_wsEnabled

		# CoAP configs
		config.coap_enable = parser.getboolean('coap', 'enable', fallback = False)
		config.coap_listenIF = parser.get('coap', 'listenIF', fallback = '0.0.0.0')
		config.coap_port = parser.getint('coap', 'port', fallback = None) 	# Default will be determined later (s.b.)
		config.coap_address = parser.get('coap', 'address', fallback = 'coap://127.0.0.1:5683') 	# Default will be determined later (s.b.)
		config.coap_timeout = parser.getfloat('coap', 'timeout', fallback = 10.0)
		config.coap_clientConnectionCacheSize = parser.getint('coap', 'clientConnectionCacheSize', fallback = 100)

		#	CoAP Client Security

		config.coap_security_caCertificateFile = parser.get('coap.security', 'caCertificateFile', fallback = None)
		config.coap_security_caPrivateKeyFile = parser.get('coap.security', 'caPrivateKeyFile', fallback = None)
		config.coap_security_dtlsVersion = parser.get('coap.security', 'dtlsVersion', fallback = 'auto')
		config.coap_security_useDTLS = parser.getboolean('coap.security', 'useDTLS', fallback = False)
		config.coap_security_verifyCertificate = parser.getboolean('coap.security', 'verifyCertificate', fallback = False)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		"""	Validate the CoAP configuration.

			Args:
				config: The configuration object.
				initial: If True, this is the initial validation.

			Raises:
				ConfigurationError if the configuration is invalid.
		"""

		# override configuration with command line arguments
		if Configuration._args_coapEnabled is not None:
			Configuration.coap_enable = Configuration._args_coapEnabled

		if config.coap_security_useDTLS:
			if (val := config.coap_address).startswith('coap:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "coap" to "coaps" in [i]\[coap]:address[/i]')
				config.coap_address = val.replace('coap:', 'coaps:')
			# registrar might still be accessible via another protocol
		else: 
			if (val := config.coap_address).startswith('coaps:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "coaps" to "coap" in [i]\[coap]:address[/i]')
				config.coap_address = val.replace('coaps:', 'coap:')
			# registrar might still be accessible via another protocol

		if not isValidPort(config.coap_port):
			raise ConfigurationError(fr'Configuration Error: Invalid port number for [i]\[coap]:port[/i]: {config.websocket_port}')
		if not (isValidateHostname(config.coap_listenIF) or isValidateIpAddress(config.coap_listenIF)):
			raise ConfigurationError(fr'Configuration Error: Invalid hostname or IP address for [i]\[coap]:listenIF[/i]: {config.coap_listenIF}')
		if config.coap_timeout < 0.0:
			raise ConfigurationError(fr'Configuration Error: Invalid timeout value for [i]\[coap]:timeout[/i]: {config.coap_timeout}')
		if config.coap_clientConnectionCacheSize < 0:
			raise ConfigurationError(fr'Configuration Error: Invalid value for [i]\[coap]:clientConnectionCacheSize[/i]: {config.coap_clientConnectionCacheSize}')

		# COAP TLS & certificates
		if not config.coap_security_useDTLS:	# clear certificates configuration if not in use
			config.coap_security_verifyCertificate = False
			config.coap_security_dtlsVersion = 'auto'
			config.coap_security_caCertificateFile = ''
			config.coap_security_caPrivateKeyFile = ''
		else:
			if not (val := config.coap_security_dtlsVersion).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				raise ConfigurationError(fr'Configuration Error: Unknown value for [i]\[coap.security]:dtlsVersion[/i]: {val}')
			config.coap_security_dtlsVersion = val # lower case
			if not (val := config.coap_security_caCertificateFile):
				raise ConfigurationError(r'Configuration Error: [i]\[coap.security]:caCertificateFile[/i] must be set when DTLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'Configuration Error: [i]\[coap.security]:caCertificateFile[/i] does not exists or is not accessible: {val}')
			if not (val := config.coap_security_caPrivateKeyFile):
				raise ConfigurationError(r'Configuration Error: [i]\[coap.security]:caPrivateKeyFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'Configuration Error: [i]\[coap.security]:caPrivateKeyFile[/i] does not exists or is not accessible: {val}')
			
		# Warning if security is enabled, because it is not supported yet.
		# Remove this warning when security is supported
		if config.coap_security_useDTLS:
			Configuration._print(r'[orange3]Configuration Warning: CoAP security is not yet supported. Security settings will be ignored.')

