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

import atexit, argparse, sys, platform, os, signal, platform
from threading import Lock

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.Constants import Constants as C, RuntimeConstants as RC
from ..etc.DateUtils import waitFor, utcTime
from ..etc.Utils import runsInIPython
from ..etc.Types import CSEStatus, LogLevel
from ..etc.Constants import RuntimeConstants as RC
from ..etc.ResponseStatusCodes import ResponseException
from ..runtime.Configuration import Configuration


from ..services.Dispatcher import Dispatcher
from ..services.RequestManager import RequestManager
from .EventManager import EventManager
from ..runtime.Importer import Importer
from ..services.NotificationManager import NotificationManager
from ..runtime.PluginManager import PluginManager, DependencyError
from ..runtime.ConsoleBase import ConsoleBase
from ..services.RegistrationManager import RegistrationManager
from ..services.RemoteCSEManager import RemoteCSEManager
from ..runtime.ScriptManager import ScriptManager
from ..services.SecurityManager import SecurityManager
from ..runtime.Storage import Storage
from ..services.TimeManager import TimeManager
from ..services.Validator import Validator
from ..services.AnnouncementManager import AnnouncementManager
from ..runtime.Logging import Logging as L

##############################################################################

# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.

announce:AnnouncementManager = None
"""	Runtime instance of the `AnnouncementManager`. """

console:ConsoleBase = None
""" Runtime instance of the `Console`. """

dispatcher:Dispatcher = None
"""	Runtime instance of the `Dispatcher`. """

event:EventManager = None
"""	Runtime instance of the `EventManager`. """

# httpServer:HttpServer = None
"""	Runtime instance of the `HttpServer`. """

importer:Importer = None
"""	Runtime instance of the `Importer`. """

notification:NotificationManager = None
"""	Runtime instance of the `NotificationManager`. """

pluginManager:PluginManager = None
"""	Runtime instance of the `PluginManager`. """

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

storage:Storage = None
"""	Runtime instance of the `Storage`. """

time:TimeManager = None
"""	Runtime instance of the `TimeManager`. """

validator:Validator = None
"""	Runtime instance of the `Validator`. """

# Global variables to hold various (configuation) values.

_cseResetLock = Lock()
""" Internal CSE's lock when resetting. """

##############################################################################

event = EventManager()					# Initialize the event manager before anything else


