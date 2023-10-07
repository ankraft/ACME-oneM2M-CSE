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
from ..etc.DateUtils import waitFor
from ..etc.Types import CSEStatus, CSEType, ContentSerializationType
from ..services.ActionManager import ActionManager
from ..services.Configuration import Configuration
from ..services.Console import Console
from ..services.Dispatcher import Dispatcher
from ..services.RequestManager import RequestManager
from ..services.EventManager import EventManager
from ..services.GroupManager import GroupManager
from ..services.HttpServer import HttpServer
from ..services.Importer import Importer
from ..services.LocationManager import LocationManager
from ..services.MQTTClient import MQTTClient
from ..services.NotificationManager import NotificationManager
from ..services.RegistrationManager import RegistrationManager
from ..services.RemoteCSEManager import RemoteCSEManager
from ..services.ScriptManager import ScriptManager
from ..services.SecurityManager import SecurityManager
from ..services.SemanticManager import SemanticManager
from ..services.Statistics import Statistics
from ..services.Storage import Storage
from ..services.TextUI import TextUI
from ..services.TimeManager import TimeManager
from ..services.TimeSeriesManager import TimeSeriesManager
from ..services.Validator import Validator
from .AnnouncementManager import AnnouncementManager
from ..services.Logging import Logging as L



# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.
action:ActionManager							= None
"""	Runtime instance of the `ActionManager`. """
announce:AnnouncementManager					= None
"""	Runtime instance of the `AnnouncementManager`. """

console:Console									= None
""" Runtime instance of the `Console`. """

dispatcher:Dispatcher							= None
"""	Runtime instance of the `Dispatcher`. """

event:EventManager								= None
"""	Runtime instance of the `EventManager`. """

groupResource:GroupManager								= None
"""	Runtime instance of the `GroupManager`. """

httpServer:HttpServer							= None
"""	Runtime instance of the `HttpServer`. """

importer:Importer								= None
"""	Runtime instance of the `Importer`. """

location:LocationManager						= None
"""	Runtime instance of the `LocationManager`. """

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

textUI:TextUI								= None
"""	Runtime instance of the `TextUI`. """

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

cseCsiSlashLess:str  							= None
""" The CSE-ID without the leading /. """

cseSpid:str										= None
""" The Service Provider ID. """

cseSPRelative:str								= None
"""	The SP-Relative CSE-ID. """

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

cseActiveSchedule:list[str]						= []
""" List of active schedules when the CSE is active and will process requests. """

_cseResetLock									= Lock()	# lock for resetting the CSE
""" Internal CSE's lock when resetting. """

_cseStartupDelay:float							= 2.0		# delay for CSE startup

##############################################################################


