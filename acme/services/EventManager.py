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
		self.addEvent('httpNotify')
		self.addEvent('httpRedirect')
		self.addEvent('httpSendRetrieve')
		self.addEvent('httpSendCreate')
		self.addEvent('httpSendUpdate')
		self.addEvent('httpSendDelete')
		self.addEvent('httpSendNotify')
		self.addEvent('createResource')
		self.addEvent('updateResource')
		self.addEvent('deleteResource')
		self.addEvent('expireResource')
		self.addEvent('createChildResource')
		self.addEvent('mqttRetrieve')
		self.addEvent('mqttCreate')
		self.addEvent('mqttDelete')
		self.addEvent('mqttUpdate')
		self.addEvent('mqttNotify')
		self.addEvent('mqttRedirect')
		self.addEvent('mqttSendRetrieve')
		self.addEvent('mqttSendCreate')
		self.addEvent('mqttSendUpdate')
		self.addEvent('mqttSendDelete')
		self.addEvent('mqttSendNotify')
		self.addEvent('requestReceived')								# Thrown whenever a request is received
		self.addEvent('responseReceived')								# Thrown whenever a response is received
		self.addEvent('cseStartup')										# After the CSE started
		self.addEvent('cseShutdown', runInBackground = False)			# When the CSE is shutdown
		self.addEvent('cseReset', runInBackground = False)				# When the CSE is reset
		self.addEvent('cseRestarted', runInBackground = False)			# After the CSE finished the reset
		self.addEvent('logError')
		self.addEvent('logWarning')
		self.addEvent('registeredToRemoteCSE')
		self.addEvent('deregisteredFromRemoteCSE')
		self.addEvent('remoteCSEHasRegistered')
		self.addEvent('remoteCSEUpdate')
		self.addEvent('remoteCSEHasDeregistered')
		self.addEvent('notification')
		self.addEvent('configUpdate', runInBackground = False)
		self.addEvent('keyboard', runInBackground = False)
		self.addEvent('acmeNotification', runInBackground = False)		# Special event if a notification targets a URL scheme "acme://"
		# No finished message bc logging is not not initialized yes


	def shutdown(self) -> bool:
		super().shutdown()
		L.isInfo and L.log('EventManager shut down')
		return True
