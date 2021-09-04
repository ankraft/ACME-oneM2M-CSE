#
#	EventManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing event handlers and events
#

from __future__ import annotations
from ..helpers import EventManager as HelpersEventManager
from ..services.Logging import Logging as L

# TODO: create/delete each resource to count! resourceCreate(ty)

# TODO move event creations from here to the resp modules.


class EventManager(HelpersEventManager.EventManager):

	def __init__(self) -> None:
		super().__init__()

		self.addEvent('httpRetrieve')
		self.addEvent('httpCreate')
		self.addEvent('httpDelete')
		self.addEvent('httpUpdate')
		self.addEvent('httpRedirect')
		self.addEvent('httpSendRetrieve')
		self.addEvent('httpSendCreate')
		self.addEvent('httpSendUpdate')
		self.addEvent('httpSendDelete')
		self.addEvent('createResource')
		self.addEvent('updateResource')
		self.addEvent('deleteResource')
		self.addEvent('expireResource')
		self.addEvent('mqttRetrieve')
		self.addEvent('mqttCreate')
		self.addEvent('mqttDelete')
		self.addEvent('mqttUpdate')
		self.addEvent('mqttRedirect')
		self.addEvent('mqttSendRetrieve')
		self.addEvent('mqttSendCreate')
		self.addEvent('mqttSendUpdate')
		self.addEvent('mqttSendDelete')
		self.addEvent('cseStartup')
		self.addEvent('cseShutdown', runInBackground=False)
		self.addEvent('logError')
		self.addEvent('logWarning')
		self.addEvent('registeredToRemoteCSE')
		self.addEvent('deregisteredFromRemoteCSE')
		self.addEvent('remoteCSEHasRegistered')
		self.addEvent('remoteCSEUpdate')
		self.addEvent('remoteCSEHasDeregistered')
		self.addEvent('notification')


	def shutdown(self) -> bool:
		super().shutdown()
		L.isInfo and L.log('EventManager shut down')
		return True
