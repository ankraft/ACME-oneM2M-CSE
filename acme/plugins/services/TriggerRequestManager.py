#
#	TriggerRequestManager.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Manager for TriggerRequest functionality
#

from acme.helpers import PluginManager
from acme.runtime.Logging import Logging as L

@PluginManager.plugin(property='triggerRequestManager', tags=['acme', 'core'])
class TriggerRequestManagerPlugin:


	@PluginManager.init
	def init(self) -> None:
		L.isInfo and L.log('RegistrationManager initialized')
		

	@PluginManager.finish
	def shutdown(self) -> None:
		L.isInfo and L.log('RegistrationManager shut down')


	@PluginManager.start
	def start(self) -> None:
		L.isInfo and L.log('RegistrationManager started')


	@PluginManager.stop
	def stop(self) -> None:
		L.isInfo and L.log('RegistrationManager stopped')


	@PluginManager.restart
	def restart(self) -> None:
		L.log('TriggerRequestManager restarted')

	##############################################################################
	