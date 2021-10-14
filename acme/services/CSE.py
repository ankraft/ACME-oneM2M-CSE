#
#	CSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Container that holds references to instances of various managing entities.
#

from __future__ import annotations
import atexit, argparse, os, time, sys
from typing import Dict, Any

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc import DateUtils
from ..etc.Types import CSEType, ContentSerializationType
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
from ..services.SecurityManager import SecurityManager
from ..services.Statistics import Statistics
from ..services.Storage import Storage
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
security:SecurityManager 						= None
statistics:Statistics							= None
storage:Storage									= None
timeSeries:TimeSeriesManager					= None
validator:Validator 							= None

supportedReleaseVersions:list[str]				= None
cseType:CSEType									= None
cseCsi:str										= None
cseCsiSlash:str  								= None
cseRi:str 										= None
cseRn:str										= None
cseOriginator:str								= None
defaultSerialization:ContentSerializationType	= None
releaseVersion:str								= None
isHeadless 										= False
shuttingDown									= False



# TODO move further configurable "constants" here



##############################################################################


def startup(args:argparse.Namespace, **kwargs: Dict[str, Any]) -> bool:
	global announce, console, dispatcher, event, group, httpServer, importer, mqttClient, notification, registration
	global remote, request, security, statistics, storage, timeSeries, validator
	global aeStatistics
	global supportedReleaseVersions, cseType, defaultSerialization, cseCsi, cseCsiSlash, cseRi, cseRn, releaseVersion
	global cseOriginator
	global isHeadless

	os.environ["FLASK_ENV"] = "development"		# get rid if the warning message from flask. 
												# Hopefully it is clear at this point that this is not a production CSE


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


	if not Configuration.init(args):
		return False

	# Initialize configurable constants
	supportedReleaseVersions = Configuration.get('cse.supportedReleaseVersions')
	cseType					 = Configuration.get('cse.type')
	cseCsi					 = Configuration.get('cse.csi')
	cseCsiSlash				 = f'{cseCsi}/'
	cseRi					 = Configuration.get('cse.ri')
	cseRn					 = Configuration.get('cse.rn')
	cseOriginator			 = Configuration.get('cse.originator')

	defaultSerialization	 = Configuration.get('cse.defaultSerialization')
	releaseVersion 			 = Configuration.get('cse.releaseVersion')

	#
	# init Logging
	#
	L.init()
	if not args.headless:
		L.console('Press ? for help')
	L.log('============')
	L.log('Starting CSE')
	L.log(f'CSE-Type: {cseType.name}')
	L.log(Configuration.print())
	
	# set the logger for the backgroundWorkers. Add an offset to compensate for
	# this and other redirect functions to determine the correct file / linenumber
	# in the log output
	BackgroundWorkerPool.setLogger(lambda l,m: L.logWithLevel(l,m, stackOffset=2))	
	console = Console()						# Start the console

	storage = Storage()						# Initiatlize the resource storage
	event = EventManager()					# Initialize the event manager
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
	
	# Import a default set of resources, e.g. the CSE, first ACP or resource structure
	# Import extra attribute policies for specializations first
	# When this fails, we cannot continue with the CSE startup
	importer = Importer()
	if not importer.doImport():
		return False
	
	# Start the HTTP server
	httpServer.run() 						# This does return (!)

	# Start the MQTT client
	if not mqttClient.run():				# This does return
		return False 					
	remote = RemoteCSEManager()				# Initialize the remote CSE manager
	announce = AnnouncementManager()		# Initialize the announcement manager

	# Send an event that the CSE startup finished
	event.cseStartup()	# type: ignore


	
	if not shuttingDown:
		L.isInfo and L.log('CSE started')
		if isHeadless:
			# when in headless mode give the CSE a moment (2s) to experience fatal errors before printing the start message
			BackgroundWorkerPool.newActor(lambda : L.console('CSE started') if not shuttingDown else None, delay=2.0 ).start()
	
	return True



def shutdown() -> None:
	"""	Gracefully shutdown the CSE programmatically. This will end the mail console loop
		to terminate.
		The actual shutdown happens in the _shutdown() method.
	"""
	global shuttingDown
	
	# indicating the shutting down status. When running in another environment the
	# atexit-handler might not be called. Therefore, we need to set it here
	shuttingDown = True
	if console:
		console.stop()				# This will end the main run loop.
	if isHeadless:
		L.console('CSE shutting down')


@atexit.register
def _shutdown() -> None:
	"""	shutdown the CSE, e.g. when receiving a keyboard interrupt or at the end of the programm run.
	"""

	L.isInfo and L.log('CSE shutting down')
	if event:	# send shutdown event
		event.cseShutdown() 	# type: ignore
	
	# shutdown the services
	console and console.shutdown()
	remote and remote.shutdown()
	mqttClient and mqttClient.shutdown()
	httpServer and httpServer.shutdown()
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
	
	L.isInfo and L.log('CSE shutdown')
	L.finit()


def resetCSE() -> None:
	""" Reset the CSE: Clear databases and import the resources again.
	"""
	L.isWarn and L.logWarn('Resetting CSE started')
	storage.purge()

	# The following event is executed synchronously to give every component
	# a chance to finish
	event.cseReset()	# type: ignore [attr-defined]   
	if not importer.doImport():
		L.isWarn and L.logErr('Error during import')
		sys.exit()	# what else can we do?
	L.isWarn and L.logWarn('Resetting CSE finished')


def run() -> None:
	console.run()

