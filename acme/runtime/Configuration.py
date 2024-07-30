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
from typing import Any, Dict, Tuple, Optional, cast, Set

import configparser, argparse, os, os.path, pathlib, importlib
from inspect import getmembers
from rich.console import Console


from ..etc.Constants import Constants as C
from ..etc.Types import CSEType, ContentSerializationType, LogLevel, TreeMode
from ..helpers.NetworkTools import getIPAddress
from ..helpers.NetworkTools import isValidPort, isValidateIpAddress, isValidateHostname
from ..runtime import Onboarding


# TODO: proper use of the baseDirectory configuration for other values

#
#	Deprecated secttions
#

# Add deprecated sections here. Format: set of (oldSection, newSection)
_deprecatedSections:Set[Tuple[str, str]] = None
"""	Deprecated sections. Mapping from old section name to new section name."""

# The following modules have their own configuration sections and are
# responsible for reading and validating their own configuration
_configModules = ( 
	'acme.databases.PostgreSQLBinding',
	'acme.databases.TinyDBBinding',
	'acme.protocols.HttpServer',
	'acme.protocols.MQTTClient',
	'acme.protocols.WebSocketServer',
	'acme.resources.ACP',
	'acme.resources.ACTR',
	'acme.resources.CNT',
	'acme.resources.LCP',
	'acme.resources.REQ',
	'acme.resources.SUB',
	'acme.resources.TS',
	'acme.resources.TSB',
	'acme.runtime.CSE',
	'acme.runtime.TextUI',	# must get its config before the Console !
	'acme.runtime.Console',
	'acme.runtime.Logging',	# Must get its config after the Console !
	'acme.runtime.ScriptManager',
	'acme.runtime.Statistics',
	'acme.runtime.Storage',
	'acme.services.AnnouncementManager',
	'acme.services.GroupManager',
	'acme.services.RemoteCSEManager',
	'acme.services.RegistrationManager',
	'acme.services.SecurityManager',
)


