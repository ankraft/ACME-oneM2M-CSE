#
#	CSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Container that holds references to instances of various managing entities.
#

"""	This module implements various functions for CSE startip, running, resetting, shutdown etc.
	It also provides various global variable that hold fixed configuration values.
	In addition is holds pointers to the various runtime instance of CSE modules, packages etc.
"""

from __future__ import annotations

import atexit, argparse, sys
from threading import Lock
from typing import Dict, Any

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.Types import CSEStatus, CSEType, ContentSerializationType
from ..services.Configuration import Configuration
from ..services.Console import Console
from ..services.Dispatcher import Dispatcher
from ..services.RequestManager import RequestManager
from ..services.EventManager import EventManager
from ..services.GroupManager import GroupManager
from ..services.HttpServer import HttpServer
from ..services.Importer import Importer
from ..services.MQTTClient import MQTTClient
from ..services.NotificationManager import NotificationManager
from ..services.RegistrationManager import RegistrationManager
from ..services.RemoteCSEManager import RemoteCSEManager
from ..services.ScriptManager import ScriptManager
from ..services.SecurityManager import SecurityManager
from ..services.SemanticManager import SemanticManager
from ..services.Statistics import Statistics
from ..services.Storage import Storage
from ..services.TimeManager import TimeManager
from ..services.TimeSeriesManager import TimeSeriesManager
from ..services.Validator import Validator
from .AnnouncementManager import AnnouncementManager
from ..services.Logging import Logging as L



# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.
announce:AnnouncementManager					= None
"""	Runtime instance of the `AnnouncementManager`. """

console:Console									= None
""" Runtime instance of the `Console`. """

dispatcher:Dispatcher							= None
"""	Runtime instance of the `Dispatcher`. """

event:EventManager								= None
"""	Runtime instance of the `EventManager`. """

group:GroupManager								= None
"""	Runtime instance of the `GroupManager`. """

httpServer:HttpServer							= None
"""	Runtime instance of the `HttpServer`. """

importer:Importer								= None
"""	Runtime instance of the `Importer`. """

mqttClient:MQTTClient							= None
"""	Runtime instance of the `MQTTClient`. """

notification:NotificationManager				= None
"""	Runtime instance of the `NotificationManager`. """

registration:RegistrationManager 				= None
"""	Runtime instance of the `RegistrationManager`. """

remote:RemoteCSEManager							= None
"""	Runtime instance of the `RemoteCSEManager`. """

request:RequestManager							= None
"""	Runtime instance of the `RequestManager`. """

script:ScriptManager							= None
"""	Runtime instance of the `ScriptManager`. """

security:SecurityManager 						= None
"""	Runtime instance of the `SecurityManager`. """

semantic:SemanticManager 						= None
"""	Runtime instance of the `SemanticManager`. """

statistics:Statistics							= None
"""	Runtime instance of the `Statistics`. """

storage:Storage									= None
"""	Runtime instance of the `Storage`. """

time:TimeManager								= None
"""	Runtime instance of the `TimeManager`. """

timeSeries:TimeSeriesManager					= None
"""	Runtime instance of the `TimeSeriesManager`. """

validator:Validator 							= None
"""	Runtime instance of the `Validator`. """


# Global variables to hold various (configuation) values.

supportedReleaseVersions:list[str]				= None
"""	List of the supported release versions. """

cseType:CSEType									= None
""" The kind of CSE: IN, MN, or ASN. """

cseCsi:str										= None
""" The CSE-ID. """

cseCsiSlash:str  								= None
""" The CSE-ID with an additional trailing /. """

cseCsiSlashLess:str  								= None
""" The CSE-ID without the leading /. """

cseSpid:str										= None
""" The Service Provider ID. """

cseAbsolute:str									= None
""" The CSE's Absolute prefix (SP-ID/CSE-ID). """

cseAbsoluteSlash:str							= None
""" The CSE's Absolute prefix with an additional trailing /. """

cseRi:str 										= None
""" The CSE's Resource ID. """

cseRn:str										= None
""" The CSE's Resource Name. """

cseOriginator:str								= None
"""	The CSE's admin originator. """

csePOA:list[str]								= []
""" The CSE's point-of-access's. """

defaultSerialization:ContentSerializationType	= None
""" The default / preferred content serialization type. """

releaseVersion:str								= None
""" The default / preferred release version. """

isHeadless 										= False
""" Indicator whether the CSE is running in headless mode. """

