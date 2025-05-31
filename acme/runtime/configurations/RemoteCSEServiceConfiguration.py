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
from ...etc.Constants import RuntimeConstants as RC
from ...etc.Types import ContentSerializationType, CSEType, CSERegistrar
from ...etc.Utils import normalizeURL
from ...etc.IDUtils import isValidCSI


class RemoteCSEServiceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		def parseRegistrar(section:str, registrar:CSERegistrar) -> None:
			# Parse a registrar configuration section and populate the registrar object
			registrar.spID = parser.get(section, 'spID', fallback=None)
			registrar.address = parser.get(section, 'address', fallback = None)
			registrar.cseID = parser.get(section, 'cseID', fallback = None)
			registrar.excludeCSRAttributes = parser.getlist(section, 'excludeCSRAttributes', fallback = [])		# type: ignore [attr-defined]
			registrar.resourceName = parser.get(section, 'resourceName', fallback = '')
			registrar.root = parser.get(section, 'root', fallback = '')
			registrar.serialization = parser.get(section, 'serialization', fallback = 'json')
			registrar.INCSEcseID = parser.get(section, 'INCSEcseID', fallback = '/id-in')


		def parseRegistrarSecurity(section:str, registrar:CSERegistrar) -> None:
			# Parse the security section for a registrar and populate the security attributes
			registrar.security.credentials.httpUsername = parser.get(section, 'httpUsername', fallback = None)
			registrar.security.credentials.httpPassword = parser.get(section, 'httpPassword', fallback = None)
			registrar.security.credentials.httpToken = parser.get(section, 'httpBearerToken', fallback = None)
			registrar.security.credentials.wsUsername = parser.get(section, 'wsUsername', fallback = None)
			registrar.security.credentials.wsPassword = parser.get(section, 'wsPassword', fallback = None)
			registrar.security.credentials.wsToken = parser.get(section, 'wsBearerToken', fallback = None)
			registrar.security.selfCredentials.httpUsername = parser.get(section, 'selfHttpUsername', fallback = None)
			registrar.security.selfCredentials.httpPassword = parser.get(section, 'selfHttpPassword', fallback = None)
			registrar.security.selfCredentials.wsUsername = parser.get(section, 'selfWsUsername', fallback = None)
			registrar.security.selfCredentials.wsPassword = parser.get(section, 'selfWsPassword', fallback = None)


		#	Registrar CSE
		registrar = CSERegistrar()
		parseRegistrar('cse.registrar', registrar)


		# config.cse_registrar_address = parser.get('cse.registrar', 'address', fallback = None)
		# config.cse_registrar_checkInterval = parser.getint('cse.registrar', 'checkInterval', fallback = 30)		# Seconds
		# config.cse_registrar_cseID = parser.get('cse.registrar', 'cseID', fallback = None)
		# config.cse_registrar_excludeCSRAttributes = parser.getlist('cse.registrar', 'excludeCSRAttributes', fallback = [])		# type: ignore [attr-defined]
		# config.cse_registrar_resourceName = parser.get('cse.registrar', 'resourceName', fallback = '')
		# config.cse_registrar_root = parser.get('cse.registrar', 'root', fallback = '')
		# config.cse_registrar_serialization = parser.get('cse.registrar', 'serialization', fallback = 'json')
		# config.cse_registrar_INCSEcseID = parser.get('cse.registrar', 'INCSEcseID', fallback = '/id-in')

		# Registrar CSE Security
		if parser.has_section('cse.registrar.security'):
			# parseRegistrarSecurity('cse.registrar.security', registrar)
			parseRegistrarSecurity('cse.registrar.security', registrar)


		# config.cse_registrar_security_httpUsername = parser.get('cse.registrar.security', 'httpUsername', fallback = None)
		# config.cse_registrar_security_httpPassword = parser.get('cse.registrar.security', 'httpPassword', fallback = None)
		# config.cse_registrar_security_httpBearerToken = parser.get('cse.registrar.security', 'httpBearerToken', fallback = None)
		# config.cse_registrar_security_wsUsername = parser.get('cse.registrar.security', 'wsUsername', fallback = None)
		# config.cse_registrar_security_wsPassword = parser.get('cse.registrar.security', 'wsPassword', fallback = None)
		# config.cse_registrar_security_wsBearerToken = parser.get('cse.registrar.security', 'wsBearerToken', fallback = None)
		# config.cse_registrar_security_selfHttpUsername = parser.get('cse.registrar.security', 'selfHttpUsername', fallback = None)
		# config.cse_registrar_security_selfHttpPassword = parser.get('cse.registrar.security', 'selfHttpPassword', fallback = None)
		# config.cse_registrar_security_selfWsUsername = parser.get('cse.registrar.security', 'selfWsUsername', fallback = None)
		# config.cse_registrar_security_selfWsPassword = parser.get('cse.registrar.security', 'selfWsPassword', fallback = None)

		config.cse_registrars[RC.cseSpid] = registrar

		# Get the SP (Mcc') configurations
		for section in parser.sections():
			if section.startswith('cse.sp.registrar.'):
				if not section.endswith('.security'):
					registrar = CSERegistrar()
					spName = section[len('cse.sp.registrar.'):]  # Extract the SP name from the section
					if spName == RC.cseSpid:
						raise ConfigurationError(r'Configuration Error: The registrar within the same Service Provider domain must be configured in the [cse.registrar] section.')
					parseRegistrar(section, registrar)
					config.cse_registrars[spName] = registrar
					continue
				else: 
					spName = section[len('cse.sp.registrar.'):-len('.security')]
					registrar = config.cse_registrars.get(spName, None)
					if not registrar:
						raise ConfigurationError(fr'Configuration Error: No SP Registrar configuration found for security section: {spName} -> {section}')
					parseRegistrarSecurity(f'cse.sp.registrar.{spName}.security', registrar)
					continue


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		# Validate CSE Type and remove default registrar if not IN
		for spName, registrar in config.cse_registrars.copy().items():

			# If the registrar has no name, use the own spID as the key
			# This seems to be a bit of a hack, but at the time when the own registrar is added, the RC.cseSpid is not yet set
			if spName is None:
				# Find the first non-None cseID or spID to use as the key
				config.cse_registrars[RC.cseSpid] = registrar
				config.cse_registrars.pop(spName)
				spName = RC.cseSpid


			match config.cse_type:
				# IN CSEs can NOT have a registrar other than other SP's one
				case CSEType.IN if spName == RC.cseSpid:
					if registrar.cseID != '/':	# "/" indicates an empty CSE ID
						raise ConfigurationError(r'Configuration Error: An IN CSE can not have a registrar (section: \[cse.registrar])')
					config.cse_registrars.pop(RC.cseSpid)

				# MN and ASN CSEs may have a registrar
				case CSEType.MN | CSEType.ASN if spName == RC.cseSpid:	
					if registrar.cseID == '/':	# "/" indicates an empty CSE ID, so remove it
						config.cse_registrars.pop(RC.cseSpid)

				# MN and ASCN CSE must not have a SP registrar
				case CSEType.MN | CSEType.ASN if spName != RC.cseSpid:	
					raise ConfigurationError(fr'Configuration Error: Service Provider Registrar: "{spName}" is not allowed for CSE Type: "{config.cse_type.name}"')

		# Validate CSE Registrars

		for spName, registrar in config.cse_registrars.items():

			# Normalize addresses
			registrar.address = normalizeURL(registrar.address)
			registrar.root = normalizeURL(registrar.root)

			# Registrar Serialization
			if isinstance(ct := registrar.serialization, str):
				registrar.serialization = ContentSerializationType.getType(ct)
				if registrar.serialization == ContentSerializationType.UNKNOWN:
					raise ConfigurationError(fr'Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}')

			if registrar.address and registrar.cseID and config.cse_type != CSEType.IN:
				if not isValidCSI(val := registrar.cseID): 
					raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:cseID[/i]: {val}')
				if len(registrar.cseID) > 0 and len(registrar.resourceName) == 0:
					raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar]:resourceName[/i]')

			if registrar.INCSEcseID:
				if not isValidCSI(val := registrar.INCSEcseID):
					raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:INCSEcseID[/i]: {val}')

			if registrar.security.credentials.httpUsername and not registrar.security.credentials.httpPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:httpPassword[/i]')
			if not registrar.security.credentials.httpUsername and registrar.security.credentials.httpPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:httpUsername[/i]')
			if registrar.security.credentials.httpToken and registrar.security.credentials.httpUsername:
				raise ConfigurationError(r'Configuration Error: Only one of [i]\[cse.registrar.security]:httpBearerToken[/i] or [i]\[cse.registrar.security]:httpUsername[/i] can be set')
			if registrar.security.credentials.wsUsername and not registrar.security.credentials.wsPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:wsPassword[/i]')
			if not registrar.security.credentials.wsUsername and registrar.security.credentials.wsPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:wsUsername[/i]')
			if registrar.security.credentials.wsToken and registrar.security.credentials.wsUsername:
				raise ConfigurationError(r'Configuration Error: Only one of [i]\[cse.registrar.security]:wsBearerToken[/i] or [i]\[cse.registrar.security]:wsUsername[/i] can be set')
			
			if registrar.security.selfCredentials.httpUsername and not registrar.security.selfCredentials.httpPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfHttpPassword[/i]')
			if not registrar.security.selfCredentials.httpUsername and registrar.security.selfCredentials.httpPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfHttpUsername[/i]')
			if registrar.security.selfCredentials.wsUsername and not registrar.security.selfCredentials.wsPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfWsPassword[/i]')
			if not registrar.security.selfCredentials.wsUsername and registrar.security.selfCredentials.wsPassword:
				raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfWsUsername[/i]')
			


		# config.cse_registrar_address = normalizeURL(config.cse_registrar_address)
		# config.cse_registrar_root = normalizeURL(config.cse_registrar_root)

		# # Registrar Serialization
		# if isinstance(ct := config.cse_registrar_serialization, str):
		# 	config.cse_registrar_serialization = ContentSerializationType.getType(ct)
		# 	if config.cse_registrar_serialization == ContentSerializationType.UNKNOWN:
		# 		raise ConfigurationError(fr'Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}')

		# if config.cse_registrar_address and config.cse_registrar_cseID and config.cse_type != CSEType.IN:
		# 	if not isValidCSI(val := config.cse_registrar_cseID): 
		# 		raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:cseID[/i]: {val}')
		# 	if len(config.cse_registrar_cseID) > 0 and len(config.cse_registrar_resourceName) == 0:
		# 		raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar]:resourceName[/i]')
		
		# if config.cse_registrar_INCSEcseID:
		# 	if not isValidCSI(val := config.cse_registrar_INCSEcseID):
		# 		raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse.registrar]:INCSEcseID[/i]: {val}')

		# if config.cse_registrar_security_httpUsername and not config.cse_registrar_security_httpPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:httpPassword[/i]')
		# if not config.cse_registrar_security_httpUsername and config.cse_registrar_security_httpPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:httpUsername[/i]')
		# if config.cse_registrar_security_httpBearerToken and config.cse_registrar_security_httpUsername:
		# 	raise ConfigurationError(r'Configuration Error: Only one of [i]\[cse.registrar.security]:httpBearerToken[/i] or [i]\[cse.registrar.security]:httpUsername[/i] can be set')
		# if config.cse_registrar_security_wsUsername and not config.cse_registrar_security_wsPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:wsPassword[/i]')
		# if not config.cse_registrar_security_wsUsername and config.cse_registrar_security_wsPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:wsUsername[/i]')
		# if config.cse_registrar_security_wsBearerToken and config.cse_registrar_security_wsUsername:
		# 	raise ConfigurationError(r'Configuration Error: Only one of [i]\[cse.registrar.security]:wsBearerToken[/i] or [i]\[cse.registrar.security]:wsUsername[/i] can be set')
		
		# if config.cse_registrar_security_selfHttpUsername and not config.cse_registrar_security_selfHttpPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfHttpPassword[/i]')
		# if not config.cse_registrar_security_selfHttpUsername and config.cse_registrar_security_selfHttpPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfHttpUsername[/i]')
		# if config.cse_registrar_security_selfWsUsername and not config.cse_registrar_security_selfWsPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfWsPassword[/i]')
		# if not config.cse_registrar_security_selfWsUsername and config.cse_registrar_security_selfWsPassword:
		# 	raise ConfigurationError(r'Configuration Error: Missing configuration [i]\[cse.registrar.security]:selfWsUsername[/i]')
		
		# # Validate SP Registrars
		# if config.cse_sp_registrars and config.cse_type != CSEType.IN:
		# 	raise ConfigurationError(r'Configuration Error: SP Registrars are only supported for IN CSEs')