#
#	CSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Container that holds references to instances of various managing entities.
#

from __future__ import annotations
import atexit, argparse, os, sys
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
from ..services.Logging import Logging as L
from ..services.MQTTClient import MQTTClient
from ..services.NotificationManager import NotificationManager
from ..services.RegistrationManager import RegistrationManager
from ..services.RemoteCSEManager import RemoteCSEManager
from ..services.ScriptManager import ScriptManager
from ..services.SecurityManager import SecurityManager
from ..services.Statistics import Statistics
from ..services.Storage import Storage
from ..services.TimeManager import TimeManager
from ..services.TimeSeriesManager import TimeSeriesManager
from ..services.Validator import Validator
from .AnnouncementManager import AnnouncementManager



# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.
announce:AnnouncementManager					= None
console:Console									= None
dispatcher:Dispatcher							= None
event:EventManager								= None
group:GroupManager								= None
httpServer:HttpServer							= None
importer:Importer								= None
mqttClient:MQTTClient							= None
notification:NotificationManager				= None
registration:RegistrationManager 				= None
remote:RemoteCSEManager							= None
request:RequestManager							= None
script:ScriptManager							= None
security:SecurityManager 						= None
statistics:Statistics							= None
storage:Storage									= None
time:TimeManager								= None
timeSeries:TimeSeriesManager					= None
validator:Validator 							= None

supportedReleaseVersions:list[str]				= None
cseType:CSEType									= None
cseCsi:str										= None
cseCsiRelative:str								= None	# Without the leading /
cseCsiSlash:str  								= None
cseSpid:str										= None
cseRi:str 										= None
cseRn:str										= None
cseOriginator:str								= None
defaultSerialization:ContentSerializationType	= None
releaseVersion:str								= None
isHeadless 										= False
cseStatus:CSEStatus								= CSEStatus.STOPPED

_cseResetLock									= Lock()	# lock for resetting the CSE


# TODO move further configurable "constants" here



##############################################################################


def startup(args:argparse.Namespace, **kwargs: Dict[str, Any]) -> bool:
	global announce, console, dispatcher, event, group, httpServer, importer, mqttClient, notification, registration
	global remote, request, script, security, statistics, storage, time, timeSeries, validator
	global aeStatistics
	global supportedReleaseVersions, cseType, defaultSerialization, cseCsi, cseCsiSlash, cseCsiRelative, cseSpid, cseRi, cseRn, releaseVersion
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
	cseCsiRelative			 = cseCsi[1:]							# no leading slash
	cseCsiSlash				 = f'{cseCsi}/'
	cseSpid					 = Configuration.get('cse.spid')
	cseRi					 = Configuration.get('cse.ri')
	cseRn					 = Configuration.get('cse.rn')
	cseOriginator			 = Configuration.get('cse.originator')

	defaultSerialization	 = Configuration.get('cse.defaultSerialization')
	releaseVersion 			 = Configuration.get('cse.releaseVersion')

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
	"""	shutdown the CSE, e.g. when receiving a keyboard interrupt or at the end of the programm run.
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
	console.run()
