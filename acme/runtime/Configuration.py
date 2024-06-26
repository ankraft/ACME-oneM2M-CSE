#
#	Configuration.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing CSE configurations
#
""" This module implements the configuration of the CSE. It reads the configuration file, performs checks,
	and provides access to the configuration values. """


from __future__ import annotations
from typing import Any, Dict, Tuple, Optional, cast

import configparser, argparse, os, os.path, pathlib
from copy import copy
import isodate
from rich.console import Console


from ..etc.Constants import Constants as C
from ..etc.Types import CSEType, ContentSerializationType,Permission
from ..helpers.NetworkTools import getIPAddress
from ..etc.Utils import normalizeURL
from ..helpers.NetworkTools import isValidPort, isValidateIpAddress, isValidateHostname
from ..runtime import Onboarding

# TODO: proper use of the baseDirectory configuration for other values

documentationLinks = {
	'cse': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#general',
	'cse.announcements': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#announcements',
	'cse.operation.jobs': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#operation_jobs',
	'cse.operation.requests': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#operation_requests',
	'cse.registrar': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#registrar',
	'cse.registration': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#cse_registration',
	'cse.security': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#security',
	'cse.statistics': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#statistics',
	'console': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#console',
	'database': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#database',
	'http': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#server_http',
	'http.cors': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#http_cors',
	'http.security': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#security_http',
	'logging': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#logging',
	'mqtt': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#client_mqtt',
	'mqtt.security': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#security_mqtt',
	'resource.acp.pv': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_acp',
	'resource.acp.pvs': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_acp',
	'resource.actr.ecp': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_actr',
	'resource.cnt': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_cnt',
	'resource.req': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_req',
	'resource.sub': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_sub',
	'resource.ts': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_ts',
	'resource.tsb': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#resource_tsb',
	'scripting': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#scripting',
	'server.http': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#id_mappings',	# TODO remove later
	'textui': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#textui',
	'webui': 'https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/docs/Configuration.md#webui',
}
"""	Documentation links for configuration settings. These are used in the console and text UIto show the documentation for a configuration setting. """

#
#	Deprecated secttions
#

_deprecatedSections = (
	('server.http', 'http'),
	('server.http.security', 'http.security'),
	('server.http.cors', 'http.cors'), 
	('client.mqtt', 'mqtt'),
	('client.mqtt.security', 'mqtt.security'),
	('cse.resource.acp', 'resource.acp'),
	('cse.resource.actr', 'resource.actr'),
	('cse.resource.cnt', 'resource.cnt'),
	('cse.resource.ts', 'resource.ts'),
	('cse.resource.tsb', 'resource.tsb'),
	('cse.resource.req', 'resource.req'),
	('cse.resource.sub', 'resource.sub'),
	('cse.webui', 'webui'),
	('cse.console', 'console'),
	('cse.textui', 'textui'),
	('cse.scripting', 'scripting')
)
"""	Deprecated sections. Mapping from old section name to new section name."""