def startup(args:argparse.Namespace, **kwargs:Dict[str, Any]) -> bool:
	"""	Startup of the CSE. Initialization of various global variables, creating and initializing of manager instances etc.
	
		Args:
			args: Startup command line arguments.
			kwargs: Optional, additional keyword arguments which are added as attributes to the *args* object.
		Return:
			False if the CSE couldn't initialized and started. 
	"""
	global action, announce, console, dispatcher, event, groupResource, httpServer, importer, location, mqttClient, notification, registration
	global remote, request, script, security, semantic, statistics, storage, textUI, time, timeSeries, validator
	global aeStatistics
	global supportedReleaseVersions, cseType, defaultSerialization, cseCsi, cseCsiSlash, cseCsiSlashLess, cseAbsoluteSlash
	global cseSpid, cseSPRelative, cseAbsolute, cseRi, cseRn, releaseVersion, csePOA
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

	event = EventManager()					# Initialize the event manager before anything else

	if not Configuration.init(args):
		cseStatus = CSEStatus.STOPPED
		return False

	# Initialize configurable constants
	supportedReleaseVersions = Configuration.get('cse.supportedReleaseVersions')
	cseType					 = Configuration.get('cse.type')
	cseCsi					 = Configuration.get('cse.cseID')
	cseCsiSlash				 = f'{cseCsi}/'
	cseCsiSlashLess			 = cseCsi[1:]
	cseSpid					 = Configuration.get('cse.serviceProviderID')
	cseAbsoluteSlash		 = f'{cseAbsolute}/'
	cseRi					 = Configuration.get('cse.resourceID')
	cseRn					 = Configuration.get('cse.resourceName')
	cseOriginator			 = Configuration.get('cse.originator')
	cseSPRelative			 = f'{cseCsi}/{cseRn}'
	cseAbsolute				 = f'//{cseSpid}{cseSPRelative}'

	defaultSerialization	 = Configuration.get('cse.defaultSerialization')
	releaseVersion 			 = Configuration.get('cse.releaseVersion')
	isHeadless				 = Configuration.get('console.headless')

	# Set the CSE's point-of-access
	csePOA					 = [ Configuration.get('http.address') ]
	if Configuration.get('mqtt.enable'):
		csePOA.append(f'mqtt://{Configuration.get("mqtt.address")}:{Configuration.get("mqtt.port")}')

	#
	# init Logging
	#
	L.init()
	L.queueOff()				# No queuing of log messages during startup
	L.log('Starting CSE')
	L.log(f'CSE-Type: {cseType.name}')
	for l in Configuration.print().split('\n'):
		L.log(l)
	
	# set the logger for the backgroundWorkers. Add an offset to compensate for
	# this and other redirect functions to determine the correct file / linenumber
	# in the log output
	BackgroundWorkerPool.setLogger(lambda l,m: L.logWithLevel(l, m, stackOffset = 2))
	BackgroundWorkerPool.setJobBalance(	balanceTarget = Configuration.get('cse.operation.jobs.balanceTarget'),
										balanceLatency = Configuration.get('cse.operation.jobs.balanceLatency'),
										balanceReduceFactor = Configuration.get('cse.operation.jobs.balanceReduceFactor'))

	textUI = TextUI()						# Start the textUI
	console = Console()						# Start the console

	storage = Storage()						# Initialize the resource storage
	statistics = Statistics()				# Initialize the statistics system
	registration = RegistrationManager()	# Initialize the registration manager
	validator = Validator()					# Initialize the resource validator
	dispatcher = Dispatcher()				# Initialize the resource dispatcher
	request = RequestManager()				# Initialize the request manager
	security = SecurityManager()			# Initialize the security manager
	httpServer = HttpServer()				# Initialize the HTTP server
	mqttClient = MQTTClient()				# Initialize the MQTT client
	notification = NotificationManager()	# Initialize the notification manager
	groupResource = GroupManager()					# Initialize the group manager
	timeSeries = TimeSeriesManager()		# Initialize the timeSeries manager
	remote = RemoteCSEManager()				# Initialize the remote CSE manager
	announce = AnnouncementManager()		# Initialize the announcement manager
	semantic = SemanticManager()			# Initialize the semantic manager
	location = LocationManager()			# Initialize the location manager
	time = TimeManager()					# Initialize the time mamanger
	script = ScriptManager()				# Initialize the script manager
	action = ActionManager()				# Initialize the action manager

	# Import a default set of resources, e.g. the CSE, first ACP or resource structure
	# Import extra attribute policies for specializations first
	# When this fails, we cannot continue with the CSE startup
	importer = Importer()
	if not importer.doImport():
		cseStatus = CSEStatus.STOPPED
		return False
	
	# Start the HTTP server
	if not httpServer.run(): 						# This does return (!)
		L.logErr('Terminating', showStackTrace = False)
		cseStatus = CSEStatus.STOPPED
		return False 					

	# Start the MQTT client
	if not mqttClient.run():				# This does return
		L.logErr('Terminating', showStackTrace = False)
		cseStatus = CSEStatus.STOPPED
		return False 					

	# Enable log queuing
	L.queueOn()	


	# Give the CSE a moment (2s) to experience fatal errors before printing the start message

	def _startUpFinished() -> None:
		"""	Internal function to print the CSE startup message after a delay
		"""
		global cseStatus
		cseStatus = CSEStatus.RUNNING
		# Send an event that the CSE startup finished
		event.cseStartup()	# type: ignore

		L.console('CSE started')
		L.log('CSE started')

	BackgroundWorkerPool.newActor(_startUpFinished, delay = _cseStartupDelay if isHeadless else _cseStartupDelay / 2.0, name = 'Delayed_startup_message' ).start()
	
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
	textUI and textUI.shutdown()
	console and console.shutdown()
	time and time.shutdown()
	location and location.shutdown()
	semantic and semantic.shutdown()
	remote and remote.shutdown()
	mqttClient and mqttClient.shutdown()
	httpServer and httpServer.shutdown()
	script and script.shutdown()
	announce and announce.shutdown()
	timeSeries and timeSeries.shutdown()
	groupResource  and groupResource.shutdown()
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
			textUI and textUI.shutdown()
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
	if waitFor(_cseStartupDelay * 3, lambda: cseStatus == CSEStatus.RUNNING):
		console.run()
	else:
		raise TimeoutError(L.logErr(f'CSE did not start within {_cseStartupDelay * 3} seconds'))
