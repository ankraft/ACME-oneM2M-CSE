#
#	Configuration.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing CSE configurations
#


import configparser, argparse, os, os.path, pathlib, ipaddress, re
from datetime import datetime

from typing import Any, Dict, Tuple, List
from InquirerPy.utils import InquirerPySessionResult
from rich.console import Console
from InquirerPy import prompt, inquirer
import isodate

from ..etc.Constants import Constants as C
from ..etc.Types import CSEType, ContentSerializationType, Permission


class Configuration(object):
	"""	The static class Configuration holds all the configuration values of the CSE. It is initialized only once by calling the static
		method init(). Access to configuration valus is done by calling Configuration.get(<key>).
	"""
	_configuration: Dict[str, Any] = {}

	_defaultConfigFile:str 			= None

	_argsConfigfile:str 			= None
	_argsLoglevel:str				= None
	_argsDBReset:bool				= None
	_argsDBStorageMode:str			= None
	_argsHeadless:bool				= None
	_argsHttpAddress:str			= None
	_argsHttpPort:int				= None
	_argsImportDirectory:str		= None
	_argsListenIF:str				= None
	_argsMqttEnabled:bool			= None
	_argsRemoteCSEEnabled:bool		= None
	_argsRunAsHttps:bool			= None
	_argsStatisticsEnabled:bool		= None


	# Internal print function that takes the headless setting into account
	@staticmethod
	def _print(msg:str) -> None:
		if not Configuration._argsHeadless:
			Console().print(msg)	# Print error message to console


	@staticmethod
	def init(args:argparse.Namespace = None) -> bool:

		# The default ini file
		Configuration._defaultConfigFile		= f'{pathlib.Path.cwd()}{os.sep}{C.defaultConfigFile}'

		# resolve the args, of any
		Configuration._argsConfigfile			= args.configfile if args and 'configfile' in args else C.defaultUserConfigFile
		Configuration._argsLoglevel				= args.loglevel if args and 'loglevel' in args else None
		Configuration._argsDBReset				= args.dbreset if args and 'dbreset' in args else False
		Configuration._argsDBStorageMode		= args.dbstoragemode if args and 'dbstoragemode' in args else None
		Configuration._argsHeadless				= args.headless if args and 'headless' in args else False
		Configuration._argsHttpAddress			= args.httpaddress if args and 'httpaddress' in args else None
		Configuration._argsHttpPort				= args.httpport if args and 'httpport' in args else None
		Configuration._argsImportDirectory		= args.importdirectory if args and 'importdirectory' in args else None
		Configuration._argsListenIF				= args.listenif if args and 'listenif' in args else None
		Configuration._argsMqttEnabled			= args.mqttenabled if args and 'mqttenabled' in args else None
		Configuration._argsRemoteCSEEnabled		= args.remotecseenabled if args and 'remotecseenabled' in args else None
		Configuration._argsRunAsHttps			= args.https if args and 'https' in args else None
		Configuration._argsStatisticsEnabled	= args.statisticsenabled if args and 'statisticsenabled' in args else None


		# Create user config file if doesn't exist
		if not os.path.exists(Configuration._argsConfigfile):
			try:
				if not Configuration._buildUserConfigFile(Configuration._argsConfigfile):
					return False
			except Exception as e:
				print(e)
				raise e


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
			if len(config.read( [Configuration._defaultConfigFile, Configuration._argsConfigfile])) == 0 and Configuration._argsConfigfile != C.defaultUserConfigFile:		# Allow 
				Configuration._print(f'[red]Configuration file missing or not readable: {Configuration._argsConfigfile}')
				return False
		except configparser.Error as e:
			Configuration._print('[red]Error in configuration file')
			Configuration._print(str(e))
			return False

		#
		#	Retrieve configuration values
		#

		try:
			Configuration._configuration = {
				'configfile'							: Configuration._argsConfigfile,
				'packageDirectory'						: pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent,	# points to the acme package directory


				#
				#	CSE
				#

				'cse.type'								: config.get('cse', 'type',											fallback = 'IN'),		# IN, MN, ASN
				'cse.spid'								: config.get('cse', 'serviceProviderID',							fallback = 'acme.example.com'),
				'cse.csi'								: config.get('cse', 'cseID',										fallback = '/id-in'),
				'cse.ri'								: config.get('cse', 'resourceID',									fallback = 'id-in'),
				'cse.rn'								: config.get('cse', 'resourceName',									fallback = 'cse-in'),
				'cse.resourcesPath'						: config.get('cse', 'resourcesPath', 								fallback = './init'),
				'cse.expirationDelta'					: config.getint('cse', 'expirationDelta', 							fallback = 60*60*24*365),	# 1 year, in seconds
				'cse.maxExpirationDelta'				: config.getint('cse', 'maxExpirationDelta',						fallback = 60*60*24*365*5),	# 5 years, in seconds
				'cse.requestExpirationDelta'			: config.getfloat('cse', 'requestExpirationDelta',					fallback = 10.0),	# 10 seconds
				'cse.originator'						: config.get('cse', 'originator',									fallback = 'CAdmin'),
				'cse.enableRemoteCSE'					: config.getboolean('cse', 'enableRemoteCSE', 						fallback = True),
				'cse.sortDiscoveredResources'			: config.getboolean('cse', 'sortDiscoveredResources',				fallback = True),
				'cse.checkExpirationsInterval'			: config.getint('cse', 'checkExpirationsInterval',					fallback = 60),		# Seconds
				'cse.flexBlockingPreference'			: config.get('cse', 'flexBlockingPreference',						fallback = 'blocking'),
				'cse.supportedReleaseVersions'			: config.getlist('cse', 'supportedReleaseVersions',					fallback = ['2a', '3', '4']), # type: ignore [attr-defined]
				'cse.releaseVersion'					: config.get('cse', 'releaseVersion',								fallback = '3'),
				'cse.defaultSerialization'				: config.get('cse', 'defaultSerialization',							fallback = 'json'),

				#
				#	CSE Security
				#

				'cse.security.enableACPChecks'			: config.getboolean('cse.security', 'enableACPChecks',			 	fallback = True),
				'cse.security.fullAccessAdmin'			: config.getboolean('cse.security', 'fullAccessAdmin',			 	fallback = True),

				#
				#	CSE Operation
				#

				'cse.operation.jobBalanceTarget'		: config.getfloat('cse.operation', 'jobBalanceTarget',			 	fallback = 3.0),
				'cse.operation.jobBalanceLatency'		: config.getint('cse.operation', 'jobBalanceLatency', 				fallback = 1000),
				'cse.operation.jobBalanceReduceFactor'	: config.getfloat('cse.operation', 'jobBalanceReduceFactor', 		fallback = 2.0),

				#
				#	HTTP Server
				#

				'http.listenIF'							: config.get('server.http', 'listenIF', 							fallback = '127.0.0.1'),
				'http.port' 							: config.getint('server.http', 'port', 								fallback = 8080),
				'http.root'								: config.get('server.http', 'root', 								fallback = ''),
				'http.address'							: config.get('server.http', 'address', 								fallback = 'http://127.0.0.1:8080'),
				'http.enableStructureEndpoint'			: config.getboolean('server.http', 'enableStructureEndpoint', 		fallback = False),
				'http.enableUpperTesterEndpoint'		: config.getboolean('server.http', 'enableUpperTesterEndpoint', 	fallback = False),
				'http.allowPatchForDelete'				: config.getboolean('server.http', 'allowPatchForDelete', 			fallback = False),

				#
				#	HTTP Server Security
				#

				'http.security.useTLS'					: config.getboolean('server.http.security', 'useTLS', 				fallback = False),
				'http.security.tlsVersion'				: config.get('server.http.security', 'tlsVersion', 					fallback = 'auto'),
				'http.security.verifyCertificate'		: config.getboolean('server.http.security', 'verifyCertificate',	fallback = False),
				'http.security.caCertificateFile'		: config.get('server.http.security', 'caCertificateFile', 			fallback = None),
				'http.security.caPrivateKeyFile'		: config.get('server.http.security', 'caPrivateKeyFile', 			fallback = None),

				#
				#	MQTT Client
				#

				'mqtt.enable'							: config.getboolean('client.mqtt', 'enable', 						fallback = False),
				'mqtt.address'							: config.get('client.mqtt', 'address', 								fallback = '127.0.0.1'),
				'mqtt.port' 							: config.getint('client.mqtt', 'port', 								fallback = None),	# Default will be determined later (s.b.)
				'mqtt.keepalive' 						: config.getint('client.mqtt', 'keepalive',							fallback = 60),
				'mqtt.listenIF' 						: config.get('client.mqtt', 'listenIF',								fallback = '127.0.0.1'),
				'mqtt.topicPrefix' 						: config.get('client.mqtt', 'topicPrefix',							fallback = ''),
				'mqtt.timeout' 							: config.getfloat('client.mqtt', 'timeout',							fallback = 5.0),

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

				'db.path'								: config.get('database', 'path', 									fallback = './data'),
				'db.inMemory'							: config.getboolean('database', 'inMemory', 						fallback = False),
				'db.cacheSize'							: config.getint('database', 'cacheSize', 							fallback = 0),		# Default: no caching
				'db.resetOnStartup' 					: config.getboolean('database', 'resetOnStartup',					fallback = False),

				#
				#	Logging
				#

				'logging.enableFileLogging'				: config.getboolean('logging', 'enableFileLogging', 				fallback = False),
				'logging.enableScreenLogging'			: config.getboolean('logging', 'enableScreenLogging', 				fallback = True),
				'logging.path'							: config.get('logging', 'path', 									fallback = './logs'),
				'logging.level'							: config.get('logging', 'level', 									fallback = 'debug'),
				'logging.size'							: config.getint('logging', 'size', 									fallback = 100000),
				'logging.count'							: config.getint('logging', 'count', 								fallback = 10),		# Number of log files
				'logging.stackTraceOnError'				: config.getboolean('logging', 'stackTraceOnError',					fallback = True),
				'logging.enableBindingsLogging'			: config.getboolean('logging', 'enableBindingsLogging',				fallback = False),
				'logging.queueSize'						: config.getint('logging', 'queueSize', 							fallback = 5000),	# Size of the log queue

				#
				#	Registrar CSE
				#

				'cse.registrar.address'					: config.get('cse.registrar', 'address', 							fallback = None),
				'cse.registrar.root'					: config.get('cse.registrar', 'root', 								fallback = ''),
				'cse.registrar.csi'						: config.get('cse.registrar', 'cseID', 								fallback = None),
				'cse.registrar.rn'						: config.get('cse.registrar', 'resourceName', 						fallback = None),
				'cse.registrar.checkInterval'			: config.getint('cse.registrar', 'checkInterval', 					fallback = 30),		# Seconds
				'cse.registrar.excludeCSRAttributes'	: config.getlist('cse.registrar', 'excludeCSRAttributes',			fallback = []),		# type: ignore [attr-defined]
				'cse.registrar.serialization'			: config.get('cse.registrar', 'serialization',						fallback = 'json'),

				#
				#	Registrations
				#

				'cse.registration.allowedAEOriginators'		: config.getlist('cse.registration', 'allowedAEOriginators',	fallback = ['C*','S*']),		# type: ignore [attr-defined]
				'cse.registration.allowedCSROriginators'	: config.getlist('cse.registration', 'allowedCSROriginators',	fallback = []),				# type: ignore [attr-defined]
				'cse.registration.checkLiveliness'			: config.getboolean('cse.registration', 'checkLiveliness',		fallback = True),


				#
				#	Announcements
				#

				'cse.announcements.checkInterval'		: config.getint('cse.announcements', 'checkInterval',				fallback = 10),


				#
				#	Statistics
				#

				'cse.statistics.enable'					: config.getboolean('cse.statistics', 'enable', 					fallback = True),
				'cse.statistics.writeInterval'			: config.getint('cse.statistics', 'writeInterval',					fallback = 60),		# Seconds


				#
				#	Defaults for Access Control Policies
				#

				'cse.acp.pv.acop'						: config.getint('cse.resource.acp', 'permission', 					fallback = Permission.ALL),
				'cse.acp.pvs.acop'						: config.getint('cse.resource.acp', 'selfPermission', 				fallback = Permission.DISCOVERY+Permission.NOTIFY+Permission.CREATE+Permission.RETRIEVE),


				#
				#	Defaults for Container Resources
				#

				'cse.cnt.enableLimits'					: config.getboolean('cse.resource.cnt', 'enableLimits', 			fallback = False),
				'cse.cnt.mni'							: config.getint('cse.resource.cnt', 'mni', 							fallback = 10),
				'cse.cnt.mbs'							: config.getint('cse.resource.cnt', 'mbs', 							fallback = 10000),


				#
				#	Defaults for Request Resources
				#

				'cse.req.minet'							: config.getint('cse.resource.req', 'minimumExpirationTime', 		fallback = 60),
				'cse.req.maxet'							: config.getint('cse.resource.req', 'maximumExpirationTime', 		fallback = 180),


				#
				#	Defaults for Subscription Resources
				#

				'cse.sub.dur'							: config.getint('cse.resource.sub', 'batchNotifyDuration', 			fallback = 60),	# seconds


				#
				#	Defaults for timeSeries Resources
				#

				'cse.ts.enableLimits'					: config.getboolean('cse.resource.ts', 'enableLimits',				fallback = False),
				'cse.ts.mni'							: config.getint('cse.resource.ts', 'mni', 							fallback = 10),
				'cse.ts.mbs'							: config.getint('cse.resource.ts', 'mbs', 							fallback = 10000),
				'cse.ts.mdn'							: config.getint('cse.resource.ts', 'mdn', 							fallback = 10),


				#
				#	Defaults for TimeSyncBeacon Resources
				#

				'cse.tsb.bcni'							: config.get('cse.resource.tsb', 'bcni', 							fallback = 'PT1H'),	# duration
				'cse.tsb.bcnt'							: config.getfloat('cse.resource.tsb', 'bcnt', 						fallback = 60.0),	# seconds


				#
				#	Web UI
				#

				'cse.webui.enable'						: config.getboolean('cse.webui', 'enable', 							fallback = True),
				'cse.webui.root'						: config.get('cse.webui', 'root', 									fallback = '/webui'),


				#
				#	Console
				#

				'cse.console.refreshInterval'			: config.getfloat('cse.console', 'refreshInterval', 				fallback = 2.0),
				'cse.console.hideResources'				: config.getlist('cse.console', 'hideResources', 					fallback = []),		# type: ignore[attr-defined]
				'cse.console.treeMode'					: config.get('cse.console', 'treeMode', 							fallback = 'normal'),
				'cse.console.treeIncludeVirtualResources': config.getboolean('cse.console', 'treeIncludeVirtualResources',	fallback = False),
				'cse.console.confirmQuit'				: config.getboolean('cse.console', 'confirmQuit', 					fallback = False),
				'cse.console.theme'						: config.get('cse.console', 'theme', 								fallback = 'dark'),

				#
				#	Scripting
				#

				'cse.scripting.scriptDirectories'		: config.getlist('cse.scripting', 'scriptDirectories',				fallback = []),	# type: ignore[attr-defined]
				'cse.scripting.verbose'					: config.getboolean('cse.scripting', 'verbose', 					fallback = False),
				'cse.scripting.fileMonitoringInterval'	: config.getfloat('cse.scripting', 'fileMonitoringInterval',		fallback = 2.0),

			}

		except configparser.InterpolationMissingOptionError as e:
			Configuration._print(f'[red]Error in configuration file: {Configuration._argsConfigfile}\n{str(e)}')
			Configuration._print('\n[red]Please check the section [bold](basic.config)[/bold] in the configuration file.\n')
			return False

		except Exception as e:	# about when findings errors in configuration
			Configuration._print(f'[red]Error in configuration file: {Configuration._argsConfigfile}\n{str(e)}')
			return False

		# Read id-mappings
		if  config.has_section('server.http.mappings'):
			Configuration._configuration['server.http.mappings'] = config.items('server.http.mappings')
			# print(config.items('server.http.mappings'))
		
		if not (v := Configuration.validate())[0]:
			Configuration._print(f'[red]{v[1]}')
		return v[0]


	@staticmethod
	def validate() -> Tuple[bool, str]:
		# Some clean-ups and overrides

		from ..etc import Utils as Utils	# cannot import at the top because of circel import

		# CSE type
		if isinstance(cseType := Configuration._configuration['cse.type'], str):
			cseType = cseType.lower()
			if  cseType == 'asn':
				Configuration._configuration['cse.type'] = CSEType.ASN
			elif cseType == 'mn':
				Configuration._configuration['cse.type'] = CSEType.MN
			else:
				Configuration._configuration['cse.type'] = CSEType.IN

		# CSE Serialization
		if isinstance(ct := Configuration._configuration['cse.defaultSerialization'], str):
			Configuration._configuration['cse.defaultSerialization'] = ContentSerializationType.toContentSerialization(ct)
			if Configuration._configuration['cse.defaultSerialization'] == ContentSerializationType.UNKNOWN:
				return False, f'Configuration Error: Unsupported \[cse]:defaultSerialization: {ct}'
		
		# Registrar Serialization
		if isinstance(ct := Configuration._configuration['cse.registrar.serialization'], str):
			Configuration._configuration['cse.registrar.serialization'] = ContentSerializationType.toContentSerialization(ct)
			if Configuration._configuration['cse.registrar.serialization'] == ContentSerializationType.UNKNOWN:
				return False, f'Configuration Error: Unsupported \[cse.registrar]:serialization: {ct}'

		# Loglevel and various overrides from command line
		from ..services.Logging import LogLevel
		if isinstance(logLevel := Configuration._configuration['logging.level'], str):	
			logLevel = logLevel.lower()
			logLevel = (Configuration._argsLoglevel or logLevel) 	# command line args override config
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
		
		# Test for correct logging queue size
		if (queueSize := Configuration._configuration['logging.queueSize']) < 0:
			return False, f'Configuration Error: \[logging]:queueSize must be 0 or greater'


		if Configuration._argsDBReset is True:					Configuration._configuration['db.resetOnStartup'] = True									# Override DB reset from command line
		if Configuration._argsDBStorageMode is not None:		Configuration._configuration['db.inMemory'] = Configuration._argsDBStorageMode == 'memory'					# Override DB storage mode from command line
		if Configuration._argsHttpAddress is not None:			Configuration._configuration['http.address'] = Configuration._argsHttpAddress								# Override server http address
		if Configuration._argsHttpPort is not None:				Configuration._configuration['http.port'] = Configuration._argsHttpPort									# Override server http port
		if Configuration._argsImportDirectory is not None:		Configuration._configuration['cse.resourcesPath'] = Configuration._argsImportDirectory						# Override import directory from command line
		if Configuration._argsListenIF is not None:				Configuration._configuration['http.listenIF'] = Configuration._argsListenIF								# Override binding network interface
		if Configuration._argsMqttEnabled is not None:			Configuration._configuration['mqtt.enable'] = Configuration._argsMqttEnabled								# Override mqtt enable
		if Configuration._argsRemoteCSEEnabled is not None:		Configuration._configuration['cse.enableRemoteCSE'] = Configuration._argsRemoteCSEEnabled					# Override remote CSE enablement
		if Configuration._argsRunAsHttps is not None:			Configuration._configuration['http.security.useTLS'] = Configuration._argsRunAsHttps						# Override useTLS
		if Configuration._argsStatisticsEnabled is not None:	Configuration._configuration['cse.statistics.enable'] = Configuration._argsStatisticsEnabled				# Override statistics enablement

		if Configuration._argsHeadless:
			Configuration._configuration['logging.enableScreenLogging'] = False

		# Correct urls
		Configuration._configuration['cse.registrar.address'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.address'])
		Configuration._configuration['http.address'] = Utils.normalizeURL(Configuration._configuration['http.address'])
		Configuration._configuration['http.root'] = Utils.normalizeURL(Configuration._configuration['http.root'])
		Configuration._configuration['cse.registrar.root'] = Utils.normalizeURL(Configuration._configuration['cse.registrar.root'])

		# Just in case: check the URL's
		if Configuration._configuration['http.security.useTLS']:
			if Configuration._configuration['http.address'].startswith('http:'):
				Configuration._print('[orange3]Configuration Warning: Changing "http" to "https" in \[server.http]:address')
				Configuration._configuration['http.address'] = Configuration._configuration['http.address'].replace('http:', 'https:')
			# registrar might still be accessible vi another protocol
			# if Configuration._configuration['cse.registrar.address'].startswith('http:'):
			# 	_print('[orange3]Configuration Warning: Changing "http" to "https" in \[cse.registrar]:address')
			# 	Configuration._configuration['cse.registrar.address'] = Configuration._configuration['cse.registrar.address'].replace('http:', 'https:')
		else: 
			if Configuration._configuration['http.address'].startswith('https:'):
				Configuration._print('[orange3]Configuration Warning: Changing "https" to "http" in \[server.http]:address')
				Configuration._configuration['http.address'] = Configuration._configuration['http.address'].replace('https:', 'http:')
			# registrar might still be accessible vi another protocol
			# if Configuration._configuration['cse.registrar.address'].startswith('https:'):
			# 	_print('[orange3]Configuration Warning: Changing "https" to "http" in \[cse.registrar]:address')
			# 	Configuration._configuration['cse.registrar.address'] = Configuration._configuration['cse.registrar.address'].replace('https:', 'http:')


		# Operation
		if Configuration._configuration['cse.operation.jobBalanceTarget'] <= 0.0:
			return False, f'Configuration Error: \[cse.operation]:jobBalanceTarget must be > 0.0'
		if Configuration._configuration['cse.operation.jobBalanceLatency'] < 0:
			return False, f'Configuration Error: \[cse.operation]:jobBalanceLatency must be >= 0'
		if Configuration._configuration['cse.operation.jobBalanceReduceFactor'] < 1.0:
			return False, f'Configuration Error: \[cse.operation]:jobBalanceReduceFactor must be >= 1.0'


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
				return False, f'Configuration Error: Unknown value for \[http.security]:tlsVersion: {val}'
			if not (val := Configuration._configuration['http.security.caCertificateFile']):
				return False, 'Configuration Error: \[http.security]:caCertificateFile must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, f'Configuration Error: \[http.security]:caCertificateFile does not exists or is not accessible: {val}'
			if not (val := Configuration._configuration['http.security.caPrivateKeyFile']):
				return False, 'Configuration Error: \[http.security]:caPrivateKeyFile must be set when TLS is enabled'
			if not os.path.exists(val):
				return False, f'Configuration Error: \[http.security]:caPrivateKeyFile does not exists or is not accessible: {val}'
		
		#
		#	MQTT client
		#
		if not Configuration._configuration['mqtt.port']:	# set the default port depending on whether to use TLS
			Configuration._configuration['mqtt.port'] = 8883 if Configuration._configuration['mqtt.security.useTLS'] else 1883
		if not (Configuration._configuration['mqtt.security.username']) != (not Configuration._configuration['mqtt.security.password']):
			return False, f'Configuration Error: Username or password missing for \[mqtt.security]]'
		# remove empty cid from the list
		Configuration._configuration['mqtt.security.allowedCredentialIDs'] = [ cid for cid in Configuration._configuration['mqtt.security.allowedCredentialIDs'] if len(cid) ]
		

		# check the csi format
		if not Utils.isValidCSI(val:=Configuration._configuration['cse.csi']):
			return False, f'Configuration Error: Wrong format for \[cse]:cseID: {val}'

		if Configuration._configuration['cse.registrar.address'] and Configuration._configuration['cse.registrar.csi']:
			if not Utils.isValidCSI(val:=Configuration._configuration['cse.registrar.csi']):
				return False, f'Configuration Error: Wrong format for \[cse.registrar]:cseID: {val}'
			if len(Configuration._configuration['cse.registrar.csi']) > 0 and len(Configuration._configuration['cse.registrar.rn']) == 0:
				return False, 'Configuration Error: Missing configuration \[cse.registrar]:resourceName'

		# Check default subscription duration
		if Configuration._configuration['cse.sub.dur'] < 1:
			return False, 'Configuration Error: \[cse.resource.sub]:batchNotifyDuration must be > 0'

		# Check flexBlocking value
		Configuration._configuration['cse.flexBlockingPreference'] = Configuration._configuration['cse.flexBlockingPreference'].lower()
		if Configuration._configuration['cse.flexBlockingPreference'] not in ['blocking', 'nonblocking']:
			return False, 'Configuration Error: \[cse]:flexBlockingPreference must be "blocking" or "nonblocking"'

		# Check release versions
		if len(srv := Configuration._configuration['cse.supportedReleaseVersions']) == 0:
			return False, 'Configuration Error: \[cse]:supportedReleaseVersions must not be empty'
		if len(rvi := Configuration._configuration['cse.releaseVersion']) == 0:
			return False, 'Configuration Error: \[cse]:releaseVersion must not be empty'
		if rvi not in srv:
			return False, f'Configuration Error: \[cse]:releaseVersion: {rvi} not in \[cse].supportedReleaseVersions: {srv}'
		# if any([s for s in srv if str(rvi) < s]):
		#	return False, f'Configuration Error: \[cse]:releaseVersion: {rvi} less than highest value in \[cse].supportedReleaseVersions: {srv}. Either increase the [i]releaseVersion[/i] or reduce the set of [i]supportedReleaseVersions[/i].'

		# Check various intervals
		if Configuration._configuration['cse.checkExpirationsInterval'] <= 0:
			return False, 'Configuration Error: \[cse]:checkExpirationsInterval must be greater than 0'
		if Configuration._configuration['cse.console.refreshInterval'] <= 0.0:
			return False, 'Configuration Error: \[cse.console]:refreshInterval must be greater than 0.0'

		# Console settings
		from ..services.Console import TreeMode
		if isinstance(tm := Configuration._configuration['cse.console.treeMode'], str):
			if not (treeMode := TreeMode.to(tm)):
				return False, f'Configuration Error: \[cse.console]:treeMode must be one of {TreeMode.names()}'
			Configuration._configuration['cse.console.treeMode'] = treeMode
		
		Configuration._configuration['cse.console.theme'] = (theme := Configuration._configuration['cse.console.theme'].lower())
		if theme not in [ 'dark', 'light' ]:
			return False, f'Configuration Error: \[cse.console]:theme must be "light" or "dark"'


		# Script settings
		if Configuration._configuration['cse.scripting.fileMonitoringInterval'] < 0.0:
			return False, f'Configuration Error: \[cse.scripting]:fileMonitoringInterval must be >= 0.0'
		if (scriptDirs := Configuration._configuration['cse.scripting.scriptDirectories']):
			lst = []
			for each in scriptDirs:
				if not each:
					continue
				if not os.path.isdir(each):
					return False, f'Configuration Error: \[cse.scripting]:scriptDirectory : directory "{each}" does not exist, is not a directory or is not accessible'
				lst.append(each)
			Configuration._configuration['cse.scripting.scriptDirectories'] = lst
			

		# TimeSyncBeacon defaults
		bcni = Configuration._configuration['cse.tsb.bcni']
		try:
			isodate.parse_duration(bcni)
		except Exception as e:
			return False, f'Configuration Error: \[cse.resource.tsb]:bcni : configuration value must be an ISO8601 duration'
		
		# Everything is fine
		return True, None


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
		return Configuration._configuration.get(key)


	@staticmethod
	def update(key:str, value:Any) -> str:
		""" Update a configuration value and inform other components via an event.

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
				return r[1].replace('\[', '[')	# unescape "\[" in error messages

			from ..services import CSE
			CSE.event.configUpdate(key, value)		# type:ignore [attr-defined]
		else:
			return f'Invalid value for key: {key}'
		return None


	@staticmethod
	def has(key:str) -> bool:
		"""	Check whether a configuration setting exsists.
		"""
		return key in Configuration._configuration


	##########################################################################
	#
	#	Interactively create a new basic configuration file
	#

	iniValues = {
		'IN' : { 
			'cseID': 'id-in',
			'cseName': 'cse-in',
			'adminID': 'CAdmin',
			'dataDirectory': '${baseDirectory}',
			'networkInterface': '127.0.0.1',
			'cseHost': '127.0.0.1',
			'httpPort': '8080',
			'logLevel': 'debug',
			'databaseInMemory': 'False',
		},
		'MN' : { 
			'cseID': 'id-mn',
			'cseName': 'cse-mn',
			'adminID': 'CAdmin',
			'dataDirectory': '${baseDirectory}',
			'networkInterface': '127.0.0.1',
			'cseHost': '127.0.0.1',
			'httpPort': '8081',
			'logLevel': 'debug',
			'databaseInMemory': 'False',
			'registrarCseHost': '127.0.0.1',
			'registrarCsePort': '8080',
			'registrarCseID': 'id-in',
			'registrarCseName': 'cse-in',

		},
		'ASN' : { 
			'cseID': 'id-asn',
			'cseName': 'cse-asn',
			'adminID': 'CAdmin',
			'dataDirectory': '${baseDirectory}',
			'networkInterface': '127.0.0.1',
			'cseHost': '127.0.0.1',
			'httpPort': '8082',
			'logLevel': 'debug',
			'databaseInMemory': 'False',
			'registrarCseHost': '127.0.0.1',
			'registrarCsePort': '8081',
			'registrarCseID': 'id-mn',
			'registrarCseName': 'cse-mn',
		}		
	}


	@staticmethod
	def _buildUserConfigFile(configFile:str) -> bool:
		from ..etc import Utils

		cseType = 'IN'
		cseEnvironment = 'Development'

		def _isValidateIpAddress(ip:str) -> bool:
			try:
				ipaddress.ip_address(ip)
			except Exception:
				return False
			return True
		

		def _isValidateHostname(hostname:str) -> bool:
			if len(hostname) > 255:
				return False
			if hostname[-1] == '.':
				hostname = hostname[:-1] # strip exactly one dot from the right, if present
			allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
			return all(allowed.match(x) for x in hostname.split("."))


		def _isValidPort(port:str) -> bool:
			try:
				_port = int(port)
			except ValueError:
				return False
			return 0 < _port <= 65535


		def basicConfig() -> InquirerPySessionResult:
			Configuration._print('\n[b]Basic configuration\n')
			return prompt(
				[
					{	'type': 'input',
						'message': 'CSE-ID:',
						'long_instruction': 'The CSE-ID of the CSE and the resource ID of the CSEBase.',
						'default': Configuration.iniValues[cseType]['cseID'],
						'validate': lambda result: Utils.isValidID(result),
						'name': 'cseID',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Name of the CSE:',
						'long_instruction': 'This is the resource name of the CSEBase.',
						'default': Configuration.iniValues[cseType]['cseName'],
						'validate': lambda result: Utils.isValidID(result),
						'name': 'cseName',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Admin Originator:',
						'long_instruction': 'The originator who has admin access rights to the CSE and the CSE\'s resources.',
						'default': Configuration.iniValues[cseType]['adminID'],
						'validate': lambda result: Utils.isValidID(result),
						'name': 'adminID',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Data root directory:',
						'long_instruction': 'The directory under which the "data", "init" and "log" directories are located.',
						'default': Configuration.iniValues[cseType]['dataDirectory'],
						'name': 'dataDirectory',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Network interface to bind to (IP address):',
						'long_instruction': 'The network interface to listen for requests. Use "0.0.0.0" for all interfaces.',
						'validate': _isValidateIpAddress,
						'default': Configuration.iniValues[cseType]['networkInterface'],
						'name': 'networkInterface',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'CSE host address (IP address or host name):',
						'long_instruction': 'IP address or host name at which the CSE is reachable for requests.',
						'validate': lambda result: _isValidateIpAddress(result) or _isValidateHostname(result),
						'default': Configuration.iniValues[cseType]['cseHost'],
						'name': 'cseHost',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'CSE host http port:',
						'long_instruction': 'TCP port at which the CSE is reachable for requests.',
						'validate': _isValidPort,
						'default': Configuration.iniValues[cseType]['httpPort'],
						'name': 'httpPort',
						'amark': '✓',
					},
					{	'type': 'rawlist',
						'message': 'Log level:',
						'long_instruction': 'Set the logging verbosity',
						"choices": lambda _: [ 'debug', 'info', 'warning', 'error', 'off' ],
						'default': 1 if cseEnvironment == 'Development' else 3,
						'name': 'logLevel',
						'amark': '✓',
					},
					{	'type': 'rawlist',
						'message': 'Database location:',
						'long_instruction': 'Store data in memory (volatile) or on disk (persistent).',
						"choices": lambda _: [ 'memory', 'disk' ],
						'default': 1 if cseEnvironment == 'Development' else 2,
						"filter": lambda result: str(result == 'memory'),
						'name': 'databaseInMemory',
						'amark': '✓',
					},
				],
			)


		def registrarConfig() -> InquirerPySessionResult:
			Configuration._print('\n[b]Registrar configuration\n')
			return prompt(
				[
					{	'type': 'input',
						'message': 'Registrar CSE-ID:',
						'long_instruction': 'The CSE-ID of the remote (registrar) CSE.',
						'default': Configuration.iniValues[cseType]['registrarCseID'],
						'validate': lambda result: Utils.isValidID(result),
						'name': 'registrarCseID',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Name of the Registrar CSE:',
						'long_instruction': 'The resource name of the remote (registrar) CSE.',
						'default': Configuration.iniValues[cseType]['registrarCseName'],
						'validate': lambda result: Utils.isValidID(result),
						'name': 'registrarCseName',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Registrar CSE IP address / host name:',
						'long_instruction': 'The IP address or host name of the remote (registrar) CSE.',
						'default': Configuration.iniValues[cseType]['registrarCseHost'],
						'validate': lambda result: _isValidateIpAddress(result) or _isValidateHostname(result),
						'name': 'registrarCseHost',
						'amark': '✓',
					},
					{	'type': 'input',
						'message': 'Registrar CSE host http port:',
						'long_instruction': 'The TCP port of the remote (registrar) CSE.',
						'validate': _isValidPort,
						'default': Configuration.iniValues[cseType]['registrarCsePort'],
						'name': 'registrarCsePort',
						'amark': '✓',
					},
				]
			)

		Console().clear()
		cnf:List[str] = []

		try:
			Configuration._print(f'[b]Creating a new [/b]{C.textLogo}[b] configuration file\n')

			# Get the CSE Type first
			questionsStart = [
				{	"type": "rawlist",
					"message": "What type of CSE do you want to run:",
					'long_instruction': 'Type of CSE to run: Infrastructure, Middle, or Application Service Node.',
					"default": 1,
					"choices": lambda _: [ 'IN', 'MN', 'ASN' ],
					"name": "cseType",
					'amark': '✓',
				},
				{	"type": "rawlist",
					"message": "Target environment:",
					'long_instruction': 'Run the CSE for development and testing, or a demonstration.',
					"default": 1,
					"choices": lambda _: [ 'Development', 'Demonstration' ],
					"name": "cseEnvironment",
					'amark': '✓',
				}
			]
			t = prompt(questionsStart)
			cseType = t['cseType']
			cseEnvironment = t['cseEnvironment']
			cnf.append(f'cseType={cseType}')
		
			# Prompt for the basic configuration
			for each in (bc := basicConfig()):
				cnf.append(f'{each}={bc[each]}')
			
			# Prompt for registrar configuration
			if cseType in [ 'MN', 'ASN' ]:
				for each in (bc := registrarConfig()):
					cnf.append(f'{each}={bc[each]}')

			# Header for the configuration
			# Split it into a header and configuration. 
			# Also easier to print with rich and the [...]'s
			cnfheader = [
					f'; {configFile}',
					';',
					'; Simplified configuration file for the [ACME] CSE',
					';',
					f'; created: {datetime.now().isoformat(" ", "seconds")}',
					';',
					f'; CSE type: {cseType}',
					f'; Environment: {cseEnvironment}',
					';',
					'',
					'',
			]
		
			# Construct the configuration
			jcnf = '[basic.config]\n' + '\n'.join(cnf)
			if cseEnvironment == 'Development':	# add more configurations for development
				jcnf += '\n\n'\
						'[server.http]\n'\
						'enableUpperTesterEndpoint=true\n'\
						'enableStructureEndpoint=true\n'
			
			# Show configuration and confirm write
			Configuration._print('\n[b]Save configuration\n')
			_jcnf = jcnf.replace("[", "\[")
			Configuration._print(f'[dim]{_jcnf}\n')

			if not inquirer.confirm(message = f'Write configuration to file {configFile}?', amark = '✓', default = True).execute():
				Configuration._print('\n[red]Configuration canceled\n')
				return False
	
		except KeyboardInterrupt:
			Configuration._print('\n[red]Configuration canceled\n')
			return False

		try:
			with open(configFile, 'w') as file:
				file.write('\n'.join(cnfheader))
				file.write(jcnf)
		except Exception as e:
			Configuration._print(str(e))
			return False

		Configuration._print(f'\n[spring_green2]New {cseType}-CSE configuration created.\n')
		return True

