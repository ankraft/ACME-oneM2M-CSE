#
#	Configuration.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing CSE configurations
#


import configparser, re, argparse, os.path, pathlib
from typing import Any, Dict
from rich.console import Console
from ..etc.Constants import Constants as C
from ..etc.Types import CSEType, ContentSerializationType, Permission


class Configuration(object):
	"""	The static class Configuration holds all the configuration values of the CSE. It is initialized only once by calling the static
		method init(). Access to configuration valus is done by calling Configuration.get(<key>).
	"""
	_configuration: Dict[str, Any] = {}

	@staticmethod
	def init(args: argparse.Namespace = None) -> bool:
		console = Console()

		from ..etc import Utils as Utils	# cannot import at the top because of circel import

		# resolve the args, of any
		argsConfigfile			= args.configfile if args and 'configfile' in args else C.defaultConfigFile
		argsLoglevel			= args.loglevel if args and 'loglevel' in args else None
		argsDBReset				= args.dbreset if args and 'dbreset' in args else False
		argsDBStorageMode		= args.dbstoragemode if args and 'dbstoragemode' in args else None
		argsHeadless			= args.headless if args and 'headless' in args else False
		argsHttpAddress			= args.httpaddress if args and 'httpaddress' in args else None
		argsHttpPort			= args.httpport if args and 'httpport' in args else None
		argsImportDirectory		= args.importdirectory if args and 'importdirectory' in args else None
		argsListenIF			= args.listenif if args and 'listenif' in args else None
		argsMqttEnabled			= args.mqttenabled if args and 'mqttenabled' in args else None
		argsRemoteCSEEnabled	= args.remotecseenabled if args and 'remotecseenabled' in args else None
		argsRemoteConfigEnabled	= args.remoteconfigenabled if args and 'remoteconfigenabled' in args else None
		argsRunAsHttps			= args.https if args and 'https' in args else None
		argsStatisticsEnabled	= args.statisticsenabled if args and 'statisticsenabled' in args else None

		# own print function that takes the headless setting into account
		def _print(out:str) -> None:
			if not argsHeadless:
				console.print(out)


		# Read and parse the configuration file
		config = configparser.ConfigParser(	interpolation=configparser.ExtendedInterpolation(),
											converters={'list': lambda x: [i.strip() for i in x.split(',')]},	# Convert csv to list
										  )
		config.read_dict({ 'basic.config': {
								'baseDirectory' 	: pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent.parent,	# points to the acme module's parent directory
								'registrarCseHost'	: '127.0.0.1',																# The IP address of the registrar CSE
								'registrarCsePort'	: 8080,																		# The TCP port of the registrar CSE
								'registrarCseID'	: 'id-in',																	# The CSE-ID of the registrar CSE
								'registrarCseName'	: 'cse-in',																	# The resource name of the registrar CSE's CSEBase
						 }
					})
		try:
			if len(config.read(argsConfigfile)) == 0 and argsConfigfile != C.defaultConfigFile:		# Allow 
				_print(f'[red]Configuration file missing or not readable: {argsConfigfile}')
				return False
		except configparser.Error as e:
			_print('[red]Error in configuration file')
			_print(str(e))
			return False

		#
		#	Retrieve configuration values
		#

		try:
			Configuration._configuration = {
				'configfile'							: argsConfigfile,
				'packageDirectory'						: pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent,	# points to the acme package directory


				#
				#	CSE
				#


				'cse.type'								: config.get('cse', 'type',								fallback = 'IN'),		# IN, MN, ASN
				'cse.spid'								: config.get('cse', 'serviceProviderID',				fallback = 'acme.example.com'),
				'cse.csi'								: config.get('cse', 'cseID',							fallback = '/id-in'),
				'cse.ri'								: config.get('cse', 'resourceID',						fallback = 'id-in'),
				'cse.rn'								: config.get('cse', 'resourceName',						fallback = 'cse-in'),
				'cse.resourcesPath'						: config.get('cse', 'resourcesPath', 					fallback = C.defaultImportDirectory),
				'cse.expirationDelta'					: config.getint('cse', 'expirationDelta', 				fallback = 60*60*24*365),	# 1 year, in seconds
				'cse.maxExpirationDelta'				: config.getint('cse', 'maxExpirationDelta',			fallback = 60*60*24*365*5),	# 5 years, in seconds
				'cse.requestExpirationDelta'			: config.getfloat('cse', 'requestExpirationDelta',		fallback = 10.0),	# 10 seconds
				'cse.originator'						: config.get('cse', 'originator',						fallback = 'CAdmin'),
				'cse.enableRemoteCSE'					: config.getboolean('cse', 'enableRemoteCSE', 			fallback = True),
				'cse.sortDiscoveredResources'			: config.getboolean('cse', 'sortDiscoveredResources',	fallback = True),
				'cse.checkExpirationsInterval'			: config.getint('cse', 'checkExpirationsInterval',		fallback = 60),		# Seconds
				'cse.flexBlockingPreference'			: config.get('cse', 'flexBlockingPreference',			fallback = 'blocking'),
				'cse.supportedReleaseVersions'			: config.getlist('cse', 'supportedReleaseVersions',		fallback = ['2a', '3', '4']), # type: ignore [attr-defined]
				'cse.releaseVersion'					: config.get('cse', 'releaseVersion',					fallback = '4'),
				'cse.defaultSerialization'				: config.get('cse', 'defaultSerialization',				fallback = 'json'),

				#
				#	CSE Security
				#
				'cse.security.enableACPChecks'			: config.getboolean('cse.security', 'enableACPChecks', 	fallback = True),
				'cse.security.fullAccessAdmin'			: config.getboolean('cse.security', 'fullAccessAdmin', 	fallback = True),

				#
				#	HTTP Server
				#

				'http.listenIF'							: config.get('server.http', 'listenIF', 				fallback = '127.0.0.1'),
				'http.port' 							: config.getint('server.http', 'port', 					fallback = 8080),
				'http.root'								: config.get('server.http', 'root', 					fallback = ''),
				'http.address'							: config.get('server.http', 'address', 					fallback = 'http://127.0.0.1:8080'),
				'http.enableRemoteConfiguration'		: config.getboolean('server.http', 'enableRemoteConfiguration', fallback = False),
				'http.enableStructureEndpoint'			: config.getboolean('server.http', 'enableStructureEndpoint', fallback = False),
				'http.enableResetEndpoint'				: config.getboolean('server.http', 'enableResetEndpoint', fallback = False),
				'http.enableUpperTesterEndpoint'		: config.getboolean('server.http', 'enableUpperTesterEndpoint', fallback = False),

				#
				#	HTTP Server Security
				#

				'http.security.useTLS'					: config.getboolean('server.http.security', 'useTLS', 			fallback = False),
				'http.security.tlsVersion'				: config.get('server.http.security', 'tlsVersion', 				fallback = 'auto'),
				'http.security.verifyCertificate'		: config.getboolean('server.http.security', 'verifyCertificate',fallback = False),
				'http.security.caCertificateFile'		: config.get('server.http.security', 'caCertificateFile', 		fallback = None),
				'http.security.caPrivateKeyFile'		: config.get('server.http.security', 'caPrivateKeyFile', 		fallback = None),

				#
				#	MQTT Client
				#

				'mqtt.enable'							: config.getboolean('client.mqtt', 'enable', 			fallback = False),
				'mqtt.address'							: config.get('client.mqtt', 'address', 					fallback = '127.0.0.1'),
				'mqtt.port' 							: config.getint('client.mqtt', 'port', 					fallback = None),	# Default will be determined later (s.b.)
				'mqtt.keepalive' 						: config.getint('client.mqtt', 'keepalive',				fallback = 60),
				'mqtt.listenIF' 						: config.get('client.mqtt', 'listenIF',					fallback = '127.0.0.1'),
				'mqtt.topicPrefix' 						: config.get('client.mqtt', 'topicPrefix',				fallback = ''),
				'mqtt.timeout' 							: config.getfloat('client.mqtt', 'timeout',				fallback = 5.0),

				#
				#	MQTT Client Security
				#

				'mqtt.security.useTLS'					: config.getboolean('client.mqtt.security', 'useTLS', 				fallback = False),
				'mqtt.security.verifyCertificate'		: config.getboolean('client.mqtt.security', 'verifyCertificate', 	fallback = False),
				'mqtt.security.caCertificateFile'		: config.get('client.mqtt.security', 'caCertificateFile',			fallback = None),
				'mqtt.security.username'				: config.get('client.mqtt.security', 'username',					fallback = None),
				'mqtt.security.password' 				: config.get('client.mqtt.security', 'password',					fallback = None),
				'mqtt.security.allowedCredentialIDs'	: config.getlist('client.mqtt.security', 'allowedCredentialIDs', 	fallback = []),	# type: ignore [attr-defined]

				#
				#	Database
				#

				'db.path'								: config.get('database', 'path', 						fallback = C.defaultDataDirectory),
				'db.inMemory'							: config.getboolean('database', 'inMemory', 			fallback = False),
				'db.cacheSize'							: config.getint('database', 'cacheSize', 				fallback = 0),		# Default: no caching
				'db.resetOnStartup' 					: config.getboolean('database', 'resetOnStartup',		fallback = False),

				#
				#	Logging
				#

				'logging.enableFileLogging'				: config.getboolean('logging', 'enableFileLogging', 	fallback = False),
				'logging.enableScreenLogging'			: config.getboolean('logging', 'enableScreenLogging', 	fallback = True),
				'logging.path'							: config.get('logging', 'path', 						fallback = C.defaultLogDirectory),
				'logging.level'							: config.get('logging', 'level', 						fallback = 'debug'),
				'logging.size'							: config.getint('logging', 'size', 						fallback = 100000),
				'logging.count'							: config.getint('logging', 'count', 					fallback = 10),		# Number of log files
				'logging.stackTraceOnError'				: config.getboolean('logging', 'stackTraceOnError',		fallback = True),
				'logging.enableBindingsLogging'			: config.getboolean('logging', 'enableBindingsLogging',	fallback = False),


				#
				#	Registrar CSE
				#

				'cse.registrar.address'					: config.get('cse.registrar', 'address', 					fallback = None),
				'cse.registrar.root'					: config.get('cse.registrar', 'root', 						fallback = ''),
				'cse.registrar.csi'						: config.get('cse.registrar', 'cseID', 						fallback = None),
				'cse.registrar.rn'						: config.get('cse.registrar', 'resourceName', 				fallback = None),
				'cse.registrar.checkInterval'			: config.getint('cse.registrar', 'checkInterval', 			fallback = 30),		# Seconds
				'cse.registrar.excludeCSRAttributes'	: config.getlist('cse.registrar', 'excludeCSRAttributes',	fallback = []),		# type: ignore [attr-defined]
				'cse.registrar.serialization'			: config.get('cse.registrar', 'serialization',				fallback = 'json'),

				#
				#	Registrations
				#

				'cse.registration.allowedAEOriginators'		: config.getlist('cse.registration', 'allowedAEOriginators',	fallback = ['C*','S*']),		# type: ignore [attr-defined]
				'cse.registration.allowedCSROriginators'	: config.getlist('cse.registration', 'allowedCSROriginators',	fallback = []),				# type: ignore [attr-defined]
				'cse.registration.checkLiveliness'			: config.getboolean('cse.registration', 'checkLiveliness',		fallback = True),


				#
				#	Announcements
				#

				'cse.announcements.checkInterval'		: config.getint('cse.announcements', 'checkInterval',	fallback = 10),


				#
				#	Statistics
				#

				'cse.statistics.enable'					: config.getboolean('cse.statistics', 'enable', 		fallback=True),
				'cse.statistics.writeInterval'			: config.getint('cse.statistics', 'writeInterval',		fallback=60),		# Seconds


				#
				#	Defaults for Access Control Policies
				#

				'cse.acp.pv.acop'						: config.getint('cse.resource.acp', 'permission', 		fallback=Permission.ALL),
				'cse.acp.pvs.acop'						: config.getint('cse.resource.acp', 'selfPermission', 	fallback=Permission.DISCOVERY+Permission.NOTIFY+Permission.CREATE+Permission.RETRIEVE),


				#
				#	Defaults for Container Resources
				#

				'cse.cnt.enableLimits'					: config.getboolean('cse.resource.cnt', 'enableLimits', fallback=False),
				'cse.cnt.mni'							: config.getint('cse.resource.cnt', 'mni', 				fallback=10),
				'cse.cnt.mbs'							: config.getint('cse.resource.cnt', 'mbs', 				fallback=10000),


				#
				#	Defaults for Request Resources
				#

				'cse.req.minet'							: config.getint('cse.resource.req', 'minimumExpirationTime', fallback=60),
				'cse.req.maxet'							: config.getint('cse.resource.req', 'maximumExpirationTime', fallback=180),


				#
				#	Defaults for Subscription Resources
				#

				'cse.sub.dur'							: config.getint('cse.resource.sub', 'batchNotifyDuration', 	fallback=60),	# seconds


				#
				#	Defaults for timeSeries Resources
				#

				'cse.ts.enableLimits'					: config.getboolean('cse.resource.ts', 'enableLimits',	fallback=False),
				'cse.ts.mni'							: config.getint('cse.resource.ts', 'mni', 				fallback=10),
				'cse.ts.mbs'							: config.getint('cse.resource.ts', 'mbs', 				fallback=10000),
				'cse.ts.mdn'							: config.getint('cse.resource.ts', 'mdn', 				fallback=10),


				#
				#	Web UI
				#

				'cse.webui.enable'						: config.getboolean('cse.webui', 'enable', 				fallback=True),
				'cse.webui.root'						: config.get('cse.webui', 'root', 						fallback='/webui'),


				#
				#	Console
				#

				'cse.console.refreshInterval'			: config.getfloat('cse.console', 'refreshInterval', 	fallback=2.0),
				'cse.console.hideResources'				: config.getlist('cse.console', 'hideResources', 		fallback=[]),		# type: ignore[attr-defined]
				'cse.console.treeMode'					: config.get('cse.console', 'treeMode', 				fallback='normal'),
				'cse.console.confirmQuit'				: config.getboolean('cse.console', 'confirmQuit', 		fallback=False),

			}

		except configparser.InterpolationMissingOptionError as e:
			_print(f'[red]Error in configuration file: {argsConfigfile}\n{str(e)}')
			_print('\n[red]Please check the section [bold]\[basic.config][/bold] in the configuration file.\n')
			return False

		except Exception as e:	# about when findings errors in configuration
			_print(f'[red]Error in configuration file: {argsConfigfile}\n{str(e)}')
			return False

		# Read id-mappings
		if  config.has_section('server.http.mappings'):
			Configuration._configuration['server.http.mappings'] = config.items('server.http.mappings')
			# print(config.items('server.http.mappings'))

		# Some clean-ups and overrides

		# CSE type
		cseType = Configuration._configuration['cse.type'].lower()
		if  cseType == 'asn':
			Configuration._configuration['cse.type'] = CSEType.ASN
		elif cseType == 'mn':
			Configuration._configuration['cse.type'] = CSEType.MN
		else:
			Configuration._configuration['cse.type'] = CSEType.IN

		# CSE Serialization
		ct = Configuration._configuration['cse.defaultSerialization']
		Configuration._configuration['cse.defaultSerialization'] = ContentSerializationType.toContentSerialization(ct)
		if Configuration._configuration['cse.defaultSerialization'] == ContentSerializationType.UNKNOWN:
			_print(f'[red]Configuration Error: Unsupported \[cse]:defaultSerialization: {ct}')
			return False
		
		# Registrar Serialization
		ct = Configuration._configuration['cse.registrar.serialization']
		Configuration._configuration['cse.registrar.serialization'] = ContentSerializationType.toContentSerialization(ct)
		if Configuration._configuration['cse.registrar.serialization'] == ContentSerializationType.UNKNOWN:
			_print(f'[red]Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}')
			return False

		# Loglevel and various overrides from command line
		from ..services.Logging import LogLevel
		logLevel = Configuration._configuration['logging.level'].lower()
		logLevel = (argsLoglevel or logLevel) 	# command line args override config
		if logLevel == 'off':
			Configuration._configuration['logging.level'] = LogLevel.OFF
		elif logLevel == 'info':
			Configuration._configuration['logging.level'] = LogLevel.INFO
		elif logLevel == 'warn':
			Configuration._configuration['logging.level'] = LogLevel.WARNING
		elif logLevel == 'error':
			Configuration._configuration['logging.level'] = LogLevel.ERROR
		else:
			Configuration._configuration['logging.level'] = LogLevel.DEBUG

		if argsDBReset is True:					Configuration._configuration['db.resetOnStartup'] = True									# Override DB reset from command line
		if argsDBStorageMode is not None:		Configuration._configuration['db.inMemory'] = argsDBStorageMode == 'memory'					# Override DB storage mode from command line
		if argsHttpAddress is not None:			Configuration._configuration['http.address'] = argsHttpAddress								# Override server http address
		if argsHttpPort is not None:			Configuration._configuration['http.port'] = argsHttpPort									# Override server http port
		if argsImportDirectory is not None:		Configuration._configuration['cse.resourcesPath'] = argsImportDirectory						# Override import directory from command line
		if argsListenIF is not None:			Configuration._configuration['http.listenIF'] = argsListenIF								# Override binding network interface
		if argsMqttEnabled is not None:			Configuration._configuration['mqtt.enable'] = argsMqttEnabled								# Override mqtt enable
		if argsRemoteConfigEnabled is not None:	Configuration._configuration['http.enableRemoteConfiguration'] = argsRemoteConfigEnabled	# Override remote/httpConfiguration
		if argsRemoteCSEEnabled is not None:	Configuration._configuration['cse.enableRemoteCSE'] = argsRemoteCSEEnabled					# Override remote CSE enablement
		if argsRunAsHttps is not None:			Configuration._configuration['http.security.useTLS'] = argsRunAsHttps						# Override useTLS
		if argsStatisticsEnabled is not None:	Configuration._configuration['cse.statistics.enable'] = argsStatisticsEnabled				# Override statistics enablement

		if argsHeadless:
			Configuration._configuration['logging.enableScreenLogging'] = False

		# Correct urls
		Configuration._configuration['cse.registrar.address'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.address'])
		Configuration._configuration['http.address'] = Utils.normalizeURL(Configuration._configuration['http.address'])
		Configuration._configuration['http.root'] = Utils.normalizeURL(Configuration._configuration['http.root'])
		Configuration._configuration['cse.registrar.root'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.root'])

		# Just in case: check the URL's
		if Configuration._configuration['http.security.useTLS']:
			if Configuration._configuration['http.address'].startswith('http:'):
				_print('[orange3]Configuration Warning: Changing "http" to "https" in \[server.http]:address')
				Configuration._configuration['http.address'] = Configuration._configuration['http.address'].replace('http:', 'https:')
			# registrar might still be accessible vi another protocol
			# if Configuration._configuration['cse.registrar.address'].startswith('http:'):
			# 	_print('[orange3]Configuration Warning: Changing "http" to "https" in \[cse.registrar]:address')
			# 	Configuration._configuration['cse.registrar.address'] = Configuration._configuration['cse.registrar.address'].replace('http:', 'https:')
		else: 
			if Configuration._configuration['http.address'].startswith('https:'):
				_print('[orange3]Configuration Warning: Changing "https" to "http" in \[server.http]:address')
				Configuration._configuration['http.address'] = Configuration._configuration['http.address'].replace('https:', 'http:')
			# registrar might still be accessible vi another protocol
			# if Configuration._configuration['cse.registrar.address'].startswith('https:'):
			# 	_print('[orange3]Configuration Warning: Changing "https" to "http" in \[cse.registrar]:address')
			# 	Configuration._configuration['cse.registrar.address'] = Configuration._configuration['cse.registrar.address'].replace('https:', 'http:')


		#
		#	Some sanity and validity checks
		#

		# TLS & certificates
		if not Configuration._configuration['http.security.useTLS']:	# clear certificates configuration if not in use
			Configuration._configuration['http.security.verifyCertificate'] = False
			Configuration._configuration['http.security.tlsVersion'] = 'auto'
			Configuration._configuration['http.security.caCertificateFile'] = None
			Configuration._configuration['http.security.caPrivateKeyFile'] = None
		else:
			if not (val := Configuration._configuration['http.security.tlsVersion']).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				_print(f'[red]Configuration Error: Unknown value for \[http.security]:tlsVersion: {val}')
				return False
			if not (val := Configuration._configuration['http.security.caCertificateFile']):
				_print('[red]Configuration Error: \[http.security]:caCertificateFile must be set when TLS is enabled')
				return False
			if not os.path.exists(val):
				_print(f'[red]Configuration Error: \[http.security]:caCertificateFile does not exists or is not accessible: {val}')
				return False
			if not (val := Configuration._configuration['http.security.caPrivateKeyFile']):
				_print('[red]Configuration Error: \[http.security]:caPrivateKeyFile must be set when TLS is enabled')
				return False
			if not os.path.exists(val):
				_print(f'[red]Configuration Error: \[http.security]:caPrivateKeyFile does not exists or is not accessible: {val}')
				return False
		
		#
		#	MQTT client
		#
		if not Configuration._configuration['mqtt.port']:	# set the default port depending on whether to use TLS
			Configuration._configuration['mqtt.port'] = 8883 if Configuration._configuration['mqtt.security.useTLS'] else 1883
		if not (Configuration._configuration['mqtt.security.username']) != (not Configuration._configuration['mqtt.security.password']):
			_print(f'[red]Configuration Error: Username or password missing for \[mqtt.security]]')
			return False
		# remove empty cid from the list
		Configuration._configuration['mqtt.security.allowedCredentialIDs'] = [ cid for cid in Configuration._configuration['mqtt.security.allowedCredentialIDs'] if len(cid) ]
		

		# check the csi format
		if not Utils.isValidCSI(val:=Configuration._configuration['cse.csi']):
			_print(f'[red]Configuration Error: Wrong format for \[cse]:cseID: {val}')
			return False

		if Configuration._configuration['cse.registrar.address'] and Configuration._configuration['cse.registrar.csi']:
			if not Utils.isValidCSI(val:=Configuration._configuration['cse.registrar.csi']):
				_print(f'[red]Configuration Error: Wrong format for \[cse.registrar]:cseID: {val}')
				return False
			if len(Configuration._configuration['cse.registrar.csi']) > 0 and len(Configuration._configuration['cse.registrar.rn']) == 0:
				_print('[red]Configuration Error: Missing configuration \[cse.registrar]:resourceName')
				return False

		# Check default subscription duration
		if Configuration._configuration['cse.sub.dur'] < 1:
			_print('[red]Configuration Error: \[cse.resource.sub]:batchNotifyDuration must be > 0')
			return False

		# Check flexBlocking value
		Configuration._configuration['cse.flexBlockingPreference'] = Configuration._configuration['cse.flexBlockingPreference'].lower()
		if Configuration._configuration['cse.flexBlockingPreference'] not in ['blocking', 'nonblocking']:
			_print('[red]Configuration Error: \[cse]:flexBlockingPreference must be "blocking" or "nonblocking"')
			return False

		# Check release versions
		if len(srv := Configuration._configuration['cse.supportedReleaseVersions']) == 0:
			_print('[red]Configuration Error: \[cse]:supportedReleaseVersions must not be empty')
			return False
			
		if len(rvi := Configuration._configuration['cse.releaseVersion']) == 0:
			_print('[red]Configuration Error: \[cse]:releaseVersion must not be empty')
			return False
		if rvi not in srv:
			_print(f'[red]Configuration Error: \[cse]:releaseVersion: {rvi} not in \[cse].supportedReleaseVersions: {srv}')
			return False
		if any([s for s in srv if str(rvi) < s]):
			_print(f'[red]Configuration Error: \[cse]:releaseVersion: {rvi} less than highest value in \[cse].supportedReleaseVersions: {srv}')
			return False

		# Check various intervals
		if Configuration._configuration['cse.checkExpirationsInterval'] <= 0:
			_print('[red]Configuration Error: \[cse]:checkExpirationsInterval must be greater than 0')
			return False
		if Configuration._configuration['cse.console.refreshInterval'] <= 0.0:
			_print('[red]Configuration Error: \[cse.console]:refreshInterval must be greater than 0.0')
			return False

		from ..services.Console import TreeMode
		if not (treeMode := TreeMode.to(Configuration._configuration['cse.console.treeMode'])):
			_print(f'[red]Configuration Error: \[cse.console]:treeMode must be one of {TreeMode.names()}')
			return False
		Configuration._configuration['cse.console.treeMode'] = treeMode

		# Everything is fine
		return True


	@staticmethod
	def print() -> str:
		result = 'Configuration:\n'		# Magic string used e.g. in tests, don't remove
		for (k,v) in Configuration._configuration.items():
			result += f'  {k} = {v}\n'
		return result


	@staticmethod
	def all() -> Dict[str, Any]:
		return Configuration._configuration


	@staticmethod
	def get(key: str) -> Any:
		"""	Retrieve a configuration value or None if no configuration could be found for a key.
		"""
		if not Configuration.has(key):
			return None
		return Configuration._configuration[key]


	@staticmethod
	def set(key: str, value: Any) -> None:
		Configuration._configuration[key] = value


	@staticmethod
	def has(key: str) -> bool:
		return key in Configuration._configuration
