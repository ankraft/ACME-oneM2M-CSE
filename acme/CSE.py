#
#	CSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Container that holds references to instances of various managing entities.
#

import atexit, argparse, os, threading, time
from Constants import Constants as C
from AnnouncementManager import AnnouncementManager
from Configuration import Configuration, defaultConfigFile
from Dispatcher import Dispatcher
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
from AEStatistics import AEStatistics
from CSENode import CSENode


# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.
announce		= None
dispatcher 		= None
event			= None
group	 		= None
httpServer		= None
notification	= None
registration 	= None
remote			= None
security 		= None
statistics		= None
storage			= None

rootDirectory	= None

aeCSENode	 	= None 
aeStatistics 	= None 
appsStarted 	= False

aeStartupDelay	= 5	# seconds

# TODO make AE registering a bit more generic


##############################################################################


#def startup(args=None, configfile=None, resetdb=None, loglevel=None):
def startup(args, **kwargs):
	global announce, dispatcher, group, httpServer, notification, registration, remote, security, statistics, storage, event
	global rootDirectory
	global aeStatistics

	rootDirectory = os.getcwd()		# get the root directory


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
	Logging.log('CSE-Type: %s' % C.cseTypes[Configuration.get('cse.type')])
	Logging.log(Configuration.print())
	

	# Initiatlize the resource storage
	storage = Storage()

	# Initialize the event manager
	event = EventManager()

	# Initialize the statistics system
	statistics = Statistics()

	# Initialize the registration manager
	registration = RegistrationManager()

	# Initialize the resource dispatcher
	dispatcher = Dispatcher()

	# Initialize the security manager
	security = SecurityManager()

	# Initialize the HTTP server
	httpServer = HttpServer()

	# Initialize the notification manager
	notification = NotificationManager()

	# Initialize the announcement manager
	announce = AnnouncementManager()

	# Initialize the group manager
	group = GroupManager()
	
	# Import a default set of resources, e.g. the CSE, first ACP or resource structure
	importer = Importer()
	if not importer.importResources():
		return

	# Initialize the remote CSE manager
	remote = RemoteCSEManager()
	remote.start()

	# Start AEs
	startAppsDelayed()	# the Apps are actually started after the CSE finished the startup

	# Start the HTTP server
	event.cseStartup()
	Logging.log('CSE started')
	httpServer.run() # This does NOT return



# Gracefully shutdown the CSE, e.g. when receiving a keyboard interrupt
@atexit.register
def shutdown():

	if appsStarted:
		stopApps()
	if remote is not None:
		remote.shutdown()
	if group is not None:
		group.shutdown()
	if announce is not None:
		announce.shutdown()
	if notification is not None:
		notification.shutdown()
	if dispatcher is not None:
		dispatcher.shutdown()
	if security is not None:
		security.shutdown()
	if registration is not None:
		registration.shutdown()
	if statistics is not None:
		statistics.shutdown()
	if event is not None:
		event.shutdown()
	if storage is not None:
		storage.shutdown()


# Delay starting the AEs in the backround. This is needed because the CSE
# has not yet started. This will be called when the cseStartup event is raised.
def startAppsDelayed():
	event.addHandler(event.cseStartup, startApps)


def startApps():
	global appsStarted, aeStatistics, aeCSENode

	if not Configuration.get('cse.enableApplications'):
		return

	time.sleep(aeStartupDelay)
	Logging.log('Starting Apps')
	appsStarted = True


	if Configuration.get('app.csenode.enable'):
		aeCSENode = CSENode()
	if Configuration.get('app.statistics.enable'):
		aeStatistics = AEStatistics()

	# Add more apps here


def stopApps():
	global appsStarted
	if appsStarted:
		Logging.log('Stopping Apps')
		appsStarted = False
		if aeStatistics is not None:
			aeStatistics.shutdown()
		if aeCSENode is not None:
			aeCSENode.shutdown()
