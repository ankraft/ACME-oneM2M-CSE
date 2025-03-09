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
from typing import Dict, Any, cast

import atexit, argparse, sys
from threading import Lock

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.Constants import Constants as C, RuntimeConstants as RC
from ..etc.DateUtils import waitFor
from ..etc.Utils import runsInIPython
from ..etc.Types import CSEStatus, CSEType, ContentSerializationType, LogLevel
from ..etc.ResponseStatusCodes import ResponseException
from ..services.ActionManager import ActionManager
from ..runtime.Configuration import Configuration
from ..runtime.Console import Console

from ..services.Dispatcher import Dispatcher
from ..services.RequestManager import RequestManager
from ..services.EventManager import EventManager
from ..services.GroupManager import GroupManager
from ..runtime.Importer import Importer
from ..services.LocationManager import LocationManager
from ..services.NotificationManager import NotificationManager
from ..services.RegistrationManager import RegistrationManager
from ..services.RemoteCSEManager import RemoteCSEManager
from ..runtime.ScriptManager import ScriptManager
from ..services.SecurityManager import SecurityManager
from ..services.SemanticManager import SemanticManager
from ..runtime.Statistics import Statistics
from ..runtime.Storage import Storage
from ..runtime.TextUI import TextUI
from ..services.TimeManager import TimeManager
from ..services.TimeSeriesManager import TimeSeriesManager
from ..services.Validator import Validator
from ..protocols.HttpServer import HttpServer
from ..protocols.CoAPServer import CoAPServer
from ..protocols.MQTTClient import MQTTClient
from ..protocols.WebSocketServer import WebSocketServer
from ..services.AnnouncementManager import AnnouncementManager
from ..runtime.Logging import Logging as L

##############################################################################

# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.

action:ActionManager = None
"""	Runtime instance of the `ActionManager`. """

announce:AnnouncementManager = None
"""	Runtime instance of the `AnnouncementManager`. """

coapServer:CoAPServer = None
"""	Runtime instance of the `CoAPServer`. """

console:Console = None
""" Runtime instance of the `Console`. """

dispatcher:Dispatcher = None
"""	Runtime instance of the `Dispatcher`. """

event:EventManager = None
"""	Runtime instance of the `EventManager`. """

groupResource:GroupManager = None
"""	Runtime instance of the `GroupManager`. """

httpServer:HttpServer = None
"""	Runtime instance of the `HttpServer`. """

importer:Importer = None
"""	Runtime instance of the `Importer`. """

location:LocationManager = None
"""	Runtime instance of the `LocationManager`. """

mqttClient:MQTTClient = None
"""	Runtime instance of the `MQTTClient`. """

notification:NotificationManager = None
"""	Runtime instance of the `NotificationManager`. """

registration:RegistrationManager = None
"""	Runtime instance of the `RegistrationManager`. """

remote:RemoteCSEManager = None
"""	Runtime instance of the `RemoteCSEManager`. """

request:RequestManager = None
"""	Runtime instance of the `RequestManager`. """

script:ScriptManager = None
"""	Runtime instance of the `ScriptManager`. """

security:SecurityManager = None
"""	Runtime instance of the `SecurityManager`. """

semantic:SemanticManager = None
"""	Runtime instance of the `SemanticManager`. """

statistics:Statistics = None
"""	Runtime instance of the `Statistics`. """

storage:Storage = None
"""	Runtime instance of the `Storage`. """

textUI:TextUI = None
"""	Runtime instance of the `TextUI`. """

time:TimeManager = None
"""	Runtime instance of the `TimeManager`. """

timeSeries:TimeSeriesManager = None
"""	Runtime instance of the `TimeSeriesManager`. """

validator:Validator = None
"""	Runtime instance of the `Validator`. """

webSocketServer:WebSocketServer	= None
"""	Runtime instance of the `WebSocketServer`. """



# Global variables to hold various (configuation) values.

