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
from ...etc.Types import ContentSerializationType
from ...etc.Utils import normalizeURL
from ...etc.IDUtils import isValidCSI


class RemoteCSEServiceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Registrar CSE
		config.cse_registrar_address = parser.get('cse.registrar', 'address', fallback = None)
		config.cse_registrar_checkInterval = parser.getint('cse.registrar', 'checkInterval', fallback = 30)		# Seconds
		config.cse_registrar_cseID = parser.get('cse.registrar', 'cseID', fallback = None)
		config.cse_registrar_excludeCSRAttributes = parser.getlist('cse.registrar', 'excludeCSRAttributes', fallback = [])		# type: ignore [attr-defined]
		config.cse_registrar_resourceName = parser.get('cse.registrar', 'resourceName', fallback = None)
		config.cse_registrar_root = parser.get('cse.registrar', 'root', fallback = '')
		config.cse_registrar_serialization = parser.get('cse.registrar', 'serialization', fallback = 'json')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		config.cse_registrar_address = normalizeURL(config.cse_registrar_address)
		config.cse_registrar_root = normalizeURL(config.cse_registrar_root)

		# Registrar Serialization
		if isinstance(ct := config.cse_registrar_serialization, str):
			config.cse_registrar_serialization = ContentSerializationType.getType(ct)
			if config.cse_registrar_serialization == ContentSerializationType.UNKNOWN:
				raise ConfigurationError(fr'Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}')

		if config.cse_registrar_address and config.cse_registrar_cseID:
			if not isValidCSI(val := config.cse_registrar_cseID):
				raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:cseID[/i]: {val}')
			if len(config.cse_registrar_cseID) > 0 and len(config.cse_registrar_resourceName) == 0:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar]:resourceName[/i]')