class Configuration(object):
	"""	The static class Configuration holds all the configuration values of the CSE. It is initialized only once by calling the static
		method init(). Access to configuration valus is done by calling Configuration.get(<key>).
	"""
	_configuration: Dict[str, Any] = {}
	""" The configuration values as a dictionary. """
	_configurationDocs: Dict[str, str] = {}
	""" The configuration values documentation as a dictionary. """

	_moduleDirectory:pathlib.Path = None
	""" The base directory of the ACME module. """
	_initDirectory:pathlib.Path = None
	""" The init directory of the ACME module. """
	_defaultConfigFilePath:pathlib.Path = None
	""" The default init file. """

	_baseDirectory:pathlib.Path = None
	""" The base directory of the ACME module. """
	_defaultConfigFile:str = None
	""" The default configuration file. """

	_argsConfigfile:str = None
	""" The configuration file passed as argument. This overrides the respective value in the configuration file. """
	_argsLoglevel:str = None
	""" The log level passed as argument. This overrides the respective value in the configuration file. """
	_argsDBReset:bool = None
	""" The reset DB flag passed as argument. This overrides the respective value in the configuration file. """
	_argsDBStorageMode:str = None
	""" The DB storage mode passed as argument. This overrides the respective value in the configuration file. """
	_argsDBDataDirectory:str = None
	""" The DB data directory passed as argument. This overrides the respective value in the configuration file. """
	_argsHeadless:bool = None
	""" The headless flag passed as argument. This overrides the respective value in the configuration file. """
	_argsHttpAddress:str = None
	""" The http address passed as argument. This overrides the respective value in the configuration file. """
	_argsHttpPort:int = None
	""" The http port passed as argument. This overrides the respective value in the configuration file. """
	_argsInitDirectory:str = None
	""" The import directory passed as argument. This overrides the respective value in the configuration file. """
	_argsLightScheme:bool = None
	""" The light scheme flag passed as argument. This overrides the respective value in the configuration file. """
	_argsListenIF:str = None
	""" The network interface passed as argument. This overrides the respective value in the configuration file. """
	_argsMqttEnabled:bool = None
	""" The mqtt enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_argsWsEnabled:bool = None
	""" The WebSocket enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_argsRemoteCSEEnabled:bool = None
	""" The remote CSE enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_argsRunAsHttps:bool = None
	""" The https flag passed as argument. This overrides the respective value in the configuration file. """
	_argsRunAsHttpWsgi:bool = None
	""" The http WSGI flag passed as argument. This overrides the respective value in the configuration file. """
	_argsBaseDirectory:str = None
	""" The runtime data directory passed as argument. This overrides the default (the CWD). """
	_argsStatisticsEnabled:bool = None
	""" The statistics enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_argsTextUI:bool = None
	""" The text UI flag passed as argument. This overrides the respective value in the configuration file. """


	# Internal print function that takes the headless setting into account
	@staticmethod
	def _print(msg:str) -> None:
		"""	Print a message to the console. If the CSE is running in headless mode, then the message is not printed.
		
			Args:
				msg: The message to print.	
		"""
		if not Configuration._argsHeadless:
			Console().print(msg)	# Print error message to console


	@staticmethod
	def init(args:Optional[argparse.Namespace] = None) -> bool:
		"""	Initialize and read the configuration. This method must be called before accessing any configuration value.

			Args:
				args: Optional arguments. If not given, then the command line arguments are used.

			Returns:
				True on success, False otherwise.
		"""

		# resolve the args, if any
		Configuration._argsConfigfile			= args.configfile if args and 'configfile' in args and args.configfile else C.defaultUserConfigFile
		Configuration._argsBaseDirectory		= args.rtDirectory if args and 'rtDirectory' in args else None	# baseDirectory
		Configuration._argsLoglevel				= args.loglevel if args and 'loglevel' in args else None
		Configuration._argsDBReset				= args.dbreset if args and 'dbreset' in args else False
		Configuration._argsDBStorageMode		= args.dbstoragemode if args and 'dbstoragemode' in args else None
		Configuration._argsDBDataDirectory		= args.dbdirectory if args and 'dbdirectory' in args else None
		Configuration._argsHeadless				= args.headless if args and 'headless' in args else False
		Configuration._argsHttpAddress			= args.httpaddress if args and 'httpaddress' in args else None
		Configuration._argsHttpPort				= args.httpport if args and 'httpport' in args else None
		Configuration._argsInitDirectory		= args.initdirectory if args and 'initdirectory' in args else None
		Configuration._argsLightScheme			= args.isLightScheme if args and 'isLightScheme' in args else None
		Configuration._argsListenIF				= args.listenif if args and 'listenif' in args else None
		Configuration._argsMqttEnabled			= args.mqttenabled if args and 'mqttenabled' in args else None
		Configuration._argsRemoteCSEEnabled		= args.remotecseenabled if args and 'remotecseenabled' in args else None
		Configuration._argsRunAsHttps			= args.https if args and 'https' in args else None
		Configuration._argsRunAsHttpWsgi		= args.httpWsgi if args and 'httpWsgi' in args else None
		Configuration._argsStatisticsEnabled	= args.statisticsenabled if args and 'statisticsenabled' in args else None
		Configuration._argsTextUI				= args.textui if args and 'textui' in args else None
		Configuration._argsWsEnabled			= args.wsenabled if args and 'wsenabled' in args else None

		# The path to the ACME module directory
		Configuration._moduleDirectory = pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent
		
		# Test that the config filename is just a filename without a path. If it is then throw an error
		if os.path.dirname(Configuration._argsConfigfile):
			Configuration._print(f'[red]Configuration file must be a filename without a path: {Configuration._argsConfigfile}')
			return False

		# The path to the init directory
		Configuration._initDirectory = Configuration._moduleDirectory / 'init'
		if Configuration._argsInitDirectory:	# Use the init directory if given as argument
			Configuration._initDirectory = pathlib.Path(Configuration._argsInitDirectory)

		# The path to the runtime data directory
		Configuration._baseDirectory = pathlib.Path(os.getcwd())
		if Configuration._argsBaseDirectory:	# Use the runtime data directory if given as argument
			Configuration._baseDirectory = pathlib.Path(Configuration._argsBaseDirectory)

		# Check and re-set the configuration file's path if the runtime data directory is given AND
		# the configuration file is not given as argument
		if Configuration._argsBaseDirectory and not args.configfile:
			Configuration._argsConfigfile = f'{Configuration._argsBaseDirectory}/{C.defaultUserConfigFile}'

		# Adapt configuration file path to the runtime data directory
		Configuration._argsConfigfile = f'{Configuration._baseDirectory}{os.sep}{os.path.basename(Configuration._argsConfigfile)}'

		# Create user config file if doesn't exist
		if not os.path.exists(Configuration._argsConfigfile):
			try:
				if Configuration._argsHeadless:
					Console().print(f'[red]Configuration file: {Configuration._argsConfigfile} is missing and cannot be created in headless mode.\n')
					return False
				result, _configFile, _baseDirectory = Onboarding.buildUserConfigFile(Configuration._argsConfigfile)
				if not result:
					return False
				Configuration._argsConfigfile = str(pathlib.Path(_configFile))
				Configuration._baseDirectory = pathlib.Path(_baseDirectory)
			except Exception as e:
				Console().print(e)
				raise e

		# Set the default ini file and check if it exists and is readable
		Configuration._defaultConfigFilePath = Configuration._initDirectory / C.defaultConfigFile
		Configuration._defaultConfigFile = str(Configuration._defaultConfigFilePath)
		if not os.access(Configuration._defaultConfigFile, os.R_OK):
			Configuration._print(f'[red]Default configuration file missing or not readable: {Configuration._defaultConfigFile}')
			return False


		# Read and parse the configuration file
		config = configparser.ConfigParser(	interpolation = configparser.ExtendedInterpolation(),
											# Convert csv to list, ignore empty elements
											converters = {'list': lambda x: [i.strip() for i in x.split(',') if i]}
										  )
	
		# Construct the default values
		_defaults = {	'basic.config': {	
							'baseDirectory' 		: Configuration._baseDirectory,			# points to the currenr working directory
							'moduleDirectory' 		: Configuration._moduleDirectory,		# points to the acme module's directory
							'initDirectory' 		: Configuration._initDirectory,			# points to the acme/init directory		
							'hostIPAddress'			: getIPAddress(),						# provide the IP address of the host

							'registrarCseHost'		: '127.0.0.1',							# The IP address of the registrar CSE
							'registrarCsePort'		: 8080,									# The TCP port of the registrar CSE
							'registrarCseID'		: 'id-in',								# The CSE-ID of the registrar CSE
							'registrarCseName'		: 'cse-in',								# The resource name of the registrar CSE's CSEBase
						}
					}
		# Add environment variables to the defaults
		_defaults.update({ 'DEFAULT': {k: v for k,v in os.environ.items()} })

		# Set the defaults
		config.read_dict(_defaults)

		try:
			if len(config.read( [Configuration._defaultConfigFile, Configuration._argsConfigfile])) == 0 and Configuration._argsConfigfile != C.defaultUserConfigFile:		# Allow 
				Configuration._print(f'[red]Configuration file missing or not readable: {Configuration._argsConfigfile}')
				return False
		except configparser.Error as e:
			Configuration._print('[red]Error in configuration file')
			Configuration._print(str(e))
			return False
		
	
		#
		#	Look for deprecated and renamed sections
		#

		for o, n in _deprecatedSections:
			if config.has_section(o):
				Configuration._print(fr'[red]Found old section name in configuration file. Please rename "\[{o}]" to "\[{n}]".')
				return False

		#
		#	Retrieve configuration values
		#

		try:
			Configuration._configuration = {
				'configfile'							: Configuration._argsConfigfile,
				'baseDirectory'							: Configuration._baseDirectory,
				'moduleDirectory'						: Configuration._moduleDirectory,	# points to the acme package directory
				'initDirectory'							: Configuration._initDirectory,			# points to the acme / init directory


				#
				#	CSE
				#

				'cse.asyncSubscriptionNotifications'			: config.getboolean('cse', 'asyncSubscriptionNotifications',		fallback = True),
				'cse.checkExpirationsInterval'					: config.getint('cse', 'checkExpirationsInterval',					fallback = 60),		# Seconds
				'cse.cseID'										: config.get('cse', 'cseID',										fallback = '/id-in'),
				'cse.defaultSerialization'						: config.get('cse', 'defaultSerialization',							fallback = 'json'),
				'cse.enableRemoteCSE'							: config.getboolean('cse', 'enableRemoteCSE', 						fallback = True),
				'cse.enableResourceExpiration'					: config.getboolean('cse', 'enableResourceExpiration', 				fallback = True),
				'cse.enableSubscriptionVerificationRequests'	: config.getboolean('cse', 'enableSubscriptionVerificationRequests',fallback = True),
				'cse.flexBlockingPreference'					: config.get('cse', 'flexBlockingPreference',						fallback = 'blocking'),
				'cse.maxExpirationDelta'						: config.getint('cse', 'maxExpirationDelta',						fallback = 60*60*24*365*5),	# 5 years, in seconds
				'cse.originator'								: config.get('cse', 'originator',									fallback = 'CAdmin'),
				'cse.poa'										: config.getlist('cse', 'poa',										fallback = ['http://127.0.0.1:8080']),	 # type: ignore [attr-defined]
				'cse.releaseVersion'							: config.get('cse', 'releaseVersion',								fallback = '4'),
				'cse.requestExpirationDelta'					: config.getfloat('cse', 'requestExpirationDelta',					fallback = 10.0),	# 10 seconds
				'cse.resourcesPath'								: config.get('cse', 'resourcesPath', 								fallback = './init'),
				'cse.resourceID'								: config.get('cse', 'resourceID',									fallback = 'id-in'),
				'cse.resourceName'								: config.get('cse', 'resourceName',									fallback = 'cse-in'),
				'cse.sendToFromInResponses'						: config.getboolean('cse', 'sendToFromInResponses',					fallback = True),
				'cse.sortDiscoveredResources'					: config.getboolean('cse', 'sortDiscoveredResources',				fallback = True),
				'cse.supportedReleaseVersions'					: config.getlist('cse', 'supportedReleaseVersions',					fallback = ['2a', '3', '4', '5']), # type: ignore [attr-defined]
				'cse.serviceProviderID'							: config.get('cse', 'serviceProviderID',							fallback = 'acme.example.com'),
				'cse.type'										: config.get('cse', 'type',											fallback = 'IN'),		# IN, MN, ASN

				#
				#	Announcements
				#

				'cse.announcements.allowAnnouncementsToHostingCSE'	: config.getboolean('cse.announcements', 'allowAnnouncementsToHostingCSE',	fallback = True),
				'cse.announcements.checkInterval'					: config.getint('cse.announcements', 'checkInterval',						fallback = 10),
				'cse.announcements.delayAfterRegistration'			: config.getfloat('cse.announcements', 'delayAfterRegistration',			fallback = 3.0),


				#
				#	CSE Operation : Jobs
				#

				'cse.operation.jobs.balanceLatency'		: config.getint('cse.operation.jobs', 'jobBalanceLatency', 			fallback = 1000),
				'cse.operation.jobs.balanceReduceFactor': config.getfloat('cse.operation.jobs', 'jobBalanceReduceFactor', 	fallback = 2.0),
				'cse.operation.jobs.balanceTarget'		: config.getfloat('cse.operation.jobs', 'jobBalanceTarget',			fallback = 3.0),

				#
				#	CSE Operation : Requests
				#

				'cse.operation.requests.enable'			: config.getboolean('cse.operation.requests', 'enable',				fallback = False),
				'cse.operation.requests.size'			: config.getint('cse.operation.requests', 'size', 					fallback = 1000),

				#
				#	Registrar CSE
				#

				'cse.registrar.address'					: config.get('cse.registrar', 'address', 							fallback = None),
				'cse.registrar.checkInterval'			: config.getint('cse.registrar', 'checkInterval', 					fallback = 30),		# Seconds
				'cse.registrar.cseID'					: config.get('cse.registrar', 'cseID', 								fallback = None),
				'cse.registrar.excludeCSRAttributes'	: config.getlist('cse.registrar', 'excludeCSRAttributes',			fallback = []),		# type: ignore [attr-defined]
				'cse.registrar.resourceName'			: config.get('cse.registrar', 'resourceName', 						fallback = None),
				'cse.registrar.root'					: config.get('cse.registrar', 'root', 								fallback = ''),
				'cse.registrar.serialization'			: config.get('cse.registrar', 'serialization',						fallback = 'json'),

				#
				#	Registrations
				#

				'cse.registration.allowedAEOriginators'		: config.getlist('cse.registration', 'allowedAEOriginators',	fallback = ['C*','S*']),		# type: ignore [attr-defined]
				'cse.registration.allowedCSROriginators'	: config.getlist('cse.registration', 'allowedCSROriginators',	fallback = []),				# type: ignore [attr-defined]
				'cse.registration.checkLiveliness'			: config.getboolean('cse.registration', 'checkLiveliness',		fallback = True),


				#
				#	CSE Security
				#

				'cse.security.enableACPChecks'			: config.getboolean('cse.security', 'enableACPChecks',			 	fallback = True),
				'cse.security.fullAccessAdmin'			: config.getboolean('cse.security', 'fullAccessAdmin',			 	fallback = True),

				#
				#	Statistics
				#

				'cse.statistics.enable'					: config.getboolean('cse.statistics', 'enable', 					fallback = True),
				'cse.statistics.writeInterval'			: config.getint('cse.statistics', 'writeInterval',					fallback = 60),		# Seconds


				#
				#	CoAP Client
				#

				'coap.enable'							: config.getboolean('coap', 'enable', 								fallback = False),
				'coap.listenIF' 						: config.get('coap', 'listenIF',									fallback = '0.0.0.0'),
				'coap.port' 							: config.getint('coap', 'port', 									fallback = None),	# Default will be determined later (s.b.)

				#
				#	CoAP Client Security
				#

				'coap.security.certificateFile'			: config.get('coap.security', 'certificateFile', 					fallback = None),
				'coap.security.privateKeyFile'			: config.get('coap.security', 'privateKeyFile', 					fallback = None),
				'coap.security.dtlsVersion'				: config.get('coap.security', 'dtlsVersion', 						fallback = 'auto'),
				'coap.security.useDTLS'					: config.getboolean('coap.security', 'useDTLS', 					fallback = False),
				'coap.security.verifyCertificate'		: config.getboolean('coap.security', 'verifyCertificate',			fallback = False),


				#
				#	Console
				#

				'console.confirmQuit'					: config.getboolean('console', 'confirmQuit', 						fallback = False),
				'console.headless'						: config.getboolean('console', 'headless', 							fallback = False),
				'console.hideResources'					: config.getlist('console', 'hideResources', 						fallback = []),		# type: ignore[attr-defined]
				'console.refreshInterval'				: config.getfloat('console', 'refreshInterval', 					fallback = 2.0),
				'console.theme'							: config.get('console', 'theme', 									fallback = 'dark'),
				'console.treeIncludeVirtualResources'	: config.getboolean('console', 'treeIncludeVirtualResources',		fallback = False),
				'console.treeMode'						: config.get('console', 'treeMode', 								fallback = 'normal'),

				#
				#	Database
				#

				'database.type'							: config.get('database', 'type',			 						fallback = 'tinydb'),
				'database.resetOnStartup' 				: config.getboolean('database', 'resetOnStartup',					fallback = False),
				'database.backupPath'					: config.get('database', 'backupPath',								fallback = './data/backup'),

				#
				#	Database PostgreSQL
				#

				'database.postgresql.host'					: config.get('database.postgresql', 'host',								fallback = 'localhost'),
				'database.postgresql.port'					: config.getint('database.postgresql', 'port', 							fallback = 5432),
				'database.postgresql.role'					: config.get('database.postgresql', 'role', 							fallback = None),	# CSE-ID
				'database.postgresql.password'				: config.get('database.postgresql', 'password', 						fallback = None),
				'database.postgresql.database'				: config.get('database.postgresql', 'database', 						fallback = 'acmecse'),
				'database.postgresql.schema'				: config.get('database.postgresql', 'schema', 							fallback = 'acmecse'),

				#
				#	Database TinyDB
				#

				'database.tinydb.path'					: config.get('database.tinydb', 'path',								fallback = './data'),
				'database.tinydb.cacheSize'				: config.getint('database.tinydb', 'cacheSize', 					fallback = 0),		# Default: no caching
				'database.tinydb.writeDelay'			: config.getint('database.tinydb', 'writeDelay', 					fallback = 1),		# Default: 1 second

				#
				#	HTTP Server
				#

				'http.address'							: config.get('http', 'address', 									fallback = 'http://127.0.0.1:8080'),
				'http.allowPatchForDelete'				: config.getboolean('http', 'allowPatchForDelete', 					fallback = False),
				'http.enableStructureEndpoint'			: config.getboolean('http', 'enableStructureEndpoint', 				fallback = False),
				'http.enableUpperTesterEndpoint'		: config.getboolean('http', 'enableUpperTesterEndpoint', 			fallback = False),
				'http.listenIF'							: config.get('http', 'listenIF', 									fallback = '0.0.0.0'),
				'http.port' 							: config.getint('http', 'port', 									fallback = 8080),
				'http.root'								: config.get('http', 'root', 										fallback = ''),
				'http.timeout' 							: config.getfloat('http', 'timeout',								fallback = 10.0),

				#
				#	HTTP Server CORS
				#

				'http.cors.enable'						: config.getboolean('http.cors', 'enable', 							fallback = False),
				'http.cors.resources'					: config.getlist('http.cors', 'resources', 							fallback = [ r'/*' ]),	# type: ignore [attr-defined]


				#
				#	HTTP Server Security
				#

				'http.security.caCertificateFile'		: config.get('http.security', 'caCertificateFile', 					fallback = None),
				'http.security.caPrivateKeyFile'		: config.get('http.security', 'caPrivateKeyFile', 					fallback = None),
				'http.security.tlsVersion'				: config.get('http.security', 'tlsVersion', 						fallback = 'auto'),
				'http.security.useTLS'					: config.getboolean('http.security', 'useTLS', 						fallback = False),
				'http.security.verifyCertificate'		: config.getboolean('http.security', 'verifyCertificate',			fallback = False),
				'http.security.enableBasicAuth'			: config.getboolean('http.security', 'enableBasicAuth',				fallback = False),
				'http.security.enableTokenAuth'			: config.getboolean('http.security', 'enableTokenAuth',				fallback = False),
				'http.security.basicAuthFile'			: config.get('http.security', 'basicAuthFile',						fallback = './certs/http_basic_auth.txt'),
				'http.security.tokenAuthFile'			: config.get('http.security', 'tokenAuthFile',						fallback = './certs/http_token_auth.txt'),


				#
				#	HTTP Server WSGI
				#

				'http.wsgi.enable'						: config.getboolean('http.wsgi', 'enable', 							fallback = False),
				'http.wsgi.connectionLimit'				: config.getint('http.wsgi', 'connectionLimit',						fallback = 100),
				'http.wsgi.threadPoolSize'				: config.getint('http.wsgi', 'threadPoolSize',						fallback = 100),


				#
				#	Logging
				#

				'logging.count'							: config.getint('logging', 'count', 								fallback = 10),		# Number of log files
				'logging.enableBindingsLogging'			: config.getboolean('logging', 'enableBindingsLogging',				fallback = False),
				'logging.enableFileLogging'				: config.getboolean('logging', 'enableFileLogging', 				fallback = False),
				'logging.enableScreenLogging'			: config.getboolean('logging', 'enableScreenLogging', 				fallback = True),
				'logging.filter'						: config.getlist('logging', 'filter',								fallback = []),		# type: ignore [attr-defined]
				'logging.level'							: config.get('logging', 'level', 									fallback = 'debug'),
				'logging.maxLogMessageLength'			: config.getint('logging', 'maxLogMessageLength',					fallback = 1000),	# Max length of a log message
				'logging.path'							: config.get('logging', 'path', 									fallback = './logs'),
				'logging.queueSize'						: config.getint('logging', 'queueSize', 							fallback = 5000),	# Size of the log queue
				'logging.size'							: config.getint('logging', 'size', 									fallback = 100000),
				'logging.stackTraceOnError'				: config.getboolean('logging', 'stackTraceOnError',					fallback = True),
				'logging.enableUTCTimezone'				: config.getboolean('logging', 'enableUTCTimezone',					fallback = False),



				#
				#	MQTT Client
				#

				'mqtt.address'							: config.get('mqtt', 'address', 									fallback = '127.0.0.1'),
				'mqtt.enable'							: config.getboolean('mqtt', 'enable', 								fallback = False),
				'mqtt.keepalive' 						: config.getint('mqtt', 'keepalive',								fallback = 60),
				'mqtt.listenIF' 						: config.get('mqtt', 'listenIF',									fallback = '0.0.0.0'),
				'mqtt.port' 							: config.getint('mqtt', 'port', 									fallback = None),	# Default will be determined later (s.b.)
				'mqtt.timeout' 							: config.getfloat('mqtt', 'timeout',								fallback = 10.0),
				'mqtt.topicPrefix' 						: config.get('mqtt', 'topicPrefix',									fallback = ''),

				#
				#	MQTT Client Security
				#

				'mqtt.security.allowedCredentialIDs'	: config.getlist('mqtt.security', 'allowedCredentialIDs', 			fallback = []),	# type: ignore [attr-defined]
				'mqtt.security.caCertificateFile'		: config.get('mqtt.security', 'caCertificateFile',					fallback = None),
				'mqtt.security.password' 				: config.get('mqtt.security', 'password',							fallback = ''),
				'mqtt.security.username'				: config.get('mqtt.security', 'username',							fallback = ''),
				'mqtt.security.useTLS'					: config.getboolean('mqtt.security', 'useTLS', 						fallback = False),
				'mqtt.security.verifyCertificate'		: config.getboolean('mqtt.security', 'verifyCertificate', 			fallback = False),


				#
				#	Defaults for Access Control Policies
				#

				'resource.acp.selfPermission'			: config.getint('resource.acp', 'selfPermission', 					fallback = Permission.DISCOVERY+Permission.NOTIFY+Permission.CREATE+Permission.RETRIEVE),


				#
				#	Defaults for Actions
				#

				'resource.actr.ecpContinuous'			: config.getint('resource.actr', 'ecpContinuous', 					fallback = 1000),
				'resource.actr.ecpPeriodic'				: config.getint('resource.actr', 'ecpPeriodic', 					fallback = 10000),


				#
				#	Defaults for Container Resources
				#

				'resource.cnt.enableLimits'				: config.getboolean('resource.cnt', 'enableLimits', 				fallback = False),
				'resource.cnt.mni'						: config.getint('resource.cnt', 'mni', 								fallback = 10),
				'resource.cnt.mbs'						: config.getint('resource.cnt', 'mbs', 								fallback = 10000),


				#
				#	Defaults for Group Resources
				#

				'resource.grp.resultExpirationTime'		: config.getint('resource.grp', 'resultExpirationTime', 			fallback = 0),


				#
				#	Defaults for LocationPolicy Resources
				#

				'resource.lcp.mni'						: config.getint('resource.lcp', 'mni', 								fallback = 10),
				'resource.lcp.mbs'						: config.getint('resource.lcp', 'mbs', 								fallback = 10000),


				#
				#	Defaults for Request Resources
				#

				'resource.req.et'						: config.getint('resource.req', 'expirationTime', 					fallback = 60),


				#
				#	Defaults for Subscription Resources
				#

				'resource.sub.batchNotifyDuration'		: config.getint('resource.sub', 'batchNotifyDuration', 				fallback = 60),	# seconds


				#
				#	Defaults for timeSeries Resources
				#

				'resource.ts.enableLimits'				: config.getboolean('resource.ts', 'enableLimits',					fallback = False),
				'resource.ts.mbs'						: config.getint('resource.ts', 'mbs', 								fallback = 10000),
				'resource.ts.mdn'						: config.getint('resource.ts', 'mdn', 								fallback = 10),
				'resource.ts.mni'						: config.getint('resource.ts', 'mni', 								fallback = 10),


				#
				#	Defaults for TimeSyncBeacon Resources
				#

				'resource.tsb.bcni'						: config.get('resource.tsb', 'bcni', 								fallback = 'PT1H'),	# duration
				'resource.tsb.bcnt'						: config.getfloat('resource.tsb', 'bcnt', 							fallback = 60.0),	# seconds

				#
				#	Scripting
				#

				'scripting.fileMonitoringInterval'		: config.getfloat('scripting', 'fileMonitoringInterval',			fallback = 2.0),
				'scripting.scriptDirectories'			: config.getlist('scripting', 'scriptDirectories',					fallback = []),	# type: ignore[attr-defined]
				'scripting.verbose'						: config.getboolean('scripting', 'verbose', 						fallback = False),
				'scripting.maxRuntime'					: config.getfloat('scripting', 'maxRuntime', 						fallback = 60.0),

				#
				#	Text UI
				#

				'textui.refreshInterval'				: config.getfloat('textui', 'refreshInterval', 						fallback = 2.0),
				'textui.startWithTUI'					: config.getboolean('textui', 'startWithTUI',						fallback = False),
				'textui.theme'							: config.get('textui', 'theme', 									fallback = 'dark'),
				'textui.maxRequestSize'					: config.getint('textui', 'maxRequestSize',							fallback = 10000),

				#
				#	WebSocket Server
				#

				'websocket.enable'						: config.getboolean('websocket', 'enable', 							fallback = False),
				'websocket.listenIF'					: config.get('websocket', 'listenIF', 								fallback = '0.0.0.0'),
				'websocket.port' 						: config.getint('websocket', 'port', 								fallback = 8180),
				'websocket.address'						: config.get('websocket', 'address', 								fallback = 'ws://127.0.0.1:8180'),
				'websocket.loglevel'					: config.get('websocket', 'loglevel', 								fallback = 'debug'),
				'websocket.timeout' 					: config.getfloat('websocket', 'timeout',							fallback = 10.0),

				#
				#	WebSocket Server Security
				#

				'websocket.security.caCertificateFile'	: config.get('websocket.security', 'caCertificateFile', 			fallback = None),
				'websocket.security.caPrivateKeyFile'	: config.get('websocket.security', 'caPrivateKeyFile', 				fallback = None),
				'websocket.security.tlsVersion'			: config.get('websocket.security', 'tlsVersion', 					fallback ='auto'),
				'websocket.security.useTLS'				: config.getboolean('websocket.security', 'useTLS', 				fallback = False),
				'websocket.security.verifyCertificate'	: config.getboolean('websocket.security', 'verifyCertificate',		fallback = False),

				#
				#	Web UI
				#

				'webui.root'							: config.get('webui', 'root', 										fallback = '/webui'),

			}
		
		except configparser.InterpolationMissingOptionError as e:
			Configuration._print(f'[red]Error in configuration file: {Configuration._argsConfigfile}\n{str(e)}')
			Configuration._print('\n[red]Please provide the option in the section [bold](basic.config)[/bold] in the configuration file or set an environment variable with that name.\n')
			return False

		except Exception as e:	# about when findings errors in configuration
			Configuration._print(f'[red]Error in configuration file: {Configuration._argsConfigfile}\n{str(e)}')
			return False

		if not (v := Configuration.validate(True))[0]:
			Configuration._print(f'[red]{v[1]}')
		return v[0]


	@staticmethod
	def validate(initial:Optional[bool] = False) -> Tuple[bool, str]:
		""" Validates the configuration and returns a tuple (bool, str) with the result and an error message if applicable. 

			Args:
				initial:	True if this is the initial validation during startup, False otherwise. Default: False

			Returns:
				A tuple (bool, str) with the result and an error message if applicable.
		"""
		from .Logging import LogLevel

		# Some clean-ups and overrides

		def _get(key:str) -> Any:
			""" Helper function to retrieve a configuration value. If the value is not found, None is returned.
			
				Args:
					key:	The configuration key to retrieve.
			"""
			return Configuration.get(key)
		

		def _put(key:str, value:Any) -> None:
			""" Helper function to set a configuration value.
			
				Args:
					key:	The configuration key to set.
			"""
			Configuration._configuration[key] = value
		

		def _getLoglevel(logLevel:str) -> Optional[int]:
			logLevel = logLevel.lower()
			logLevel = (Configuration._argsLoglevel or logLevel) 	# command line args override config
			match logLevel:
				case 'off':
					return LogLevel.OFF
				case 'info':
					return LogLevel.INFO
				case 'warn' | 'warning':
					return LogLevel.WARNING
				case 'error':
					return LogLevel.ERROR
				case 'debug':
					return LogLevel.DEBUG
				case _:
					return None
				

		from ..etc.ACMEUtils import isValidCSI	# cannot import at the top because of circel import

		# CSE type
		if isinstance(cseType := _get('cse.type'), str):
			cseType = cseType.lower()
			match cseType:
				case 'asn':
					_put('cse.type', CSEType.ASN)
				case 'mn':
					_put('cse.type', CSEType.MN)
				case 'in':
					_put('cse.type', CSEType.IN)
				case _:
					return False, fr'Configuration Error: Unsupported \[cse]:type: {cseType}'

		# CSE Serialization
		if isinstance(ct := _get('cse.defaultSerialization'), str):
			_put('cse.defaultSerialization', ContentSerializationType.getType(ct))
			if _get('cse.defaultSerialization') == ContentSerializationType.UNKNOWN:
				return False, fr'Configuration Error: Unsupported \[cse]:defaultSerialization: {ct}'
		
		# Registrar Serialization
		if isinstance(ct := _get('cse.registrar.serialization'), str):
			_put('cse.registrar.serialization', ContentSerializationType.getType(ct))
			if _get('cse.registrar.serialization') == ContentSerializationType.UNKNOWN:
				return False, fr'Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}'

		# Loglevel and various overrides from command line
		logLevel = _get('logging.level')
		logLevel = cast(LogLevel, logLevel).name if isinstance(logLevel, LogLevel) else logLevel
		if isinstance(logLevel, str):
			if (ll := _getLoglevel(logLevel)) is None:
				return False, fr'Configuration Error: Unsupported \[logging]:level: {logLevel}'
			_put('logging.level', ll)
		else:
			return False, fr'Configuration Error: Unsupported \[logging]:level: {logLevel}'
		# from ..services.Logging import LogLevel
		# if isinstance(logLevel := _get('logging.level'), str):	
		# 	logLevel = logLevel.lower()
		# 	logLevel = (Configuration._argsLoglevel or logLevel) 	# command line args override config

		# 	match logLevel:
		# 		case 'off':
		# 			_put('logging.level', LogLevel.OFF)
		# 		case 'info':
		# 			_put('logging.level', LogLevel.INFO)
		# 		case 'warn' | 'warning':
		# 			_put('logging.level', LogLevel.WARNING)
		# 		case 'error':
		# 			_put('logging.level', LogLevel.ERROR)
		# 		case 'debug':
		# 			_put('logging.level', LogLevel.DEBUG)
		# 		case _:
		# 			return False, f'Configuration Error: Unsupported \[logging]:level: {logLevel}'
				
		
		# Test for correct logging queue size
		if (queueSize := Configuration._configuration['logging.queueSize']) < 0:
			return False, fr'Configuration Error: \[logging]:queueSize must be 0 or greater'

		# Overwriting some configurations from command line
		if Configuration._argsDBReset is True:					_put('database.resetOnStartup', True)									# Override DB reset from command line
		if Configuration._argsDBDataDirectory is not None:		_put('database.path', Configuration._argsDBDataDirectory)				# Override DB data directory from command line
		if Configuration._argsDBStorageMode is not None:		_put('database.type', Configuration._argsDBStorageMode)					# Override DB storage mode from command line
		if Configuration._argsHeadless is True:					_put('console.headless', True)
		if Configuration._argsHttpAddress is not None:			_put('http.address', Configuration._argsHttpAddress)					# Override server http address
		if Configuration._argsHttpPort is not None:				_put('http.port', Configuration._argsHttpPort)							# Override server http port
		if Configuration._argsInitDirectory is not None:		_put('cse.resourcesPath', Configuration._argsInitDirectory)				# Override import directory from command line
		if Configuration._argsLightScheme is not None:			_put('console.theme', Configuration._argsLightScheme)					# Override console theme 
		if Configuration._argsLightScheme is not None:			_put('textui.theme', Configuration._argsLightScheme)					# Override textui theme
		if Configuration._argsListenIF is not None:				_put('http.listenIF', Configuration._argsListenIF)						# Override binding network interface
		if Configuration._argsMqttEnabled is not None:			_put('mqtt.enable', Configuration._argsMqttEnabled)						# Override mqtt enable
		if Configuration._argsRemoteCSEEnabled is not None:		_put('cse.enableRemoteCSE', Configuration._argsRemoteCSEEnabled)		# Override remote CSE enablement
		if Configuration._argsRunAsHttps is not None:			_put('http.security.useTLS', Configuration._argsRunAsHttps)				# Override useTLS
		if Configuration._argsRunAsHttpWsgi is not None:		_put('http.wsgi.enable', Configuration._argsRunAsHttpWsgi)				# Override use WSGI
		if Configuration._argsStatisticsEnabled is not None:	_put('cse.statistics.enable', Configuration._argsStatisticsEnabled)		# Override statistics enablement
		if Configuration._argsTextUI is not None:				_put('textui.startWithTUI', Configuration._argsTextUI)
		if Configuration._argsWsEnabled is not None:			_put('websocket.enable', Configuration._argsWsEnabled)					# Override websocket enable

		# Correct urls
		_put('cse.registrar.address', normalizeURL(Configuration._configuration['cse.registrar.address']))
		_put('http.address', normalizeURL(Configuration._configuration['http.address']))
		_put('http.root', normalizeURL(Configuration._configuration['http.root']))
		_put('websocket.address', normalizeURL(Configuration._configuration['websocket.address']))
		_put('cse.registrar.root', normalizeURL(Configuration._configuration['cse.registrar.root']))

		# Just in case: check the URL's (http, ws)
		if _get('http.security.useTLS'):
			if _get('http.address').startswith('http:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "http" to "https" in [i]\[http]:address[/i]')
				_put('http.address', _get('http.address').replace('http:', 'https:'))
			# registrar might still be accessible via another protocol
		else: 
			if _get('http.address').startswith('https:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "https" to "http" in [i]\[http]:address[/i]')
				_put('http.address', _get('http.address').replace('https:', 'http:'))
			# registrar might still be accessible via another protocol

		if _get('websocket.security.useTLS'):
			if _get('websocket.address').startswith('ws:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "ws" to "wss" in [i]\[websocket]:address[/i]')
				_put('websocket.address', 
		 _get('websocket.address').replace('ws:', 'wss:'))
			# registrar might still be accessible via another protocol
		else: 
			if _get('websocket.address').startswith('wss:'):
				Configuration._print(r'[orange3]Configuration Warning: Changing "wss" to "ws" in [i]\[websocket]:address[/i]')
				_put('websocket.address', _get('websocket.address').replace('wss:', 'ws:'))
			# registrar might still be accessible via another protocol


		# Operation
		if _get('cse.operation.jobs.balanceTarget') <= 0.0:
			return False, fr'Configuration Error: [i]\[cse.operation.jobs]:balanceTarget[/i] must be > 0.0'
		if _get('cse.operation.jobs.balanceLatency') < 0:
			return False, fr'Configuration Error: [i]\[cse.operation.jobs]:balanceLatency[/i] must be >= 0'
		if _get('cse.operation.jobs.balanceReduceFactor') < 1.0:
			return False, fr'Configuration Error: [i]\[cse.operation.jobs]:balanceReduceFactor[/i] must be >= 1.0'


		#
		#	Some sanity and validity checks
		#

		# HTTP server
		if not isValidPort(_get('http.port')):
			return False, fr'Configuration Error: Invalid port number for [i]\[http]:port[/i]: {_get("http.port")}'
		if not (isValidateHostname(_get('http.listenIF')) or isValidateIpAddress(_get('http.listenIF'))):
			return False, fr'Configuration Error: Invalid hostname or IP address for [i]\[http]:listenIF[/i]: {_get("http.listenIF")}'
		
		# HTTP TLS & certificates
		if not _get('http.security.useTLS'):	# clear certificates configuration if not in use
			_put('http.security.verifyCertificate', False)
			_put('http.security.tlsVersion', 'auto')
			_put('http.security.caCertificateFile', '')
			_put('http.security.caPrivateKeyFile', '')
		else:
			if not (val := _get('http.security.tlsVersion')).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				return False, fr'Configuration Error: Unknown value for [i]\[http.security]:tlsVersion[/i]: {val}'
			if not (val := _get('http.security.caCertificateFile')):
				return False, r'Configuration Error: [i]\[http.security]:caCertificateFile[/i] must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, fr'Configuration Error: [i]\[http.security]:caCertificateFile[/i] does not exists or is not accessible: {val}'
			if not (val := _get('http.security.caPrivateKeyFile')):
				return False, r'Configuration Error: [i]\[http.security]:caPrivateKeyFile[/i] must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, fr'Configuration Error: [i]\[http.security]:caPrivateKeyFile[/i] does not exists or is not accessible: {val}'
		

		# HTTP CORS
		if initial and _get('http.cors.enable') and not _get('http.security.useTLS'):
			Configuration._print(r'[orange3]Configuration Warning: [i]\[http.security].useTLS[/i] (https) should be enabled when [i]\[http.cors].enable[/i] is enabled.')


		# HTTP authentication
		if _get('http.security.enableBasicAuth') and not _get('http.security.basicAuthFile'):
			return False, r'Configuration Error: [i]\[http.security]:httpBasicAuthFile[/i] must be set when HTTP Basic Auth is enabled'
		if _get('http.security.enableTokenAuth') and not _get('http.security.tokenAuthFile'):
			return False, r'Configuration Error: [i]\[http.security]:httpTokenAuthFile[/i] must be set when HTTP Token Auth is enabled'
	

		# HTTP WSGI
		if _get('http.wsgi.enable') and _get('http.security.useTLS'):
			# WSGI and TLS cannot both be enabled
			return False, r'Configuration Error: [i]\[http.security].useTLS[/i] (https) cannot be enabled when [i]\[http.wsgi].enable[/i] is enabled (WSGI and TLS cannot both be enabled).'
		if _get('http.wsgi.threadPoolSize') < 1:
			return False, r'Configuration Error: [i]\[http.wsgi]:threadPoolSize[/i] must be > 0'
		if _get('http.wsgi.connectionLimit') < 1:
			return False, r'Configuration Error: [i]\[http.wsgi]:connectionLimit[/i] must be > 0'

		
		#
		#	MQTT client
		#
		if not _get('mqtt.port'):	# set the default port depending on whether to use TLS
			_put('mqtt.port', 8883) if _get('mqtt.security.useTLS') else 1883
		if not _get('mqtt.security.username') != (not _get('mqtt.security.password')):	# Hack: != -> either both are empty, or both are set
			return False, fr'Configuration Error: Username or password missing for [i]\[mqtt.security][/i]'
		# remove empty cid from the list
		_put('mqtt.security.allowedCredentialIDs', [ cid for cid in _get('mqtt.security.allowedCredentialIDs') if len(cid) ])


		#
		#	WebSocket server
		#
		if not isValidPort(_get('websocket.port')):
			return False, fr'Configuration Error: Invalid port number for [i]\[websocket]:port[/i]: {_get("websocket.port")}'	
		if not (isValidateHostname(_get('websocket.listenIF')) or isValidateIpAddress(_get('websocket.listenIF'))):
			return False, fr'Configuration Error: Invalid hostname or IP address for [i]\[websocket]:listenIF[/i]: {_get("websocket.listenIF")}'

		logLevel = _get('websocket.loglevel')
		logLevel = cast(LogLevel, logLevel).name if isinstance(logLevel, LogLevel) else logLevel
		if isinstance(logLevel, str):
			if (ll := _getLoglevel(logLevel)) is None:
				return False, fr'Configuration Error: Unsupported \[websocket]:loglevel: {logLevel}'
			_put('websocket.loglevel', ll)
		else:
			return False, fr'Configuration Error: Unsupported \[websocket]:loglevel: {logLevel}'

		# WebSocket TLS & certificates
		if not _get('websocket.security.useTLS'):	# clear certificates configuration if not in use
			_put('websocket.security.verifyCertificate', False)
			_put('websocket.security.tlsVersion', 'auto')
			_put('websocket.security.caCertificateFile', '')
			_put('websocket.security.caPrivateKeyFile', '')
		else:
			if not (val := _get('websocket.security.tlsVersion')).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				return False, fr'Configuration Error: Unknown value for [i]\[websocket.security]:tlsVersion[/i]: {val}'
			if not (val := _get('websocket.security.caCertificateFile')):
				return False, r'Configuration Error: [i]\[websocket.security]:caCertificateFile[/i] must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, fr'Configuration Error: [i]\[websocket.security]:caCertificateFile[/i] does not exists or is not accessible: {val}'
			if not (val := _get('websocket.security.caPrivateKeyFile')):
				return False, r'Configuration Error: [i]\[websocket.security]:caPrivateKeyFile[/i] must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, fr'Configuration Error: [i]\[websocket.security]:caPrivateKeyFile[/i] does not exists or is not accessible: {val}'

		# COAP TLS & certificates
		if not _get('coap.security.useDTLS'):	# clear certificates configuration if not in use
			_put('coap.security.verifyCertificate', False)
			_put('coap.security.tlsVersion', 'auto')
			_put('coap.security.caCertificateFile', '')
			_put('coap.security.caPrivateKeyFile', '')
		else:
			if not (val := _get('coap.security.dtlsVersion')).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				return False, fr'Configuration Error: Unknown value for [i]\[coap.security]:dtlsVersion[/i]: {val}'
			if not (val := _get('coap.security.certificateFile')):
				return False, r'Configuration Error: [i]\[coap.security]:certificateFile[/i] must be set when DTLS is enabled'
			if not os.path.exists(val):
				return False, fr'Configuration Error: [i]\[coap.security]:certificateFile[/i] does not exists or is not accessible: {val}'
			if not (val := _get('coap.security.privateKeyFile')):
				return False, r'Configuration Error: [i]\[coap.security]:privateKeyFile[/i] must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, fr'Configuration Error: [i]\[coap.security]:privateKeyFile[/i] does not exists or is not accessible: {val}'


		# check the csi format and value
		if not isValidCSI(val := _get('cse.cseID')):
			return False, fr'Configuration Error: Wrong format for [i]\[cse]:cseID[/i]: {val}'
		if _get('cse.cseID')[1:] == _get('cse.resourceName'):
			return False, fr'Configuration Error: [i]\[cse]:cseID[/i] must be different from [i]\[cse]:resourceName[/i]'

		if _get('cse.registrar.address') and _get('cse.registrar.cseID'):
			if not isValidCSI(val := _get('cse.registrar.cseID')):
				return False, fr'Configuration Error: Wrong format for [i]\[cse.registrar]:cseID[/i]: {val}'
			if len(_get('cse.registrar.cseID')) > 0 and len(_get('cse.registrar.resourceName')) == 0:
				return False, r'Configuration Error: Missing configuration [i]\[cse.registrar]:resourceName[/i]'

		# Check default subscription duration
		if _get('resource.sub.batchNotifyDuration') < 1:
			return False, r'Configuration Error: [i]\[resource.sub]:batchNotifyDuration[/i] must be > 0'

		# Check flexBlocking value
		_put('cse.flexBlockingPreference', _get('cse.flexBlockingPreference').lower())
		if _get('cse.flexBlockingPreference') not in ['blocking', 'nonblocking']:
			return False, r'Configuration Error: [i]\[cse]:flexBlockingPreference[/i] must be "blocking" or "nonblocking"'

		# Check release versions
		if len(srv := _get('cse.supportedReleaseVersions')) == 0:
			return False, r'Configuration Error: [i]\[cse]:supportedReleaseVersions[/i] must not be empty'
		if len(rvi := _get('cse.releaseVersion')) == 0:
			return False, r'Configuration Error: [i]\[cse]:releaseVersion[/i] must not be empty'
		if rvi not in srv:
			return False, fr'Configuration Error: [i]\[cse]:releaseVersion[/i]: {rvi} not in [i]\[cse].supportedReleaseVersions[/i]: {srv}'
		# if any([s for s in srv if str(rvi) < s]):
		#	return False, f'Configuration Error: \[cse]:releaseVersion: {rvi} less than highest value in \[cse].supportedReleaseVersions: {srv}. Either increase the [i]releaseVersion[/i] or reduce the set of [i]supportedReleaseVersions[/i].'

		# Check various intervals
		if _get('cse.checkExpirationsInterval') <= 0:
			return False, r'Configuration Error: [i]\[cse]:checkExpirationsInterval[/i] must be > 0'
		if _get('console.refreshInterval') <= 0.0:
			return False, r'Configuration Error: [i]\[console]:refreshInterval[/i] must be > 0.0'
		if _get('cse.maxExpirationDelta') <= 0:
			return False, r'Configuration Error: [i]\[cse]:maxExpirationDelta[/i] must be > 0'

		# Console settings
		from .Console import TreeMode
		if isinstance(tm := _get('console.treeMode'), str):
			if not (treeMode := TreeMode.to(tm)):
				return False, fr'Configuration Error: [i]\[console]:treeMode[/i] must be one of {TreeMode.names()}'
			_put('console.treeMode', treeMode)
		
		_put('console.theme', (theme := _get('console.theme').lower()))
		if theme not in [ 'dark', 'light' ]:
			return False, fr'Configuration Error: [i]\[console]:theme[/i] must be "light" or "dark"'

		if _get('console.headless'):
			_put('logging.enableScreenLogging', False)
			_put('textui.startWithTUI', False)


		# Script settings
		if _get('scripting.fileMonitoringInterval') < 0.0:
			return False, fr'Configuration Error: [i]\[scripting]:fileMonitoringInterval[/i] must be >= 0.0'
		if _get('scripting.maxRuntime') < 0.0:
			return False, fr'Configuration Error: [i]\[scripting]:maxRuntime[/i] must be >= 0.0'
		if (scriptDirs := _get('scripting.scriptDirectories')):
			lst = []
			for each in scriptDirs:
				if not each:
					continue
				if not os.path.isdir(each):
					return False, fr'Configuration Error: [i]\[scripting]:scriptDirectory[/i]: directory "{each}" does not exist, is not a directory or is not accessible'
				lst.append(each)
			_put('scripting.scriptDirectories', lst)
			

		# TimeSyncBeacon defaults
		bcni = _get('resource.tsb.bcni')
		try:
			isodate.parse_duration(bcni)
		except Exception as e:
			return False, fr'Configuration Error: [i]\[resource.tsb]:bcni[/i]: configuration value must be an ISO8601 duration'
		
		# Check group resource defaults
		if _get('resource.grp.resultExpirationTime') < 0:
			return False, fr'Configuration Error: [i]\[resource.grp]:resultExpirationTime[/i] must be >= 0'
		

		# Text UI settings
		if _get('textui.maxRequestSize') <= 0:
			return False, r'Configuration Error: [i]\[textui]:maxRequestSize[/i] must be > 0s'
		_put('textui.theme', (theme := _get('textui.theme').lower()))
		if theme not in [ 'dark', 'light' ]:
			return False, fr'Configuration Error: [i]\[textui]:theme[/i] must be "light" or "dark"'


		
		# Database settings
		_put('database.type', (dbType := _get('database.type').lower()))

		if dbType not in ['tinydb', 'postgresql', 'memory']:
			return False, fr'Configuration Error: [i]\[database]:type[/i] must be "tinydb", "postgresql", or "memory"'
		# Everything is fine
		return True, None


	@staticmethod
	def print() -> str:
		"""	Prints the current configuration to the console.

			Returns:
				A string with the current configuration.
		"""	
		result = 'Configuration:\n'		# Magic string used e.g. in tests, don't remove
		for (k,v) in Configuration._configuration.items():
			result += f'  {k} = {v}\n'
		return result


	@staticmethod
	def all() -> Dict[str, Any]:
		"""	Returns the complete configuration as a dictionary.

			Returns:
				A dictionary with the complete configuration.
		"""
		return Configuration._configuration


	@staticmethod
	def get(key: str) -> Any:
		"""	Retrieve a configuration value or None if no configuration could be found for a key.

			Args:
				key:	The configuration key to retrieve.

			Returns:
				The configuration value or None if no configuration could be found for a key.
		"""
		return Configuration._configuration.get(key)
	

	@staticmethod
	def addDoc(key: str, markdown:str) -> None:
		"""	Adds a documentation for a configuration key.

			Args:
				key:		The configuration key to add the documentation for.
				markdown:	The documentation in markdown format.
		"""
		if key:
			Configuration._configurationDocs[key] = markdown

	
	@staticmethod
	def getDoc(key:str) -> Optional[str]:
		"""	Retrieves the documentation for a configuration key.
		
			Args:
				key:	The configuration key to retrieve the documentation for.
				
			Returns:
				The documentation in markdown format or None if no documentation could be found for the key.
		"""
		return Configuration._configurationDocs.get(key)


	@staticmethod
	def update(key:str, value:Any) -> Optional[str]:
		""" Update a configuration value and inform other components via an event.

			Args:
				key:	The configuration key to update.
				value:	The new value for the configuration key.

			Returns:
				None if no error occurs, or a string with an error message, what has gone wrong while validating
		"""
		if key not in Configuration._configuration:
			return f'Unknown key: {key}'
		if value is not None:	# ignore invalid values
			original = Configuration._configuration[key]
			Configuration._configuration[key] = value
			if not (r := Configuration.validate())[0]:
				Configuration._configuration[key] = original
				return r[1].replace(r'\[', '[')	# unescape "\[" in error messages

			from . import CSE
			CSE.event.configUpdate(key, value)		# type:ignore [attr-defined]
		else:
			return f'Invalid value for key: {key}'
		return None


	@staticmethod
	def has(key:str) -> bool:
		"""	Check whether a configuration setting exsists.

			Args:
				key:	The configuration key to check.

			Returns:
				True if the configuration key exists, False otherwise.
		"""
		return key in Configuration._configuration