_cseResetLock = Lock()
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
	global action, announce, coapServer, console, dispatcher, event, groupResource, httpServer, importer, location, mqttClient
	global notification, registration, remote, request, script, security, semantic, statistics, storage, textUI, time
	global timeSeries, validator, webSocketServer

	# Set status
	RC.cseStatus = CSEStatus.STARTING

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
		RC.cseStatus = CSEStatus.STOPPED
		return False

	# Initialize configurable constants
	# cseType					 = Configuration.cse_type
	RC.supportedReleaseVersions = Configuration.cse_supportedReleaseVersions
	RC.cseType = cast(CSEType, Configuration.cse_type)
	RC.cseCsi = Configuration.cse_cseID
	RC.cseRn = Configuration.cse_resourceName
	RC.cseRi = Configuration.cse_resourceID
	RC.cseCsiSlash = f'{RC.cseCsi}/'
	RC.cseCsiSlashLen = len(RC.cseCsiSlash)
	RC.cseCsiSlashLess = RC.cseCsi[1:]
	RC.cseSpid = Configuration.cse_serviceProviderID
	RC.cseSPRelative = f'{RC.cseCsi}/{RC.cseRn}'
	RC.cseAbsolute = f'//{RC.cseSpid}{RC.cseSPRelative}'
	RC.cseAbsoluteSlash = f'{RC.cseAbsolute}/'
	RC.cseOriginator = Configuration.cse_originator
	RC.slashCseOriginator = f'/{RC.cseOriginator}'


	RC.defaultSerialization = cast(ContentSerializationType, Configuration.cse_defaultSerialization)
	RC.releaseVersion = Configuration.cse_releaseVersion
	RC.isHeadless = Configuration.console_headless

	# Set the CSE's point-of-access
	RC.csePOA = [ Configuration.http_address ]
	if Configuration.mqtt_enable:
		RC.csePOA.append(f'mqtt://{Configuration.mqtt_address}:{Configuration.mqtt_port}')
	if Configuration.websocket_enable:
		RC.csePOA.append(Configuration.websocket_address)
	if Configuration.coap_enable:
		RC.csePOA.append(Configuration.coap_address)
	
	# Other configuration values
	RC.idLength = Configuration.cse_idLength

	#
	# init Logging
	#
	L.init()
	L.queueOff()				# No queuing of log messages during startup
	L.log('Starting CSE')
	L.log(f'CSE-Type: {RC.cseType.name}')
	if args.printconfig:
		for l in Configuration.print().split('\n'):
			L.log(l)
	
	# set the logger for the backgroundWorkers. Add an offset to compensate for
	# this and other redirect functions to determine the correct file / linenumber
	# in the log output
	BackgroundWorkerPool.setLogger(lambda l,m: L.logWithLevel(l, m, stackOffset = 2))
	BackgroundWorkerPool.setJobBalance(	balanceTarget = Configuration.cse_operation_jobs_balanceTarget,
										balanceLatency = Configuration.cse_operation_jobs_balanceLatency,
										balanceReduceFactor = Configuration.cse_operation_jobs_balanceReduceFactor)

	try:
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
		coapServer = CoAPServer()				# Initialize the CoAP server
		mqttClient = MQTTClient()				# Initialize the MQTT client
		webSocketServer = WebSocketServer()		# Initialize the WebSocket server
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

		# → Experimental late loading
		#
		# import importlib
		# mod = importlib.import_module('acme.services.ActionManager')
		# action = mod.ActionManager()	

		# mod = importlib.import_module('acme.runtime.ScriptManager')			# Initialize the action manager
		# # script = mod.ScriptManager()				# Initialize the script manager
		# thismodule = sys.modules[__name__]
		# setattr(thismodule, 'script', mod.ScriptManager())

		# Import a default set of resources, e.g. the CSE, first ACP or resource structure
		# Import extra attribute policies for specializations first
		# When this fails, we cannot continue with the CSE startup
		importer = Importer()
		if not importer.doImport():
			RC.cseStatus = CSEStatus.STOPPED
			return False
		
		# Start the HTTP server
		if not httpServer.run(): 						# This does return (!)
			L.logErr('Terminating', showStackTrace = False)
			RC.cseStatus = CSEStatus.STOPPED
			return False 					

		# Start the CoAP server
		if not coapServer.run():					# This does return
			L.logErr('Terminating', showStackTrace = False)
			RC.cseStatus = CSEStatus.STOPPED
			return False

		# Start the MQTT client
		if not mqttClient.run():				# This does return
			L.logErr('Terminating', showStackTrace = False)
			RC.cseStatus = CSEStatus.STOPPED
			return False 

		# Start the WebSocket server
		if not webSocketServer.run():			# This does return
			L.logErr('Terminating', showStackTrace = False)
			RC.cseStatus = CSEStatus.STOPPED
			return False
	
	except ResponseException as e:
		L.logErr(f'Error during startup: {e.dbg}')
		RC.cseStatus = CSEStatus.STOPPED
		return False
	except Exception as e:
		L.logErr(f'Error during startup: {e}', exc = e)
		RC.cseStatus = CSEStatus.STOPPED
		return False

	# Enable log queuing
	L.queueOn()	


	# Give the CSE a moment (2s) to experience fatal errors before printing the start message

	def _startUpFinished() -> None:
		"""	Internal function to print the CSE startup message after a delay
		"""
		RC.cseStatus = CSEStatus.RUNNING
		# Send an event that the CSE startup finished
		event.cseStartup()	# type: ignore

		L.console('CSE started')
		L.log('CSE started')

	BackgroundWorkerPool.newActor(_startUpFinished, delay = C.cseStartupDelay if RC.isHeadless else C.cseStartupDelay / 2.0, name = 'Delayed_startup_message' ).start()
	
	return True


