#
#	NotificationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles subscriptions and sending of notifications. 
#

from __future__ import annotations
import sys
import isodate
from typing import Callable, Union
from threading import Lock
from tinydb.utils import V

from ..etc.Constants import Constants as C
from ..etc.Types import CSERequest, ContentSerializationType, MissingData, ResourceTypes, Result, NotificationContentType, NotificationEventType
from ..etc.Types import ResponseStatusCode as RC, EventCategory
from ..etc.Types import JSON, Parameters
from ..etc import Utils, DateUtils
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..services import CSE
from ..resources.Resource import Resource
from ..helpers.BackgroundWorker import BackgroundWorkerPool

# TODO: removal policy (e.g. unsuccessful tries)

SenderFunction = Callable[[str], bool]	# type:ignore[misc] # bc cyclic definition 
""" Type definition for sender callback function. """


class NotificationManager(object):


	def __init__(self) -> None:
		self.lockBatchNotification = Lock()	# Lock for batchNotifications
		L.isInfo and L.log('NotificationManager initialized')


	def shutdown(self) -> bool:
		L.isInfo and L.log('NotificationManager shut down')
		return True

	###########################################################################
	#
	#	Subscriptions
	#

	def addSubscription(self, subscription:Resource, originator:str) -> Result:
		"""	Add a new subscription. Check each receipient with verification requests. """
		L.isDebug and L.logDebug('Adding subscription')
		if not (res := self._verifyNusInSubscription(subscription, originator = originator)).status:	# verification requests happen here
			return res
		return Result.successResult() if CSE.storage.addSubscription(subscription) else Result.errorResult(rsc = RC.internalServerError, dbg = 'cannot add subscription to database')


	def removeSubscription(self, subscription:Resource) -> Result:
		""" Remove a subscription. Send the deletion notifications, if possible. """
		L.isDebug and L.logDebug('Removing subscription')

		# Send outstanding batchNotifications for a subscription
		self._flushBatchNotifications(subscription)

		# Send a deletion request to the subscriberURI
		if not self._sendDeletionNotification(su := subscription['su'], subscription.ri):
			L.isDebug and L.logDebug(f'Deletion request failed for: {su}') # but ignore the error

		# Send a deletion request to the associatedCrossResourceSub
		if (acrs := subscription['acrs']):
			self._sendDeletionNotification([ nu for nu in acrs ], subscription.ri)
		
		# Finally remove subscriptions from storage
		return Result.successResult() if CSE.storage.removeSubscription(subscription) else Result.errorResult(rsc = RC.internalServerError, dbg = 'cannot remove subscription from database')


	def updateSubscription(self, subscription:Resource, previousNus:list[str], originator:str) -> Result:
		L.isDebug and L.logDebug('Updating subscription')
		if not (res := self._verifyNusInSubscription(subscription, previousNus, originator = originator)).status:	# verification requests happen here
			return res
		return Result.successResult() if CSE.storage.updateSubscription(subscription) else Result.errorResult(rsc = RC.internalServerError, dbg = 'cannot update subscription in database')


	def getSubscriptionsByNetChty(self, ri:str, net:list[NotificationEventType] = None, chty:ResourceTypes = None) -> list[JSON]:
		"""	Returns a (possible empty) list of subscriptions for a resource. An optional filter can be used 
			to return only those subscriptions with a specific enc/net.
			
			Args:
				resource: the parent resource for the subscriptions
				net: optional filter for enc/net
				chty: optional single child resource typ
			Return:
				List of storage subscription documents, NOT Subscription resources.
			"""
		if not (subs := CSE.storage.getSubscriptionsForParent(ri)):
			return []
		result:list[JSON] = []
		for each in subs:
			if net and any(x in net for x in each['net']):
				result.append(each)
		
		# filter by chty if set
		if chty:
			result = [ each for each in result if (_chty := each['chty']) is None or chty in _chty]

		return result


	def checkSubscriptions(self, resource:Resource, 
								 reason:NotificationEventType, 
								 childResource:Resource = None, 
								 modifiedAttributes:JSON = None,
								 ri:str = None,
								 missingData:dict[str, MissingData] = None,
								 now:float = None) -> None:
		if resource and resource.isVirtual():
			return 
		ri = resource.ri if not ri else ri
		L.isDebug and L.logDebug(f'Checking subscriptions ({reason.name}) ri: {ri}')

		# ATTN: The "subscription" returned here are NOT the <sub> resources,
		# but an internal representation from the 'subscription' DB !!!
		# Access to attributes is different bc the structure is flattened
		if not (subs := CSE.storage.getSubscriptionsForParent(ri)):
			return
		for sub in subs:
			# Prevent own notifications for subscriptions 
			if childResource and \
				sub['ri'] == childResource.ri and \
				reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:
					continue
			if reason not in sub['net']:	# check whether reason is actually included in the subscription
				continue
			if reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:	# reasons for child resources
				chty = sub['chty']
				if chty and not childResource.ty in chty:	# skip if chty is set and child.type is not in the list
					continue
				self._handleSubscriptionNotification(sub, reason, resource = childResource, modifiedAttributes = modifiedAttributes)
			
			# Check Update and enc/atr vs the modified attributes 
			elif reason == NotificationEventType.resourceUpdate and (atr := sub['atr']) and modifiedAttributes:
				found = False
				for k in atr:
					if k in modifiedAttributes:
						found = True
				if found:
					self._handleSubscriptionNotification(sub, reason, resource = resource, modifiedAttributes = modifiedAttributes)
				else:
					L.isDebug and L.logDebug('Skipping notification: No matching attributes found')
			
			# Check for missing data points (only for <TS>)
			elif reason == NotificationEventType.reportOnGeneratedMissingDataPoints and missingData:
				md = missingData[sub['ri']]
				if md.missingDataCurrentNr >= md.missingDataNumber:	# Always send missing data if the count is greater then the minimum number
					self._handleSubscriptionNotification(sub, NotificationEventType.reportOnGeneratedMissingDataPoints, missingData=md)
					md.missingDataList = []	# delete only the sent missing data points

			else: # all other reasons that target the resource
				self._handleSubscriptionNotification(sub, reason, resource, modifiedAttributes = modifiedAttributes)


	def checkPerformBlockingUpdate(self, resource:Resource, originator:str, updatedAttributes:JSON, finished:Callable = None) -> Result:
		L.isDebug and L.logDebug('check blocking UPDATE')

		# Get blockingUpdate <sub> for this resource , if any
		subs = self.getSubscriptionsByNetChty(resource.ri, [NotificationEventType.blockingUpdate])
		
		# Later: BlockingUpdateDirectChild

		# TODO 2) Prevent or block all other UPDATE request primitives to this target resource.

		for eachSub in subs:

			notification = {
				'm2m:sgn' : {
					'nev' : {
						'net' : NotificationEventType.blockingUpdate.value
					},
					'sur' : Utils.spRelRI(eachSub['ri'])
				}
			}

			# Check attributes in enc
			if atr := eachSub['atr']:
				jsn, _ = Utils.pureResource(updatedAttributes)
				if len(set(jsn.keys()).intersection(atr)) == 0:	# if the intersection between updatedAttributes and the enc/atr contains is empty, then continue
					L.isDebug and L.logDebug(f'skipping <SUB>: {eachSub["ri"]} because configured enc/attribute condition doesn\'t match')
					continue

			# Don't include virtual resources
			if not resource.isVirtual():
				# Add representation
				Utils.setXPath(notification, 'm2m:sgn/nev/rep', updatedAttributes)
				

			# Send notification and handle possible negative response status codes
			if not (res := self._sendRequest(eachSub['nus'][0], notification)).status:
				return res	# Something else went wrong
			if res.rsc == RC.OK:
				if finished:
					finished()
				continue

			# Modify the result status code for some failure response status codes
			if res.rsc == RC.targetNotReachable:
				res.dbg = L.logDebug(f'remote entity not reachable: {eachSub["nus"][0]}')
				res.rsc = RC.remoteEntityNotReachable
				res.status = False
				return res
			elif res.rsc == RC.operationNotAllowed:
				res.dbg = L.logDebug(f'operation denied by remote entity: {eachSub["nus"][0]}')
				res.rsc = RC.operationDeniedByRemoteEntity
				res.status = False
				return res
			
			# General negative response status code
			res.status = False
			return res

		# TODO 5) Allow all other UPDATE request primitives for this target resource.

		return Result.successResult()


	def checkPerformBlockingRetrieve(self, resource:Resource, originator:str, request:CSERequest, finished:Callable = None) -> Result:
		# TODO originator in notification?
		# TODO check notify permission for originator
		# TODO blockingRetrieveDirectChildren.
		# TODO getSubscriptionsByNetChty + chty optional
		# EXPERIMENTAL
		
		L.isDebug and L.logDebug('check blocking RETRIEVE')

		# Get blockingRetrieve <sub> for this resource , if any
		subs = self.getSubscriptionsByNetChty(resource.ri, [NotificationEventType.blockingRetrieve])
		# get and add blockingRetrieveDirectChild <sub> for this resource type, if any
		subs.extend(self.getSubscriptionsByNetChty(resource.pi, [NotificationEventType.blockingRetrieveDirectChild], chty = resource.ty))
		# L.logWarn(resource)

		for eachSub in subs:
			maxAgeRequest:float = None
			maxAgeSubscription:float = None

			# Check for maxAge attribute provided in the request
			if (maxAgeS := request.args.attributes.get('ma')) is not None:	# TODO attribute name
				try:
					maxAgeRequest = DateUtils.fromDuration(maxAgeS)
				except Exception as e:
					L.logWarn(dbg := f'error when parsing maxAge in request: {str(e)}')
					return Result.errorResult(dbg = dbg)

			# Check for maxAge attribute provided in the subscription
			if (maxAgeS := eachSub['ma']) is not None:	# EXPERIMENTAL
				try:
					maxAgeSubscription = DateUtils.fromDuration(maxAgeS)
				except Exception as e:
					L.logWarn(dbg := f'error when parsing maxAge in subscription: {str(e)}')
					return Result.errorResult(dbg = dbg)
				
			# Return if neither the request nor the subscription have a maxAge set
			if maxAgeRequest is None and maxAgeSubscription is None:
				L.isDebug and L.logDebug(f'no maxAge configured, blocking RETRIEVE notification not necessary')
				return Result.successResult()


			# Is one reached?
			L.isDebug and L.logDebug(f'request.maxAge: {maxAgeRequest} subscription.maxAge: {maxAgeSubscription}')
			maxAgeSubscription = maxAgeSubscription if maxAgeSubscription is not None else sys.float_info.max
			maxAgeRequest = maxAgeRequest if maxAgeRequest is not None else sys.float_info.max

			# L.logWarn(resource)

			if resource.lt > DateUtils.getResourceDate(-int(min(maxAgeRequest, maxAgeSubscription))):
				L.isDebug and L.logDebug(f'too early, no blocking RETRIEVE notification necessary')
				return Result.successResult()
			L.isDebug and L.logDebug(f'blocking RETRIEVE notification necessary')

			notification = {
				'm2m:sgn' : {
					'nev' : {
						'net' : eachSub['net'][0],	# Add the first and hopefully only NET to the notification
					},
					'sur' : Utils.spRelRI(eachSub['ri'])
				}
			}
			# Don't include virtual resources
			if not resource.isVirtual():
				# Add representation
				Utils.setXPath(notification, 'm2m:sgn/nev/rep', resource.asDict())

			if not (res := self._sendRequest(eachSub['nus'][0], notification)).status:
				# TODO: correct RSC according to 7.3.2.9 - see above!
				return res
			if finished:
				finished()

		return Result.successResult()


	###########################################################################
	#
	#	Notifications in general
	#

	def sendNotificationWithDict(self, data:JSON, nus:list[str]|str, originator:str = None) -> None:
		"""	Send a notification to a single URI or a list of URIs. A URI may be a resource ID, then
			the *poa* of that resource is taken. Also, the serialization is determined when 
			actually sending the notification.
		"""
		for nu in nus:
			self._sendRequest(nu, data, originator = originator)


	#########################################################################


	def _verifyNusInSubscription(self, subscription:Resource, previousNus:list[str] = None, originator:str = None) -> Result:
		"""	Check all the notification URI's in a subscription. A verification request is sent to new URI's. Notifications to the originator are not sent.

			If `previousNus` is given then only new nus are notified.
		"""
		if nus := subscription.nu:
			# notify new nus (verification request). New ones are the ones that are not in the previousNU list
			for nu in nus:
				if not previousNus or (nu not in previousNus):	# send only to new entries in nu
					# Skip notifications to originator
					if nu == originator or Utils.compareIDs(nu, originator):
						L.isDebug and L.logDebug(f'Notification URI skipped: uri: {nu} == originator: {originator}')
						continue
					# Send verification notification to target (either direct URL, or an entity)
					if not self._sendVerificationRequest(nu, subscription.ri, originator = originator):
						# Return when even a single verification request fails
						return Result.errorResult(rsc = RC.subscriptionVerificationInitiationFailed, dbg = f'Verification request failed for: {nu}')

		return Result.successResult()


	#########################################################################


	def _sendVerificationRequest(self, uri:Union[str, list[str]], ri:str, originator:str = None) -> bool:
		""""	Define the callback function for verification notifications and send
				the notification.
		"""

		def sender(uri:str) -> bool:
			L.isDebug and L.logDebug(f'Sending verification request to: {uri}')
			verificationRequest = {
				'm2m:sgn' : {
					'vrq' : True,
					'sur' : Utils.spRelRI(ri)
				}
			}
			# Set the creator attribute if there is an originator for the subscription
			originator and Utils.setXPath(verificationRequest, 'm2m:sgn/cr', originator)
	
			if not (res := self._sendRequest(uri, verificationRequest, noAccessIsError = True)).status:
				L.isDebug and L.logDebug(f'Sending verification request failed for: {uri}: {res.dbg}')
				return False
			if res.rsc != RC.OK:
				L.isDebug and L.logDebug(f'Verification notification response if not OK: {res.rsc} for: {uri}: {res.dbg}')
				return False
			return True


		return self._sendNotification(uri, sender)


	def _sendDeletionNotification(self, uri:Union[str, list[str]], ri:str) -> bool:
		"""	Define the callback function for deletion notifications and send
			the notification
		"""

		def sender(uri:str) -> bool:
			L.isDebug and L.logDebug(f'Sending deletion notification to: {uri}')
			deletionNotification = {
				'm2m:sgn' : {
					'sud' : True,
					'sur' : Utils.spRelRI(ri)
				}
			}

			if not (res := self._sendRequest(uri, deletionNotification)).status:
				L.isDebug and L.logDebug(f'Deletion request failed for: {uri}: {res.dbg}')
				return False
			return True


		return self._sendNotification(uri, sender) if uri else True	# Ignore if the uri is None


	def _handleSubscriptionNotification(self, sub:JSON, reason:NotificationEventType, resource:Resource = None, modifiedAttributes:JSON = None, missingData:MissingData = None) ->  bool:
		"""	Send a subscription notification.
		"""
		L.isDebug and L.logDebug(f'Handling notification for reason: {reason}')

		def sender(uri:str) -> bool:
			"""	Sender callback function for a single normal subscription notifications
			"""
			L.isDebug and L.logDebug(f'Sending notification to: {uri}, reason: {reason}	')
			notificationRequest = {
				'm2m:sgn' : {
					'nev' : {
						'rep' : {},
						'net' : NotificationEventType.resourceUpdate
					},
					'sur' : Utils.spRelRI(sub['ri'])
				}
			}

			nct = sub['nct']
			creator = sub.get('cr')	# creator, might be None
			# switch to poupate data
			data = None
			nct == NotificationContentType.all						and (data := resource.asDict())
			nct == NotificationContentType.ri 						and (data := { 'm2m:uri' : resource.ri })
			nct == NotificationContentType.modifiedAttributes		and (data := { resource.tpe : modifiedAttributes })
			nct == NotificationContentType.timeSeriesNotification	and (data := { 'm2m:tsn' : missingData.asDict() })
			# TODO nct == NotificationContentType.triggerPayload

			# Add some values to the notification
			reason is not None and Utils.setXPath(notificationRequest, 'm2m:sgn/nev/net', reason)
			data is not None and Utils.setXPath(notificationRequest, 'm2m:sgn/nev/rep', data)
			creator is not None and Utils.setXPath(notificationRequest, 'm2m:sgn/cr', creator)	# Set creator in notification if it was present in subscription

			# Check for batch notifications
			if sub['bn']:
				return self._storeBatchNotification(uri, sub, notificationRequest)
			else:
				if not self._sendRequest(uri, notificationRequest).status:
					L.isDebug and L.logDebug(f'Notification failed for: {uri}')
					return False
				return True

		result = self._sendNotification(sub['nus'], sender)	# ! This is not a <sub> resource, but the internal data structure, therefore 'nus

		# Handle subscription expiration in case of a successful notification
		if result and (exc := sub['exc']):
			L.isDebug and L.logDebug(f'Decrement expirationCounter: {exc} -> {exc-1}')

			exc -= 1
			subResource = CSE.storage.retrieveResource(ri=sub['ri']).resource
			if exc < 1:
				L.isDebug and L.logDebug(f'expirationCounter expired. Removing subscription: {subResource.ri}')
				CSE.dispatcher.deleteResource(subResource)	# This also deletes the internal sub
			else:
				subResource.setAttribute('exc', exc)		# Update the exc attribute
				subResource.dbUpdate()						# Update the real subscription
				CSE.storage.updateSubscription(subResource)	# Also update the internal sub
		return result								


	def _sendNotification(self, uris:Union[str, list[str]], senderFunction:SenderFunction) -> bool:
		"""	Send a notification to a single or to multiple targets if necessary. 
		
			Call the infividual callback functions to do the resource preparation and the the actual sending.

			Returns True, even when nothing was sent.
		"""
		#	Event when notification is happening, not sent
		CSE.event.notification() # type: ignore

		if isinstance(uris, str):
			return senderFunction(uris)
		else:
			for uri in uris:
				if not senderFunction(uri):
					return False
		return True


	def _sendRequest(self, uri:str, 
						   notificationRequest:JSON, 
						   parameters:Parameters = None, 
						   originator:str = None,
						   noAccessIsError:bool = False,
						   ct:ContentSerializationType = None) -> Result:
		"""	Send a Notification request to a single target.
		"""
		return CSE.request.sendNotifyRequest(	uri, 
												originator if originator else CSE.cseCsi,
												data = notificationRequest,
												parameters = parameters,
												ct = ct,
												noAccessIsError = noAccessIsError)


	##########################################################################
	#
	#	Batch Notifications
	#

	def _flushBatchNotifications(self, subscription:Resource) -> None:
		"""	Send and remove any outstanding batch notifications for a subscription.
		"""
		L.isDebug and L.logDebug(f'Flush batch notification')

		ri = subscription.ri
		# Get the subscription information (not the <sub> resource itself!).
		# Then get all the URIs/notification targets from that subscription. They might already
		# be filtered.
		if sub := CSE.storage.getSubscription(ri):
			ln = sub['ln'] if 'ln' in sub else False
			for nu in sub['nus']:
				self._stopNotificationBatchWorker(ri, nu)						# Stop a potential worker for that particular batch
				self._sendSubscriptionAggregatedBatchNotification(ri, nu, ln)	# Send all remaining notifications


	def _storeBatchNotification(self, nu:str, sub:JSON, notificationRequest:JSON) -> bool:
		"""	Store a subscription's notification for later sending. For a single nu.
		"""
		L.isDebug and L.logDebug(f'Store batch notification nu: {nu}')

		# Rename key name
		if 'm2m:sgn' in notificationRequest:
			notificationRequest['sgn'] = notificationRequest.pop('m2m:sgn')

		# Alway add the notification first before doing the other handling
		ri = sub['ri']
		CSE.storage.addBatchNotification(ri, nu, notificationRequest)

		#  Check for actions
		if (num := Utils.findXPath(sub, 'bn/num')) and (cnt := CSE.storage.countBatchNotifications(ri, nu)) >= num:
			L.isDebug and L.logDebug(f'Sending batch notification: bn/num: {num}  countBatchNotifications: {cnt}')

			ln = sub['ln'] if 'ln' in sub else False
			self._stopNotificationBatchWorker(ri, nu)	# Stop the worker, not needed
			self._sendSubscriptionAggregatedBatchNotification(ri, nu, ln)

		# Check / start Timer worker to guard the batch notification duration
		else:
			try:
				dur = isodate.parse_duration(Utils.findXPath(sub, 'bn/dur')).total_seconds()
			except Exception:
				return False
			self._startNewBatchNotificationWorker(ri, nu, dur)
		return True


	def _sendSubscriptionAggregatedBatchNotification(self, ri:str, nu:str, ln:bool = False) -> bool:
		"""	Send and remove(!) the available BatchNotifications for an ri & nu.
		"""
		with self.lockBatchNotification:
			L.isDebug and L.logDebug(f'Sending aggregated subscription notifications for ri: {ri}')

			# Collect the stored notifications for the batch and aggregate them
			notifications = []
			for notification in sorted(CSE.storage.getBatchNotifications(ri, nu), key = lambda x: x['tstamp']):	# type: ignore[no-any-return] # sort by timestamp added
				if n := Utils.findXPath(notification['request'], 'sgn'):
					notifications.append(n)
			if len(notifications) == 0:	# This can happen when the subscription is deleted and there are no outstanding notifications
				return False

			additionalParameters = None
			if ln:
				notifications = notifications[-1:]
				additionalParameters = { 'ec' : str(EventCategory.Latest.value) }	# event category

			# Aggregate and send
			notificationRequest = {
				'm2m:agn' : { 'm2m:sgn' : notifications }
			}

			#	TODO check whether nu is an RI. Get that resource as target reosurce and pass it on to the send request
			#
			#	TODO This could actually be the part to handle batch notifications correctly. always store the target's ri
			#		 if it is a resource. only determine which poa and the ct later (ie here).
			#

			# Delete old notifications
			if not CSE.storage.removeBatchNotifications(ri, nu):
				L.isWarn and L.logWarn('Error removing aggregated batch notifications')
				return False

			# Send the request
			if not self._sendRequest(nu, notificationRequest, parameters = additionalParameters).status:
				L.isWarn and L.logWarn('Error sending aggregated batch notifications')
				return False

			return True

