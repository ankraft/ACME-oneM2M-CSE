#
#	NotificationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles subscriptions and sending of notifications. 
#

"""	This module implements the notification manager service functionality for the CSE.
"""

from __future__ import annotations
from typing import Callable, Union, Any, cast, Optional

import sys, copy
from threading import Lock, current_thread

import isodate
from ..etc.Types import CSERequest, MissingData, ResourceTypes, NotificationContentType, NotificationEventType, TimeWindowType, EventEvaluationMode
from ..etc.Types import EventCategory, JSON, JSONLIST, ResourceTypes, Operation, OperationMonitor
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException, exceptionFromRSC
from ..etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR, SUBSCRIPTION_VERIFICATION_INITIATION_FAILED
from ..etc.ResponseStatusCodes import TARGET_NOT_REACHABLE, REMOTE_ENTITY_NOT_REACHABLE, OPERATION_NOT_ALLOWED
from ..etc.ResponseStatusCodes import OPERATION_DENIED_BY_REMOTE_ENTITY, NOT_FOUND
from ..etc.DateUtils import fromDuration, getResourceDate, cronMatchesTimestamp, utcDatetime
from ..etc.ACMEUtils import toSPRelative, pureResource, compareIDs
from ..etc.Utils import isAcmeUrl
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.TextTools import setXPath, findXPath
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.CRS import CRS
from ..resources.SUB import SUB
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..runtime.Logging import Logging as L

# TODO: removal policy (e.g. unsuccessful tries)

SenderFunction = Callable[[str], bool]	# type:ignore[misc] # bc cyclic definition 
""" Type definition for sender callback function. """


