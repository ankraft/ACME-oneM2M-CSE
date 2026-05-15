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
from ..runtime.ConsoleBase import ConsoleBase
from ..runtime.Factory import Factory
from ..runtime.Importer import Importer
from ..runtime.Logging import Logging as L
from ..runtime.Management import ManagementSupport
from ..runtime.PluginSupport import pluginManager, DependencyError, provide
from ..runtime.ScriptManager import ScriptManager
from ..runtime.Storage import Storage
from ..runtime.EventManager import eventManager

from ..services.Dispatcher import Dispatcher
from ..services.RequestManager import RequestManager
from ..services.NotificationManager import NotificationManager
from ..services.RegistrationManager import RegistrationManager
from ..services.SecurityManager import SecurityManager
from ..services.Validator import Validator

##############################################################################

# singleton main components. These variables will hold all the various manager
# components that are used throughout the CSE implementation.

console:ConsoleBase = None
""" Runtime instance of the `acme.plugins.runtime.Console.Console` or `acme.plugins.runtime.MinimalConsole.MinimalConsole`. """

dispatcher:Dispatcher = Dispatcher()
"""	Runtime instance of the `Dispatcher`. """

factory:Factory = Factory()
"""	Runtime instance of the resource factory. """

importer:Importer = Importer()
"""	Runtime instance of the `Importer`. """

managementSupport:ManagementSupport = ManagementSupport()
"""	Runtime instance of the `ManagementSupport`. """

notification:NotificationManager = NotificationManager()
"""	Runtime instance of the `NotificationManager`. """

registration:RegistrationManager = RegistrationManager()
"""	Runtime instance of the `RegistrationManager`. """

request:RequestManager = RequestManager()
"""	Runtime instance of the `RequestManager`. """

script:ScriptManager = ScriptManager()
"""	Runtime instance of the `ScriptManager`. """

security:SecurityManager = SecurityManager()
"""	Runtime instance of the `SecurityManager`. """

storage:Storage = Storage()
"""	Runtime instance of the `Storage`. """

validator:Validator = Validator()
"""	Runtime instance of the `Validator`. """

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
	BackgroundWorkerPool.setLogger(lambda l,m: L.logWithLevel(l, m, stackOffset=2))
	BackgroundWorkerPool.setJobBalance(	balanceTarget=Configuration.cse_operation_jobs_balanceTarget,
										balanceLatency=Configuration.cse_operation_jobs_balanceLatency,
										balanceReduceFactor=Configuration.cse_operation_jobs_balanceReduceFactor)

	try:
		# Provide the main components to the plugin manager, so that they can be injected into 
		# plugins and other components. 
		pluginManager.provide('acme.runtime.Factory', factory)
		pluginManager.provide('acme.runtime.Importer', importer)
		pluginManager.provide('acme.runtime.Storage', storage)		
		pluginManager.provide('acme.services.Dispatcher', dispatcher)	
		pluginManager.provide('acme.services.NotificationManager', notification)
		pluginManager.provide('acme.services.RegistrationManager', registration)
		pluginManager.provide('acme.services.RequestManager', request)
		pluginManager.provide('acme.services.SecurityManager', security)
		pluginManager.provide('acme.services.Validator', validator)
		pluginManager.provide('acme.runtime.ScriptManager', script)
		pluginManager.provide('acme.runtime.Management', managementSupport)


		# TODO provide the eventmanger as well? Check the usage in ACME modules

		# TODO add a FORCESHUTDOWN event

		
		# Initialize the plugin manager
		# This loads, configures and validates the plugins as well
		pluginManager.startup()					# Initialize and starts
		importer.initialize()					# Call the initialize method
		
		# Start the database plugins and the storage first
		pluginManager.start(tags=['acme', 'database'])	

		storage.initialize()					# Initialize the storage manager

		importer.importResourcePolicies()		# Before initializing other components, import the resource policies

		# Initialize other components
		registration.initialize()
		validator.initialize()
		dispatcher.initialize()	
		security.initialize()
		request.initialize()
		script.initialize()	
		notification.initialize()
		
		# Start the remaining plugins
		pluginManager.start(tags=['acme', 'binding'])
		pluginManager.start(tags=['acme', 'core'])	
		pluginManager.start(tags=['acme', 'remote'])
		pluginManager.start(tags=['acme', 'ui'])


		# Check whether all plugin dependencies are resolved. This is done after starting the plugins to give them a chance to resolve their dependencies. If this fails, we cannot continue with the CSE startup.
		pluginManager.setupFinished()				
		
		# Import attribute, flexContainer and enum policies, and configuration documentation
		#
		# After this, the CSE reads the scripts from the default and runtime init directories.
		# It also runs the init script, if there is one. 
		#
		# When this fails, we cannot continue with the CSE startup
		if not importer.importPolicies() or not importer.importScripts():
			RC.cseStatus = CSEStatus.STOPPED
			return False

		# Start any non-ACME plugins 
		pluginManager.start(excludedTags=['acme'])

		# event.cseBootstrap()	# Send an event that the CSE bootstrap finished. This is executed after all components are initialized and started, but before importing policies and scripts.
		
		
	except ResponseException as e:
		L.logErr(f'Error during startup: {e.dbg}')
		RC.cseStatus = CSEStatus.STOPPED
		return False
	except KeyError as e:
		L.logErr(f'Error during startup: {e}')
		import traceback
		traceback.print_exc()
		RC.cseStatus = CSEStatus.STOPPED
		return False
	except (DependencyError, ValueError) as e:
		L.logErr(f'Error during startup: {e}')
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
		eventManager.cseStartup()	# type: ignore

		L.console('CSE started')
		L.log('CSE started')

	BackgroundWorkerPool.newActor(_startUpFinished, delay=C.cseStartupDelay if RC.isHeadless else C.cseStartupDelay / 2.0, name='Delayed_startup_message').start()
	
	return True


