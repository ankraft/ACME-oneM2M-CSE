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
			registrar.INCSEcseID = parser.get(section, 'INCSEcseID', fallback = None)
			registrar.originator = parser.get(section, 'originator', fallback = None)
			

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

		# Registrar CSE Security
		if parser.has_section('cse.registrar.security'):
			# parseRegistrarSecurity('cse.registrar.security', registrar)
			parseRegistrarSecurity('cse.registrar.security', registrar)

		config.cse_registrars[RC.cseSpid] = registrar

		# Get the SP (Mcc') configurations
		spMapping:dict[str, str] = {}
		for section in parser.sections():
			if section.startswith('cse.sp.registrar.'):
				if not section.endswith('.security'):
					registrar = CSERegistrar()
					spName = section[len('cse.sp.registrar.'):]  # Extract the SP name from the section
					if spName == RC.cseSpid:
						raise ConfigurationError(r'Configuration Error: The registrar within the same Service Provider domain must be configured in the [cse.registrar] section.')
					parseRegistrar(section, registrar)
					spMapping[spName] = registrar.spID 					# Map the SP name to its spID
					config.cse_registrars[registrar.spID] = registrar	# Store the registrar in the configuration under its spID

				else: 
					spName = section[len('cse.sp.registrar.'):-len('.security')]
					if spName not in spMapping:
						raise ConfigurationError(fr'Configuration Error: No SP Registrar configuration found for security section: {spName} -> {section}')
					spName = spMapping[spName]  # Use the mapped SP name if available
					registrar = config.cse_registrars.get(spName, None)
					if not registrar:
						raise ConfigurationError(fr'Configuration Error: No SP Registrar configuration found for security section: {spName} -> {section}')
					parseRegistrarSecurity(f'cse.sp.registrar.{spName}.security', registrar)
				

	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		# Validate CSE Type and remove default registrar if not IN
		for spName, registrar in config.cse_registrars.copy().items():

			# First finish the registrar initialization. This can only be done after all the other configurations have been read
			config.cse_registrars[spName].postInit()

			# Set the correct originator
			if registrar.originator is None:
				# If the originator is not set, use the own Service Provider ID as the originator
				registrar.originator = RC.cseCsi
				if registrar.spID is not None and registrar.spID != RC.cseSpid:
					# If the Service Provider ID is set and is not the own Service Provider ID, expand the
					# originator to include the Service Provider ID and CSE ID
					registrar.originator = f'//{RC.cseSpid}{RC.cseCsi}'

			# If the registrar has no name, use the own spID as the key
			# This seems to be a bit of a hack, but at the time when the own registrar is added, the RC.cseSpid is not yet set
			if spName is None:
				# Find the first non-None cseID or spID to use as the key
				registrar.spID = registrar.spID or RC.cseSpid	# Use the own Service Provider ID if not set
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

			if spName != RC.cseSpid:
				if not registrar.spID:
					raise ConfigurationError(fr'Configuration Error: Missing \[cse.sp.registrar.{spName}]:spID for registrar: {spName}')
				if not registrar.cseID:
					raise ConfigurationError(fr'Configuration Error: Missing \[cse.sp.registrar.{spName}]:cseID for registrar: {spName}')
				if not registrar.resourceName:
					raise ConfigurationError(fr'Configuration Error: Missing \[cse.sp.registrar.{spName}]:resourceName for registrar: {spName}')
				if not registrar.address:
					raise ConfigurationError(fr'Configuration Error: Missing \[cse.sp.registrar.{spName}]:address for registrar: {spName}')

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
			