def startup(args:argparse.Namespace, **kwargs:Dict[str, Any]) -> bool:
	"""	Startup of the CSE. Initialization of various global variables, creating and initializing of manager instances etc.
	
		Args:
			args: Startup command line arguments.
			kwargs: Optional, additional keyword arguments which are added as attributes to the *args* object.
		Return:
			False if the CSE couldn't initialized and started. 
	"""
	global announce, dispatcher, importer
	global notification, pluginManager, registration, remote, request, script, security
	global storage, time, validator

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

	if not Configuration.init(args):
		RC.cseStatus = CSEStatus.STOPPED
		return False

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
	BackgroundWorkerPool.setJobBalance(	balanceTarget=Configuration.cse_operation_jobs_balanceTarget,
										balanceLatency=Configuration.cse_operation_jobs_balanceLatency,
										balanceReduceFactor=Configuration.cse_operation_jobs_balanceReduceFactor)

	try:
		# Initialize the plugin manager
		# This loads, configures and runs the plugins as well
		pluginManager = PluginManager()	
		pluginManager.start(tags=['database'])	# Start the database plugins first


		storage = Storage()						# Initialize the resource storage

		importer = Importer()					# Initialize the importer
		importer.importResourcePolicies()		# Before initializing other components, import the resource policies
		registration = RegistrationManager()	# Initialize the registration manager
		validator = Validator()					# Initialize the resource validator
		dispatcher = Dispatcher()				# Initialize the resource dispatcher
		request = RequestManager()				# Initialize the request manager
		
		security = SecurityManager()			# Initialize the security manager

		notification = NotificationManager()	# Initialize the notification manager
		remote = RemoteCSEManager()				# Initialize the remote CSE manager
		announce = AnnouncementManager()		# Initialize the announcement manager
		time = TimeManager()					# Initialize the time manager
		script = ScriptManager()				# Initialize the script manager
		
		pluginManager.start(excludedTags=['database'])	# Start the remaining plugins after all components are initialized.

		# Import attribute, flexContainer and enum policies, and configuration documentation
		#
		# After this, the CSE reads the scripts from the default and runtime init directories.
		# It also runs the init script, if there is one. 
		#
		# When this fails, we cannot continue with the CSE startup
		if not importer.importPolicies() or not importer.importScripts():
			RC.cseStatus = CSEStatus.STOPPED
			return False
		
	except ResponseException as e:
		L.logErr(f'Error during startup: {e.dbg}')
		RC.cseStatus = CSEStatus.STOPPED
		return False
	except KeyError as e:
		L.logErr(f'Error during startup: {e}')
		RC.cseStatus = CSEStatus.STOPPED
		return False
	except (DependencyError, ValueError) as e:
		RC.cseStatus = CSEStatus.STOPPED
		return False
	except Exception as e:
		L.logErr(f'Error during startup: {e}', exc=e)
		RC.cseStatus = CSEStatus.STOPPED
		return False

	# Enable log queuing
	L.queueOn()	


	# Give the CSE a moment (2s) to experience fatal errors before printing the start message

	def _startUpFinished() -> None:
		"""	Internal function to print the CSE startup message after a delay
		"""
		RC.cseStatus = CSEStatus.RUNNING
		RC.startupTime = utcTime()	# Set the startup time when the CSE is fully started and running

		# Send an event that the CSE startup finished
		event.cseStartup()	# type: ignore

		L.console('CSE started')
		L.log('CSE started')

	BackgroundWorkerPool.newActor(_startUpFinished, delay=C.cseStartupDelay if RC.isHeadless else C.cseStartupDelay / 2.0, name='Delayed_startup_message').start()
	
	return True


def shutdown() -> None:
	"""	Gracefully shutdown the CSE programmatically. This will end the main console loop
		to terminate.

		The actual shutdown happens in the _shutdown() method.
	"""
	if RC.cseStatus in [ CSEStatus.SHUTTINGDOWN, CSEStatus.STOPPED ]:
		return
	
	# indicating the shutting down status. When running in another environment the
	# atexit-handler might not be called. Therefore, we need to set it here
	if RC.cseStatus != CSEStatus.SHUTTINGDOWNRESTART:	# only set this if we are not restarting
		RC.cseStatus = CSEStatus.SHUTTINGDOWN
	if console:
		console.stop()				# This will end the main run loop.
	
	if runsInIPython():
		L.console('CSE shut down', nlb = True)


@atexit.register
def _shutdown() -> None:
	"""	Shutdown the CSE, e.g. when receiving a keyboard interrupt or at the end of the programm run.
	"""
	if RC.cseStatus not in [CSEStatus.RUNNING, CSEStatus.SHUTTINGDOWNRESTART]:
		return
	L.console('CSE shutting down now', nlb=True)
	
	# The status STOPPINGRESTART is used to indicate that the CSE is shutting down to restart.
	# This is a normal shutdown but in the end the CSE process will return with a special exit code
	# to indicate that the CSE is restarting. This code is 82 (ASCII code for 'R').
	_cseStatus = RC.cseStatus	
	RC.cseStatus = CSEStatus.SHUTTINGDOWN
	L.queueOff()
	L.isInfo and L.log('CSE shutting down')
	if event:	# send shutdown event
		event.cseShutdown() 	# type: ignore
	
	# shutdown the services
	# Stop all the plugins, except the database plugins, which are needed during shutdown 
	# This leaves only the database plugins running
	pluginManager and pluginManager.stop(excludedTags=['database'])

	time and time.shutdown()
	remote and remote.shutdown()
	script and script.shutdown()
	announce and announce.shutdown()
	notification and notification.shutdown()
	request and request.shutdown()
	dispatcher and dispatcher.shutdown()
	security and security.shutdown()
	validator and validator.shutdown()
	registration and registration.shutdown()
	event and event.shutdown()
	storage  and storage.shutdown()
	
	# This shutdowns all plugins, including the ones, which only have been stopped before
	pluginManager and pluginManager.shutdown()	

	L.isInfo and L.log('CSE shut down')
	L.console('CSE shut down', nlb = True)

	L.finit()
	RC.cseStatus = CSEStatus.STOPPED

	# If the CSE is stopping to restart, we exit with a special exit code
	if _cseStatus == CSEStatus.SHUTTINGDOWNRESTART:
		os._exit(82) 