@provide('acme.runtime.CSE.shutdown')
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
	if eventManager:	# send shutdown event
		eventManager.cseShutdown() 	# type: ignore
	
	# Shutdown any non-ACME plugins 
	pluginManager.stop(excludedTags=['acme'])

	# shutdown the services
	# Stop all the plugins, except the database plugins, which are needed during shutdown 
	# This leaves only the database plugins running
	pluginManager and pluginManager.stop(tags=['acme', 'ui'])
	pluginManager and pluginManager.stop(tags=['acme', 'remote'])
	pluginManager and pluginManager.stop(tags=['acme', 'core'])

	script and script.shutdown()
	notification and notification.shutdown()
	request and request.shutdown()
	dispatcher and dispatcher.shutdown()
	security and security.shutdown()
	validator and validator.shutdown()
	registration and registration.shutdown()

	storage  and storage.shutdown()
	pluginManager and pluginManager.stop(tags=['acme', 'database'])
	pluginManager and pluginManager.stop(tags=['acme', 'bindings'])

	# This shutdowns all plugins, stopping the ones that are still running
	pluginManager and pluginManager.shutdown()	

	L.isInfo and L.log('CSE shut down')
	L.console('CSE shut down', nlb = True)

	L.finit()
	RC.cseStatus = CSEStatus.STOPPED

	# If the CSE is stopping to restart, we exit with a special exit code
	if _cseStatus == CSEStatus.SHUTTINGDOWNRESTART:
		os._exit(82) 


@provide('acme.runtime.CSE.forceShutdown')
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


@provide('acme.runtime.CSE.resetCSE')
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
		pluginManager.pausePlugins(tags=['acme', 'binding'])
		# Restart all plugins, except core plugins. They are restarted via an event
		pluginManager.restartPlugins(tags=['acme', 'core'])	
		pluginManager.restartPlugins(tags=['acme', 'ui'])	

		storage.purge()

		pluginManager.restartPlugins(excludedTags=['acme'])

		# The following event is executed synchronously to give every component
		# a chance to finish
		eventManager.cseReset()	# type: ignore [attr-defined]

		# We only import policies, documentation and scripts during restart
		# But we don't import the resource policies again.
		if not importer.importPolicies() or not importer.importScripts():
			pluginManager.textUI and pluginManager.textUI.shutdown()
			L.logErr('Error during import')
			sys.exit()	# what else can we do?

		# Unpause all binding plugins to start receiving requests again after reset.
		pluginManager.unpausePlugins(tags=['acme', 'binding'])	

		# Restart remote plugins after the main
		pluginManager.restartPlugins(tags=['acme', 'remote'])	


		# Enable log queuing again
		L.queueOn()

		# Send restarted event
		eventManager.cseRestarted()	# type: ignore [attr-defined]   

		RC.cseStatus = CSEStatus.RUNNING
		RC.startupTime = utcTime()	# Set the startup time when the CSE is fully started and running
		L.isWarn and L.logWarn('Resetting CSE finished')


def restartCSE() -> None:
	"""	Restart the CSE. This actually shuts down and terminates the CSE but with a special exit code 
		to indicate that the CSE should be restarted. 
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
		if console:
			console.run()
	else:
		raise TimeoutError(L.logErr(f'CSE did not start within {C.cseStartupDelay * 3} seconds'))


@provide('acme.runtime.CSE.setConsole')
def setConsole(consoleInstance: ConsoleBase) -> None:
	"""	Set the console instance for the CSE. This is used to set the console instance from the main console plugin.

		Args:
			consoleInstance: The console instance to set.
	"""
	global console
	console = consoleInstance


# @event.cseStartup
# def testEvent(name: str) -> None:
# 	print(f'Event {name} received')
