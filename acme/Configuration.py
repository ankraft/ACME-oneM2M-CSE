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
from Types import CSEType
from rich.console import Console


class Configuration(object):
	_configuration: Dict[str, Any] = {}

	@staticmethod
	def init(args: argparse.Namespace = None) -> bool:
		global _configuration
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


		# Read and parse the configuration file
		config = configparser.ConfigParser(	interpolation=configparser.ExtendedInterpolation(),
											converters={'list': lambda x: [i.strip() for i in x.split(',')]}	# Convert csv to list
										  )
		try:
			if len(config.read(argsConfigfile)) == 0 and argsConfigfile != C.defaultConfigFile:		# Allow 
				console.print('[red]Configuration file missing or not readable: %s' % argsConfigfile)
				return False
		except configparser.Error as e:
			console.print('[red]Error in configuration file')
			console.print(e)
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
				'logging.enableFileLogging'			: config.getboolean('logging', 'enableFileLogging', 	fallback=True),
				'logging.path'						: config.get('logging', 'path', 						fallback=C.defaultLogDirectory),
				'logging.level'						: config.get('logging', 'level', 						fallback='debug'),
				'logging.size'						: config.getint('logging', 'size', 						fallback=100000),
				'logging.count'						: config.getint('logging', 'count', 					fallback=10),		# Number of log files

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

				#
				#	CSE Security
				#
				'cse.security.enableACPChecks'		: config.getboolean('cse.security', 'enableACPChecks', 	fallback=True),
				'cse.security.adminACPI'			: config.get('cse.security', 'adminACPI', 				fallback='acpAdmin'),
				'cse.security.defaultACPI'			: config.get('cse.security', 'defaultACPI', 			fallback='acpDefault'),
				'cse.security.csebaseAccessACPI'	: config.get('cse.security', 'csebaseAccessACPI', 		fallback='acpCSEBaseAccess'),
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

				#
				#	Registrations
				#

				'cse.registration.allowedAEOriginators'	: config.getlist('cse.registration', 'allowedAEOriginators',	fallback=['C*','S*']),		# type: ignore
				'cse.registration.allowedCSROriginators': config.getlist('cse.registration', 'allowedCSROriginators',	fallback=[]),				# type: ignore


				#
				#	Announcements
				#

				'cse.announcements.enable'			: config.getboolean('cse.announcements', 'enable',		fallback=True),
				'cse.announcements.checkInterval'	: config.getint('cse.announcements', 'checkInterval',	fallback=10),


				#
				#	Statistics
				#

				'cse.statistics.enable'				: config.getboolean('cse.statistics', 'enable', 		fallback=True),
				'cse.statistics.writeIntervall'		: config.getint('cse.statistics', 'writeIntervall',		fallback=60),		# Seconds


				#
				#	Defaults for Container Resources
				#

				'cse.cnt.mni'						: config.getint('cse.resource.cnt', 'mni', 				fallback=10),
				'cse.cnt.mbs'						: config.getint('cse.resource.cnt', 'mbs', 				fallback=10000),

				#
				#	Defaults for Access Control Policies
				#

				'cse.acp.pv.acop'					: config.getint('cse.resource.acp', 'permission', 		fallback=63),
				'cse.acp.pvs.acop'					: config.getint('cse.resource.acp', 'selfPermission', 	fallback=51),
				'cse.acp.addAdminOrignator'			: config.getboolean('cse.resource.acp', 'addAdminOrignator',	fallback=True),


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
				'app.statistics.aeAPI'				: config.get('app.statistics', 'aeAPI', 				fallback='ae-statistics'),
				'app.statistics.fcntRN'				: config.get('app.statistics', 'fcntRN', 				fallback='statistics'),
				'app.statistics.fcntCND'			: config.get('app.statistics', 'fcntCND', 				fallback='acme.statistics'),
				'app.statistics.fcntType'			: config.get('app.statistics', 'fcntType', 				fallback='acme:csest'),
				'app.statistics.originator'			: config.get('app.statistics', 'originator',			fallback='C'),
				'app.statistics.intervall'			: config.getint('app.statistics', 'intervall', 			fallback=10),		# seconds

				#
				#	App: CSE Node 
				#

				'app.csenode.enable'				: config.getboolean('app.csenode', 'enable', 			fallback=True),
				'app.csenode.nodeRN'				: config.get('app.csenode', 'nodeRN', 					fallback='cse-node'),
				'app.csenode.nodeID'				: config.get('app.csenode', 'nodeID', 					fallback='cse-node'),
				'app.csenode.originator'			: config.get('app.csenode', 'originator',				fallback='CAdmin'),
				'app.csenode.batteryLowLevel'		: config.getint('app.csenode', 'batteryLowLevel',		fallback=20),		# percent
				'app.csenode.batteryChargedLevel'	: config.getint('app.csenode', 'batteryChargedLevel',	fallback=100),		# percent
				'app.csenode.intervall'				: config.getint('app.csenode', 'updateIntervall', 		fallback=60),		# seconds

			}

		except Exception as e:	# about when findings errors in configuration
			console.print('[red]Error in configuration file: %s - %s' % (argsConfigfile, str(e)))
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



		# Loglevel from command line
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

		# Override DB reset from command line
		if argsDBReset is True:
			Configuration._configuration['db.resetOnStartup'] = True

		# Override DB storage mode from command line
		if argsDBStorageMode is not None:
			Configuration._configuration['db.inMemory'] = argsDBStorageMode == 'memory'

		# Override import directory from command line
		if argsImportDirectory is not None:
			Configuration._configuration['cse.resourcesPath'] = argsImportDirectory

		# Override app enablement
		if argsAppsEnabled is not None:
			Configuration._configuration['cse.enableApplications'] = argsAppsEnabled

		# Override remote CSE enablement
		if argsRemoteCSEEnabled is not None:
			Configuration._configuration['cse.enableRemoteCSE'] = argsRemoteCSEEnabled

		# Override validation enablement
		if argsValidationEnabled is not None:
			Configuration._configuration['cse.enableValidation'] = argsValidationEnabled

		# Override statistics enablement
		if argsStatisticsEnabled is not None:
			Configuration._configuration['cse.statistics.enable'] = argsStatisticsEnabled

		# Override useTLS
		if argsRunAsHttps is not None:
			Configuration._configuration['cse.security.useTLS'] = argsRunAsHttps

		# Correct urls
		Configuration._configuration['cse.registrar.address'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.address'])
		Configuration._configuration['http.address'] = Utils.normalizeURL(Configuration._configuration['http.address'])
		Configuration._configuration['http.root'] = Utils.normalizeURL(Configuration._configuration['http.root'])
		Configuration._configuration['cse.registrar.root'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.root'])

		# Just in case: check the URL's
		if Configuration._configuration['cse.security.useTLS']:
			if Configuration._configuration['http.address'].startswith('http:'):
				console.print('[orange3]Configuration Warning: Changing "http" to "https" in \[server.http]:address')
				Configuration._configuration['http.address'] = Configuration._configuration['http.address'].replace('http:', 'https:')
			# registrar might still be accessible vi another protocol
			# if Configuration._configuration['cse.registrar.address'].startswith('http:'):
			# 	console.print('[orange3]Configuration Warning: Changing "http" to "https" in \[cse.registrar]:address')
			# 	Configuration._configuration['cse.registrar.address'] = Configuration._configuration['cse.registrar.address'].replace('http:', 'https:')
		else: 
			if Configuration._configuration['http.address'].startswith('https:'):
				console.print('[orange3]Configuration Warning: Changing "https" to "http" in \[server.http]:address')
				Configuration._configuration['http.address'] = Configuration._configuration['http.address'].replace('https:', 'http:')
			# registrar might still be accessible vi another protocol
			# if Configuration._configuration['cse.registrar.address'].startswith('https:'):
			# 	console.print('[orange3]Configuration Warning: Changing "https" to "http" in \[cse.registrar]:address')
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
				console.print('[red]Configuration Error: Unknown value for \[cse.security]:tlsVersion: %s' % val)
				return False
			if (val := Configuration._configuration['cse.security.caCertificateFile']) is None:
				console.print('[red]Configuration Error: \[cse.security]:caCertificateFile must be set when TLS is enabled')
				return False
			if not os.path.exists(val):
				console.print('[red]Configuration Error: \[cse.security]:caCertificateFile does not exists or is not accessible: %s' % val)
				return False
			if (val := Configuration._configuration['cse.security.caPrivateKeyFile']) is None:
				console.print('[red]Configuration Error: \[cse.security]:caPrivateKeyFile must be set when TLS is enabled')
				return False
			if not os.path.exists(val):
				console.print('[red]Configuration Error: \[cse.security]:caPrivateKeyFile does not exists or is not accessible: %s' % val)
				return False

		# check the csi format
		rx = re.compile('^/[^/\s]+') # Must start with a / and must not contain a further / or white space
		if re.fullmatch(rx, (val:=Configuration._configuration['cse.csi'])) is None:
			console.print('[red]Configuration Error: Wrong format for \[cse]:cseID: %s' % val)
			return False

		if Configuration._configuration['cse.registrar.address'] is not None and Configuration._configuration['cse.registrar.csi'] is not None:
			if re.fullmatch(rx, (val:=Configuration._configuration['cse.registrar.csi'])) is None:
				console.print('[red]Configuration Error: Wrong format for \[cse.registrar]:cseID: %s' % val)
				return False
			if len(Configuration._configuration['cse.registrar.csi']) > 0 and len(Configuration._configuration['cse.registrar.rn']) == 0:
				console.print('[red]Configuration Error: Missing configuration [cse.registrar]:resourceName')
				return False


		# Everything is fine
		return True


	@staticmethod
	def print() -> str:
		result = 'Configuration:\n'
		for kv in Configuration._configuration.items():
			result += '  %s = %s\n' % kv
		return result


	@staticmethod
	def all() -> Dict[str, Any]:
		return Configuration._configuration


	@staticmethod
	def get(key: str) -> Any:
		if not Configuration.has(key):
			return None
		return Configuration._configuration[key]


	@staticmethod
	def set(key: str, value: Any) -> None:
		Configuration._configuration[key] = value


	@staticmethod
	def has(key: str) -> bool:
		return key in Configuration._configuration