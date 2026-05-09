#
#	MinimalConsole.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This plugin defines a minimal console for the CSE.

	Though this is a plugin, it provides the main console functionality for the CSE. 
	It is either this plugin or the rich console plugin that is used to run the main
	loop of the CSE.

	Note, that this plugin does not fully follow the plugin lifecycle, as
	it is not started by the PluginManager, but instead it is run
	directly by the CSE. 
"""

from __future__ import annotations
from typing import Callable

from ...helpers.KeyHandler import loop, Commands, FunctionKey
from ...etc.Constants import RuntimeConstants as RC
from ...runtime.Logging import Logging as L											# type: ignore
from ...runtime.ConsoleBase import ConsoleBase
from ...runtime.PluginSupport import plugin, start, requires
from ...runtime.EventManager import EventManager, EventData, eventManager

@plugin(tags=['acme', 'ui'])
@requires(cseSetConsole='acme.runtime.CSE.setConsole')
class MinimalConsole(ConsoleBase):
	"""	Plugin class to add a minimal console functionality to the CSE. 
	"""

	cseSetConsole: Callable[[ConsoleBase], None] = None
	""" Function to set the console instance in the CSE. """

	@start
	def startMinimalConsole(self) -> None:
		"""	Initialize the minimal console plugin. Set the console instance in the CSE. 
		"""
		self.cseSetConsole(self)
		L.isDebug and L.logDebug('Minimal Console initialized')


	def run(self) -> None:
		"""	Run the console. This is a blocking call that will run until the console is stopped, either
			by a shutdown command, interrupt, or by a shutdown of the CSE. 
		"""
		L.isDebug and L.logDebug('Running Minimal Console plugin')
		commands:Commands = {
			'Q': 				self.shutdownCSE,
			FunctionKey.CTRL_C: self.shutdownCSE,
			'#': 				lambda ch: self.runTUI() if not RC.isHeadless else None
		}

		loop(commands, 
			 catchKeyboardInterrupt=True, 
			 headless=RC.isHeadless,
			 catchAll=lambda ch: eventManager.keyboard(EventData(payload=ch)), # type: ignore [attr-defined]
			 nextKey='#' if self.doStartWithTextUI() else None,
			 ignoreException=False,
			)