def forceShutdown() -> None:
	"""	Force shutdown the CSE. 
	
		This is different for different platforms. On Windows, we send a SIGINT to the process,
		while on other platforms we raise a SIGINT signal. This is to ensure that the CSE can
		shutdown gracefully, even if the main thread is blocked or busy.

		This function might not return, e.g. when running under Windows, where the process is killed.
	"""	
	_platform = platform.system()
	L.isDebug and L.logDebug(f'Forcing CSE shutdown (Platform: {_platform})')

	
	if pluginManager.textUI and pluginManager.textUI.tuiApp:	# Shutdown the TextUI first
		pluginManager.textUI.shutdown()	
		import time as _time
		_time.sleep(1)	 			# Give the TextUI a moment to shutdown

	# Platform specific shutdown
	# On Windows, we send a SIGINT to the process, which will be caught by the main thread
	match _platform:
		case 'Windows':
			_shutdown()
			os.kill(os.getpid(), signal.SIGINT)
		case _:
			signal.raise_signal(signal.SIGINT)	# raise SIGINT to shutdown the CSE


def resetCSE() -> None:
	""" Reset the CSE: Clear databases and import the resources again.
	"""
	with _cseResetLock:
		RC.cseStatus = CSEStatus.RESETTING
		L.isWarn and L.logWarn('Resetting CSE started')
		L.enableScreenLogging = Configuration.logging_enableScreenLogging	# Set screen logging to the originally configured values

		L.setLogLevel(cast(LogLevel, Configuration.logging_level))
		L.queueOff()	# Disable log queuing for restart
		
		# Pause all binding plugins to stop receiving requests during reset.
		pluginManager.pausePlugins(tags='binding')
		# Restart all plugins, except core plugins. They are restarted via an event
		pluginManager.restartPlugins()	

		storage.purge()

		# The following event is executed synchronously to give every component
		# a chance to finish
		event.cseReset()	# type: ignore [attr-defined]

		# We only import policies, documentation and scripts during restart
		# But we don't import the resource policies again.
		if not importer.importPolicies() or not importer.importScripts():
			pluginManager.textUI and pluginManager.textUI.shutdown()
			L.logErr('Error during import')
			sys.exit()	# what else can we do?
		remote.restart()


		# Unpause all binding plugins to start receiving requests again after reset.
		pluginManager.unpausePlugins(tags='binding')	

		# Enable log queuing again
		L.queueOn()

		# Send restarted event
		event.cseRestarted()	# type: ignore [attr-defined]   

		RC.cseStatus = CSEStatus.RUNNING
		RC.startupTime = utcTime()	# Set the startup time when the CSE is fully started and running
		L.isWarn and L.logWarn('Resetting CSE finished')


def restartCSE() -> None:
	"""	Restart the CSE. This is a convenience function that calls the shutdown() function.
	"""
	if RC.cseStatus != CSEStatus.RUNNING:
		L.logErr('CSE is not running, cannot restart')
		return
	L.isWarn and L._log(LogLevel.WARNING, 'Restarting CSE', immediate=True)
	if console:
		console.stop()
	_shutdown()
	RC.cseStatus = CSEStatus.SHUTTINGDOWNRESTART


def run() -> None:
	"""	Run the CSE.

		Raises:
			TimeoutError: If the CSE does not start within the specified time.
	"""
	if waitFor(C.cseStartupDelay * 3, lambda: RC.cseStatus==CSEStatus.RUNNING):
		console.run()
	else:
		raise TimeoutError(L.logErr(f'CSE did not start within {C.cseStartupDelay * 3} seconds'))




# @event.cseStartup
# def testEvent(name: str) -> None:
# 	print(f'Event {name} received')
