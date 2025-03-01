#
#	RemoteCSEServiceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Remote CSE Manager configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...etc.Types import ContentSerializationType, CSEType
from ...etc.Utils import normalizeURL
from ...etc.IDUtils import isValidCSI


class RemoteCSEServiceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Registrar CSE
		config.cse_registrar_address = parser.get('cse.registrar', 'address', fallback = None)
		config.cse_registrar_checkInterval = parser.getint('cse.registrar', 'checkInterval', fallback = 30)		# Seconds
		config.cse_registrar_cseID = parser.get('cse.registrar', 'cseID', fallback = None)
		config.cse_registrar_excludeCSRAttributes = parser.getlist('cse.registrar', 'excludeCSRAttributes', fallback = [])		# type: ignore [attr-defined]
		config.cse_registrar_resourceName = parser.get('cse.registrar', 'resourceName', fallback = '')
		config.cse_registrar_root = parser.get('cse.registrar', 'root', fallback = '')
		config.cse_registrar_serialization = parser.get('cse.registrar', 'serialization', fallback = 'json')
		config.cse_registrar_INCSEcseID = parser.get('cse.registrar', 'INCSEcseID', fallback = '/id-in')

		# Registrar CSE Security
		config.cse_registrar_security_httpUsername = parser.get('cse.registrar.security', 'httpUsername', fallback = None)
		config.cse_registrar_security_httpPassword = parser.get('cse.registrar.security', 'httpPassword', fallback = None)
		config.cse_registrar_security_httpBearerToken = parser.get('cse.registrar.security', 'httpBearerToken', fallback = None)
		config.cse_registrar_security_wsUsername = parser.get('cse.registrar.security', 'wsUsername', fallback = None)
		config.cse_registrar_security_wsPassword = parser.get('cse.registrar.security', 'wsPassword', fallback = None)
		config.cse_registrar_security_wsBearerToken = parser.get('cse.registrar.security', 'wsBearerToken', fallback = None)

		config.cse_registrar_security_selfHttpUsername = parser.get('cse.registrar.security', 'selfHttpUsername', fallback = None)
		config.cse_registrar_security_selfHttpPassword = parser.get('cse.registrar.security', 'selfHttpPassword', fallback = None)
		config.cse_registrar_security_selfWsUsername = parser.get('cse.registrar.security', 'selfWsUsername', fallback = None)
		config.cse_registrar_security_selfWsPassword = parser.get('cse.registrar.security', 'selfWsPassword', fallback = None)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		config.cse_registrar_address = normalizeURL(config.cse_registrar_address)
		config.cse_registrar_root = normalizeURL(config.cse_registrar_root)

		# Registrar Serialization
		if isinstance(ct := config.cse_registrar_serialization, str):
			config.cse_registrar_serialization = ContentSerializationType.getType(ct)
			if config.cse_registrar_serialization == ContentSerializationType.UNKNOWN:
				raise ConfigurationError(fr'Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}')

		if config.cse_registrar_address and config.cse_registrar_cseID and config.cse_type != CSEType.IN:
			if not isValidCSI(val := config.cse_registrar_cseID): 
				raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:cseID[/i]: {val}')
			if len(config.cse_registrar_cseID) > 0 and len(config.cse_registrar_resourceName) == 0:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar]:resourceName[/i]')
		
		if config.cse_registrar_INCSEcseID:
			if not isValidCSI(val := config.cse_registrar_INCSEcseID):
				raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:INCSEcseID[/i]: {val}')

		if config.cse_registrar_security_httpUsername and not config.cse_registrar_security_httpPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:httpPassword[/i]')
		if not config.cse_registrar_security_httpUsername and config.cse_registrar_security_httpPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:httpUsername[/i]')
		if config.cse_registrar_security_httpBearerToken and config.cse_registrar_security_httpUsername:
			raise ConfigurationError(r'Configuration Error: Only one of [i]\[cse.registrar.security]:httpBearerToken[/i] or [i]\[cse.registrar.security]:httpUsername[/i] can be set')
		if config.cse_registrar_security_wsUsername and not config.cse_registrar_security_wsPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:wsPassword[/i]')
		if not config.cse_registrar_security_wsUsername and config.cse_registrar_security_wsPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:wsUsername[/i]')
		if config.cse_registrar_security_wsBearerToken and config.cse_registrar_security_wsUsername:
			raise ConfigurationError(r'Configuration Error: Only one of [i]\[cse.registrar.security]:wsBearerToken[/i] or [i]\[cse.registrar.security]:wsUsername[/i] can be set')
		
		if config.cse_registrar_security_selfHttpUsername and not config.cse_registrar_security_selfHttpPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfHttpPassword[/i]')
		if not config.cse_registrar_security_selfHttpUsername and config.cse_registrar_security_selfHttpPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfHttpUsername[/i]')
		if config.cse_registrar_security_selfWsUsername and not config.cse_registrar_security_selfWsPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfWsPassword[/i]')
		if not config.cse_registrar_security_selfWsUsername and config.cse_registrar_security_selfWsPassword:
			raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfWsUsername[/i]')