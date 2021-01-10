#
#	NotificationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles subscriptions and sending of notifications. 
#

import requests
import isodate
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from typing import List, Union, Callable
from threading import Lock
from Logging import Logging
from Constants import Constants as C
from Types import Result, NotificationContentType, NotificationEventType, Permission, ResponseCode as RC, ContentSerializationType
from Configuration import Configuration
import Utils, CSE
from helpers.BackgroundWorker import BackgroundWorkerPool
from resources.Resource import Resource

# TODO: removal policy (e.g. unsuccessful tries)
# TODO: latestNotify support

# TODO: completly rework the batch handling. Store the notification, but only evaluate the TO when sending!
# TODO: Change the evaluation of poa's. Only one successful receiver per POA. This means that evaluation of TO happens at the very end just before sending the requestz.
# TODO: support different serializations. Also ct= argument in URL



class NotificationManager(object):

	def __init__(self) -> None:
		self.lockBatchNotification = Lock()	# Lock for batchNotifications
		self.enableNotifications = Configuration.get('cse.enableNotifications')

		if self.enableNotifications:
			Logging.log('Notifications ENABLED')
		else:
			Logging.log('Notifications DISABLED')
		Logging.log('NotificationManager initialized')


	def shutdown(self) -> bool:
		Logging.log('NotificationManager shut down')
		return True

	###########################################################################
	#
	#	Subscriptions
	#

	# def addSubscription(self, subscription:Resource, originator:str) -> Result:
	# 	if not self.enableNotifications:
	# 		return Result(status=False, rsc=RC.subscriptionVerificationInitiationFailed, dbg='notifications are disabled')
	# 	Logging.logDebug('Adding subscription')
	# 	if (res := self._checkNusInSubscription(subscription, originator=originator)).lst is None:	# verification requests happen here
	# 		return Result(status=False, rsc=res.rsc, dbg=res.dbg)
	# 	return Result(status=True) if CSE.storage.addSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot add subscription to database')

	def addSubscription(self, subscription:Resource, originator:str) -> Result:
		if not self.enableNotifications:
			return Result(status=False, rsc=RC.subscriptionVerificationInitiationFailed, dbg='notifications are disabled')
		Logging.logDebug('Adding subscription')
		if (res := self._checkNusInSubscription(subscription, originator=originator)).lst is None:	# verification requests happen here
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)
		return Result(status=True) if CSE.storage.addSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot add subscription to database')



	def removeSubscription(self, subscription: Resource) -> Result:
		""" Remove a subscription. Send the deletion notifications, if possible. """
		Logging.logDebug('Removing subscription')

		# This check does allow for removal of subscriptions
		if not self.enableNotifications:
			return Result(status=False, rsc=RC.subscriptionVerificationInitiationFailed, dbg='notifications are disabled')

		# Send outstanding batchNotifications for a subscription
		self._flushBatchNotifications(subscription)

		# Send a deletion request to the subscriberURI
		if (sus := self._getNotificationURLs([subscription['su']])) is not None:
			for su in sus:
				if not self._sendDeletionNotification(su, subscription.ri):
					Logging.logDebug(f'Deletion request failed: {su}') # but ignore the error

		# Send a deletion request to the associatedCrossResourceSub
		if (acrs := subscription['acrs']) is not None and (nus := self._getNotificationURLs(acrs)) is not None:
			for nu in nus:
				if not self._sendDeletionNotification(nu, subscription.ri):
					Logging.logDebug(f'Deletion request failed: {nu}') # but ignore the error
		
		# Finally remove subscriptions from storage
		return Result(status=True) if CSE.storage.removeSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot remove subscription from database')


	def updateSubscription(self, subscription:Resource, newDict:dict, previousNus:List[str], originator:str) -> Result:
		Logging.logDebug('Updating subscription')
		#previousSub = CSE.storage.getSubscription(subscription.ri)
		if (res := self._checkNusInSubscription(subscription, newDict, previousNus, originator=originator)).lst is None:	# verification/delete requests happen here
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)
		return Result(status=True) if CSE.storage.updateSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot update subscription in database')


	def checkSubscriptions(self, resource:Resource, reason:NotificationEventType, childResource:Resource=None, modifiedAttributes:dict=None) -> None:
		if not self.enableNotifications:
			return

		if Utils.isVirtualResource(resource):
			return 

		Logging.logDebug('Checking subscriptions for notifications')
		ri = resource.ri

		# ATTN: The "subscription" returned here are NOT the <sub> resources,
		# but an internal representation from the 'subscription' DB !!!
		# Access to attributes is different bc the structure is flattened
		subs = CSE.storage.getSubscriptionsForParent(ri)
		if subs is None or len(subs) == 0:
			return

		Logging.logDebug(f'Checking subscription for: {ri}, reason: {reason:d}')
		for sub in subs:
			# Prevent own notifications for subscriptions 
			if childResource is not None and \
				sub['ri'] == childResource.ri and \
				reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:
					continue
			if reason not in sub['net']:	# check whether reason is actually included in the subscription
				continue
			if reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:	# reasons for child resources
				chty = sub['chty']
				if chty is not None and not childResource.ty in chty:	# skip if chty is set and child.type is not in the list
					continue
				self._handleSubscriptionNotification(sub, reason, childResource, modifiedAttributes=modifiedAttributes)
			# Check Update and enc/atr vs the modified attribuets 
			elif reason == NotificationEventType.resourceUpdate and (atr := sub['atr']) is not None and modifiedAttributes is not None:
				found = False
				for k in atr:
					if k in modifiedAttributes:
						found = True
				if found:
					self._handleSubscriptionNotification(sub, reason, resource, modifiedAttributes=modifiedAttributes)
				else:
					Logging.logDebug('Skipping notification: No matching attributes found')

			else: # all other reasons that target the resource
				self._handleSubscriptionNotification(sub, reason, resource, modifiedAttributes=modifiedAttributes)


	# def sendOutstandingNotifications(self, ri:str) -> None:
	# 	"""	Send outstanding Notifications for a subscription (for ri).
	# 	"""
	# 	subs = CSE.storage.getSubscriptions(ri)
	# 	if subs is None or len(subs) == 0:
	# 		return
	# 	for sub in subs:
	# 		for nu in self._getNotificationURLs(sub['nus']):
	# 			pass # TODO

	###########################################################################
	#
	#	Notifications in general
	#

	def sendNotificationWithDict(self, data:dict, nus:Union[List[str], str], originator:str=None) -> None:
		if nus is not None and len(nus) > 0:
			for nu in self._getNotificationURLs(nus):
				self._sendRequest(nu, data, originator=originator)



	#########################################################################

	# Return resolved notification URLs, so also POA from referenced AE's etc
	def _getNotificationURLs(self, nus:Union[List[str], str], originator:str=None) -> List[str]:

		if nus is None:
			return []
		nusl = nus if isinstance(nus, list) else [ nus ]	# make a list out of it even when it is a single value
		result = []
		for nu in nusl:
			if nu is None or len(nu) == 0:
				continue
			# check if it is a direct URL
			Logging.logDebug(f'Checking next notification target: {nu}')
			if Utils.isURL(nu):
				result.append(nu)
			else:
				if (resource := CSE.dispatcher.retrieveResource(nu).resource) is None:
					Logging.logWarn(f'Resource not found to get URL: {nu}')
					return None

				# If the Originator is the notification target then exclude it from the list of targets
				# Test for AE and CSE (CSE starts with a /)
				if originator is not None and (resource.ri == originator or resource.ri == f'/{originator}'):
					Logging.logDebug(f'Notification target is the originator, no verification request for: {nu}')
					continue
				if not CSE.security.hasAccess(originator, resource, Permission.NOTIFY):	# check whether AE/CSE may receive Notifications
				# if not CSE.security.hasAccess('', resource, Permission.NOTIFY):	# check whether AE/CSE may receive Notifications
					Logging.logWarn(f'No access to resource: {nu}')
					return None
				if (poa := resource.poa) is not None and isinstance(poa, list):	#TODO? check whether AE or CSEBase
					result += poa
		return result


	def _checkNusInSubscription(self, subscription:Resource, newDict:dict=None, previousNus:List[str]=None, originator:str=None) -> Result:
		"""	Check all the notification URI's in a subscription. 
			A verification request is sent to new URI's.
			A deletion request is sent when URI's are removed.
		"""
		newNus = []
		if newDict is None:	# If there is no new resource structure, get the one from the subscription to work with
			newDict = subscription.asDict()

		# Resolve the URI's in the previousNus.
		if previousNus is not None:
			if (previousNus := self._getNotificationURLs(previousNus, originator)) is None:
				# Fail if any of the NU's cannot be retrieved or accessed
				return Result(rsc=RC.subscriptionVerificationInitiationFailed, dbg='cannot retrieve all previous nu''s')

		# Are there any new URI's?
		if (nuAttribute := Utils.findXPath(newDict, 'm2m:sub/nu')) is not None:

			# Resolve the URI's for the new NU's
			if (newNus := self._getNotificationURLs(nuAttribute, originator)) is None:
				# Fail if any of the NU's cannot be retrieved
				return Result(rsc=RC.subscriptionVerificationInitiationFailed, dbg='cannot retrieve all new nu''s')

			# notify new nus (verification request). New ones are the ones that are not in the previousNU list
			for nu in newNus:
				if previousNus is None or (nu not in previousNus):
					if not self._sendVerificationRequest(nu, subscription.ri, originator=originator):
						Logging.logDebug(f'Verification request failed: {nu}')
						return Result(rsc=RC.subscriptionVerificationInitiationFailed, dbg=f'verification request failed for nu: {nu}')