class Configuration(object):
	"""	The static class Configuration holds all the configuration values of the CSE. It is initialized only once by calling the static
		method init(). Access to configuration valus is done by calling Configuration.get(<key>) or by
		accessing an attribute with the same name as the configuration key (with all "." replaced by "_").

		Example:
			::

				print(Configuration.get('http.port'))
				print(Configuration.http_port)
		
			
	"""
	console_confirmQuit:bool
	console_headless:bool
	console_hideResources:list[str]
	console_refreshInterval:float
	console_theme:str
	console_treeIncludeVirtualResource:bool
	console_treeMode:str|TreeMode

	cse_asyncSubscriptionNotifications:bool
	cse_checkExpirationsInterval:int
	cse_cseID:str
	cse_defaultSerialization:str|ContentSerializationType
	cse_enableRemoteCSE:bool
	cse_enableResourceExpiration:bool
	cse_enableSubscriptionVerificationRequests:bool
	cse_flexBlockingPreference:str
	cse_maxExpirationDelta:int
	cse_originator:str
	cse_poa:list[str]
	cse_releaseVersion:str
	cse_requestExpirationDelta:float
	cse_resourcesPath:str
	cse_resourceID:str
	cse_resourceName:str
	cse_sendToFromInResponses:bool
	cse_sortDiscoveredResources:bool
	cse_supportedReleaseVersions:list[str]
	cse_serviceProviderID:str
	cse_type:str|CSEType

	cse_announcements_allowAnnouncementsToHostingCSE:bool
	cse_announcements_checkInterval:int
	cse_announcements_delayAfterRegistration:float

	cse_operation_jobs_balanceLatency:int
	cse_operation_jobs_balanceReduceFactor:float
	cse_operation_jobs_balanceTarget:float

	cse_operation_requests_enable:bool
	cse_operation_requests_size:int

	cse_registrar_address:str
	cse_registrar_checkInterval:int
	cse_registrar_cseID:str
	cse_registrar_excludeCSRAttributes:list[str]
	cse_registrar_resourceName:str
	cse_registrar_root:str
	cse_registrar_serialization:str|ContentSerializationType

	cse_registration_allowedAEOriginators:list[str]
	cse_registration_allowedCSROriginators:list[str]
	cse_registration_checkLiveliness:bool

	cse_security_enableACPChecks:bool
	cse_security_fullAccessAdmin:bool

	database_type:str
	database_resetOnStartup:bool
	database_backupPath:str

	database_tinydb_path:str
	database_tinydb_cacheSize:int
	database_tinydb_writeDelay:int

	database_postgresql_host:str
	database_postgresql_port:int
	database_postgresql_role:str
	database_postgresql_password:str
	database_postgresql_database:str
	database_postgresql_schema:str

	http_address:str
	http_allowPatchForDelete:bool
	http_enableStructureEndpoint:bool
	http_enableUpperTesterEndpoint:bool
	http_listenIF:str
	http_port:int
	http_root:str
	http_timeout:float

	http_cors_enable:bool
	http_cors_resources:list[str]

	http_security_caCertificateFile:str
	http_security_caPrivateKeyFile:str
	http_security_tlsVersion:str
	http_security_useTLS:bool
	http_security_verifyCertificate:bool
	http_security_enableBasicAuth:bool
	http_security_enableTokenAuth:bool
	http_security_basicAuthFile:str
	http_security_tokenAuthFile:str

	http_wsgi_enable:bool
	http_wsgi_connectionLimit:int
	http_wsgi_threadPoolSize:int

	logging_count:int
	logging_enableBindingsLogging:bool
	logging_enableFileLogging:bool
	logging_enableScreenLogging:bool
	logging_filter:list
	logging_level:str|LogLevel
	logging_maxLogMessageLength:int
	logging_path:str
	logging_queueSize:int
	logging_size:int
	logging_stackTraceOnError:bool
	logging_enableUTCTimezone:bool

	mqtt_address:str
	mqtt_enable:bool
	mqtt_keepalive:int
	mqtt_listenIF:str
	mqtt_port:int
	mqtt_timeout:float
	mqtt_topicPrefix:str

	mqtt_security_allowedCredentialIDs:list[str]
	mqtt_security_caCertificateFile:str
	mqtt_security_password:str
	mqtt_security_username:str
	mqtt_security_useTLS:bool
	mqtt_security_verifyCertificate:bool

	resource_acp_selfPermission:int

	resource_actr_ecpContinuous:int
	resource_actr_ecpPeriodic:int

	resource_cnt_enableLimits:bool
	resource_cnt_mni:int
	resource_cnt_mbs:int

	resource_grp_resultExpirationTime:int

	resource_lcp_mni:int
	resource_lcp_mbs:int

	resource_req_et:int

	resource_sub_batchNotifyDuration:int

	resource_ts_enableLimits:bool
	resource_ts_mbs:int
	resource_ts_mdn:int
	resource_ts_mni:int

	resource_tsb_bcni:str
	resource_tsb_bcnt:float

	scripting_fileMonitoringInterval:float
	scripting_maxRuntime:float
	scripting_scriptDirectories:list[str]
	scripting_verbose:bool

	cse_statistics_enable:bool
	cse_statistics_writeInterval:int

	textui_refreshInterval:float
	textui_startWithTUI:bool
	textui_theme:str
	textui_maxRequestSize:int
	textui_notificationTimeout:float

	webui_root:str

	websocket_enable:bool
	websocket_address:str
	websocket_listenIF:str
	websocket_loglevel:int|str
	websocket_port:int
	websocket_timeout:float

	websocket_security_caCertificateFile:str
	websocket_security_caPrivateKeyFile:str
	websocket_security_tlsVersion:str
	websocket_security_useTLS:bool
	websocket_security_verifyCertificate:bool

	moduleDirectory:pathlib.Path = None
	""" The base directory of the ACME module. """
	baseDirectory:pathlib.Path = None
	""" The base directory of the ACME module. """
	initDirectory:pathlib.Path = None
	""" The init directory of the ACME module. """
	configfile:str = None
	""" The configuration file. """


	_configuration: Dict[str, Any] = {}
	""" The configuration values as a dictionary. """
	_configurationDocs: Dict[str, str] = {}
	""" The configuration values documentation as a dictionary. """

	_defaultConfigFilePath:pathlib.Path = None
	""" The default init file. """

	_defaultConfigFile:str = None
	""" The default configuration file. """

	_args_configfile:str = None
	""" The configuration file passed as argument. This overrides the respective value in the configuration file. """
	_args_loglevel:str = None
	""" The log level passed as argument. This overrides the respective value in the configuration file. """
	_args_DBReset:bool = None
	""" The reset DB flag passed as argument. This overrides the respective value in the configuration file. """
	_args_DBStorageMode:str = None
	""" The DB storage mode passed as argument. This overrides the respective value in the configuration file. """
	_args_DBDataDirectory:str = None
	""" The DB data directory passed as argument. This overrides the respective value in the configuration file. """
	_args_headless:bool = None
	""" The headless flag passed as argument. This overrides the respective value in the configuration file. """
	_args_httpAddress:str = None
	""" The http address passed as argument. This overrides the respective value in the configuration file. """
	_args_httpPort:int = None
	""" The http port passed as argument. This overrides the respective value in the configuration file. """
	_args_initDirectory:str = None
	""" The import directory passed as argument. This overrides the respective value in the configuration file. """
	_args_lightScheme:str = None
	""" The light scheme flag passed as argument. This overrides the respective value in the configuration file. """
	_args_listenIF:str = None
	""" The network interface passed as argument. This overrides the respective value in the configuration file. """
	_args_mqttEnabled:bool = None
	""" The mqtt enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_args_wsEnabled:bool = None
	""" The WebSocket enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_args_remoteCSEEnabled:bool = None
	""" The remote CSE enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_args_runAsHttps:bool = None
	""" The https flag passed as argument. This overrides the respective value in the configuration file. """
	_args_runAsHttpWsgi:bool = None
	""" The http WSGI flag passed as argument. This overrides the respective value in the configuration file. """
	_args_baseDirectory:str = None
	""" The runtime data directory passed as argument. This overrides the default (the CWD). """
	_args_statisticsEnabled:bool = None
	""" The statistics enabled flag passed as argument. This overrides the respective value in the configuration file. """
	_args_textUI:bool = None
	""" The text UI flag passed as argument. This overrides the respective value in the configuration file. """			


	# Internal print function that takes the headless setting into account
	@staticmethod
	def _print(msg:str) -> None:
		"""	Print a message to the console. If the CSE is running in headless mode, then the message is not printed.
		
			Args:
				msg: The message to print.	
		"""
		if not Configuration._args_headless:
			Console().print(msg)	# Print error message to console


	@staticmethod
	def init(args:Optional[argparse.Namespace] = None) -> bool:
		"""	Initialize and read the configuration. This method must be called before accessing any configuration value.

			Args:
				args: Optional arguments. If not given, then the command line arguments are used.

			Returns:
				True on success, False otherwise.
		"""

		# resolve the args and set them as attributes
		Configuration._args_configfile			= args.configfile if args and 'configfile' in args and args.configfile else C.defaultUserConfigFile
		Configuration._args_baseDirectory		= args.rtDirectory if args and 'rtDirectory' in args else None	# baseDirectory
		Configuration._args_loglevel			= args.loglevel if args and 'loglevel' in args else None
		Configuration._args_DBReset				= args.dbreset if args and 'dbreset' in args else False
		Configuration._args_DBStorageMode		= args.dbstoragemode if args and 'dbstoragemode' in args else None
		Configuration._args_DBDataDirectory		= args.dbdirectory if args and 'dbdirectory' in args else None
		Configuration._args_headless			= args.headless if args and 'headless' in args else False
		Configuration._args_httpAddress			= args.httpaddress if args and 'httpaddress' in args else None
		Configuration._args_httpPort			= args.httpport if args and 'httpport' in args else None
		Configuration._args_initDirectory		= args.initdirectory if args and 'initdirectory' in args else None
		Configuration._args_lightScheme			= args.lightScheme if args and 'lightScheme' in args else None
		Configuration._args_listenIF			= args.listenif if args and 'listenif' in args else None
		Configuration._args_mqttEnabled			= args.mqttenabled if args and 'mqttenabled' in args else None
		Configuration._args_remoteCSEEnabled	= args.remotecseenabled if args and 'remotecseenabled' in args else None
		Configuration._args_runAsHttps			= args.https if args and 'https' in args else None
		Configuration._args_runAsHttpWsgi		= args.httpWsgi if args and 'httpWsgi' in args else None
		Configuration._args_statisticsEnabled	= args.statisticsenabled if args and 'statisticsenabled' in args else None
		Configuration._args_textUI				= args.textui if args and 'textui' in args else None
		Configuration._args_wsEnabled			= args.wsenabled if args and 'wsenabled' in args else None

		# The path to the ACME module directory
		Configuration.moduleDirectory = pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent
		
		# Test that the config filename is just a filename without a path. If it is then throw an error
		if os.path.dirname(Configuration._args_configfile):
			Configuration._print(f'[red]Configuration file must be a filename without a path: {Configuration._args_configfile}')
			return False

		# Find out the path to the init directory
		Configuration.initDirectory = Configuration.moduleDirectory / 'init'
		if Configuration._args_initDirectory:	# Use the init directory if given as argument
			Configuration.initDirectory = pathlib.Path(Configuration._args_initDirectory)

		# Get the path to the runtime data directory
		Configuration.baseDirectory = pathlib.Path(os.getcwd())
		if Configuration._args_baseDirectory:	# Use the runtime data directory if given as argument
			Configuration.baseDirectory = pathlib.Path(Configuration._args_baseDirectory)

		# Check and re-set the configuration file's path if the runtime data directory is given AND
		# the configuration file is not given as argument
		if Configuration._args_baseDirectory and not args.configfile:
			Configuration._args_configfile = f'{Configuration._args_baseDirectory}/{C.defaultUserConfigFile}'

		# Adapt configuration file path to the runtime data directory
		Configuration._args_configfile = f'{Configuration.baseDirectory}{os.sep}{os.path.basename(Configuration._args_configfile)}'

		# Create user config file if doesn't exist
		if not os.path.exists(Configuration._args_configfile):
			try:
				if Configuration._args_headless:
					Console().print(f'[red]Configuration file: {Configuration._args_configfile} is missing and cannot be created in headless mode.\n')
					return False
				result, _configFile, _baseDirectory = Onboarding.buildUserConfigFile(Configuration._args_configfile)
				if not result:
					return False
				Configuration._args_configfile = str(pathlib.Path(_configFile))
				Configuration.baseDirectory = pathlib.Path(_baseDirectory)
			except Exception as e:
				Console().print(e)
				raise e
		Configuration.configfile = Configuration._args_configfile

		# Set the default ini file and check if it exists and is readable
		Configuration._defaultConfigFilePath = Configuration.initDirectory / C.defaultConfigFile
		Configuration._defaultConfigFile = str(Configuration._defaultConfigFilePath)
		if not os.access(Configuration._defaultConfigFile, os.R_OK):
			Configuration._print(f'[red]Default configuration file missing or not readable: {Configuration._defaultConfigFile}')
			return False



		# Read and parse the configuration file
		config = configparser.ConfigParser(	interpolation = configparser.ExtendedInterpolation(),
											# Convert csv to list, ignore empty elements
											converters = {'list': lambda x: [i.strip() for i in x.split(',') if i]}
										  )
	
		# Construct the default values that are used for interpolation
		_defaults = {	'basic.config': {	
							'baseDirectory' 		: Configuration.baseDirectory,			# points to the currenr working directory
							'moduleDirectory' 		: Configuration.moduleDirectory,		# points to the acme module's directory
							'initDirectory' 		: Configuration.initDirectory,			# points to the acme/init directory		
							'hostIPAddress'			: getIPAddress(),						# provide the IP address of the host

							'registrarCseHost'		: '127.0.0.1',							# The IP address of the registrar CSE
							'registrarCsePort'		: 8080,									# The TCP port of the registrar CSE
							'registrarCseID'		: 'id-in',								# The CSE-ID of the registrar CSE
							'registrarCseName'		: 'cse-in',								# The resource name of the registrar CSE's CSEBase
						}
					}
		# Add environment variables to the defaults
		_defaults.update({ 'DEFAULT': {k: v.replace('$', '$$') for k,v in os.environ.items()} })

		# Set the defaults
		config.read_dict(_defaults)
		

		try:
			if len(config.read( [Configuration._defaultConfigFile, Configuration.configfile])) == 0 and Configuration._args_configfile != C.defaultUserConfigFile:		# Allow 
				Configuration._print(f'[red]Configuration file missing or not readable: {Configuration._args_configfile}')
				return False
		except configparser.Error as e:
			Configuration._print('[red]Error in configuration file')
			Configuration._print(str(e))
			return False
	
		
		#	Look for deprecated and renamed sections and print an error message
		if _deprecatedSections:
			for o, n in _deprecatedSections:
				if config.has_section(o):
					Configuration._print(fr'[red]Found old section name in configuration file. Please rename "\[{o}]" to "\[{n}]".')
					return False


		#	Retrieve configuration values
		try:
			Configuration._configuration = {

				# TODO Move these sections later to the respective modules
				# TODO Same with th evalidation
				#	CoAP Client

				'coap.enable'							: config.getboolean('coap', 'enable', 								fallback = False),
				'coap.listenIF' 						: config.get('coap', 'listenIF',									fallback = '0.0.0.0'),
				'coap.port' 							: config.getint('coap', 'port', 									fallback = None),	# Default will be determined later (s.b.)

				#	CoAP Client Security

				'coap.security.certificateFile'			: config.get('coap.security', 'certificateFile', 					fallback = None),
				'coap.security.privateKeyFile'			: config.get('coap.security', 'privateKeyFile', 					fallback = None),
				'coap.security.dtlsVersion'				: config.get('coap.security', 'dtlsVersion', 						fallback = 'auto'),
				'coap.security.useDTLS'					: config.getboolean('coap.security', 'useDTLS', 					fallback = False),
				'coap.security.verifyCertificate'		: config.getboolean('coap.security', 'verifyCertificate',			fallback = False),

			}

			# Call the configuration handlerfor each module
			for m in _configModules:
				importlib.import_module(m).readConfiguration(config, Configuration)
		
		except configparser.InterpolationMissingOptionError as e:
			Configuration._print(f'[red]Error in configuration file: {Configuration.configfile}\n{str(e)}')
			Configuration._print('\n[red]Please provide the option in the section [bold](basic.config)[/bold] in the configuration file or set an environment variable with that name.\n')
			return False

		except Exception as e:	# about when findings errors in configuration
			Configuration._print(f'[red]Error in configuration file: {Configuration.configfile}\n{str(e)}')
			return False

		# Validate the configuration for each module
		for m in _configModules:
			try:
				importlib.import_module(m).validateConfiguration(Configuration, True)
			except ConfigurationError as e:
				Configuration._print(f'[red]{str(e)}')
				return False

		# Validate the general configuration
		# TODO remove this later
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

		# Everything is fine
		return True, None


	@staticmethod
	def print() -> str:
		"""	Prints the current configuration to the console.

			Returns:
				A string with the current configuration.
		"""	
		result = 'Configuration:\n'		# Magic string used e.g. in tests, don't remove
		for (k, v) in Configuration.all().items():
			result += f'  {k} = {v}\n'
		return result


	@staticmethod
	def all() -> Dict[str, Any]:
		"""	Returns the complete configuration as a dictionary.

			Returns:
				A dictionary with the complete configuration.
		"""
		def isprop(v:Any) -> bool:
			return not callable(v)
		
		attributeNames = [ k for k,v in getmembers(Configuration, isprop) if not k.startswith('_') ]
		return { k.replace('_', '.'): getattr(Configuration, k) for k in attributeNames }


	@staticmethod
	def get(key: str) -> Any:
		"""	Retrieve a configuration value or None if no configuration could be found for a key.
			The key is case-insensitive and dots are replaced by underscores.

			Example:
				The following example retrieves the value of the configuration key 'http.port':

				::

					print(Configuration.get('http.port'))

			Args:
				key:	The configuration key to retrieve.

			Returns:
				The configuration value or None if no configuration could be found for a key.
		"""
		if Configuration.has(key):
			return cast(Any, getattr(Configuration, key.replace('.', '_')))
		return None
	

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



	# TODO change to exception
	@staticmethod
	def update(key:str, value:Any) -> Optional[str]:
		""" Update a configuration value and inform other components via an event.

			Args:
				key:	The configuration key to update.
				value:	The new value for the configuration key.

			Returns:
				None if no error occurs, or a string with an error message, what has gone wrong while validating
		"""
		if not Configuration.has(key):
			return f'Unknown key: {key}'
		if value is not None:	# ignore invalid values
			original = Configuration.get(key)
			setattr(Configuration, key.replace('.', '_'), value)

			# TODO This worked before when there was only one validation function.
			# Now that we have multiple validation functions, we need to call them all, or
			# we need to store the proper validation function in the configuration for each key.
			# if not (r := Configuration.validate())[0]:
			# 	Configuration._configuration[key] = original
			# 	return r[1].replace(r'\[', '[')	# unescape "\[" in error messages

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
		return hasattr(Configuration, key.replace('.', '_'))
		

class ConfigurationError(Exception):
    pass
