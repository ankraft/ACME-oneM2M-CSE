#
#	EventManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing event handlers and events
#
"""	Implementation of the EventManager, which manages events and event handlers. """

from __future__ import annotations

from ..helpers.EventManager import EventManager as HelpersEventManager, Event, EventHandler, EventData, onEvent

# TODO: create/delete each resource to count! resourceCreate(ty)

# TODO move event creations from here to the resp modules.


class EventManager(HelpersEventManager):
	""" Event manager class. 
	"""

	def __init__(self) -> None:
		""" Initialize the event manager and create all events. 
		"""
		super().__init__()

		# Create events for all operations and protocols
		for proto in ('coap', 'http', 'mqtt', 'ws'):
			for op in ('Retrieve', 'Create', 'Delete', 'Update', 'Notify'):
				self.addEvent(f'{proto}{op}')
				self.addEvent(f'{proto}Send{op}')

		# Create events for all resource operations
		for op in ('retrieve', 'create', 'update', 'delete', 'expire', 
			 	   'change'  # whenever a resource is updated or changed in any way
				   ):
			self.addEvent(f'{op}Resource')
		
		self.addEvent('createChildResource')
		self.addEvent('requestReceived')								# Thrown whenever a request is received
		self.addEvent('responseReceived')								# Thrown whenever a response is received
		self.addEvent('cseStartup')										# After the CSE started
		self.addEvent('cseShutdown', runInBackground=False)				# When the CSE is shutdown
		self.addEvent('cseReset', runInBackground=False)				# When the CSE is reset
		self.addEvent('cseRestarted', runInBackground=False)			# After the CSE finished the reset
		self.addEvent('logError')
		self.addEvent('logWarning')
		self.addEvent('registeredToRegistrarCSE')
		self.addEvent('deregisteredFromRegistrarCSE')
		self.addEvent('registreeCSEHasRegistered')
		self.addEvent('csrUpdated')
		self.addEvent('registreeCSEHasDeregistered')
		self.addEvent('registeredToRemoteCSE')							# After this CSE has also registered to the registering remote CSE
		self.addEvent('aeHasRegistered')								# AE has registered
		self.addEvent('aeHasDeregistered')								# AE has dereigistered
		self.addEvent('notification')
		self.addEvent('configUpdate', runInBackground=False)
		self.addEvent('keyboard', runInBackground=False)
		self.addEvent('acmeNotification', runInBackground=False)		# Special event if a notification targets a URL scheme "acme://"
		# No finished message bc logging is not not initialized yes


# Initialize the event manager singleton instance.
eventManager: EventManager = EventManager()
""" Event manager singleton instance. """