#
#	CSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Container that holds references to instances of various managing entities.
#

import atexit, argparse, os, threading, time
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

from AEStatistics import AEStatistics
from CSENode import CSENode
import Utils



# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.
announce:AnnouncementManager		= None
dispatcher:Dispatcher				= None
request:RequestManager				= None
event:EventManager					= None
group:GroupManager					= None
httpServer:HttpServer				= None
notification:NotificationManager	= None
registration:RegistrationManager 	= None
remote:RemoteCSEManager				= None
security:SecurityManager 			= None
statistics:Statistics				= None
storage:Storage						= None
validator:Validator 				= None

rootDirectory:str					= None

aeCSENode:CSENode				 	= None 
aeStatistics:AEStatistics 		 	= None 
appsStarted:bool 					= False


# TODO make AE registering a bit more generic


##############################################################################


#def startup(args=None, configfile=None, resetdb=None, loglevel=None):
def startup(args: argparse.Namespace, **kwargs: Dict[str, Any]) -> None:
	global announce, dispatcher, group, httpServer, notification, validator
	global registration, remote, request, security, statistics, storage, event
	global rootDirectory
	global aeStatistics

	rootDirectory = os.getcwd()					# get the root directory
	os.environ["FLASK_ENV"] = "development"		# get rid if the warning message from flask. 
												# Hopefully it is clear at this point that this is not a production CSE



	# Handle command line arguments and load the configuration
	if args is None:
		args = argparse.Namespace()		# In case args is None create a new args object and populate it
		args.configfile	= None
		args.resetdb	= False
		args.loglevel	= None
		for key, value in kwargs.items():
			args.__setattr__(key, value)

	if not Configuration.init(args):
		return

	# init Logging
	Logging.init()
	Logging.log('============')
	Logging.log('Starting CSE')
	Logging.log('CSE-Type: %s' % Utils.getCSETypeAsString())
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
	Logging.log('CSE started')
	httpServer.run() # This does NOT return



# Gracefully shutdown the CSE, e.g. when receiving a keyboard interrupt
@atexit.register
def shutdown() -> None:
	Logging.log('CSE shutting down')
	if event is not None:
		event.cseShutdown() 	# type: ignore
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
