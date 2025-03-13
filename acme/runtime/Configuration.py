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

import configparser, argparse, os, os.path, pathlib
from inspect import getmembers
from rich.console import Console


from ..etc.Constants import Constants as C
from ..etc.Types import CSEType, ContentSerializationType, LogLevel, TreeMode
from ..helpers.NetworkTools import getIPAddress




# TODO: proper use of the baseDirectory configuration for other values

#
#	Deprecated secttions
#

# Add deprecated sections here. Format: set of (oldSection, newSection)
_deprecatedSections:Set[Tuple[str, str]] = None
"""	Deprecated sections. Mapping from old section name to new section name."""

class Configuration(object):
	"""	The static class Configuration holds all the configuration values of the CSE. It is initialized only once by calling the static
		method init(). Access to configuration valus is done by calling Configuration.get(<key>) or by
		accessing an attribute with the same name as the configuration key (with all "." replaced by "_").

		Example:
			::

				print(Configuration.get('http.port'))
				print(Configuration.http_port)
		
			
	"""

	coap_enable:bool
	"""	Enable or disable the CoAP server. """

	coap_listenIF:str
	"""	The network interface to listen on for CoAP. """

	coap_port:int
	"""	The port to listen on for CoAP. """

	coap_address:str
	"""	The address to listen on for CoAP. """

	coap_timeout:float
	"""	The timeout for CoAP requests. """

	coap_clientConnectionCacheSize:int
	"""	The size of the client connection cache. """


	coap_security_caCertificateFile:str
	"""	The CA certificate file for CoAP. """

	coap_security_caPrivateKeyFile:str
	"""	The CA private key file for CoAP. """

	coap_security_dtlsVersion:str
	"""	The DTLS version for CoAP. """

	coap_security_useDTLS:bool
	"""	Enable or disable DTLS for CoAP. """

	coap_security_verifyCertificate:bool
	"""	Enable or disable certificate verification for CoAP. """


	console_confirmQuit:bool
	"""	Confirm quitting the console. """

	console_headless:bool
	"""	Run the CSE in headless mode. """

	console_hideResources:list[str]
	"""	Resources to hide in the console. """

	console_refreshInterval:float
	"""	The refresh interval for the console. """

	console_theme:str
	"""	The theme for the console. """

	console_treeIncludeVirtualResource:bool
	"""	Include virtual resources in the console tree. """

	console_treeMode:str|TreeMode
	"""	The tree mode for the console. """


	cse_asyncSubscriptionNotifications:bool
	"""	Enable or disable asynchronous subscription notifications. """

	cse_checkExpirationsInterval:int
	"""	The interval to check for resource expirations. """

	cse_cseID:str
	"""	The CSE-ID of the CSE. """

	cse_defaultSerialization:str|ContentSerializationType
	"""	The default serialization for the CSE. """

	cse_enableRemoteCSE:bool
	"""	Enable or disable remote CSEs. """

	cse_enableResourceExpiration:bool
	"""	Enable or disable resource expiration. """

	cse_enableSubscriptionVerificationRequests:bool
	"""	Enable or disable subscription verification requests. """

	cse_flexBlockingPreference:str
	"""	The flex blocking preference for the CSE. """

	cse_maxExpirationDelta:int
	"""	The maximum expiration delta for resources. """

	cse_originator:str
	"""	The originator for the CSE. """

	cse_poa:list[str]
	"""	The Points of Access for the CSE. """

	cse_releaseVersion:str
	"""	The release version of the CSE. """

	cse_requestExpirationDelta:float
	"""	The request expiration delta for the CSE. """

	cse_resourcesPath:str
	"""	The path to the resources. """

	cse_resourceID:str
	"""	The resource ID of the CSE. """

	cse_resourceName:str
	"""	The resource name of the CSE. """

	cse_sendToFromInResponses:bool
	"""	Send the To and From in responses. """

	cse_sortDiscoveredResources:bool
	"""	Sort discovered resources. """

	cse_supportedReleaseVersions:list[str]
	"""	The supported release versions of the CSE. """

	cse_serviceProviderID:str
	"""	The service provider ID of the CSE. """

	cse_type:str|CSEType
	"""	The type of the CSE. """

	cse_idLength:int
	"""	The length of the generated resource IDs. """

	cse_announcements_allowAnnouncementsToHostingCSE:bool
	"""	Allow announcements to the hosting CSE. """

	cse_announcements_delayAfterRegistration:float
	"""	The delay after registration for announcements. """


	cse_operation_jobs_balanceLatency:int
	"""	The latency for balancing jobs. """

	cse_operation_jobs_balanceReduceFactor:float
	"""	The reduce factor for balancing jobs. """

	cse_operation_jobs_balanceTarget:float
	"""	The target for balancing jobs. """


	cse_operation_requests_enable:bool
	"""	Enable or disable operation requests. """

	cse_operation_requests_size:int
	"""	The size of the operation requests. """


	cse_registrar_address:str
	"""	The address of the registrar. """

	cse_registrar_checkInterval:int
	"""	The interval to check the registrar. """

	cse_registrar_cseID:str
	"""	The CSE-ID of the registrar. """

	cse_registrar_excludeCSRAttributes:list[str]
	"""	Attributes to exclude from CSR. """

	cse_registrar_resourceName:str
	"""	The resource name of the registrar. """

	cse_registrar_root:str
	"""	The root of the registrar. """

	cse_registrar_serialization:str|ContentSerializationType
	"""	The serialization for the registrar. """

	cse_registrar_INCSEcseID:str
	"""	The CSE-ID of the IN-CSE on the top-level of the CSE deployment tree. """


	cse_registrar_security_httpUsername:str
	"""	The username for HTTP basic security when registering to a http server with basic auth. """

	cse_registrar_security_httpPassword:str
	"""	The password for HTTP basic security when registering to a http server with basic auth. """

	cse_registrar_security_httpBearerToken:str
	"""	The token for HTTP bearer token security when registering to a http server with bearer token auth. """

	cse_registrar_security_wsUsername:str
	"""	The username for HTTP basic security when registering to a WebSocket server with basic auth. """

	cse_registrar_security_wsPassword:str
	"""	The password for HTTP basic security when registering to a WebSocket server with basic auth. """

	cse_registrar_security_wsBearerToken:str
	"""	The token for HTTP bearer token security when registering to a WebSocket server with bearer token auth. """

	cse_registrar_security_selfHttpUsername:str
	"""	The username for HTTP basic security to be used by the registrar CSE when connecting via http to this CSE. """

	cse_registrar_security_selfHttpPassword:str
	"""	The password for HTTP basic security to be used by the registrar CSE when connecting via http to this CSE. """

	cse_registrar_security_selfWsUsername:str
	"""	The username for HTTP basic security to be used by the registrar CSE when connecting via WebSocket to this CSE. """

	cse_registrar_security_selfWsPassword:str
	"""	The password for HTTP basic security to be used by the registrar CSE when connecting via WebSocjet to this CSE. """


	cse_registration_allowedAEOriginators:list[str]
	"""	Allowed AE originators for registration. """

	cse_registration_allowedCSROriginators:list[str]
	"""	Allowed CSR originators for registration. """

	cse_registration_checkLiveliness:bool
	"""	Check liveliness for registration. """



	cse_security_secret:str
	"""	The main secret key for the CSE. """

	cse_security_enableACPChecks:bool
	"""	Enable or disable ACP checks. """

	cse_security_fullAccessAdmin:bool
	"""	Full access for admin. """


	database_type:str
	"""	The type of the database. """

	database_resetOnStartup:bool
	"""	Reset the database on startup. """

	database_backupPath:str
	"""	The path for the database backup. """


	database_tinydb_path:str
	"""	The path to the TinyDB database. """

	database_tinydb_cacheSize:int
	"""	The cache size for the TinyDB database. """

	database_tinydb_writeDelay:int
	"""	The write delay for the TinyDB database. """


	database_postgresql_host:str
	"""	The host of the PostgreSQL database. """

	database_postgresql_port:int
	"""	The port of the PostgreSQL database. """

	database_postgresql_role:str
	"""	The role of the PostgreSQL database. """

	database_postgresql_password:str
	"""	The password of the PostgreSQL database. """

	database_postgresql_database:str
	"""	The database of the PostgreSQL database. """

	database_postgresql_schema:str
	"""	The schema of the PostgreSQL database. """


	http_address:str
	"""	The address to listen on for HTTP the http server. """

	http_allowPatchForDelete:bool
	"""	Allow PATCH for DELETE operations. """

	http_enableStructureEndpoint:bool
	"""	Enable the structure endpoint. """

	http_enableUpperTesterEndpoint:bool
	"""	Enable the upper tester endpoint. """

	http_listenIF:str
	"""	The network interface to listen on for HTTP. """

	http_port:int
	"""	The port to listen on for HTTP. """

	http_root:str
	"""	The root of the HTTP path. """

	http_timeout:float
	"""	The timeout for HTTP requests. """


	http_cors_enable:bool
	"""	Enable or disable CORS. """

	http_cors_resources:list[str]
	"""	The resources for CORS. """


	http_security_caCertificateFile:str
	"""	The CA certificate file for HTTP. """

	http_security_caPrivateKeyFile:str
	"""	The CA private key file for HTTP. """

	http_security_tlsVersion:str
	"""	The TLS version for HTTP. """

	http_security_useTLS:bool
	"""	Enable or disable TLS for HTTP. """

	http_security_verifyCertificate:bool
	"""	Enable or disable certificate verification for HTTP. """

	http_security_enableBasicAuth:bool
	"""	Enable or disable basic authentication for HTTP. """

	http_security_enableTokenAuth:bool
	"""	Enable or disable token authentication for HTTP. """

	http_security_basicAuthFile:str
	"""	The file for basic authentication for HTTP. """

	http_security_tokenAuthFile:str
	"""	The file for token authentication for HTTP. """


	http_wsgi_enable:bool
	"""	Enable or disable the WSGI server. """

	http_wsgi_connectionLimit:int
	"""	The connection limit for the WSGI server. """

	http_wsgi_threadPoolSize:int
	"""	The thread pool size for the WSGI server. """


	logging_count:int
	"""	The number of log entries. """

	logging_enableBindingsLogging:bool
	"""	Enable or disable bindings logging. """

	logging_enableFileLogging:bool
	"""	Enable or disable file logging. """

	logging_enableScreenLogging:bool
	"""	Enable or disable screen logging. """

	logging_filter:list
	"""	The filter for logging. """

	logging_level:str|LogLevel
	"""	The log level. """

	logging_maxLogMessageLength:int
	"""	The maximum log message length. """

	logging_path:str
	"""	The path for logging. """

	logging_queueSize:int
	"""	The queue size for logging. """

	logging_size:int
	"""	The size of the log. """

	logging_stackTraceOnError:bool
	"""	Enable or disable stack trace on error. """

	logging_enableUTCTimezone:bool
	"""	Enable or disable UTC timezone. """


	mqtt_address:str
	"""	The address to listen on for the MQTT server. """

	mqtt_enable:bool
	"""	Enable or disable the MQTT server. """

	mqtt_keepalive:int
	"""	The keepalive for MQTT. """

	mqtt_listenIF:str
	"""	The network interface to listen on for MQTT. """

	mqtt_port:int
	"""	The port to listen on for MQTT. """

	mqtt_timeout:float
	"""	The timeout for MQTT requests. """

	mqtt_topicPrefix:str
	"""	The topic prefix for MQTT. """


	mqtt_security_allowedCredentialIDs:list[str]
	"""	The allowed credential IDs for MQTT. """

	mqtt_security_caCertificateFile:str
	"""	The CA certificate file for MQTT. """

	mqtt_security_password:str
	"""	The password for MQTT. """

	mqtt_security_username:str
	"""	The username for MQTT. """

	mqtt_security_useTLS:bool
	"""	Enable or disable TLS for MQTT. """

	mqtt_security_verifyCertificate:bool
	"""	Enable or disable certificate verification for MQTT. """


	resource_acp_selfPermission:int
	"""	The self permission for ACP. """


	resource_actr_ecpContinuous:int
	"""	The continuous for ACTR. """

	resource_actr_ecpPeriodic:int
	"""	The periodic for ACTR. """


	resource_cnt_enableLimits:bool
	"""	Enable or disable limits for CNT. """

	resource_cnt_mni:int
	"""	The MNI for CNT. """

	resource_cnt_mbs:int
	"""	The MBS for CNT. """

	resource_cnt_mia:int
	"""	The MIA for CNT. """


	resource_fcnt_enableLimits:bool
	"""	Enable or disable limits for FCNT. """

	resource_fcnt_mni:int
	"""	The MNI for FCNT. """

	resource_fcnt_mbs:int
	"""	The MBS for FCNT. """

	resource_fcnt_mia:int
	"""	The MIA for FCNT. """


	resource_grp_resultExpirationTime:int
	"""	The result expiration time for GRP. """

	resource_lcp_mni:int
	"""	The MNI for LCP. """

	resource_lcp_mbs:int
	"""	The MBS for LCP. """


	resource_req_et:int
	"""	The expiration time for REQ. """


	resource_sub_batchNotifyDuration:int
	"""	The batch notify duration for SUB. """


	resource_ts_enableLimits:bool
	"""	Enable or disable limits for TS. """

	resource_ts_mbs:int
	"""	The MBS for TS. """

	resource_ts_mdn:int
	"""	The MDN for TS. """

	resource_ts_mni:int
	"""	The MNI for TS. """

	resource_ts_mia:int
	"""	The MIA for TS. """


	resource_tsb_bcni:str
	"""	The BCNI for TSB. """

	resource_tsb_bcnt:float
	"""	The BCNT for TSB. """


	scripting_fileMonitoringInterval:float
	"""	The file monitoring interval for scripting. """

	scripting_maxRuntime:float
	"""	The maximum runtime for scripting. """

	scripting_scriptDirectories:list[str]
	"""	The script directories for scripting. """

	scripting_verbose:bool
	"""	Enable or disable verbose mode for scripting. """


	cse_statistics_enable:bool
	"""	Enable or disable statistics. """

	cse_statistics_writeInterval:int
	"""	The write interval for statistics. """


	textui_refreshInterval:float
	"""	The refresh interval for the text UI. """

	textui_startWithTUI:bool
	"""	Start with the text UI. """

	textui_theme:str
	"""	The theme for the text UI. """

	textui_maxRequestSize:int
	"""	The maximum request size for the text UI. """

	textui_notificationTimeout:float
	"""	The notification timeout for the text UI. """

	textui_enableTextEditorSyntaxHighlighting:bool
	"""	Enable or disable text editor syntax highlighting for the text UI. """


	webui_root:str
	"""	The root path for the web UI. """


	websocket_enable:bool
	"""	Enable or disable the WebSocket server. """


	websocket_address:str
	"""	The address to listen on for the WebSocket server. """

	websocket_listenIF:str
	"""	The network interface to listen on for WebSocket. """

	websocket_loglevel:int|str
	"""	The log level for WebSocket. """

	websocket_port:int
	"""	The port to listen on for WebSocket. """

	websocket_timeout:float
	"""	The timeout for WebSocket requests. """


	websocket_security_caCertificateFile:str
	"""	The CA certificate file for WebSocket. """

	websocket_security_caPrivateKeyFile:str
	"""	The CA private key file for WebSocket. """

	websocket_security_tlsVersion:str
	"""	The TLS version for WebSocket. """

	websocket_security_useTLS:bool
	"""	Enable or disable TLS for WebSocket. """

	websocket_security_verifyCertificate:bool
	"""	Enable or disable certificate verification for WebSocket. """

	websocket_security_enableBasicAuth:bool
	"""	Enable or disable basic authentication for WebSocket. """

	websocket_security_enableTokenAuth:bool
	"""	Enable or disable token authentication for WebSocket. """
	
	websocket_security_basicAuthFile:str
	"""	The file for basic authentication for WebSocket. """

	websocket_security_tokenAuthFile:str
	"""	The file for token authentication for WebSocket. """


	moduleDirectory:pathlib.Path = None
	""" The base directory of the ACME module. """
	baseDirectory:pathlib.Path = None
	""" The base directory of the ACME module. """
	initDirectory:pathlib.Path = None
	""" The init directory of the ACME module. """
	configfile:str = None
	""" The configuration file. """


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
	_args_coapEnabled:bool = None
	""" The coap enabled flag passed as argument. This overrides the respective value in the configuration file. """
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
		Configuration._args_coapEnabled			= args.coapenabled if args and 'coapenabled' in args else None
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
				
				# load onboarding module and create user config file.
				# After that, remove the module from the modules list, because it is not needed anymore
				from ..runtime import Onboarding
				result, _configFile, _baseDirectory = Onboarding.buildUserConfigFile(Configuration._args_configfile)
				import sys
				del sys.modules[Onboarding.__name__]	# Remove the module again to save some memory
				del Onboarding

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
							'baseDirectory' 		: Configuration.baseDirectory,					# points to the currenr working directory
							'moduleDirectory' 		: Configuration.moduleDirectory,				# points to the acme module's directory
							'initDirectory' 		: Configuration.initDirectory,					# points to the acme/init directory		
							'hostIPAddress'			: getIPAddress(),								# provide the IP address of the host

							'registrarCseHost'		: '127.0.0.1',									# The IP address of the registrar CSE
							'registrarCsePort'		: 8080,											# The TCP port of the registrar CSE
							'registrarCseID'		: '',											# The CSE-ID of the registrar CSE
							'registrarCseName'		: '',											# The resource name of the registrar CSE's CSEBase

							'secret'				: os.getenv('ACME_SECURITY_SECRET', 'acme'),	# The main secret key for the CSE. 
						}
					}
		# Add environment variables to the defaults
		_defaults.update({ 'DEFAULT': {k: v.replace('$', '$$') for k,v in os.environ.items()} })

		# Add (empty) default for supported environment variables to the defaults dictionary for the interpolation during reading the configuration file
		_envVariables = { e: os.getenv(e, '') if e not in _defaults else _defaults[e]
			for e in (
					'ACME_MQTT_SECURITY_PASSWORD', 'ACME_MQTT_SECURITY_USERNAME',
					'ACME_DATABASE_POSTGRESQL_PASSWORD',
					'ACME_CSE_REGISTRAR_SECURITY_HTTPUSERNAME', 'ACME_CSE_REGISTRAR_SECURITY_HTTPPASSWORD', 'ACME_CSE_REGISTRAR_SECURITY_HTTPBEARERTOKEN',
					'ACME_CSE_REGISTRAR_SECURITY_WSUSERNAME', 'ACME_CSE_REGISTRAR_SECURITY_WSPASSWORD', 'ACME_CSE_REGISTRAR_SECURITY_WSBEARERTOKEN',
					'ACME_CSE_REGISTRAR_SECURITY_SELFHTTPUSERNAME', 'ACME_CSE_REGISTRAR_SECURITY_SELFHTTPPASSWORD',
					'ACME_CSE_REGISTRAR_SECURITY_SELFWSUSERNAME', 'ACME_CSE_REGISTRAR_SECURITY_SELFWSPASSWORD',
				)
		}
		_defaults['DEFAULT'].update(_envVariables)

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

			# Call the configuration handler for each module
			# The "readConfiguration" methods are responsible for reading the configuration values from the configuration file
			# and to set the respective attributes in the Configuration class.
			# Validations are done later below.
			for m in _moduleConfigs:
				m.readConfiguration(config, Configuration)	# type:ignore [arg-type]
		
		except configparser.InterpolationMissingOptionError as e:
			Configuration._print(f'[red]Error in configuration file: {Configuration.configfile}\n{str(e)}')
			Configuration._print('\n[red]Please provide the option in the section [bold](basic.config)[/bold] in the configuration file or set an environment variable with that name.\n')
			return False

		except Exception as e:	# about when findings errors in configuration
			Configuration._print(f'[red]Error in configuration file: {Configuration.configfile}\n{str(e)}')
			return False

		# Validate the configuration for each module
		for m in _moduleConfigs:
			try:
				m.validateConfiguration(Configuration, True)	# type:ignore [arg-type]
			except ConfigurationError as e:
				Configuration._print(f'[red]{str(e)}')
				return False

		return True


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