cseStatus:CSEStatus								= CSEStatus.STOPPED
""" The CSE's internal runtime status. """

_cseResetLock									= Lock()	# lock for resetting the CSE
""" Internal CSE's lock when resetting. """


##############################################################################


def startup(args:argparse.Namespace, **kwargs:Dict[str, Any]) -> bool:
	"""	Startup of the CSE. Initialization of various global variables, creating and initializing of manager instances etc.
	
		Args:
			args: Startup command line arguments.
			kwargs: Optional, additional keyword arguments which are added as attributes to the *args* object.
		Return:
			False if the CSE couldn't initialized and started. 
	"""
	global announce, console, dispatcher, event, group, httpServer, importer, mqttClient, notification, registration
	global remote, request, script, security, semantic, statistics, storage, time, timeSeries, validator
	global aeStatistics
	global supportedReleaseVersions, cseType, defaultSerialization, cseCsi, cseCsiSlash, cseCsiSlashLess, cseAbsoluteSlash
	global cseSpid, cseAbsolute, cseRi, cseRn, releaseVersion, csePOA
	global cseOriginator
	global isHeadless, cseStatus

	# Set status
	cseStatus = CSEStatus.STARTING

	# Handle command line arguments and load the configuration
	if not args:
		args = argparse.Namespace()		# In case args is None create a new args object and populate it
		args.configfile	= None
		args.resetdb	= False
		args.loglevel	= None
		args.headless	= False
		for key, value in kwargs.items():
			args.__setattr__(key, value)
	isHeadless = args.headless

	event = EventManager()					# Initialize the event manager before anything else

	if not Configuration.init(args):
		cseStatus = CSEStatus.STOPPED
		return False

	# Initialize configurable constants
	supportedReleaseVersions = Configuration.get('cse.supportedReleaseVersions')
	cseType					 = Configuration.get('cse.type')
	cseCsi					 = Configuration.get('cse.csi')
	cseCsiSlash				 = f'{cseCsi}/'
	cseCsiSlashLess			 = cseCsi[1:]
	cseSpid					 = Configuration.get('cse.spid')
	cseAbsolute				 = f'//{cseSpid}/{cseCsi}'
	cseAbsoluteSlash		 = f'{cseAbsolute}/'
	cseRi					 = Configuration.get('cse.ri')
	cseRn					 = Configuration.get('cse.rn')
	cseOriginator			 = Configuration.get('cse.originator')

	defaultSerialization	 = Configuration.get('cse.defaultSerialization')
	releaseVersion 			 = Configuration.get('cse.releaseVersion')

	# Set the CSE's point-of-access
	csePOA					 = [ Configuration.get('http.address') ]
	if Configuration.get('mqtt.enable'):
		csePOA.append(f'mqtt://{Configuration.get("mqtt.address")}:{Configuration.get("mqtt.port")}')

	#
	# init Logging
	#
	L.init()
	L.log('Starting CSE')
	L.log(f'CSE-Type: {cseType.name}')
	L.log(Configuration.print())
	L.queueOff()				# No queuing of log messages during startup
	
	# set the logger for the backgroundWorkers. Add an offset to compensate for
	# this and other redirect functions to determine the correct file / linenumber
	# in the log output
	BackgroundWorkerPool.setLogger(lambda l,m: L.logWithLevel(l, m, stackOffset = 2))
	BackgroundWorkerPool.setJobBalance(	balanceTarget = Configuration.get('cse.operation.jobBalanceTarget'),
										balanceLatency = Configuration.get('cse.operation.jobBalanceLatency'),
										balanceReduceFactor = Configuration.get('cse.operation.jobBalanceReduceFactor'))

	console = Console()						# Start the console

	storage = Storage()						# Initiatlize the resource storage
	statistics = Statistics()				# Initialize the statistics system
	registration = RegistrationManager()	# Initialize the registration manager
	validator = Validator()					# Initialize the resource validator
	dispatcher = Dispatcher()				# Initialize the resource dispatcher
	request = RequestManager()				# Initialize the request manager
	security = SecurityManager()			# Initialize the security manager
	httpServer = HttpServer()				# Initialize the HTTP server
	mqttClient = MQTTClient()				# Initialize the MQTT client
	notification = NotificationManager()	# Initialize the notification manager
	group = GroupManager()					# Initialize the group manager
	timeSeries = TimeSeriesManager()		# Initialize the timeSeries manager
	remote = RemoteCSEManager()				# Initialize the remote CSE manager
	announce = AnnouncementManager()		# Initialize the announcement manager
	semantic = SemanticManager()			# Initialize the semantic manager
	time = TimeManager()					# Initialize the time mamanger
	script = ScriptManager()				# Initialize the script manager

	# Import a default set of resources, e.g. the CSE, first ACP or resource structure
	# Import extra attribute policies for specializations first
	# When this fails, we cannot continue with the CSE startup
	importer = Importer()
	if not importer.doImport():
		cseStatus = CSEStatus.STOPPED
		return False
	
	# Start the HTTP server
	httpServer.run() 						# This does return (!)

	# Start the MQTT client
	if not mqttClient.run():				# This does return
		L.logErr('Terminating')
		cseStatus = CSEStatus.STOPPED
		return False 					

	# Enable log queuing
	L.queueOn()	

	# Send an event that the CSE startup finished
	cseStatus = CSEStatus.RUNNING
	event.cseStartup()	# type: ignore

	# Give the CSE a moment (2s) to experience fatal errors before printing the start message
	BackgroundWorkerPool.newActor(lambda : (L.console('CSE started'), L.log('CSE started')) if cseStatus == CSEStatus.RUNNING else None, delay = 2.0 if isHeadless else 0.5, name = 'Delayed startup message' ).start()
	
	return True


