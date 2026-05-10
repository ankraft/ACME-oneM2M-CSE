#
#	ConsoleBase.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Base class for console plugins. """

from typing import Optional, TYPE_CHECKING
import sys

from ..helpers.KeyHandler import FunctionKey, stopLoop, waitForKeypress
from ..helpers.PluginManager import requires
from ..etc.Constants import RuntimeConstants as RC
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration

if TYPE_CHECKING:
	from acme.plugins.runtime.TextUI import TextUI

@requires(textUI='acme.plugins.runtime.TextUI', required=False)
class ConsoleBase:
	"""	Base class for console plugins. 
	"""

	textUI: TextUI = None	# type: ignore
	""" Injected TextUI instance. """

	def shutdown(self) -> bool:
		"""	Shutdown the *Console* instance.
			
			Return:
				Always returns *True*.
		"""
		L.isInfo and L.log('Console shut down')
		return True


	def stop(self) -> None:
		"""	Stop the console loop. 
		"""
		stopLoop()


	def run(self) -> None:
		""" This method must be implemented by a derived class.
			It runs the main console loop. This is a blocking call that will run until
			the console is stopped.
		"""
		raise NotImplementedError('The run method must be implemented by a derived class')
	

	def runTUI(self, key:Optional[str]=None
			) -> None:
		"""	Open the text UI.
		"""
		if self.textUI:
			if not self.textUI.runUI():
				# If the TUI was closed with an error or when shutting down, 
				# stop the console loop and raise a KeyboardInterrupt to stop the CSE.
				raise KeyboardInterrupt() 
		else:
			L.console('Text UI not enabled', isError=True)


	def shutdownCSE(self, key:str) -> None:
		"""	Shutdown the CSE. Confirm shutdown before actually doing that.

			Args:
				key: Input key. Ignored.
		"""
		if not RC.isHeadless:
			if Configuration.console_confirmQuit:
				L.off()
				L.console('Press quit-key again to confirm -> ', plain=True, end='')
				if waitForKeypress(5) not in ['Q', FunctionKey.CTRL_C]:
					L.console('canceled')
					L.on()
					return
				L.console('confirmed')
				L.on()
		sys.exit()


	def doStartWithTextUI(self) -> bool:
		"""	Check if the console should start with the text UI. 
			
			Return:
				*True* if the console should start with the text UI, *False* otherwise.
		"""
		return Configuration.textui_startWithTUI and not RC.isHeadless