def shutdown() -> None:
	"""	Gracefully shutdown the CSE programmatically. This will end the mail console loop
		to terminate.

		The actual shutdown happens in the _shutdown() method.
	"""
	if RC.cseStatus in [ CSEStatus.STOPPING, CSEStatus.STOPPED ]:
		return
	
	# indicating the shutting down status. When running in another environment the
	# atexit-handler might not be called. Therefore, we need to set it here
	RC.cseStatus = CSEStatus.STOPPING
	if console:
		console.stop()				# This will end the main run loop.
	
	if runsInIPython():
		L.console('CSE shut down', nlb = True)


@atexit.register
def _shutdown() -> None:
	"""	Shutdown the CSE, e.g. when receiving a keyboard interrupt or at the end of the programm run.
	"""
	if RC.cseStatus != CSEStatus.RUNNING:
		return
		
	RC.cseStatus = CSEStatus.STOPPING
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
	coapServer and coapServer.shutdown()
	webSocketServer and webSocketServer.shutdown()
	mqttClient and mqttClient.shutdown()
	httpServer and httpServer.shutdown()
	script and script.shutdown()
	announce and announce.shutdown()
	timeSeries and timeSeries.shutdown()
	groupResource and groupResource.shutdown()
	notification and notification.shutdown()
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
	RC.cseStatus = CSEStatus.STOPPED


def resetCSE() -> None:
	""" Reset the CSE: Clear databases and import the resources again.
	"""
	with _cseResetLock:
		RC.cseStatus = CSEStatus.RESETTING
		L.isWarn and L.logWarn('Resetting CSE started')
		L.enableScreenLogging = Configuration.logging_enableScreenLogging	# Set screen logging to the originally configured values

		L.setLogLevel(cast(LogLevel, Configuration.logging_level))
		L.queueOff()	# Disable log queuing for restart
		
		httpServer.pause()
		mqttClient.pause()
		webSocketServer.shutdown()	# WS Server needs to be shutdown to close connections
		coapServer.pause()

		storage.purge()

		# The following event is executed synchronously to give every component
		# a chance to finish
		event.cseReset()	# type: ignore [attr-defined]   
		if not importer.doImport():
			textUI and textUI.shutdown()
			L.logErr('Error during import')
			sys.exit()	# what else can we do?
		remote.restart()

		coapServer.unpause()
		webSocketServer.run()	# WS Server restart
		mqttClient.unpause()
		httpServer.unpause()

		# Enable log queuing again
		L.queueOn()

		# Send restart event
		event.cseRestarted()	# type: ignore [attr-defined]   

		RC.cseStatus = CSEStatus.RUNNING
		L.isWarn and L.logWarn('Resetting CSE finished')


def run() -> None:
	"""	Run the CSE.
	"""
	if waitFor(C.cseStartupDelay * 3, lambda: RC.cseStatus == CSEStatus.RUNNING):
		console.run()
	else:
		raise TimeoutError(L.logErr(f'CSE did not start within {C.cseStartupDelay * 3} seconds'))