def shutdown() -> None:
	"""	Gracefully shutdown the CSE programmatically. This will end the mail console loop
		to terminate.

		The actual shutdown happens in the _shutdown() method.
	"""
	global cseStatus
	
	if cseStatus in [ CSEStatus.STOPPING, CSEStatus.STOPPED ]:
		return
	
	# indicating the shutting down status. When running in another environment the
	# atexit-handler might not be called. Therefore, we need to set it here
	cseStatus = CSEStatus.STOPPING
	if console:
		console.stop()				# This will end the main run loop.
	
	from ..etc.Utils import runsInIPython
	if runsInIPython():
		L.console('CSE shut down', nlb = True)


@atexit.register
def _shutdown() -> None:
	"""	Shutdown the CSE, e.g. when receiving a keyboard interrupt or at the end of the programm run.
	"""
	global cseStatus

	if cseStatus != CSEStatus.RUNNING:
		return
		
	cseStatus = CSEStatus.STOPPING
	L.queueOff()
	L.isInfo and L.log('CSE shutting down')
	if event:	# send shutdown event
		event.cseShutdown() 	# type: ignore
	
	# shutdown the services
	console and console.shutdown()
	time and time.shutdown()
	semantic and semantic.shutdown()
	remote and remote.shutdown()
	mqttClient and mqttClient.shutdown()
	httpServer and httpServer.shutdown()
	script and script.shutdown()
	announce and announce.shutdown()
	timeSeries and timeSeries.shutdown()
	group  and group.shutdown()
	notification  and notification.shutdown()
	request and request.shutdown()
	dispatcher and dispatcher.shutdown()
	security and security.shutdown()
	validator and validator.shutdown()
	registration and registration.shutdown()
	statistics and statistics.shutdown()
	event and event.shutdown()
	storage  and storage.shutdown()
	
	L.isInfo and L.log('CSE shut down')
	L.console('CSE shut down', nlb = True)

	L.finit()
	cseStatus = CSEStatus.STOPPED


def resetCSE() -> None:
	""" Reset the CSE: Clear databases and import the resources again.
	"""
	global cseStatus

	with _cseResetLock:
		cseStatus = CSEStatus.RESETTING
		L.isWarn and L.logWarn('Resetting CSE started')
		L.enableScreenLogging = Configuration.get('logging.enableScreenLogging')	# Set screen logging to the originally configured values

		L.setLogLevel(Configuration.get('logging.level'))
		L.queueOff()	# Disable log queuing for restart
		
		httpServer.pause()
		mqttClient.pause()

		storage.purge()

		# The following event is executed synchronously to give every component
		# a chance to finish
		event.cseReset()	# type: ignore [attr-defined]   
		if not importer.doImport():
			L.logErr('Error during import')
			sys.exit()	# what else can we do?
		remote.restart()
		mqttClient.unpause()
		httpServer.unpause()

		# Enable log queuing again
		L.queueOn()

		# Send restart event
		event.cseRestarted()	# type: ignore [attr-defined]   

		cseStatus = CSEStatus.RUNNING
		L.isWarn and L.logWarn('Resetting CSE finished')


def run() -> None:
	"""	Run the CSE.
	"""
	console.run()
