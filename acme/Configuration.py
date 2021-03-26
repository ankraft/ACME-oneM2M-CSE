#
#	Configuration.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing CSE configurations
#


import logging, configparser, re, argparse, ssl, os.path
from typing import Any, Dict
from Constants import Constants as C
from Types import CSEType, ContentSerializationType
from rich.console import Console


class Configuration(object):
	"""	The static class Configuration holds all the configuration values of the CSE. It is initialized only once by calling the static
		method init(). Access to configuration valus is done by calling Configuration.get(<key>).
	"""
	_configuration: Dict[str, Any] = {}

	@staticmethod
	def init(args: argparse.Namespace = None) -> bool:
		console = Console()

		import Utils	# cannot import at the top because of circel import

		# resolve the args, of any
		argsConfigfile			= args.configfile if args is not None and 'configfile' in args else C.defaultConfigFile
		argsLoglevel			= args.loglevel if args is not None and 'loglevel' in args else None
		argsDBReset				= args.dbreset if args is not None and 'dbreset' in args else False
		argsDBStorageMode		= args.dbstoragemode if args is not None and 'dbstoragemode' in args else None
		argsImportDirectory		= args.importdirectory if args is not None and 'importdirectory' in args else None
		argsAppsEnabled			= args.appsenabled if args is not None and 'appsenabled' in args else None
		argsRemoteCSEEnabled	= args.remotecseenabled if args is not None and 'remotecseenabled' in args else None
		argsValidationEnabled	= args.validationenabled if args is not None and 'validationenabled' in args else None
		argsStatisticsEnabled	= args.statisticsenabled if args is not None and 'statisticsenabled' in args else None
		argsRunAsHttps			= args.https if args is not None and 'https' in args else None
		argsRemoteConfigEnabled	= args.remoteconfigenabled if args is not None and 'remoteconfigenabled' in args else None
		argsListenIF			= args.listenif if args is not None and 'listenif' in args else None
		argsHttpAddress			= args.httpaddress if args is not None and 'httpaddress' in args else None
		argsHeadless			= args.headless if args is not None and 'headless' in args else False

		# own print function that takes the headless setting into account
		def _print(out:str) -> None:
			if not argsHeadless:
				console.print(out)


		# Read and parse the configuration file
		config = configparser.ConfigParser(	interpolation=configparser.ExtendedInterpolation(),
											converters={'list': lambda x: [i.strip() for i in x.split(',')]}	# Convert csv to list
										  )
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
				'configfile'					: argsConfigfile,

				#
				#	HTTP Server
				#

				'http.listenIF'						: config.get('server.http', 'listenIF', 				fallback='127.0.0.1'),
				'http.port' 						: config.getint('server.http', 'port', 					fallback=8080),
				'http.root'							: config.get('server.http', 'root', 					fallback=''),
				'http.address'						: config.get('server.http', 'address', 					fallback='http://127.0.0.1:8080'),
				'http.multiThread'					: config.getboolean('server.http', 'multiThread', 		fallback=True),
				'http.enableRemoteConfiguration'	: config.getboolean('server.http', 'enableRemoteConfiguration', fallback=False),
				'http.enableStructureEndpoint'		: config.getboolean('server.http', 'enableStructureEndpoint', fallback=False),

				#
				#	Database
				#

				'db.path'							: config.get('database', 'path', 						fallback=C.defaultDataDirectory),
				'db.inMemory'						: config.getboolean('database', 'inMemory', 			fallback=False),
				'db.cacheSize'						: config.getint('database', 'cacheSize', 				fallback=0),		# Default: no caching
				'db.resetOnStartup' 				: config.getboolean('database', 'resetOnStartup',		fallback=False),

				#
				#	Logging
				#

				'logging.enable'					: config.getboolean('logging', 'enable', 				fallback=True),
				'logging.enableFileLogging'			: config.getboolean('logging', 'enableFileLogging', 	fallback=False),
				'logging.enableScreenLogging'		: config.getboolean('logging', 'enableScreenLogging', 	fallback=True),
				'logging.path'						: config.get('logging', 'path', 						fallback=C.defaultLogDirectory),
				'logging.level'						: config.get('logging', 'level', 						fallback='debug'),
				'logging.size'						: config.getint('logging', 'size', 						fallback=100000),
				'logging.count'						: config.getint('logging', 'count', 					fallback=10),		# Number of log files
				'logging.stackTraceOnError'			: config.getboolean('logging', 'stackTraceOnError',			fallback=True),

				#
				#	CSE
				#

				'cse.type'							: config.get('cse', 'type',								fallback='IN'),		# IN, MN, ASN
				'cse.spid'							: config.get('cse', 'serviceProviderID',				fallback='acme'),
				'cse.csi'							: config.get('cse', 'cseID',							fallback='/id-in'),
				'cse.ri'							: config.get('cse', 'resourceID',						fallback='id-in'),
				'cse.rn'							: config.get('cse', 'resourceName',						fallback='cse-in'),
				'cse.resourcesPath'					: config.get('cse', 'resourcesPath', 					fallback=C.defaultImportDirectory),
				'cse.expirationDelta'				: config.getint('cse', 'expirationDelta', 				fallback=60*60*24*365),	# 1 year, in seconds
				'cse.maxExpirationDelta'			: config.getint('cse', 'maxExpirationDelta',			fallback=60*60*24*365*5),	# 5 years, in seconds
				'cse.originator'					: config.get('cse', 'originator',						fallback='CAdmin'),
				'cse.enableApplications'			: config.getboolean('cse', 'enableApplications', 		fallback=True),
				'cse.applicationsStartupDelay'		: config.getint('cse', 'applicationsStartupDelay',		fallback=5),		# Seconds
				'cse.enableNotifications'			: config.getboolean('cse', 'enableNotifications', 		fallback=True),
				'cse.enableRemoteCSE'				: config.getboolean('cse', 'enableRemoteCSE', 			fallback=True),
				'cse.enableTransitRequests'			: config.getboolean('cse', 'enableTransitRequests',		fallback=True),
				'cse.enableValidation'				: config.getboolean('cse', 'enableValidation', 			fallback=True),
				'cse.sortDiscoveredResources'		: config.getboolean('cse', 'sortDiscoveredResources',	fallback=True),
				'cse.checkExpirationsInterval'		: config.getint('cse', 'checkExpirationsInterval',		fallback=60),		# Seconds
				'cse.flexBlockingPreference'		: config.get('cse', 'flexBlockingPreference',			fallback='blocking'),
				'cse.supportedReleaseVersions'		: config.getlist('cse', 'supportedReleaseVersions',		fallback=C.supportedReleaseVersions), # type: ignore
				'cse.releaseVersion'				: config.get('cse', 'releaseVersion',					fallback='3'),
				'cse.defaultSerialization'			: config.get('cse', 'defaultSerialization',				fallback='json'),

				#
				#	CSE Security
				#
				'cse.security.enableACPChecks'		: config.getboolean('cse.security', 'enableACPChecks', 	fallback=True),
				'cse.security.fullAccessAdmin'		: config.getboolean('cse.security', 'fullAccessAdmin', 	fallback=True),
				'cse.security.useTLS'				: config.getboolean('cse.security', 'useTLS', 			fallback=False),
				'cse.security.tlsVersion'			: config.get('cse.security', 'tlsVersion', 				fallback='auto'),
				'cse.security.verifyCertificate'	: config.getboolean('cse.security', 'verifyCertificate',fallback=False),
				'cse.security.caCertificateFile'	: config.get('cse.security', 'caCertificateFile', 		fallback=None),
				'cse.security.caPrivateKeyFile'		: config.get('cse.security', 'caPrivateKeyFile', 		fallback=None),

				#
				#	Registrar CSE
				#

				'cse.registrar.address'				: config.get('cse.registrar', 'address', 				fallback=None),
				'cse.registrar.root'				: config.get('cse.registrar', 'root', 					fallback=None),
				'cse.registrar.csi'					: config.get('cse.registrar', 'cseID', 					fallback=None),
				'cse.registrar.rn'					: config.get('cse.registrar', 'resourceName', 			fallback=None),
				'cse.registrar.checkInterval'		: config.getint('cse.registrar', 'checkInterval', 		fallback=30),		# Seconds
				'cse.registrar.excludeCSRAttributes': config.getlist('cse.registrar', 'excludeCSRAttributes',fallback=[]),		# type: ignore
				'cse.registrar.serialization'		: config.get('cse.registrar', 'serialization',			fallback='json'),

				#
				#	Registrations
				#

				'cse.registration.allowedAEOriginators'	: config.getlist('cse.registration', 'allowedAEOriginators',	fallback=['C*','S*']),		# type: ignore
				'cse.registration.allowedCSROriginators': config.getlist('cse.registration', 'allowedCSROriginators',	fallback=[]),				# type: ignore
				'cse.registration.checkLiveliness'		: config.getboolean('cse.registration', 'checkLiveliness',		fallback=True),


				#
				#	Announcements
				#

				'cse.announcements.enable'			: config.getboolean('cse.announcements', 'enable',		fallback=True),
				'cse.announcements.checkInterval'	: config.getint('cse.announcements', 'checkInterval',	fallback=10),


				#
				#	Statistics
				#

				'cse.statistics.enable'				: config.getboolean('cse.statistics', 'enable', 		fallback=True),
				'cse.statistics.writeInterval'		: config.getint('cse.statistics', 'writeInterval',		fallback=60),		# Seconds


				#
				#	Defaults for Access Control Policies
				#

				'cse.acp.pv.acop'					: config.getint('cse.resource.acp', 'permission', 		fallback=63),
				'cse.acp.pvs.acop'					: config.getint('cse.resource.acp', 'selfPermission', 	fallback=51),


				#
				#	Defaults for Container Resources
				#

				'cse.cnt.enableLimits'				: config.getboolean('cse.resource.cnt', 'enableLimits', fallback=False),
				'cse.cnt.mni'						: config.getint('cse.resource.cnt', 'mni', 				fallback=10),
				'cse.cnt.mbs'						: config.getint('cse.resource.cnt', 'mbs', 				fallback=10000),


				#
				#	Defaults for Request Resources
				#

				'cse.req.minet'						: config.getint('cse.resource.req', 'minimumExpirationTime', fallback=60),
				'cse.req.maxet'						: config.getint('cse.resource.req', 'maximumExpirationTime', fallback=180),


				#
				#	Defaults for Subscription Resources
				#

				'cse.sub.dur'						: config.getint('cse.resource.sub', 'batchNotifyDuration', 	fallback=60),	# seconds


				#
				#	Web UI
				#

				'cse.webui.enable'					: config.getboolean('cse.webui', 'enable', 				fallback=True),
				'cse.webui.root'					: config.get('cse.webui', 'root', 						fallback='/webui'),


				#
				#	App: Statistics AE
				#
	
				'app.statistics.enable'				: config.getboolean('app.statistics', 'enable', 		fallback=True),
				'app.statistics.aeRN'				: config.get('app.statistics', 'aeRN', 					fallback='statistics'),
				'app.statistics.aeAPI'				: config.get('app.statistics', 'aeAPI', 				fallback='Nstatistics'),
				'app.statistics.fcntRN'				: config.get('app.statistics', 'fcntRN', 				fallback='statistics'),
				'app.statistics.fcntCND'			: config.get('app.statistics', 'fcntCND', 				fallback='acme.statistics'),
				'app.statistics.fcntType'			: config.get('app.statistics', 'fcntType', 				fallback='acme:csest'),
				'app.statistics.originator'			: config.get('app.statistics', 'originator',			fallback='C'),
				'app.statistics.interval'			: config.getint('app.statistics', 'interval', 			fallback=10),		# seconds

				#
				#	App: CSE Node 
				#

				'app.csenode.enable'				: config.getboolean('app.csenode', 'enable', 			fallback=True),
				'app.csenode.nodeRN'				: config.get('app.csenode', 'nodeRN', 					fallback='cse-node'),
				'app.csenode.nodeID'				: config.get('app.csenode', 'nodeID', 					fallback='cse-node'),
				'app.csenode.originator'			: config.get('app.csenode', 'originator',				fallback='CAdmin'),
				'app.csenode.batteryLowLevel'		: config.getint('app.csenode', 'batteryLowLevel',		fallback=20),		# percent
				'app.csenode.batteryChargedLevel'	: config.getint('app.csenode', 'batteryChargedLevel',	fallback=100),		# percent
				'app.csenode.interval'				: config.getint('app.csenode', 'updateInterval', 		fallback=60),		# seconds

			}

		except Exception as e:	# about when findings errors in configuration
			_print(f'[red]Error in configuration file: {argsConfigfile} - {str(e)}')
			return False

		# Read id-mappings
		if  config.has_section('server.http.mappings'):
			Configuration._configuration['server.http.mappings'] = config.items('server.http.mappings')
			#print(config.items('server.http.mappings'))

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
		Configuration._configuration['cse.defaultSerialization'] = ContentSerializationType.to(ct)
		if Configuration._configuration['cse.defaultSerialization'] == ContentSerializationType.UNKNOWN:
			_print(f'[red]Configuration Error: Unsupported \[cse]:defaultSerialization: {ct}')
			return False
		
		# Registrar Serialization
		ct = Configuration._configuration['cse.registrar.serialization']
		Configuration._configuration['cse.registrar.serialization'] = ContentSerializationType.to(ct)
		if Configuration._configuration['cse.registrar.serialization'] == ContentSerializationType.UNKNOWN:
			_print(f'[red]Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}')
			return False

		# Loglevel and various overrides from command line
		logLevel = Configuration._configuration['logging.level'].lower()
		logLevel = (argsLoglevel or logLevel) 	# command line args override config
		if logLevel == 'off':
			Configuration._configuration['logging.enable'] = False
			Configuration._configuration['logging.level'] = logging.DEBUG
		elif logLevel == 'info':
			Configuration._configuration['logging.level'] = logging.INFO
		elif logLevel == 'warn':
			Configuration._configuration['logging.level'] = logging.WARNING
		elif logLevel == 'error':
			Configuration._configuration['logging.level'] = logging.ERROR
		else:
			Configuration._configuration['logging.level'] = logging.DEBUG

		if argsDBReset is True:					Configuration._configuration['db.resetOnStartup'] = True									# Override DB reset from command line
		if argsDBStorageMode is not None:		Configuration._configuration['db.inMemory'] = argsDBStorageMode == 'memory'					# Override DB storage mode from command line
		if argsImportDirectory is not None:		Configuration._configuration['cse.resourcesPath'] = argsImportDirectory						# Override import directory from command line
		if argsAppsEnabled is not None:			Configuration._configuration['cse.enableApplications'] = argsAppsEnabled					# Override app enablement
		if argsRemoteCSEEnabled is not None:	Configuration._configuration['cse.enableRemoteCSE'] = argsRemoteCSEEnabled					# Override remote CSE enablement
		if argsValidationEnabled is not None:	Configuration._configuration['cse.enableValidation'] = argsValidationEnabled				# Override validation enablement
		if argsStatisticsEnabled is not None:	Configuration._configuration['cse.statistics.enable'] = argsStatisticsEnabled				# Override statistics enablement
		if argsRunAsHttps is not None:			Configuration._configuration['cse.security.useTLS'] = argsRunAsHttps						# Override useTLS
		if argsRemoteConfigEnabled is not None:	Configuration._configuration['http.enableRemoteConfiguration'] = argsRemoteConfigEnabled	# Override remote/httpConfiguration
		if argsListenIF is not None:			Configuration._configuration['http.listenIF'] = argsListenIF								# Override binding network interface
		if argsHttpAddress is not None:			Configuration._configuration['http.address'] = argsHttpAddress								# Override server http address

		if argsHeadless is not None and argsHeadless:
			Configuration._configuration['logging.enableScreenLogging'] = False

		# Correct urls
		Configuration._configuration['cse.registrar.address'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.address'])
		Configuration._configuration['http.address'] = Utils.normalizeURL(Configuration._configuration['http.address'])
		Configuration._configuration['http.root'] = Utils.normalizeURL(Configuration._configuration['http.root'])
		Configuration._configuration['cse.registrar.root'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.root'])

		# Just in case: check the URL's
		if Configuration._configuration['cse.security.useTLS']:
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
		if not Configuration._configuration['cse.security.useTLS']:	# clear certificates configuration if not in use
			Configuration._configuration['cse.security.verifyCertificate'] = False
			Configuration._configuration['cse.security.tlsVersion'] = 'auto'
			Configuration._configuration['cse.security.caCertificateFile'] = None
			Configuration._configuration['cse.security.caPrivateKeyFile'] = None
		else:
			if not (val := Configuration._configuration['cse.security.tlsVersion']).lower() in [ 'tls1.1', 'tls1.2', 'auto' ]:
				_print(f'[red]Configuration Error: Unknown value for \[cse.security]:tlsVersion: {val}')
				return False
			if (val := Configuration._configuration['cse.security.caCertificateFile']) is None:
				_print('[red]Configuration Error: \[cse.security]:caCertificateFile must be set when TLS is enabled')
				return False
			if not os.path.exists(val):
				_print(f'[red]Configuration Error: \[cse.security]:caCertificateFile does not exists or is not accessible: {val}')
				return False
			if (val := Configuration._configuration['cse.security.caPrivateKeyFile']) is None:
				_print('[red]Configuration Error: \[cse.security]:caPrivateKeyFile must be set when TLS is enabled')
				return False
			if not os.path.exists(val):
				_print(f'[red]Configuration Error: \[cse.security]:caPrivateKeyFile does not exists or is not accessible: {val}')
				return False

		# check the csi format
		rx = re.compile('^/[^/\s]+') # Must start with a / and must not contain a further / or white space
		if re.fullmatch(rx, (val:=Configuration._configuration['cse.csi'])) is None:
			_print(f'[red]Configuration Error: Wrong format for \[cse]:cseID: {val}')
			return False

		if Configuration._configuration['cse.registrar.address'] is not None and Configuration._configuration['cse.registrar.csi'] is not None:
			if re.fullmatch(rx, (val:=Configuration._configuration['cse.registrar.csi'])) is None:
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
		if len(Configuration._configuration['cse.supportedReleaseVersions']) == 0:
			_print('[red]Configuration Error: \[cse]:supportedReleaseVersions must not be empty')
			return False
		for rv in Configuration._configuration['cse.supportedReleaseVersions']:
			if rv not in C.supportedReleaseVersions:
				_print(f'[red]Configuration Error: \[cse]:supportedReleaseVersions: unsupported version: {rv}')
				return False

		if len(Configuration._configuration['cse.releaseVersion']) == 0:
			_print('[red]Configuration Error: \[cse]:releaseVersion must not be empty')
			return False
		for rv in Configuration._configuration['cse.releaseVersion']:
			srv = Configuration._configuration['cse.supportedReleaseVersions']
			if rv not in srv:
				_print(f'[red]Configuration Error: \[cse]:releaseVersion: {rv} not in \[cse].supportedReleaseVersions: {srv}')
				return False
		
		# Check configured app api
		if len(api := Configuration._configuration['app.statistics.aeAPI']) < 2 or api[0] not in ['R', 'N']:
			_print('[red]Configuration Error: \[app.statistics]:aeAPI must not be empty and must start with "N" or "R"')
			return False

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