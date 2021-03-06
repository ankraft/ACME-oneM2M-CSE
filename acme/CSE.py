#
#	CSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Container that holds references to instances of various managing entities.
#

from __future__ import annotations
import atexit, argparse, os, threading, time, sys
from typing import Dict, Optional, Any
from Constants import Constants as C
from AnnouncementManager import AnnouncementManager
from Configuration import Configuration
from Dispatcher import Dispatcher
from RequestManager import RequestManager
from EventManager import EventManager
from GroupManager import GroupManager
from HttpServer import HttpServer
from Importer import Importer
from Logging import Logging
from NotificationManager import NotificationManager
from RegistrationManager import RegistrationManager
from RemoteCSEManager import RemoteCSEManager
from SecurityManager import SecurityManager
from Statistics import Statistics
from Storage import Storage
from Validator import Validator
from Types import CSEType, ContentSerializationType

from AEStatistics import AEStatistics
from CSENode import CSENode
import Utils
from helpers.KeyHandler import loop, stopLoop, readline
from helpers.BackgroundWorker import BackgroundWorkerPool



# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.
announce:AnnouncementManager					= None
dispatcher:Dispatcher							= None
request:RequestManager							= None
event:EventManager								= None
group:GroupManager								= None
httpServer:HttpServer							= None
notification:NotificationManager				= None
registration:RegistrationManager 				= None
remote:RemoteCSEManager							= None
security:SecurityManager 						= None
statistics:Statistics							= None
storage:Storage									= None
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



# TODO move further configurable "constants" here

# TODO make AE registering a bit more generic




##############################################################################


#def startup(args=None, configfile=None, resetdb=None, loglevel=None):
def startup(args:argparse.Namespace, **kwargs: Dict[str, Any]) -> None:
	global announce, dispatcher, group, httpServer, notification, validator
	global registration, remote, request, security, statistics, storage, event
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
		return

	# Initialize configurable constants
	supportedReleaseVersions = Configuration.get('cse.supportedReleaseVersions')
	cseType					 = Configuration.get('cse.type')
	cseCsi					 = Configuration.get('cse.csi')
	cseRi					 = Configuration.get('cse.ri')
	cseRn					 = Configuration.get('cse.rn')
	cseOriginator			 = Configuration.get('cse.originator')

	defaultSerialization	 = Configuration.get('cse.defaultSerialization')

	# init Logging
	Logging.init()
	if not args.headless:
		Logging.console('Press ? for help')
	Logging.log('============')
	Logging.log('Starting CSE')
	Logging.log(f'CSE-Type: {cseType.name}')
	Logging.log('Configuration:')
	Logging.log(Configuration.print())


	# Initiatlize the resource storage
	storage = Storage()

	# Initialize the event manager
	event = EventManager()

	# Initialize the statistics system
	statistics = Statistics()

	# Initialize the registration manager
	registration = RegistrationManager()

	# Initialize the resource validator
	validator = Validator()

	# Initialize the resource dispatcher
	dispatcher = Dispatcher()

	# Initialize the request manager
	request = RequestManager()

	# Initialize the security manager
	security = SecurityManager()

	# Initialize the HTTP server
	httpServer = HttpServer()

	# Initialize the notification manager
	notification = NotificationManager()

	# Initialize the group manager
	group = GroupManager()
	
	# Import a default set of resources, e.g. the CSE, first ACP or resource structure
	# Import extra attribute policies for specializations first 
	importer = Importer()
	if not importer.importAttributePolicies() or not importer.importResources():
		return

	# Initialize the remote CSE manager
	remote = RemoteCSEManager()

	# Initialize the announcement manager
	announce = AnnouncementManager()

	# Start AEs
	startAppsDelayed()	# the Apps are actually started after the CSE finished the startup

	# Start the HTTP server
	event.cseStartup()	# type: ignore
	httpServer.run() # This does return (!)
	
	Logging.log('CSE started')
	if isHeadless:
		Logging.console('CSE started')

	#
	#	Enter an endless loop.
	#	Execute keyboard commands in the keyboardHandler's loop() function.
	#
	commands = {
		'?'     : _keyHelp,
		'h'		: _keyHelp,
		'\n'	: lambda c: print(),	# 1 empty line
		'\x03'  : _keyShutdownCSE,		# See handler below
		'c'		: _keyConfiguration,
		'C'		: _keyClearScreen,
		'D'		: _keyDeleteResource,
		'i'		: _keyInspectResource,
		'l'     : _keyToggleLogging,
		'Q'		: _keyShutdownCSE,		# See handler below
		'r'		: _keyCSERegistrations,
		's'		: _keyStatistics,
		't'		: _keyResourceTree,
		'w'		: _keyWorkers,
	}

	#	Endless runtime loop. This handles key input & commands
	#	The CSE's shutdown happens in one of the key handlers below
	loop(commands, catchKeyboardInterrupt=True, headless=args.headless)