# TODO expiration counter

	# def _checkExpirationCounter(self, sub:dict) -> bool:
	# 	if 'exc' in sub and (exc := sub['exc'] is not None:
	# 		if (subscription := CSE.dispatcher.retrieveResource(sub['ri']).resource) is None:
	# 			return False
	# 	return Result(status=True) if CSE.storage.updateSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot update subscription in database')


	def _startNewBatchNotificationWorker(self, ri:str, nu:str, dur:float) -> bool:
		if dur is None or dur < 1:	
			L.logErr('BatchNotification duration is < 1')
			return False
		# Check and start a notification worker to send notifications after some time
		if len(BackgroundWorkerPool.findWorkers(self._workerID(ri, nu))) > 0:	# worker started, return
			return True
		L.isDebug and L.logDebug(f'Starting new batchNotificationsWorker. Duration : {dur:f} seconds')
		BackgroundWorkerPool.newActor(self._sendSubscriptionAggregatedBatchNotification, delay=dur, name=self._workerID(ri, nu)).start(ri=ri, nu=nu)
		return True


	def _stopNotificationBatchWorker(self, ri:str, nu:str) -> None:
		BackgroundWorkerPool.stopWorkers(self._workerID(ri, nu))


	def _workerID(self, ri:str, nu:str) -> str:
		return f'{ri};{nu}'