#############################################################################
#
#	Instantiating Configuration modules
#
#	These modules are responsible for reading and validating their own configuration
#
#	This happens at the end of the module, because the Configuration class must be
#	initialized before the modules can be initialized.

# Import all configuration modules

from ..runtime.configurations.ACPResourceConfiguration import ACPResourceConfiguration
from ..runtime.configurations.ACTRResourceConfiguration import ACTRResourceConfiguration
from ..runtime.configurations.AnnouncementServiceConfiguration import AnnouncementServiceConfiguration
from ..runtime.configurations.CNTResourceConfiguration import CNTResourceConfiguration
from ..runtime.configurations.CoAPServerConfiguration import CoAPServerConfiguration
from ..runtime.configurations.ConsoleConfiguration import ConsoleConfiguration
from ..runtime.configurations.CSEConfiguration import CSEConfiguration
from ..runtime.configurations.FCNTResourceConfiguration import FCNTResourceConfiguration
from ..runtime.configurations.GroupServiceConfiguration import GroupServiceConfiguration
from ..runtime.configurations.HTTPServerConfiguration import HTTPServerConfiguration
from ..runtime.configurations.LCPResourceConfiguration import LCPResourceConfiguration
from ..runtime.configurations.LoggingConfiguration import LoggingConfiguration
from ..runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ..runtime.configurations.MQTTConfiguration import MQTTConfiguration
from ..runtime.configurations.PostgreSQLBindingConfiguration import PostgreSQLBindingConfiguration
from ..runtime.configurations.RegistrationServiceConfiguration import RegistrationServiceConfiguration
from ..runtime.configurations.RemoteCSEServiceConfiguration import RemoteCSEServiceConfiguration
from ..runtime.configurations.REQResourceConfiguration import REQResourceConfiguration
from ..runtime.configurations.ScriptingConfiguration import ScriptingConfiguration
from ..runtime.configurations.SecurityServiceConfiguration import SecurityServiceConfiguration
from ..runtime.configurations.StatisticsConfiguration import StatisticsConfiguration
from ..runtime.configurations.StorageConfiguration import StorageConfiguration
from ..runtime.configurations.SUBResourceConfiguration import SUBResourceConfiguration
from ..runtime.configurations.TextUIConfiguration import TextUIConfiguration
from ..runtime.configurations.TinyDBBindingConfiguration import TinyDBBindingConfiguration
from ..runtime.configurations.TSBResourceConfiguration import TSBResourceConfiguration
from ..runtime.configurations.TSResourceConfiguration import TSResourceConfiguration
from ..runtime.configurations.WebSocketConfiguration import WebSocketConfiguration


# Instantiate all configuration modules here

_moduleConfigs:list[ModuleConfiguration] = [

	# Runtime configurations
	CSEConfiguration(),
	TextUIConfiguration(), # must get its config before the Console !
	ConsoleConfiguration(),
	LoggingConfiguration(), # must get its config after the Console !
	ScriptingConfiguration(),
	StatisticsConfiguration(),

	# Service configurations
	AnnouncementServiceConfiguration(),
	GroupServiceConfiguration(),
	RegistrationServiceConfiguration(),
	RemoteCSEServiceConfiguration(),
	SecurityServiceConfiguration(),

	# Storage configurations
	StorageConfiguration(),
	PostgreSQLBindingConfiguration(),
	TinyDBBindingConfiguration(),

	# Binding configurations
	CoAPServerConfiguration(),
	HTTPServerConfiguration(),
	MQTTConfiguration(),
	WebSocketConfiguration(),

	# Resource configurations
	ACPResourceConfiguration(),
	ACTRResourceConfiguration(),
	CNTResourceConfiguration(),
	FCNTResourceConfiguration(),
	LCPResourceConfiguration(),
	REQResourceConfiguration(),
	SUBResourceConfiguration(),
	TSResourceConfiguration(),
	TSBResourceConfiguration(),

]