class NotificationManager(object):
	"""	This class defines functionalities to handle subscriptions and notifications.

		Attributes:
			lockBatchNotification: Internal lock instance for locking certain batch notification methods.
	"""

	__slots__ = (
		'lockBatchNotification',
		'lockNotificationEventStats',

		'_eventNotification',
	)


	def __init__(self) -> None:
		"""	Initialization of a *NotificationManager* instance.
		"""

		self.lockBatchNotification = Lock()					# Lock for batchNotifications
		self.lockNotificationEventStats = Lock()			# Lock for notificationEventStats

		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore
		
		# Optimize event handling
		self._eventNotification = CSE.event.notification	# type: ignore

		L.isInfo and L.log('NotificationManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Notification Manager.
		
			Returns:
				Boolean that indicates the success of the operation
		"""
		L.isInfo and L.log('NotificationManager shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the NotificationManager service.

			Args:
				name: The name of the event.
		"""
		L.isInfo and L.log('NotificationManager: Stopping all <CRS> window workers')

		# Stop all crossResourceSubscription workers
		periodicWorkers = BackgroundWorkerPool.stopWorkers('crsPeriodic_*')
		BackgroundWorkerPool.stopWorkers('crsSliding_*')

		# Restart the periodic crossResourceSubscription workers with its old arguments
		for worker in periodicWorkers:
			worker.start(**worker.args)

		L.isDebug and L.logDebug('NotificationManager restarted')

	###########################################################################
	#
	#	Subscriptions
	#

	def addSubscription(self, subscription:SUB, originator:str) -> None:
		"""	Add a new subscription. 

			Check each receipient with verification requests.
			
			Args:
				subscription: The new <sub> resource.
				originator: The request originator.
			
			Raises:
				`INTERNAL_SERVER_ERROR`: In case there is an internal DB error.
		"""
		L.isDebug and L.logDebug('Adding subscription')
		self._verifyNusInSubscription(subscription, originator = originator)	# verification requests happen here
		
		if not CSE.storage.upsertSubscription(subscription):
			raise INTERNAL_SERVER_ERROR('cannot add subscription to database')


	def removeSubscription(self, subscription:SUB|CRS, originator:str) -> None:
		""" Remove a subscription. 

			Send the deletion notifications, if possible.

			Args:
				subscription: The <sub> resource to remove.
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug('Removing subscription')

		# Send outstanding batchNotifications for a subscription
		self._flushBatchNotifications(subscription)

		# Send a deletion request to the subscriberURI
		if (su := subscription.su):
			if not self.sendDeletionNotification(su, subscription.ri):
				L.isWarn and L.logWarn(f'Deletion request failed for: {su}') # but ignore the error

		# Send a deletion request to the associatedCrossResourceSub
		if (acrs := subscription.acrs):
			self.sendDeletionNotification([ nu for nu in acrs ], subscription.ri)
		
		# Finally remove subscriptions from storage
		try:
			if not CSE.storage.removeSubscription(subscription):
				raise INTERNAL_SERVER_ERROR('cannot remove subscription from database')
		except NOT_FOUND:
			pass	# ignore, could be expected


	def updateSubscription(self, subscription:SUB, previousNus:list[str], originator:str) -> None:
		"""	Update a subscription.

			This method indirectly updates or rebuild the *notificationStatsInfo* attribute. It should be called
			add the end when updating a subscription.
		
			Args:
				subscription: The <sub> resource to update.
				previousNus: List of previous NUs of the same <sub> resoure.
				originator: The request originator.
			
			Return:
				Result object.
			"""
		L.isDebug and L.logDebug('Updating subscription')
		self._verifyNusInSubscription(subscription, previousNus, originator = originator)	# verification requests happen here
		if not CSE.storage.upsertSubscription(subscription):
			raise INTERNAL_SERVER_ERROR('cannot update subscription in database')


	def getSubscriptionsByNetChty(self, ri:str, 
										net:Optional[list[NotificationEventType]] = None, 
										chty:Optional[ResourceTypes] = None) -> JSONLIST:
		"""	Returns a (possible empty) list of subscriptions for a resource. 
		
			Args:
				net: optional filter for enc/net
				chty: optional single child resource typ

			Return:
				List of storage subscription documents, NOT Subscription resources.
			"""
		if not (subs := CSE.storage.getSubscriptionsForParent(ri)):
			return []
		result:JSONLIST = []
		for each in subs:
			if _n := each.get('net'):	# net might be empty of None
				if net and any(x in net for x in _n):
					result.append(each)
		
		# filter by chty if set
		if chty:
			result = [ each for each in result if (_chty := each['chty']) is None or chty in _chty]

		return result


	def checkOperationSubscription(self, resource:Resource,
								op:Operation,
								originator:str) -> None:
		# TODO doc
		L.isDebug and L.logDebug(f'Checking operation subscriptions ({op.name}) originator: {originator}')

		self.checkSubscriptions(resource, reason = NotificationEventType.notSet, originator = originator, operation = op)


	def checkSubscriptions(	self, 
							resource:Optional[Resource], 
							reason:NotificationEventType, 
							originator:str,
							childResource:Optional[Resource] = None, 
							modifiedAttributes:Optional[JSON] = None,
							ri:Optional[str] = None,
							missingData:Optional[dict[str, MissingData]] = None,
							operation:Optional[Operation] = None) -> None:
		"""	Check and handle resource events.

			This method looks for subscriptions of a resource and tests, whether an event, like *update* etc, 
			will lead to a notification. It then creates and sends the notification to all targets.

			Args:
				resource: The resource that received the event resp. request.
				reason: The `NotificationEventType` to check.
				originator: The originator of the request that caused the event.
				childResource: An optional child resource of *resource* that might be updated or created etc.
				modifiedAttributes: An optional `JSON` structure that contains updated attributes.
				ri: Optionally provided resource ID of `Resource`. If it is provided, then *resource* might be *None*.
					It will then be used to retrieve the resource.
				missingData: An optional dictionary of missing data structures in case the *TimeSeries* missing data functionality is handled.
				operation: An optional operation that is checked against the subscription's operationMonitor. This overrides the *reason*.
		"""
		
		if resource and resource.isVirtual():
			return 
		if childResource and childResource.isVirtual():
			return
		
		# Check whether the resource has subscriptions at all
		if resource and resource.getSubscriptionCounter() == 0:
			return
			
		ri = resource.ri if not ri else ri
		L.isDebug and L.logDebug(f'Checking subscriptions ({reason.name}({reason.value})) ri: {ri}')

		# ATTN: The "subscription" returned here are NOT the <sub> resources,
		# but an internal representation from the 'subscription' DB !!!
		# Access to attributes is different bc the structure is flattened
		if (subs := CSE.storage.getSubscriptionsForParent(ri)) is None:
			return
		
		# EXPERIMENTAL Add "subi" subscriptions to the list of subscriptions to check
		if resource and (subi := resource.subi) is not None:
			for eachSubi in subi:
				if (sub := CSE.storage.getSubscription(eachSubi)) is None:
					L.logErr(f'Cannot retrieve subscription: {eachSubi}')
					continue
				# TODO ensure uniqueness
				subs.append(sub)

		for sub in subs:

			# Test for operationMonitor condition first. Any will match successfull.
			# Only if the operationMonitor is set
			foundOperationMonitor:OperationMonitor|None = None
			if operation is not None:
				if (om := sub.get('om')) is not None:
					for o in om:
						_org = o.get('org')
						_op = o.get('ops')

						# Test whether a originator is set and if it is NOT the same as the originator of the request
						if _org is not None and _org != originator:
							continue
						if _op is not None and _op != operation:
							continue
						foundOperationMonitor = o
						break
				# Skip if no operationMonitor condition is found
				if not foundOperationMonitor:
					continue

			# Now test for the reason, only if no operationMonitor is set
			if foundOperationMonitor is None:
				net = sub.get('net')
				# Test for the NET condition
				if net is None:
					continue
				if reason not in net:
					continue

			# Prevent own notifications for subscriptions 
			ri = sub.get('ri')

			# Test whether reason is included in the subscription
			if childResource and \
				ri == childResource.ri and \
				reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:
					continue

			# Check the subscription's schedule, but only if it is not an immediate notification
			if not ((nec := sub.get('nec')) and nec == EventCategory.Immediate):
				if (_sc := CSE.storage.searchScheduleForTarget(ri)):
					_ts = utcDatetime()

					# Check whether the current time matches the schedule
					for s in _sc:
						if cronMatchesTimestamp(s, _ts):
							break
					else:
						# No schedule matches the current time, so continue with the next subscription
						continue

			match reason:
				case NotificationEventType.createDirectChild | NotificationEventType.deleteDirectChild:	# reasons for child resources
					chty = sub['chty']
					if chty and not childResource.ty in chty:	# skip if chty is set and child.type is not in the list
						continue
					self._handleSubscriptionNotification(sub, 
														 reason, 
														 resource = childResource, 
														 modifiedAttributes = modifiedAttributes, 
														 asynchronous = Configuration.cse_asyncSubscriptionNotifications,
														 operationMonitor = foundOperationMonitor,
														 originator = originator)
					self.countNotificationEvents(ri)
			
				# Check Update and enc/atr vs the modified attributes 
				case NotificationEventType.resourceUpdate if (atr := sub.get('atr')) and modifiedAttributes:
					found = False
					for k in atr:
						if k in modifiedAttributes:
							found = True
					if found:	# any one found
						self._handleSubscriptionNotification(sub, 
															 reason, 
															 resource = resource, 
															 modifiedAttributes = modifiedAttributes,
															 asynchronous = Configuration.cse_asyncSubscriptionNotifications,
															 operationMonitor = foundOperationMonitor,
															 originator = originator)
						self.countNotificationEvents(ri)
					else:
						L.isDebug and L.logDebug('Skipping notification: No matching attributes found')
			
				#  Check for missing data points (only for <TS>)
				case NotificationEventType.reportOnGeneratedMissingDataPoints if missingData:
					md = missingData[sub.get('ri')]
					if md.missingDataCurrentNr >= md.missingDataNumber:	# Always send missing data if the count is greater then the minimum number
						self._handleSubscriptionNotification(sub, 
															 NotificationEventType.reportOnGeneratedMissingDataPoints, 
															 missingData = copy.deepcopy(md),
															 asynchronous = Configuration.cse_asyncSubscriptionNotifications,
															 operationMonitor = foundOperationMonitor)
						self.countNotificationEvents(ri)
						md.clearMissingDataList()

				case NotificationEventType.blockingUpdate | NotificationEventType.blockingRetrieve | NotificationEventType.blockingRetrieveDirectChild:
					self._handleSubscriptionNotification(sub, 
														reason, 
														resource, 
														modifiedAttributes = modifiedAttributes,
														asynchronous = False,
														operationMonitor = foundOperationMonitor,
														originator = originator)	# blocking NET always synchronous!
					self.countNotificationEvents(ri)

				# case NotificationEventType.notSet:	# ignore
				# 	pass

				# all other reasons that target the resource
				case _:
					self._handleSubscriptionNotification(sub, 
														reason, 
														resource, 
														modifiedAttributes = modifiedAttributes,
														asynchronous = Configuration.cse_asyncSubscriptionNotifications,
														operationMonitor = foundOperationMonitor,
														originator = originator)
					self.countNotificationEvents(ri)


	def checkPerformBlockingUpdate(self, resource:Resource, 
										 originator:str, 
										 updatedAttributes:JSON, 
										 finished:Optional[Callable] = None) -> None:
		"""	Check for and perform a *blocking update* request for resource updates that have this event type 
			configured.

			Args:
				resource: The updated resource.
				originator: The originator of the original request.
				updatedAttributes: A structure of all the updated attributes.
				finished: Callable that is called when the notifications were successfully sent and a response was received.
		"""
		L.isDebug and L.logDebug('Looking for blocking UPDATE')

		# TODO 2) Prevent or block all other UPDATE request primitives to this target resource.

		# Get blockingUpdate <sub> for this resource , if any, and iterate over them.
		# This should only be one!
		for eachSub in self.getSubscriptionsByNetChty(resource.ri, [NotificationEventType.blockingUpdate]):

			# TODO check notification permission!

			notification:JSON = {
				'm2m:sgn' : {
					'nev' : {
						'net' : NotificationEventType.blockingUpdate.value
					},
					'sur' : toSPRelative(eachSub['ri'])
				}
			}

			# Check attributes in enc
			if atr := eachSub['atr']:
				jsn, _, _ = pureResource(updatedAttributes)
				if len(set(jsn.keys()).intersection(atr)) == 0:	# if the intersection between updatedAttributes and the enc/atr contains is empty, then continue
					L.isDebug and L.logDebug(f'skipping <SUB>: {eachSub["ri"]} because configured enc/attribute condition doesn\'t match')
					continue

			# Don't include virtual resources
			if not resource.isVirtual():
				# Add representation
				setXPath(notification, 'm2m:sgn/nev/rep', updatedAttributes)
				

			# Send notification and handle possible negative response status codes
			try:
				res = CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
															   to = eachSub['nus'][0],
															   originator = originator,
															   pc = notification)
												   )[0].result	# there should be at least one result
				if res.rsc == ResponseStatusCode.OK:
					if finished:
						finished()
					continue
			
				# "Forward" an exception
				raise exceptionFromRSC(res.rsc)
				
			# Modify the result status code for some failure response status codes
			except TARGET_NOT_REACHABLE:
				raise REMOTE_ENTITY_NOT_REACHABLE(L.logDebug(f'remote entity not reachable: {eachSub["nus"][0]}'))
			except OPERATION_NOT_ALLOWED:
				raise OPERATION_DENIED_BY_REMOTE_ENTITY(L.logDebug(f'operation denied by remote entity: {eachSub["nus"][0]}'))
			except:
					# General negative response status code
				raise
			

		# TODO 5) Allow all other UPDATE request primitives for this target resource.


	def checkPerformBlockingRetrieve(self, 
									 resource:Resource, 
									 request:CSERequest, 
									 finished:Optional[Callable] = None) -> None:
		r"""Perform a blocking RETRIEVE. If this notification event type is configured a RETRIEVE operation to
			a resource causes a notification to a target. It is expected that the target is updating the resource
			**before** responding to the notification.

			A NOTIFY permission check is done against the originator of the \<subscription> resource, not
			the originator of the request.

			Note:
				This functionality is experimental and not part of the oneM2M spec yet.

			Args:
				resource: The resource that is the target of the RETRIEVE request.
				request: The original request.
				finished: Callable that is called when the notifications were successfully sent and received.
			Return:
				Result instance indicating success or failure.
		"""

		# TODO check notify permission for originator
		# TODO prevent second notification to same 
		# EXPERIMENTAL
		L.isDebug and L.logDebug('Looking for blocking RETRIEVE')

		# Get blockingRetrieve <sub> for this resource , if any
		subs = self.getSubscriptionsByNetChty(resource.ri, [NotificationEventType.blockingRetrieve])
		# get and add blockingRetrieveDirectChild <sub> for this resource type, if any
		subs.extend(self.getSubscriptionsByNetChty(resource.pi, [NotificationEventType.blockingRetrieveDirectChild], chty = resource.ty))

		# Do this for all subscriptions
		countNotifications = 0
		for eachSub in subs:	# This should be only one!
			maxAgeRequest:float = None
			maxAgeSubscription:float = None

			# Check for maxAge attribute provided in the request
			maxAgeRequest = request._ma

			# Check for maxAge attribute provided in the subscription
			maxAgeSubscription = eachSub['ma']	# EXPERIMENTAL blocking retrieve
				
			# Return if neither the request nor the subscription have a maxAge set
			if maxAgeRequest is None and maxAgeSubscription is None:
				L.isDebug and L.logDebug(f'no maxAge configured, blocking RETRIEVE notification not necessary')
				return


			# Is either "maxAge" of the request or the subscription reached?
			L.isDebug and L.logDebug(f'request.maxAge: {maxAgeRequest} subscription.maxAge: {maxAgeSubscription}')
			maxAgeSubscription = maxAgeSubscription if maxAgeSubscription is not None else sys.float_info.max
			maxAgeRequest = maxAgeRequest if maxAgeRequest is not None else sys.float_info.max

			if resource.lt > getResourceDate(-int(min(maxAgeRequest, maxAgeSubscription))):
				# To early for this subscription
				continue
			L.isDebug and L.logDebug(f'blocking RETRIEVE notification necessary')

			notification = {
				'm2m:sgn' : {
					'nev' : {
						'net' : eachSub['net'][0],	# Add the first and hopefully only NET to the notification
					},
					'sur' : toSPRelative(eachSub['ri'])
				}
			}
			# Add creator of the subscription!
			(subOriginator := eachSub['org']) is not None and setXPath(notification, 'm2m:sgn/cr', subOriginator)	# Set creator in notification if it was present in subscription

			# Add representation, but don't include virtual resources
			if not resource.isVirtual():
				setXPath(notification, 'm2m:sgn/nev/rep', resource.asDict())

			countNotifications += 1
			CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
													 to = eachSub['nus'][0], 
													 originator = subOriginator,
										  			 pc = notification))
			# TODO: correct RSC according to 7.3.2.9 - see above!
		
		if countNotifications == 0:
			L.isDebug and L.logDebug(f'No blocking <sub> or too early, no blocking RETRIEVE notification necessary')
			return
		
		# else
		L.isDebug and L.logDebug(f'Sent {countNotifications} notification(s) for blocking RETRIEVE')
		if finished:
			finished()



	###########################################################################
	#
	#	CrossResourceSubscriptions
	#

	def addCrossResourceSubscription(self, crs:CRS, originator:str) -> None:
		"""	Add a new crossResourceSubscription. 
		
			Check each receipient in the *nu* attribute with verification requests. 

			Args:
				crs: The new <crs> resource to check.
				originator: The request originator.
			
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug('Adding crossResourceSubscription')
		self._verifyNusInSubscription(crs, originator = originator)	# verification requests happen here


	def updateCrossResourceSubscription(self, crs:CRS, previousNus:list[str], originator:str) -> None:
		"""	Update a crossResourcesubscription. 
		
			Check each new receipient in the *nu* attribute with verification requests. 

			This method indirectly updates or rebuild the *notificationStatsInfo* attribute. It should be called
			add the end when updating a subscription.


			Args:
				crs: The new <crs> resource to check.
				previousNus: A list of the resource's previous NUs.
				originator: The request originator.
			
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug('Updating crossResourceSubscription')
		self._verifyNusInSubscription(crs, previousNus, originator = originator)	# verification requests happen here


	def removeCrossResourceSubscription(self, crs:CRS) -> None:
		"""	Remove a crossResourcesubscription. 
		
			Send a deletion request to the *subscriberURI* target.

			Args:
				crs: The new <crs> resource to remove.
			
			Return:
				Result object.
		"""
		L.isDebug and L.logDebug('Removing crossResourceSubscription')

		# Send a deletion request to the subscriberURI
		if (su := crs.su):
			if not self.sendDeletionNotification(su, crs.ri):
				L.isWarn and L.logWarn(f'Deletion request failed for: {su}') # but ignore the error



	def _crsCheckForNotification(self, data:list[str], 
			      					   crsRi:str, 
									   subCount:int, 
									   eem:EventEvaluationMode = EventEvaluationMode.ALL_EVENTS_PRESENT) -> None:
		"""	Test whether a notification must be sent for a a <crs> window.

			This method also sends the notification(s) if the window requirements are met.
			
			Args:
				data: List of unique resource IDs.
				crsRi: The resource ID of the <crs> resource for the window.
				subCount: Maximum number of expected resource IDs in *data*.
				eem: EventEvaluationMode.
		"""
		
		# First make sure that the list in 'data' only contains unique resource IDs
		data = list(set(data))

		L.isDebug and L.logDebug(f'Checking <crs>: {crsRi} window properties: unique notification count: {len(data)}, max expected count: {subCount}, eem: {eem}')

		# Test for conditions
		if	((eem is None or eem == EventEvaluationMode.ALL_EVENTS_PRESENT) and len(data) == subCount) or \
			(eem == EventEvaluationMode.ALL_OR_SOME_EVENTS_PRESENT and 1 <= len(data) <= subCount) or \
			(eem == EventEvaluationMode.SOME_EVENTS_MISSING and 1 <= len(data) < subCount) or \
			(eem == EventEvaluationMode.ALL_OR_SOME_EVENTS_MISSING and 0 <= len(data) < subCount) or \
			(eem == EventEvaluationMode.ALL_EVENTS_MISSING and len(data) == 0):

			L.isDebug and L.logDebug(f'Received sufficient notifications - sending notification')
			
			# Check the crossResourceSubscription's schedule, if there is one
			if (_sc := CSE.storage.searchScheduleForTarget(crsRi)):
				_ts = utcDatetime()

				# Check whether the current time matches any schedule
				for s in _sc:
					if cronMatchesTimestamp(s, _ts):
						break
				else:
					# No schedule matches the current time, so clear the data and just return
					L.isDebug and L.logDebug(f'No matching schedule found for <crs>: {crsRi}')
					return

			try:
				resource = CSE.dispatcher.retrieveResource(crsRi)
			except ResponseException as e:
				L.logWarn(f'Cannot retrieve <crs> resource: {crsRi}: {e.dbg}')	# Not much we can do here
				return

			crs = cast(CRS, resource)

			# Send the notification directly. Handle the counting of sent notifications and received responses
			# in pre and post functions for the notifications of each target
			dct:JSON = { 'm2m:sgn' : {
					'sur' : toSPRelative(crs.ri)
				}
			}
			self.sendNotificationWithDict(dct, 
										  crs.nu, 
										  originator = RC.cseCsi,
										  background = True,
										  preFunc = lambda target: self.countSentReceivedNotification(crs, target),
										  postFunc = lambda target: self.countSentReceivedNotification(crs, target, isResponse = True)
										 )
			self.countNotificationEvents(crs.ri, sub = crs)	# Count notification events
			
			# Check for <crs> expiration
			if (exc := crs.exc):
				exc -= 1
				crs.setAttribute('exc', exc)
				L.isDebug and L.logDebug(f'Reducing <crs> expiration counter to {exc}')
				crs.dbUpdate(True)
				if exc <= 0:
					L.isDebug and L.logDebug(f'<crs>: {crs.ri} expiration counter expired. Deleting resources.')
					CSE.dispatcher.deleteLocalResource(crs, originator = crs.getOriginator())

		else:
			L.isDebug and L.logDebug(f'No notification sent')


	# Time Window Monitor : Periodic

	def _getPeriodicWorkerName(self, ri:str) -> str:
		"""	Return the name of a periodic window worker.
		
			Args:
				ri: Resource ID for which the worker is running.
			
			Return:
				String with the worker name.
		"""
		return f'crsPeriodic_{ri}'


	def startCRSPeriodicWindow(self, crsRi:str, 
			    					 tws:str, 
									 expectedCount:int,
									 eem:EventEvaluationMode = EventEvaluationMode.ALL_EVENTS_PRESENT) -> None:

		crsTws = fromDuration(tws)
		L.isDebug and L.logDebug(f'Starting PeriodicWindow for crs: {crsRi}. TimeWindowSize: {crsTws}. TimeWindowInterpretation: {eem}')

		# Start a background worker. "data", which will contain the RI's later is empty
		BackgroundWorkerPool.newWorker(crsTws, 
									   self._crsPeriodicWindowMonitor, 
									   name = self._getPeriodicWorkerName(crsRi), 
									   startWithDelay = True,
									   data = []).start(crsRi = crsRi, expectedCount = expectedCount, eem = eem)


	def stopCRSPeriodicWindow(self, crsRi:str) -> None:
		L.isDebug and L.logDebug(f'Stopping PeriodicWindow for crs: {crsRi}')
		BackgroundWorkerPool.stopWorkers(self._getPeriodicWorkerName(crsRi))


	def _crsPeriodicWindowMonitor(self, _data:list[str], 
							   			_worker:BackgroundWorker,
			       						crsRi:str, 
										expectedCount:int,
										eem:EventEvaluationMode = EventEvaluationMode.ALL_EVENTS_PRESENT) -> bool: 
		L.isDebug and L.logDebug(f'Checking periodic window for <crs>: {crsRi}')
		self._crsCheckForNotification(_data, crsRi, expectedCount, eem)
		_worker.data = []
		return True


	# Time Window Monitor : Sliding

	def _getSlidingWorkerName(self, ri:str) -> str:
		"""	Return the name of a sliding window worker.
		
			Args:
				ri: Resource ID for which the worker is running.
			
			Return:
				String with the worker name.
		"""
		return f'crsSliding_{ri}'


	def startCRSSlidingWindow(self, crsRi:str,
			   						tws:str, 
									sur:str, 
									subCount:int,
									eem:EventEvaluationMode = EventEvaluationMode.ALL_EVENTS_PRESENT) -> BackgroundWorker:
		crsTws = fromDuration(tws)
		L.isDebug and L.logDebug(f'Starting SlidingWindow for crs: {crsRi}. TimeWindowSize: {crsTws}. SubScount: {subCount}')

		# Start an actor for the sliding window. "data" already contains the first notification source in an array
		return BackgroundWorkerPool.newActor(self._crsSlidingWindowMonitor, 
											 crsTws,
											 name = self._getSlidingWorkerName(crsRi), 
											 data = [ sur ]).start(crsRi = crsRi, subCount = subCount, eem = eem)


	def stopCRSSlidingWindow(self, crsRi:str) -> None:
		L.isDebug and L.logDebug(f'Stopping SlidingWindow for crs: {crsRi}')
		BackgroundWorkerPool.stopWorkers(self._getSlidingWorkerName(crsRi))


	def _crsSlidingWindowMonitor(self, _data:Any,
							  		   _worker:BackgroundWorker,
			      					   crsRi:str, 
									   subCount:int, 
									   eem:EventEvaluationMode = EventEvaluationMode.ALL_EVENTS_PRESENT) -> bool:
		L.isDebug and L.logDebug(f'Checking sliding window for <crs>: {crsRi}')
		self._crsCheckForNotification(_data, crsRi, subCount, eem)
		_worker.data = []
		# _data.clear()
		return True


	# Received Notification handling

	def receivedCrossResourceSubscriptionNotification(self, sur:str, crs:Resource) -> None:
		crsRi = crs.ri
		crsTwt = crs.twt
		crsTws = crs.tws
		L.isDebug and L.logDebug(f'Received notification for <crs>: {crsRi}, twt: {crsTwt}, tws: {crsTws}')
		match crsTwt:
			case TimeWindowType.SLIDINGWINDOW:
				if (workers := BackgroundWorkerPool.findWorkers(self._getSlidingWorkerName(crsRi))):
					L.isDebug and L.logDebug(f'Adding notification to worker: {workers[0].name}')
					if sur not in workers[0].data:
						workers[0].data.append(sur)
				else:
					workers = [ self.startCRSSlidingWindow(crsRi, crsTws, sur, crs._countSubscriptions(), crs.eem) ]	# sur is added automatically when creating actor

			case TimeWindowType.PERIODICWINDOW:
				if (workers := BackgroundWorkerPool.findWorkers(self._getPeriodicWorkerName(crsRi))):
					if sur not in workers[0].data:
						workers[0].data.append(sur)

			# No else: Periodic is running or not

		workers and L.isDebug and L.logDebug(f'Worker data: {workers[0].data}')
		


	###########################################################################
	#
	#	Notifications in general
	#

	def sendNotificationWithDict(self, dct:JSON, 
									   nus:list[str]|str, 
									   originator:Optional[str] = None, 
									   background:Optional[bool] = False, 
									   preFunc:Optional[Callable] = None, 
									   postFunc:Optional[Callable] = None) -> None:
		"""	Send a notification to a single URI or a list of URIs. 
		
			A URI may be a resource ID, then the *poa* of that resource is taken. 
			Also, the serialization is determined when each of the notifications is actually sent.

			Pre- and post-functions can be given that are called before and after sending each
			notification.
			
			Args:
				dct: Dictionary to send as the notification. It already contains the full request.
				nus: A single URI or a list of URIs.
				originator: The originator on which behalf to send the notification. 
				background: Send the notifications in a background task.
				preFunc: Function that is called before each notification sending, with the notification target as a single argument.
				postFunc: Function that is called after each notification sending, with the notification target as a single argument.
		"""

		def _sender(nu: str, originator:str, content:JSON) -> bool:
			if preFunc:
				preFunc(nu)
			CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
													 to = nu, 
													 originator = originator, 
													 pc = content))
			if postFunc:
				postFunc(nu)
			return True

		if isinstance(nus, str):
			nus = [ nus ]
		for nu in nus:
			if background:
				BackgroundWorkerPool.newActor(_sender, 
											  name = f'NO_{current_thread().name}').start(nu = nu, 
																						  originator = originator,
																						  content = dct)
			else:
				_sender(nu, originator = originator, content = dct)


	###########################################################################
	#
	#	Notification Statistics
	#

	def validateAndConstructNotificationStatsInfo(self, sub:SUB|CRS, add:Optional[bool] = True) -> None:
		r"""Update and fill the *notificationStatsInfo* attribute of a \<sub> or \<crs> resource.

			This method adds, if necessary, the necessarry stat info structures for each notification
			URI. It also removes structures for notification URIs that are not present anymore.

			Note:
				For this the *notificationURIs* attribute must be fully validated first.
			
			Args:
				sub: The \<sub> or \<crs> resource for whoich to validate the attribute.
				add: If True, add the *notificationStatsInfo* attribute if not present.
		"""

		# Optionally add the attribute
		if add:
			sub.setAttribute('nsi', [], overwrite = False)

		if (nsi := sub.nsi) is None:	# nsi attribute must be at least an empty list
			return
		nus = sub.nu

		# Remove from nsi when not in nu (anymore)
		for nsiEntry in list(nsi):
			if nsiEntry['tg'] not in nus:
				nsi.remove(nsiEntry)
		
		# Add new nsi structure for new targets in nu 
		for nu in nus:
			for nsiEntry in nsi:
				if nsiEntry['tg'] == nu:
					break

			# target not found in nsi, add it
			else:
				nsi.append({	'tg': nu,
								'rqs': 0,
								'rsr': 0,
								'noec': 0
							})


	def countSentReceivedNotification(self, sub:SUB|CRS, 
											target:str, 
											isResponse:Optional[bool] = False, 
											count:Optional[int] = 1) -> None:
		"""	If Notification Stats are enabled for a <sub> or <crs> resource, then
			increase the count for sent notifications or received responses.

			Args:
				sub: <sub> or <crs> resource.
				target: URI of the notification target.
				isResponse: Indicates whether a sent notification or a received response should be counted for.
				count: Number of notifications to count.
		"""
		if not sub or not sub.nse:	# Don't count if not present or disabled
			return
		
		L.isDebug and L.logDebug(f'Incrementing notification stats for: {sub.ri} ({"response" if isResponse else "request"})')

		activeField  = 'rsr' if isResponse else 'rqs'
		
		# Search and add to existing target
		# We have to lock this to prevent race conditions in some cases with CRS handling
		with self.lockNotificationEventStats:
			sub.dbReloadDict()	# get a fresh copy of the subscription

			# Add nsi if not present. This happens when the first notification is sent after enabling the recording
			if sub.nsi is None:
				self.validateAndConstructNotificationStatsInfo(sub, True)	# nsi is filled here again

			for each in sub.nsi:
				if each['tg'] == target:
					each[activeField] += count
					break
			sub.dbUpdate(True)


	def countNotificationEvents(self, ri:str, 
									  sub:Optional[SUB|CRS] = None) -> None:
		r"""This method count and stores the number of notification events for a subscription.
			It increments the count for each of the notification targets.

			After handling the resource is updated in the database.
			
			Args:
				ri: Resource ID of a \<sub> or \<csr> resource to handle.
		"""
		if sub is None:
			try:
				sub = CSE.dispatcher.retrieveLocalResource(ri) # type:ignore[assignment]
				# TODO check resource type?
			except ResponseException as e:
				return
		if not sub.nse:	# Don't count if not present or disabled
			return
		
		L.isDebug and L.logDebug(f'Incrementing notification event stat for: {sub.ri}')
		
		# Search and add to existing target
		# We have to lock this to prevent race conditions in some cases with CRS handling
		with self.lockNotificationEventStats:
			sub.dbReloadDict()	# get a fresh copy of the subscription

			# Add nsi if not present. This happens when the first notification is sent after enabling the recording
			if sub.nsi is None:
				self.validateAndConstructNotificationStatsInfo(sub, True)	# nsi is filled here again

			for each in sub.nsi:
				each['noec'] += 1
			sub.dbUpdate(True)


	def updateOfNSEAttribute(self, sub:CRS|SUB, newNse:bool) -> None:
		""" Handle an update of the *notificationStatsEnable* attribute of a <sub> or <crs>
			resource. 

			Note:
				This removes the *notificationStatsEnable* attribute, which must be added and filled later again, 
				e.g. when validating the *notificationURIs* attribute. 
				For this the *notificationURIs* attribute must be fully validated first.

			Args:
				sub: Either a <sub> or <crs> resource.
				newNse: The new value for the *nse* attribute. This may be empty if not present in the update.
			
		"""
		# nse is not deleted, it is a mandatory attribute
		if newNse is not None:	# present in the request
			oldNse = sub.nse
			if oldNse: # self.nse == True
				if newNse == False:
					pass # Stop collecting, but keep notificationStatsInfo
				else: # Both are True
					# Remove the nsi
					sub.delAttribute('nsi')
					# After SDS-2022-184R01: nsi is not added yet, but when the first statistics are collected. See countNotificationEvents()
			else:	# self.nse == False
				if newNse == True:
					sub.delAttribute('nsi')
					# After SDS-2022-184R01: nsi is not added yet, but when the first statistics are collected. See countNotificationEvents()
		else:
			# nse is removed (present in resource, but None, and neither True or False)
			sub.delAttribute('nsi')


	#########################################################################


	def _verifyNusInSubscription(self, subscription:SUB|CRS, 
									   previousNus:Optional[list[str]] = None, 
									   originator:Optional[str] = None) -> None:
		"""	Check all the notification URI's in a subscription. 
		
			A verification request is sent to new URI's. 
			Notifications to the originator are not sent.

			If *previousNus* is given then only new nus are notified.

			Args:
				subscription: <sub> or <crs> resource.
				previousNus: The list of previous NUs.
				originator: The originator on which behalf to send the notification. 
			
			Raises:
				`SUBSCRIPTION_VERIFICATION_INITIATION_FAILED`: In case a subscription verification fails.
		"""
		if (nus := subscription.nu):
			ri = subscription.ri
			# notify new nus (verification request). New ones are the ones that are not in the previousNU list
			for nu in nus:
				if not previousNus or (nu not in previousNus):	# send only to new entries in nu
					# Skip notifications to originator
					if nu == originator or compareIDs(nu, originator):
						L.isDebug and L.logDebug(f'Notification URI skipped: uri: {nu} == originator: {originator}')
						continue
					# Send verification notification to target (either direct URL, or an entity)
					if not self.sendVerificationRequest(nu, ri, originator = originator):
						# Return when even a single verification request fails
						raise SUBSCRIPTION_VERIFICATION_INITIATION_FAILED(f'Verification request failed for: {nu}')

		# Add/Update NotificationStatsInfo structure
		self.validateAndConstructNotificationStatsInfo(subscription, False) # DON'T add nsi here if not present


	#########################################################################


	def sendVerificationRequest(self, uri:Union[str, list[str]], 
									  ri:str, 
									  originator:Optional[str] = None) -> bool:
		"""	Define the callback function for verification notifications and send
				the notification. 

				Args:
					uri: The URI to send the verification request to. This may be a list of URI's. Each URI could be a direct URL, or an entity.
					ri: The resource ID of the subscription.
					originator: The originator on which behalf to send the notification.
		"""

		# Skip verification requests if disabled
		if not Configuration.cse_enableSubscriptionVerificationRequests:
			L.isDebug and L.logDebug('Skipping verification request (disabled)')
			return True

		def sender(uri:str) -> bool:
			# Skip verification requests to acme: receivers
			if isAcmeUrl(uri):
				L.isDebug and L.logDebug(f'Skipping verification request to internal target: {uri}')
				return True

			L.isDebug and L.logDebug(f'Sending verification request to: {uri}')
			verificationRequest:JSON = {
				'm2m:sgn' : {
					'vrq' : True,
					'sur' : toSPRelative(ri)
				}
			}
			# Set the creator attribute if there is an originator for the subscription
			originator and setXPath(verificationRequest, 'm2m:sgn/cr', originator)
	
			try:
				res = CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
															   to = uri, 
															   originator = RC.cseCsi,
															   pc = verificationRequest)
												   )[0].result	# there should be at least one result
			except ResponseException as e:
				L.isDebug and L.logDebug(f'Sending verification request failed for: {uri}: {e.dbg}')
				return False
			if res.rsc != ResponseStatusCode.OK:
				L.isDebug and L.logDebug(f'Verification notification response is not OK: {res.rsc} for: {uri}: {res.dbg}')
				return False
			return True


		return self._sendNotification(uri, sender)


	def sendDeletionNotification(self, uri:Union[str, list[str]], ri:str) -> bool:
		"""	Send a Deletion Notification to a single or a list of target.

			Args:
				uri: Single or a list of notification target URIs.
				ri: ResourceID of the subscription.
			Return:
				Boolean indicat
		"""

		def sender(uri:str) -> bool:
			L.isDebug and L.logDebug(f'Sending deletion notification to: {uri}')
			deletionNotification:JSON = {
				'm2m:sgn' : {
					'sud' : True,
					'sur' : toSPRelative(ri)
				}
			}

			try:
				CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
														 to = uri, 
														 originator = RC.cseCsi,
											  			 pc = deletionNotification))
			except ResponseException as e:
				L.isDebug and L.logDebug(f'Deletion request failed for: {uri}: {e.dbg}')
				return False
			return True


		return self._sendNotification(uri, sender) if uri else True	# Ignore if the uri is None


	def _handleSubscriptionNotification(self, sub:JSON, 
											  notificationEventType:NotificationEventType, 
											  resource:Optional[Resource] = None, 
											  modifiedAttributes:Optional[JSON] = None, 
											  missingData:Optional[MissingData] = None,
											  asynchronous:bool = False,
											  operationMonitor:Optional[OperationMonitor] = None,
											  originator:str = None) ->  bool:
		"""	Send a subscription notification.

			Args:
				sub: The <sub> resource.
				notificationEventType: The notification event type.
				resource: The resource that triggered the notification.
				modifiedAttributes: The modified attributes of the resource.
				missingData: The missing data of the resource.
				asynchronous: If True, send the notification in the background.
				operationMonitor: The operationMonitor information.
				originator: The originator on which behalf to send the notification.

			Return:
				True if the notification was sent successfully, False otherwise.
		"""
		L.isDebug and L.logDebug(f'Handling notification for notificationEventType: {notificationEventType} for notificationContentType: {sub["nct"]}')


		def _doSendNotification(uri:str, subscription:SUB, notificationRequest:JSON) -> bool:
			try:
				CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
														 to = uri, 
											  			 originator = RC.cseCsi,
											  			 pc = notificationRequest))
			except ResponseException as e:
				L.isDebug and L.logDebug(f'Notification failed for: {uri} : {e.dbg}')
				return False
			self.countSentReceivedNotification(subscription, uri, isResponse = True) # count received notification
			return True


		def sender(uri:str) -> bool:
			"""	Sender callback function for a single normal subscription notifications
			"""
			L.isDebug and L.logDebug(f'Sending notification to: {uri}, reason: {notificationEventType}, asynchronous: {asynchronous}')
			notificationRequest:JSON = {
				'm2m:sgn' : {
					'nev' : {
						'net' : NotificationEventType.resourceUpdate.value
					},
					'sur' : toSPRelative(sub['ri'])
				}
			}

			# get the notificationContentType
			nct = sub['nct']
			# TODO check what the content is for operation monitor
			# if operationMonitor is not None:	# special case of operationMonitor
			# 	nct = NotificationContentType.allAttributes

			creator = sub.get('cr')	# creator, might be None
			# switch to populate data
			match nct:
				case NotificationContentType.allAttributes:
					data = resource.asDict()
				case NotificationContentType.ri:
					data = { 'm2m:uri' : resource.ri }
				case NotificationContentType.modifiedAttributes:
					data = { resource.typeShortname : modifiedAttributes }
				case NotificationContentType.timeSeriesNotification:
					data = { 'm2m:tsn' : missingData.asDict() }
				# TODO
				case NotificationContentType.triggerPayload:
					pass
				case _:
					data = None
			# TODO nct == NotificationContentType.triggerPayload

			# Add some attributes to the notification
			notificationEventType is not None and setXPath(notificationRequest, 'm2m:sgn/nev/net', notificationEventType.value)
			data is not None and setXPath(notificationRequest, 'm2m:sgn/nev/rep', data)
			operationMonitor is not None and setXPath(notificationRequest, 'm2m:sgn/nev/om', operationMonitor)
			creator is not None and setXPath(notificationRequest, 'm2m:sgn/cr', creator)	# Set creator in notification if it was present in subscription

			# Add the originator that caused the event to the notificaton
			# See SDS-2023-0096 and SDS-2023-0143
			if originator and sub.get('eeno'):
				setXPath(notificationRequest, 'm2m:sgn/cr', originator)

			# Check for batch notifications
			if sub['bn']:
				return self._storeBatchNotification(uri, sub, notificationRequest)
			else:
				# If nse is set to True then count this notification request
				subscription = None
				if sub['nse']:
					try:
						subscription = cast(SUB, CSE.dispatcher.retrieveResource(sub['ri']))
					except ResponseException as e:
						L.logErr(f'Cannot retrieve <sub> resource: {sub["ri"]}: {e.dbg}')
						return False
					self.countSentReceivedNotification(subscription, uri)	# count sent notification
				
				# Send the notification
				if asynchronous:
					BackgroundWorkerPool.runJob(lambda: _doSendNotification(uri, subscription, notificationRequest), 
																		  name = f'NOT_{sub["ri"]}')
					return True
				return _doSendNotification(uri, subscription, notificationRequest)


		result = self._sendNotification(sub['nus'], sender)	# ! This is not a <sub> resource, but the internal data structure, therefore 'nus

		# Handle subscription expiration in case of a successful notification
		if result and (exc := sub['exc']):
			L.isDebug and L.logDebug(f'Decrement expirationCounter: {exc} -> {exc-1}')

			exc -= 1
			subResource = CSE.storage.retrieveResource(ri=sub['ri'])
			if exc < 1:
				L.isDebug and L.logDebug(f'expirationCounter expired. Removing subscription: {subResource.ri}')
				CSE.dispatcher.deleteLocalResource(subResource)	# This also deletes the internal sub
			else:
				subResource.setAttribute('exc', exc)		# Update the exc attribute
				subResource.dbUpdate(True)						# Update the real subscription
				CSE.storage.upsertSubscription(subResource)	# Also update the internal sub
		return result								


	def _sendNotification(self, uris:Union[str, list[str]], senderFunction:SenderFunction) -> bool:
		"""	Send a notification to a single or to multiple targets if necessary. 
		
			Call the infividual callback functions to do the resource preparation and the the actual sending.

			Args:
				uris: Either a string or a list of strings of notification receivers.
				senderFunction: A function that is called to perform the actual notification sending.
			
			Return:
				Returns *True*, even when nothing was sent, and *False* when any *senderFunction* returned False. 
		"""
		#	Event when notification is happening, not sent
		self._eventNotification()

		if isinstance(uris, str):
			return senderFunction(uris)
		else:
			for uri in uris:
				if not senderFunction(uri):
					return False
			return True



	##########################################################################
	#
	#	Batch Notifications
	#

	def _flushBatchNotifications(self, subscription:Resource) -> None:
		"""	Send and remove any outstanding batch notifications for a subscription.
		"""
		# TODO doc
		L.isDebug and L.logDebug(f'Flush batch notification')

		ri = subscription.ri
		# Get the subscription information (not the <sub> resource itself!).
		# Then get all the URIs/notification targets from that subscription. They might already
		# be filtered.
		if sub := CSE.storage.getSubscription(ri):
			ln = sub.get('ln', False)
			for nu in sub['nus']:
				self._stopNotificationBatchWorker(ri, nu)						# Stop a potential worker for that particular batch
				self._sendSubscriptionAggregatedBatchNotification(ri, nu, ln, sub)	# Send all remaining notifications


	def _storeBatchNotification(self, nu:str, sub:JSON, notificationRequest:JSON) -> bool:
		"""	Store a subscription's notification for later sending. For a single nu.
		"""
		# TODO doc
		L.isDebug and L.logDebug(f'Store batch notification nu: {nu}')

		# Rename key name
		if 'm2m:sgn' in notificationRequest:
			notificationRequest['sgn'] = notificationRequest.pop('m2m:sgn')

		# Alway add the notification first before doing the other handling
		ri = sub['ri']
		CSE.storage.addBatchNotification(ri, nu, notificationRequest)

		#  Check for actions
		ln = sub.get('ln', False)
		if (num := findXPath(sub, 'bn/num')) and (cnt := CSE.storage.countBatchNotifications(ri, nu)) >= num:
			L.isDebug and L.logDebug(f'Sending batch notification: bn/num: {num}  countBatchNotifications: {cnt}')

			self._stopNotificationBatchWorker(ri, nu)	# Stop the worker, not needed
			self._sendSubscriptionAggregatedBatchNotification(ri, nu, ln, sub)

		# Check / start Timer worker to guard the batch notification duration
		else:
			try:
				dur = isodate.parse_duration(findXPath(sub, 'bn/dur')).total_seconds()
			except Exception:
				return False
			self._startNewBatchNotificationWorker(ri, nu, ln, sub, dur)
		return True


	def _sendSubscriptionAggregatedBatchNotification(self, ri:str, nu:str, ln:bool, sub:JSON) -> bool:
		"""	Send and remove(!) the available BatchNotifications for an ri & nu.

			While the sent notifications and the respective received responses are counted here, the
			expiration counter is not. It depends on the events, not the notifications.

			Args:
				ri: Resource ID of the <sub> or <crs> resource.
				nu: A single notification URI.
				ln: *latestNotify*, if *True* then only send the latest notification.
				sub: The internal *sub* structure.
			
			Return:
				Indication of the success of the sending.
		"""
		with self.lockBatchNotification:
			L.isDebug and L.logDebug(f'Sending aggregated subscription notifications for ri: {ri}')

			# Collect the stored notifications for the batch and aggregate them
			notifications = []
			for notification in sorted(CSE.storage.getBatchNotifications(ri, nu), key = lambda x: x['tstamp']):	# type: ignore[no-any-return] # sort by timestamp added
				if n := findXPath(notification['request'], 'sgn'):
					notifications.append(n)
			if (notificationCount := len(notifications)) == 0:	# This can happen when the subscription is deleted and there are no outstanding notifications
				return False

			parameters:CSERequest = None
			ec:EventCategory = None
			if ln:
				notifications = notifications[-1:]
				# Add event category
				ec = EventCategory.Latest

			# Aggregate and send
			notificationRequest:JSON = {
				'm2m:agn' : {
					 'm2m:sgn' : notifications 
				}
			}

			# Delete old notifications
			if not CSE.storage.removeBatchNotifications(ri, nu):
				L.isWarn and L.logWarn('Error removing aggregated batch notifications')
				return False

			# If nse is set to True then count this notification request
			subscription = None
			nse = sub['nse']
			if nse:
				try:
					subscription = cast(SUB, CSE.dispatcher.retrieveResource(sub['ri']))
				except ResponseException as e:
					L.logErr(f'Cannot retrieve <sub> resource: {sub["ri"]}: {e.dbg}')
					return False
				self.countSentReceivedNotification(subscription, nu, count = notificationCount)	# count sent notification
				
			# Send the request
			try:
				CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
														 to = nu, 
														 originator = RC.cseCsi,
														 pc = notificationRequest,
														 ec = ec))
			except ResponseException as e:
				L.isWarn and L.logWarn(f'Error sending aggregated batch notifications: {e.dbg}')
				return False
			if nse:
				self.countSentReceivedNotification(subscription, nu, isResponse = True, count = notificationCount) # count received notification

			return True


	def _startNewBatchNotificationWorker(self, ri:str, nu:str, ln:bool, sub:JSON, dur:float) -> bool:
		# TODO doc
		if dur is None or dur < 1:	
			L.logErr('BatchNotification duration is < 1')
			return False
		# Check and start a notification worker to send notifications after some time
		if len(BackgroundWorkerPool.findWorkers(self._workerID(ri, nu))) > 0:	# worker started, return
			return True
		L.isDebug and L.logDebug(f'Starting new batchNotificationsWorker. Duration : {dur:f} seconds')
		BackgroundWorkerPool.newActor(self._sendSubscriptionAggregatedBatchNotification, 
									  delay = dur,
									  name = self._workerID(ri, nu)).start(ri = ri, nu = nu, ln = ln, sub = sub)
		return True


	def _stopNotificationBatchWorker(self, ri:str, nu:str) -> None:
		# TODO doc
		BackgroundWorkerPool.stopWorkers(self._workerID(ri, nu))


	def _workerID(self, ri:str, nu:str) -> str:
		"""	Return an ID for a batch notification background worker.
		
			Args:
				ri: ResourceID of a subscription.
				nu: Notification URI of a notification target.
			
			Return:
				String with the ID.
		"""
		return f'{ri};{nu}'

