#
#	CSEConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" CSE configurations"""

from __future__ import annotations
from typing import Optional

import configparser
from ...etc.Types import CSEType, ContentSerializationType
from ...etc.Constants import RuntimeConstants as RC
from ...etc.IDUtils import isValidCSI
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration



class CSEConfiguration(ModuleConfiguration):
	""" CSE configurations
	"""

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		""" Read the configuration from the configuration file.
		
			Args:
				parser: The configuration parser
				config: The configuration instance
		"""

		#	CSE

		config.cse_asyncSubscriptionNotifications = parser.getboolean('cse', 'asyncSubscriptionNotifications', fallback = True)
		config.cse_checkExpirationsInterval = parser.getint('cse', 'checkExpirationsInterval', fallback = 60)		# Seconds
		config.cse_cseID = parser.get('cse', 'cseID', fallback = '/id-in')
		config.cse_defaultSerialization = parser.get('cse', 'defaultSerialization', fallback = 'json')
		config.cse_enableRemoteCSE = parser.getboolean('cse', 'enableRemoteCSE', fallback = True)
		config.cse_enableResourceExpiration = parser.getboolean('cse', 'enableResourceExpiration', fallback = True)
		config.cse_enableSubscriptionVerificationRequests = parser.getboolean('cse', 'enableSubscriptionVerificationRequests', fallback = True)
		config.cse_flexBlockingPreference = parser.get('cse', 'flexBlockingPreference', fallback = 'blocking')
		config.cse_maxExpirationDelta = parser.getint('cse', 'maxExpirationDelta', fallback = 60*60*24*365*5)	# 5 years, in seconds
		config.cse_originator = parser.get('cse', 'originator', fallback = 'CAdmin')
		config.cse_poa = parser.getlist('cse', 'poa', fallback = ['http://127.0.0.1:8080'])	 # type: ignore [attr-defined]
		config.cse_releaseVersion = parser.get('cse', 'releaseVersion', fallback = '4')
		config.cse_requestExpirationDelta = parser.getfloat('cse', 'requestExpirationDelta', fallback = 10.0)	# 10 seconds
		config.cse_resourcesPath = parser.get('cse', 'resourcesPath', fallback = './init')
		config.cse_resourceID = parser.get('cse', 'resourceID', fallback = 'id-in')
		config.cse_resourceName = parser.get('cse', 'resourceName', fallback = 'cse-in')
		config.cse_sendToFromInResponses = parser.getboolean('cse', 'sendToFromInResponses', fallback = True)
		config.cse_sortDiscoveredResources = parser.getboolean('cse', 'sortDiscoveredResources', fallback = True)
		config.cse_supportedReleaseVersions = parser.getlist('cse', 'supportedReleaseVersions', fallback = ['2a', '3', '4', '5']) # type: ignore [attr-defined]
		config.cse_serviceProviderID = parser.get('cse', 'serviceProviderID', fallback = 'acme.example.com')
		config.cse_type = parser.get('cse', 'type', fallback = 'IN')		# IN, MN, ASN
		config.cse_idLength = parser.getint('cse', 'idLength', fallback = 10)

		#	CSE Operation : Jobs

		config.cse_operation_jobs_balanceLatency = parser.getint('cse.operation.jobs', 'jobBalanceLatency', fallback = 1000)
		config.cse_operation_jobs_balanceReduceFactor = parser.getfloat('cse.operation.jobs', 'jobBalanceReduceFactor', fallback = 2.0)
		config.cse_operation_jobs_balanceTarget = parser.getfloat('cse.operation.jobs', 'jobBalanceTarget', fallback = 3.0)

		#	CSE Operation : Requests

		config.cse_operation_requests_enable = parser.getboolean('cse.operation.requests', 'enable', fallback = False)
		config.cse_operation_requests_size = parser.getint('cse.operation.requests', 'size', fallback = 1000)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		""" Validate the configuration.
		
			Args:
				config: The configuration object
				initial: If True, this is the initial validation

			Raises:
				ConfigurationError if the configuration is invalid
		"""

		# override configuration with command line arguments
		if Configuration._args_initDirectory is not None:
			Configuration.cse_resourcesPath = Configuration._args_initDirectory
		if Configuration._args_remoteCSEEnabled is not None:
			Configuration.cse_enableRemoteCSE = Configuration._args_remoteCSEEnabled
		if Configuration._args_statisticsEnabled is not None:
			Configuration.cse_statistics_enable = Configuration._args_statisticsEnabled

		# CSE type
		if isinstance(config.cse_type, str):
			config.cse_type = config.cse_type.lower()
			match config.cse_type:
				case 'asn':
					config.cse_type = CSEType.ASN
				case 'mn':
					config.cse_type = CSEType.MN
				case 'in':
					config.cse_type = CSEType.IN
				case _:
					raise ConfigurationError(fr'Configuration Error: Unsupported \[cse]:type: {RC.cseType}')

		# CSE Serialization
		if isinstance(config.cse_defaultSerialization, str):
			config.cse_defaultSerialization = ContentSerializationType.getType(config.cse_defaultSerialization)
			if config.cse_defaultSerialization == ContentSerializationType.UNKNOWN:
				raise ConfigurationError(fr'Configuration Error: Unsupported \[cse]:defaultSerialization: {config.cse_defaultSerialization}')
			
		# Operation
		if config.cse_operation_jobs_balanceTarget <= 0.0:
			raise ConfigurationError(fr'Configuration Error: [i]\[cse.operation.jobs]:balanceTarget[/i] must be > 0.0')
		if config.cse_operation_jobs_balanceLatency < 0:
			raise ConfigurationError(fr'Configuration Error: [i]\[cse.operation.jobs]:balanceLatency[/i] must be >= 0')
		if config.cse_operation_jobs_balanceReduceFactor < 1.0:
			raise ConfigurationError(fr'Configuration Error: [i]\[cse.operation.jobs]:balanceReduceFactor[/i] must be >= 1.0')

		# check the csi format and value
		if not isValidCSI(config.cse_cseID):
			raise ConfigurationError(fr'Configuration Error: Wrong format for [i]\[cse]:cseID[/i]: {config.cse_cseID}')
		if config.cse_cseID[1:] == config.cse_resourceName:
			raise ConfigurationError(fr'Configuration Error: [i]\[cse]:cseID[/i] must be different from [i]\[cse]:resourceName[/i]')

		# Check flexBlocking value
		config.cse_flexBlockingPreference = config.cse_flexBlockingPreference.lower()
		if config.cse_flexBlockingPreference not in ['blocking', 'nonblocking']:
			raise ConfigurationError(r'Configuration Error: [i]\[cse]:flexBlockingPreference[/i] must be "blocking" or "nonblocking"')

		# Check release versions
		if len(config.cse_supportedReleaseVersions) == 0:
			raise ConfigurationError(r'Configuration Error: [i]\[cse]:supportedReleaseVersions[/i] must not be empty')
		if len(config.cse_releaseVersion) == 0:
			raise ConfigurationError(r'Configuration Error: [i]\[cse]:releaseVersion[/i] must not be empty')
		if config.cse_releaseVersion not in config.cse_supportedReleaseVersions:
			raise ConfigurationError(fr'Configuration Error: [i]\[cse]:releaseVersion[/i]: {config.cse_releaseVersion} not in [i]\[cse].supportedReleaseVersions[/i]: {config.cse_supportedReleaseVersions}')

		# Check various intervals
		if config.cse_checkExpirationsInterval <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[cse]:checkExpirationsInterval[/i] must be > 0')
		if config.cse_maxExpirationDelta <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[cse]:maxExpirationDelta[/i] must be > 0')


		# Check ID Length
		if config.cse_idLength < 1:
			raise ConfigurationError(r'Configuration Error: [i]\[cse]:idLength[/i] must be > 0')