# TODO is this really correct? Also the above (new verification request) There is nothing in the spec about this, except TS-0001 10.2.10.4 Update <subscription>
		# notify removed nus (deletion notification) if nu = null
		if 'nu' in newDict: # if nu not present, nothing to do
			if previousNus is not None:
				for nu in previousNus:
					if nu not in newNus:
						if not self._sendDeletionNotification(nu, subscription.ri):
							Logging.logDebug('Deletion request failed') # but ignore the error

		return Result(lst=newNus)

	# def _buildReceipientList(self, sub:Resource) -> list:



	#########################################################################


	def _sendVerificationRequest(self, uri:str, ri:str, originator:str=None) -> bool:

		def sender(url:str, serialization:ContentSerializationType) -> bool:
			Logging.logDebug(f'Sending verification request to: {url}')
			verificationRequest = {
				'm2m:sgn' : {
					'vrq' : True,
					'sur' : Utils.fullRI(ri)
				}
			}
			originator is not None and Utils.setXPath(verificationRequest, 'm2m:sgn/cr', originator)
			return self._sendRequest(url, verificationRequest)


		return self._sendNotification([ uri ], sender)


	def _sendDeletionNotification(self, uri:str, ri:str) -> bool:
	
		def sender(url:str, serialization:ContentSerializationType) -> bool:
			Logging.logDebug(f'Sending deletion notification to: {url}')
			deletionNotification = {
				'm2m:sgn' : {
					'sud' : True,
					'sur' : Utils.fullRI(ri)
				}
			}
			return self._sendRequest(url, deletionNotification)


		return self._sendNotification([ uri ], sender)


	def _handleSubscriptionNotification(self, sub:dict, reason:NotificationEventType, resource:Resource, modifiedAttributes:dict=None) ->  bool:
		"""	Send a subscription notification.
		"""
		Logging.logDebug(f'Handling notification for reason: {reason}')

		def sender(url:str, serialization:ContentSerializationType) -> bool:
			Logging.logDebug(f'Sending notification to: {url}, reason: {reason}')
			notificationRequest = {
				'm2m:sgn' : {
					'nev' : {
						'rep' : {},
						'net' : NotificationEventType.resourceUpdate
					},
					'sur' : Utils.fullRI(sub['ri'])
				}
			}
			data = None
			nct = sub['nct']
			nct == NotificationContentType.all					and (data := resource.asDict())
			nct == NotificationContentType.ri 					and (data := { 'm2m:uri' : resource.ri })
			nct == NotificationContentType.modifiedAttributes	and (data := { resource.tpe : modifiedAttributes })
			# TODO nct == NotificationContentType.triggerPayload

			# Add some values to the notification
			reason is not None 									and Utils.setXPath(notificationRequest, 'm2m:sgn/nev/net', reason)
			data is not None 									and Utils.setXPath(notificationRequest, 'm2m:sgn/nev/rep', data)

			# Check for batch notifications
			if sub['bn'] is not None:
				return self._storeBatchNotification(url, sub, notificationRequest, serialization)
			else:
				return self._sendRequest(url, notificationRequest, serialization=serialization)


		return self._sendNotification(sub['nus'], sender)	# ! This is not a <sub> resource, but the internal data structure, therefore 'nus




	def _sendNotification(self, uris:list, sendingFunction:Callable) -> bool:
		"""	Send a notification to multiple targets if necessary. Determine the content serialization from either the ct parameter
			or the csz attribute of an AE/CSE, or the CSE's default.
			Call a callback function to do the actual sending.
		"""
		
		def _sendNotificationWithSerialization(url:str, sendingFunction:Callable, csz:list=None) -> bool:
			""" Prepare to send a notification. Determine which content serialization to use first.
				This is done either by looking at the 'ct' argument in a URL, the given csz list, or the CSE default.
				The actual sending is done in a handler function.
			"""
			ct = None
			scheme = None

			# Dissect url and check whether ct is an argumemnt. If yes, then remove it
			# and keep it to check later
			uu = list(urlparse(url))
			qs = parse_qs(uu[4], keep_blank_values=True)
			if ('ct' in qs):
				ct = qs.pop('ct')[0]	# remove the ct=
				uu[4] = urlencode(qs, doseq=True)
				url = urlunparse(uu)	# reconstruct url w/o ct
			scheme = uu[0]

			# Check scheme first
			if scheme not in C.supportedSchemes:
				return False	# Scheme not supported

			if ct is not None:
				# if ct is given then check whether it is supported, 
				# otherwise ignore this url
				if ct not in C.supportedContentSerializationsSimple:
					return False	# Requested serialization not supported
				cst = ContentSerializationType.to(ct)

			elif csz is not None:
				# if csz is given then build an intersection between the given list and
				# the list of supported serializations. Then take the first one
				# as the one to use.
				common = [x for x in csz if x in C.supportedContentSerializations]	# build intersection, keep the old sort order
				if len(common) == 0:
					return False
				cst = ContentSerializationType.to(common[0]) # take the first
			
			else:
				# Just use default serialization.
				cst = CSE.defaultSerialization

			# Actual send the notification
			return sendingFunction(url, cst)

		#
		# Iterate over the notification target list.
		# This list contains URLs and unresolved ri to resources with poa attribute (e.g. AE)
		#

		for notificationTarget in uris:
			if not Utils.isURL(notificationTarget):	# test for id or url
				# The notification target is an indirect resource with poa
				if (resource := CSE.dispatcher.retrieveResource(notificationTarget).resource) is None:
					Logging.logWarn(f'Resource not found to get URL: {notificationTarget}')
					return False
				# if not CSE.security.hasAccess('', resource, Permission.NOTIFY):	# check whether AE/CSE may receive Notifications
				# 	Logging.logWarn(f'No access to resource: {nu}')
				# 	return None
				if resource.poa is None:	# check that the resource has a poa
					Logging.logWarn(f'Resource {notificationTarget} has no "poa" attribute')
					return False
				
				# Send the notification to one (!) of the indirect resource's poa
				for p in resource.poa:
					if _sendNotificationWithSerialization(p, sendingFunction, resource.csz):	# only send to 1 URL in the indirect resource
						break
				else:
					return False	# Loop went through, but not one connection was OK
			else:
				if not _sendNotificationWithSerialization(notificationTarget, sendingFunction):
					return False

		return True


	def _sendRequest(self, url:str, notificationRequest:dict, headers:dict=None, originator:str=None, serialization:ContentSerializationType=None) -> bool:
		"""	Actually send a Notification request.
		"""
		originator = originator if originator is not None else CSE.cseCsi
		return CSE.httpServer.sendCreateRequest(url, originator, data=notificationRequest, headers=headers, ct=serialization).rsc == RC.OK


	#
	#	Batch Notifications
	#


	def _flushBatchNotifications(self, subscription:Resource) -> None:
		ri = subscription.ri
		sub = CSE.storage.getSubscription(ri)

		if (nus := self._getNotificationURLs(sub['nus'])) is not None: # TODO
			ln = sub['ln'] if 'ln' in sub else False
			for nu in nus:
				self._stopNotificationBatchWorker(ri, nu)						# Stop a potential worker for that particular batch
				self._sendSubscriptionAggregatedBatchNotification(ri, nu, ln)	# Send all remaining notifications


	def _storeBatchNotification(self, nu:str, sub:dict, notificationRequest:dict, serialization:ContentSerializationType) -> bool:
		"""	Store a subscription's notification for later sending. For a single nu.
		"""
		# Rename key name
		if 'm2m:sgn' in notificationRequest:
			notificationRequest['sgn'] = notificationRequest.pop('m2m:sgn')

		# Alway add the notification first before doing the other handling
		ri = sub['ri']
		CSE.storage.addBatchNotification(ri, nu, notificationRequest, serialization)

		#  Check for actions
		if (num := Utils.findXPath(sub, 'bn/num')) is not None and (countBN := CSE.storage.countBatchNotifications(ri, nu)) >= num:
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


	def _sendSubscriptionAggregatedBatchNotification(self, ri:str, nu:str, ln:bool=False) -> bool:
		"""	Send and remove(!) the available BatchNotifications for an ri & nu.
		"""
		with self.lockBatchNotification:
			Logging.logDebug(f'Sending aggregated subscription notifications for ri: {ri}')
			# Collect the notifications	
			notifications = []
			serialization = None
			for notification in sorted(CSE.storage.getBatchNotifications(ri, nu), key=lambda x: x['tstamp']):	# sort by timestamp added
				if (n := Utils.findXPath(notification['request'], 'sgn')) is not None:
					notifications.append(n)
				serialization = ContentSerializationType(notification['csz'])	# The last serialization type wins
			if len(notifications) == 0:	# This can happen when the subscription is deleted and there are no outstanding notifications
				return False

			additionalHeaders = None
			if ln:
				notifications = notifications[-1:]
				additionalHeaders = { C.hfcEC : C.hfvECLatest }

			# Aggregate and send
			notificationRequest = {
				'm2m:agn' : { 'm2m:sgn' : notifications }
			}
			if not self._sendRequest(nu, notificationRequest, headers=additionalHeaders, serialization=serialization):
				Logging.logWarn('Error sending aggregated batch notifications')
				return False

			# Delete old notifications
			if not CSE.storage.removeBatchNotifications(ri, nu):
				Logging.logWarn('Error removing aggregated batch notifications')
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
			Logging.logErr('BatchNotification duration is < 1')
			return False
		Logging.logDebug(f'Starting new batchNotificationsWorker. Duration : {dur:f} seconds')

		# Check and start a notification worker to send notifications after some time
		if len(BackgroundWorkerPool.findWorkers(self._workerID(ri, nu))) > 0:	# worker started, return
			return True
		BackgroundWorkerPool.newActor(dur, self._sendSubscriptionAggregatedBatchNotification, name=self._workerID(ri, nu)).start(ri=ri, nu=nu)
		return True


	def _stopNotificationBatchWorker(self, ri:str, nu:str) -> None:
		BackgroundWorkerPool.stopWorkers(self._workerID(ri, nu))


	def _workerID(self, ri:str, nu:str) -> str:
		return f'{ri};{nu}'

