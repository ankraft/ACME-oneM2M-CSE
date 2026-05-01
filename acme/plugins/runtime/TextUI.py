#
#	TextUI.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	A Textual UI for ACME CSE
#
"""	This module defines a textual UI for ACME CSE.
"""

from __future__ import annotations

from typing import Optional, Any, Literal
import asyncio

from ...runtime import CSE
from ...runtime.Logging import Logging as L
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.PluginSupport import plugin, start, stop, restart, configure, validate
from ...runtime.EventManager import EventManager, onEvent, EventData, EventHandler
from ...etc.Types import CSEStatus
from ...etc.Constants import RuntimeConstants as RC

from ...textui.ACMETuiApp import ACMETuiApp, ACMETuiQuitReason

eventManager = EventManager()	# type: ignore
"""	Event manager singleton instance. """

# TODO Delete resource? After better dialog option is available
# TODO Copy resource


_textUI:TextUI = None
"""	Active textUI instance """

@EventHandler
@plugin(property='textUI', tags=['acme', 'ui'])
class TextUI(object):

	__slots__ = (
		'tuiApp'
	)
	
	def __init__(self) -> None:
		self.tuiApp:ACMETuiApp = None


	@start
	def start(self) -> None:
		global _textUI

		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)	# type: ignore

		# Add handlers for registrations here. This is not done in the textUI classes because it it
		# is not always clear when they are removed and re-created

		CSE.event.addHandler([CSE.event.aeHasRegistered, 									# type:ignore[attr-defined]
							  CSE.event.aeHasDeregistered, 									# type:ignore[attr-defined]
							  CSE.event.deregisteredFromRegistrarCSE, 						# type:ignore[attr-defined]
							  CSE.event.registeredToRemoteCSE], self.registrationUpdate)	# type:ignore[attr-defined]

		_textUI = self
		L.isInfo and L.log('TextUI initialized')

		
	@stop
	def shutdown(self) -> bool:
		global _textUI
		if _textUI.tuiApp:
			_textUI.tuiApp.exit()
		#_textUI = None
		L.isInfo and L.log('TextUI shut down')
		return True


	@restart
	def restart(self) -> None:
		"""	Restart the TextUI service.
		"""
		L.logDebug('TextUI restarted')


	# TODO the following parameters do not match the event signatures, but we ignore this for now until
	# the arguments are used.
	# def registrationUpdate(self, name:str, resource:Resource, dct:dict=None, anotherResource:Resource=None) -> None:
	def registrationUpdate(self, *args, **kwargs) -> None:		# type: ignore[no-untyped-def]
		if self.tuiApp and self.tuiApp.containerRegistrations:
			self.tuiApp.containerRegistrations.registrationsUpdate()


	@onEvent(eventManager.registeredToRegistrarCSE)
	@onEvent(eventManager.registreeCSEHasRegistered)
	@onEvent(eventManager.registreeCSEHasDeregistered)
	@onEvent(eventManager.csrUpdated)
	def registrationUpdate2(self, eventData: EventData) -> None:		# type: ignore[no-untyped-def]
		if self.tuiApp and self.tuiApp.containerRegistrations:
			self.tuiApp.containerRegistrations.registrationsUpdate()

	
	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'textui.startWithTUI', 
				 		'textui.theme', 
						'textui.refreshInterval', 
						'textui.maxRequestSize' ]:
			return

		# Restart TUI
		self.tuiApp.restart()
	

	def runUI(self) -> bool:

		# Disable console logging
		previousScreenLogging = L.enableScreenLogging
		L.enableScreenLogging = False
		while True and RC.cseStatus == CSEStatus.RUNNING:
			self.tuiApp = ACMETuiApp()
			try:
				asyncio.run(self.tuiApp.run())
			except ValueError:	# This may have something to do with running in a non-async context. Ignore for now.
				L.console('Press # to return to UI')
			except Exception as e:
				L.logErr(str(e), exc = e)
			finally:
				self.tuiApp.cleanUp()
			if self.tuiApp.quitReason != ACMETuiQuitReason.restart:
				break
		
		# Re-enable console logging
		L.enableScreenLogging = previousScreenLogging

		result = self.tuiApp is not None and self.tuiApp.quitReason != ACMETuiQuitReason.quitAll	# False leads to ACME quit
		self.tuiApp = None
		return result


	#########################################################################


	def refreshResources(self) -> None:
		"""	Refresh the resources.
		"""
		if self.tuiApp:
			self.tuiApp.refreshResources()
			
	def scriptPrint(self, scriptName:str, msg:str) -> None:
		"""	Print a line to the script output.

			Args:
				scriptName: Name of the script.
				msg: Message to print.
		"""
		if self.tuiApp:
			self.tuiApp.scriptPrint(scriptName, msg)
	

	def scriptLog(self, scriptName:str, msg:str) -> None:
		"""	Print a line to the script log output.

			Args:
				scriptName: Name of the script.
				msg: Message to print.
		"""
		if self.tuiApp:
			self.tuiApp.scriptLog(scriptName, msg)
	

	def scriptLogError(self, scriptName:str, msg:str) -> None:
		"""	Print a line to the script log output.

			Args:
				scriptName: Name of the script.
				msg: Message to print.
		"""
		if self.tuiApp:
			self.tuiApp.scriptLogError(scriptName, msg)
	

	def scriptClearConsole(self, scriptName:str) -> None:
		"""	Clear the script console.

			Args:
				scriptName: Name of the script.
		"""
		if self.tuiApp:
			self.tuiApp.scriptClearConsole(scriptName)
	

	def scriptShowConfirmation(self, msg:str, 
									 title:str, 
									 confirmButtonText:Optional[str]='Confirm', 
									 cancelButtonText:Optional[str]='Cancel') -> Optional[bool]:
		"""	Show a confirmation dialog.

			Args:
				msg: Message to show.
				title: Title of the dialog.
				confirmButtonText: Text for the confirm button.
				cancelButtonText: Text for the cancel button.

			Returns:
				True if the user confirmed, False if the user cancelled, None if TUI is not available.
		"""
		if self.tuiApp:
			return self.tuiApp.showConfirmation(msg, title, confirmButtonText, cancelButtonText)
		return None
	

	def scriptShowNotification(self, msg:str, title:str, severity:Literal['information', 'warning', 'error'], timeout:float) -> None:
		"""	Show a notification.

			Args:
				msg: Message to show.
				title: Title of the notification.
				severity: Severity of the notification.
				timeout: Timeout in seconds.
		"""
		if self.tuiApp:
			self.tuiApp.showNotification(msg, title, severity, timeout)


	def scriptVisualBell(self, scriptName:str) -> None:
		"""	Visual bell.

			Args:
				scriptName: Name of the script.
		"""
		if self.tuiApp:
			self.tuiApp.scriptVisualBell(scriptName)


	#########################################################################
	#
	#	Configuration
	#

	@configure
	def configure(self, config: Configuration) -> None:
		parser = config.configParser

		#	Text UI
		config.textui_enable = parser.getboolean('textui', 'enable', fallback=True)
		config.textui_refreshInterval = parser.getfloat('textui', 'refreshInterval', fallback=2.0)
		config.textui_startWithTUI = parser.getboolean('textui', 'startWithTUI', fallback=False)
		config.textui_theme = parser.get('textui', 'theme', fallback='dark')
		config.textui_maxRequestSize = parser.getint('textui', 'maxRequestSize', fallback=10000)
		config.textui_notificationTimeout = parser.getfloat('textui', 'notificationTimeout', fallback=2.0)
		config.textui_enableTextEditorSyntaxHighlighting = parser.getboolean('textui', 'enableTextEditorSyntaxHighlighting', fallback=False)


	@validate
	def validate(self, config: Configuration) -> None:

		# override configuration with command line arguments
		if Configuration._args_lightScheme is not None:
			Configuration.textui_theme = Configuration._args_lightScheme
		if Configuration._args_textUI is not None:
			Configuration.textui_startWithTUI = Configuration._args_textUI

		# Text UI settings
		if config.textui_maxRequestSize <= 0:
			raise ConfigurationError(r'[i]\[textui]:maxRequestSize[/i] must be > 0s')
		config.textui_theme = config.textui_theme.lower()
		if config.textui_theme not in [ 'dark', 'light' ]:
			raise ConfigurationError(fr'[i]\[textui]:theme[/i] must be "light" or "dark"')
		if config.textui_maxRequestSize < 0:
			raise ConfigurationError(fr'[i]\[textui]:maxRequestSize[/i] must be >= 0')
		if config.textui_notificationTimeout < 0.0:
			raise ConfigurationError(fr'[i]\[textui]:notificationTimeout[/i] must be >= 0')

