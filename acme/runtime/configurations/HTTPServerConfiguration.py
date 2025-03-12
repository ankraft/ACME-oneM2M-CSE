#
#	HTTPServerConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	HTTP Server Binding configurations
#

from __future__ import annotations
from typing import Optional

import configparser, os

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...etc.Utils import normalizeURL
from ...helpers.NetworkTools import isValidPort, isValidateIpAddress, isValidateHostname

class HTTPServerConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		"""	Read the configuration from the configuration file.

			Args:
				parser: The configuration parser.
				config: The configuration object.
		"""

		#	HTTP Server
		config.http_address = parser.get('http', 'address', fallback = 'http://127.0.0.1:8080')
		config.http_allowPatchForDelete = parser.getboolean('http', 'allowPatchForDelete', fallback = False)
		config.http_enableStructureEndpoint = parser.getboolean('http', 'enableStructureEndpoint', fallback = False)
		config.http_enableUpperTesterEndpoint = parser.getboolean('http', 'enableUpperTesterEndpoint', fallback = False)
		config.http_listenIF = parser.get('http', 'listenIF', fallback = '0.0.0.0')
		config.http_port = parser.getint('http', 'port', fallback = 8080)
		config.http_root = parser.get('http', 'root', fallback = '')
		config.http_timeout = parser.getfloat('http', 'timeout', fallback = 10.0)

		#	HTTP Server CORS
		config.http_cors_enable = parser.getboolean('http.cors', 'enable', fallback = False)
		config.http_cors_resources = parser.getlist('http.cors', 'resources', fallback = [ r'/*' ])	# type: ignore[attr-defined]

		#	HTTP Server Security
		config.http_security_caCertificateFile = parser.get('http.security', 'caCertificateFile', fallback = None)
		config.http_security_caPrivateKeyFile = parser.get('http.security', 'caPrivateKeyFile', fallback = None)
		config.http_security_tlsVersion = parser.get('http.security', 'tlsVersion', fallback = 'auto')
		config.http_security_useTLS = parser.getboolean('http.security', 'useTLS', fallback = False)
		config.http_security_verifyCertificate = parser.getboolean('http.security', 'verifyCertificate', fallback = False)
		config.http_security_enableBasicAuth = parser.getboolean('http.security', 'enableBasicAuth', fallback = False)
		config.http_security_enableTokenAuth = parser.getboolean('http.security', 'enableTokenAuth', fallback = False)
		config.http_security_basicAuthFile = parser.get('http.security', 'basicAuthFile', fallback = './certs/http_basic_auth.txt')
		config.http_security_tokenAuthFile = parser	.get('http.security', 'tokenAuthFile', fallback = './certs/http_token_auth.txt')

		#	HTTP Server WSGI
		config.http_wsgi_enable = parser.getboolean('http.wsgi', 'enable', fallback = False)
		config.http_wsgi_connectionLimit = parser.getint('http.wsgi', 'connectionLimit', fallback = 100)
		config.http_wsgi_threadPoolSize = parser.getint('http.wsgi', 'threadPoolSize', fallback = 100)

		#	Web UI
		config.webui_root = parser.get('webui', 'root', fallback = '/webui')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		"""	Validate the configuration.

			Args:
				config: The configuration object.
				initial: If True, the configuration is validated for the first time.
		"""

		# override configuration with command line arguments
		if Configuration._args_httpAddress is not None:
			Configuration.http_address = Configuration._args_httpAddress
		if Configuration._args_httpPort is not None:
			Configuration.http_port = Configuration._args_httpPort
		if Configuration._args_listenIF is not None:
			Configuration.http_listenIF = Configuration._args_listenIF
		if Configuration._args_runAsHttps is not None:
			Configuration.http_security_useTLS = Configuration._args_runAsHttps
		if Configuration._args_runAsHttpWsgi is not None:
			Configuration.http_wsgi_enable = Configuration._args_runAsHttpWsgi

		config.http_address = normalizeURL(config.http_address)
		config.http_root = normalizeURL(config.http_root)

		# Just in case: check the URL's (http, ws)
		if config.http_security_useTLS:
			if config.http_address.startswith('http:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "http" to "https" in [i]\[http]:address[/i]')
				config.http_address = config.http_address.replace('http:', 'https:')
			# registrar might still be accessible via another protocol
		else: 
			if config.http_address.startswith('https:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "https" to "http" in [i]\[http]:address[/i]')
				config.http_address = config.http_address.replace('https:', 'http:')
			# registrar might still be accessible via another protocol

		# HTTP server
		if not isValidPort(config.http_port):
			raise ConfigurationError(fr'Configuration Error: Invalid port number for [i]\[http]:port[/i]: {config.http_port}')
		if not (isValidateHostname(config.http_listenIF) or isValidateIpAddress(config.http_listenIF)):
			raise ConfigurationError(fr'Configuration Error: Invalid hostname or IP address for [i]\[http]:listenIF[/i]: {config.http_listenIF}')
		if config.http_timeout < 0.0:
			raise ConfigurationError(fr'Configuration Error: Invalid timeout value for [i]\[http]:timeout[/i]: {config.http_timeout}')
		
		# HTTP TLS & certificates
		if not config.http_security_useTLS:	# clear certificates configuration if not in use
			config.http_security_verifyCertificate = False
			config.http_security_tlsVersion = 'auto'
			config.http_security_caCertificateFile = ''
			config.http_security_caPrivateKeyFile = ''
		else:
			if not (val := config.http_security_tlsVersion).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				raise ConfigurationError(fr'Configuration Error: Unknown value for [i]\[http.security]:tlsVersion[/i]: {val}')
			if not (val := config.http_security_caCertificateFile):
				raise ConfigurationError(r'Configuration Error: [i]\[http.security]:caCertificateFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'Configuration Error: [i]\[http.security]:caCertificateFile[/i] does not exists or is not accessible: {val}')
			if not (val := config.http_security_caPrivateKeyFile):
				raise ConfigurationError(r'Configuration Error: [i]\[http.security]:caPrivateKeyFile[/i] must be set when TLS is enabled')
			if not os.path.exists(val):
				raise ConfigurationError(fr'Configuration Error: [i]\[http.security]:caPrivateKeyFile[/i] does not exists or is not accessible: {val}')

		# HTTP Security
		Configuration.http_security_tlsVersion = Configuration.http_security_tlsVersion.lower()

		# HTTP CORS
		if initial and config.http_cors_enable and not config.http_security_useTLS:
			Configuration._print(r'[orange3]Configuration Warning: [i]\[http.security].useTLS[/i] (https) should be enabled when [i]\[http.cors].enable[/i] is enabled.')

		# HTTP authentication
		if config.http_security_enableBasicAuth and not config.http_security_basicAuthFile:
			raise ConfigurationError(r'Configuration Error: [i]\[http.security]:basicAuthFile[/i] must be set when HTTP Basic Auth is enabled')
		if config.http_security_enableTokenAuth and not config.http_security_tokenAuthFile:
			raise ConfigurationError(r'Configuration Error: [i]\[http.security]:tokenAuthFile[/i] must be set when HTTP Token Auth is enabled')

		# HTTP WSGI
		if config.http_wsgi_enable and config.http_security_useTLS:
			# WSGI and TLS cannot both be enabled
			raise ConfigurationError(r'Configuration Error: [i]\[http.security].useTLS[/i] (https) cannot be enabled when [i]\[http.wsgi].enable[/i] is enabled (WSGI and TLS cannot both be enabled).')
		if config.http_wsgi_threadPoolSize < 1:
			raise ConfigurationError(r'Configuration Error: [i]\[http.wsgi]:threadPoolSize[/i] must be > 0')
		if config.http_wsgi_connectionLimit < 1:
			raise ConfigurationError(r'Configuration Error: [i]\[http.wsgi]:connectionLimit[/i] must be > 0')
