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
from AnnouncementManager import AnnouncementManager
from Configuration import Configuration
from Console import Console
from Dispatcher import Dispatcher
from RequestManager import RequestManager
from EventManager import EventManager
from GroupManager import GroupManager
from HttpServer import HttpServer
from Importer import Importer
from Logging import Logging as L
from MQTTClient import MQTTClient
from NotificationManager import NotificationManager
from RegistrationManager import RegistrationManager
from RemoteCSEManager import RemoteCSEManager
from SecurityManager import SecurityManager
from Statistics import Statistics
from Storage import Storage
from TimeSeriesManager import TimeSeriesManager
from Validator import Validator
from Types import CSEType, ContentSerializationType


from AEStatistics import AEStatistics
from CSENode import CSENode
import Utils
from helpers.BackgroundWorker import BackgroundWorkerPool




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

rootDirectory:str								= None

aeCSENode:CSENode				 				= None 
aeStatistics:AEStatistics 		 				= None 
appsStarted:bool 								= False

supportedReleaseVersions:list[str]				= None
cseType:CSEType									= None
cseCsi:str										= None
cseRi:str 										= None
cseRn:str										= None
cseOriginator:str								= None
defaultSerialization:ContentSerializationType	= None
isHeadless 										= False
shuttingDown									= False



# TODO move further configurable "constants" here



##############################################################################


#def startup(args=None, configfile=None, resetdb=None, loglevel=None):
def startup(args:argparse.Namespace, **kwargs: Dict[str, Any]) -> bool:
	global announce, console, dispatcher, event, group, httpServer, importer, mqttClient, notification, registration
	global remote, request, security, statistics, storage, timeSeries, validator
	global rootDirectory
	global aeStatistics
	global supportedReleaseVersions, cseType, defaultSerialization, cseCsi, cseRi, cseRn
	global cseOriginator
	global isHeadless

	rootDirectory = os.getcwd()					# get the root directory
	os.environ["FLASK_ENV"] = "development"		# get rid if the warning message from flask. 
												# Hopefully it is clear at this point that this is not a production CSE


	# Handle command line arguments and load the configuration
	if args is None:
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
	cseRi					 = Configuration.get('cse.ri')
	cseRn					 = Configuration.get('cse.rn')
	cseOriginator			 = Configuration.get('cse.originator')

	defaultSerialization	 = Configuration.get('cse.defaultSerialization')

	# init Logging
	L.init()
	if not args.headless:
		L.console('Press ? for help')
	L.log('============')
	L.log('Starting CSE')
	L.log(f'CSE-Type: {cseType.name}')
	#L.log('Configuration:')
	L.log(Configuration.print())

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
	if not importer.importAttributePolicies() or not importer.importResources():
		return False

	remote = RemoteCSEManager()				# Initialize the remote CSE manager
	announce = AnnouncementManager()		# Initialize the announcement manager
	startAppsDelayed()						# Start the App. They are actually started after the CSE finished the startup

	console = Console()						# Start the console

	# Send an event that the CSE startup finished
	event.cseStartup()	# type: ignore

	# Start the HTTP server
	httpServer.run() # This does return (!)

	# Start the MQTT client
	mqttClient.run() # This does return
	
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
	console.stop()				# This will end the main run loop.
	if isHeadless:
		L.console('CSE shutting down')


@atexit.register
def _shutdown() -> None:
	"""	shutdown the CSE, e.g. when receiving a keyboard interrupt or at the end of the programm run.
	"""

	L.isInfo and L.log('CSE shutting down')
	if event is not None:
		event.cseShutdown() 	# type: ignore
	console is not None and console.shutdown()
	mqttClient is not None and mqttClient.shutdown()
	httpServer is not None and httpServer.shutdown()
	announce is not None and announce.shutdown()
	remote is not None and remote.shutdown()
	timeSeries is not None and timeSeries.shutdown()
	group is not None and group.shutdown()
	notification is not None and notification.shutdown()
	request is not None and request.shutdown()
	dispatcher is not None and dispatcher.shutdown()
	security is not None and security.shutdown()
	validator is not None and validator.shutdown()
	registration is not None and registration.shutdown()
	statistics is not None and statistics.shutdown()
	event is not None and event.shutdown()
	storage is not None and storage.shutdown()
	L.isInfo and L.log('CSE shutdown')
	L.finit()


def resetCSE() -> None:
	""" Reset the CSE: Clear databases and import the resources again.
	"""
	L.isWarn and L.logWarn('Resetting CSE started')
	storage.purge()
	if not importer.importAttributePolicies() or not importer.importResources():
		L.isWarn and L.logErr('Error during import')
		sys.exit()	# what else can we do?
	L.isWarn and L.logWarn('Resetting CSE finished')


def run() -> None:
	console.run()

##############################################################################
#
#	Application handler
#


# Delay starting the AEs in the backround. This is needed because the CSE
# has not yet started. This will be called when the cseStartup event is raised.
def startAppsDelayed() -> None:
	event.addHandler(event.cseStartup, startApps) 	# type: ignore
	event.addHandler(event.cseShutdown, stopApps)	# type: ignore


def startApps() -> None:
	global appsStarted, aeStatistics, aeCSENode

	if not Configuration.get('cse.enableApplications'):
		return

	time.sleep(Configuration.get('cse.applicationsStartupDelay'))
	L.isInfo and L.log('Starting Apps')
	appsStarted = True

	if Configuration.get('app.csenode.enable'):
		aeCSENode = CSENode()
	if not appsStarted:	# shutdown?
		return
	if Configuration.get('app.statistics.enable'):
		aeStatistics = AEStatistics()

	# Add more apps here


def stopApps() -> None:
	global appsStarted
	if appsStarted:
		appsStarted = False
		L.isInfo and L.log('Stopping Apps')
		if aeStatistics is not None:
			aeStatistics.shutdown()
		if aeCSENode is not None:
			aeCSENode.shutdown()