def shutdown() -> None:
	stopLoop()	# This will end the main run loop


@atexit.register
def _shutdown() -> None:
	"""	Gracefully shutdown the CSE, e.g. when receiving a keyboard interrupt.
	"""
	Logging.log('CSE shutting down')
	if event is not None:
		event.cseShutdown() 	# type: ignore
	httpServer is not None and httpServer.shutdown()
	announce is not None and announce.shutdown()
	remote is not None and remote.shutdown()
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
	Logging.log('CSE shutdown')
	Logging.finit()



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
	Logging.log('Starting Apps')
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
		Logging.log('Stopping Apps')
		if aeStatistics is not None:
			aeStatistics.shutdown()
		if aeCSENode is not None:
			aeCSENode.shutdown()


##############################################################################
#
#	Various keyboard command handlers
#

def _keyHelp(key:str) -> None:
	"""	Print help for keyboard commands.
	"""
	Logging.console("""**Console Commands**  
- h, ?  - This help
- Q, ^C - Shutdown CSE
- c     - Show configuration
- C     - Clear the console screen
- D     - Delete resource
- i     - Inspect resource
- l     - Toggle logging on/off
- r     - Show CSE registrations
- s     - Show statistics
- t     - Show resource tree
- w     - Show worker threads status
-
""", extranl=True)


def _keyShutdownCSE(key:str) -> None:
	"""	Shutdown the CSE.
	"""
	if not isHeadless:
		Logging.console('Shutdown CSE')
	sys.exit()


def _keyToggleLogging(key:str) -> None:
	"""	Toggle through the log levels.
	"""
	Logging.enableScreenLogging = not Logging.enableScreenLogging
	Logging.console(f'Logging enabled -> **{Logging.enableScreenLogging}**')


def _keyWorkers(key:str) -> None:
	"""	Print the worker and actor threads.
	"""
	result = '**Worker & Actor Threads**\n'
	for w in BackgroundWorkerPool.backgroundWorkers.values():
		a = 'A' if w.count == 1 else 'W'
		result += f'- {w.name:20} ({a}) | interval : {w.updateIntervall:<8} | runs : {w.numberOfRuns:<8}\n'
	Logging.console(result, extranl=True)


def _keyConfiguration(key:str) -> None:
	"""	Print the configuration.
	"""
	result = '**Configuration**\n'
	conf = Configuration.print().split('\n')
	for c in conf:
		if c.startswith('Configuration:'):
			continue
		c = c.replace('*', '\\*')
		result += f'- {c}\n'
	Logging.console(result, extranl=True)


def _keyClearScreen(key:str) -> None:
	"""	Clear the console screen.
	"""
	Logging.consoleClear()


def _keyResourceTree(key:str) -> None:
	"""	Render the CSE's resource tree.
	"""
	Logging.console('**Resource Tree**', extranl=True)
	Logging.console(statistics.getResourceTreeRich())
	Logging.console()


def _keyCSERegistrations(key:str) -> None:
	"""	Render CSE registrations.
	"""
	Logging.console('**CSE Registrations**', extranl=True)
	Logging.console(statistics.getCSERegistrationsRich())
	Logging.console()


def _keyStatistics(key:str) -> None:
	""" Render various statistics & counts.
	"""
	Logging.console('**Statistics**', extranl=True)
	Logging.console(statistics.getStatisticsRich())
	Logging.console()


def _keyDeleteResource(key:str) -> None:
	"""	Delete a resource from the CSE.
	"""
	Logging.console('**Delete Resource**', extranl=True)
	loggingOld = Logging.loggingEnabled
	Logging.loggingEnabled = False

	if (ri := readline('ri=')) is None:
		Logging.console()
	elif len(ri) > 0:
		if (res := dispatcher.retrieveResource(ri)).resource is None:
			Logging.console(res.dbg, isError=True)
		else:
			if (res := dispatcher.deleteResource(res.resource, withDeregistration=True)).resource is None:
				Logging.console(res.dbg, isError=True)
			else:
				Logging.console('ok')

	Logging.loggingEnabled = loggingOld


def _keyInspectResource(key:str) -> None:
	"""	Inspect a resource.
	"""
	Logging.console('**Inspect Resource**', extranl=True)
	loggingOld = Logging.loggingEnabled
	Logging.loggingEnabled = False
	
	if (ri := readline('ri=')) is None:
		Logging.console()
	elif len(ri) > 0:
		if (res := dispatcher.retrieveResource(ri)).resource is None:
			Logging.console(res.dbg, isError=True)
		else:
			Logging.console(res.resource.asDict())

	Logging.loggingEnabled = loggingOld