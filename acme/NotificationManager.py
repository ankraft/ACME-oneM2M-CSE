#
#	NotificationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles subscriptions and sending of notifications. 
#

import requests, json
import isodate
from typing import List, Union
from threading import Lock
from Logging import Logging
from Constants import Constants as C
from Types import Result, NotificationContentType, NotificationEventType, Permission, ResponseCode as RC
from Configuration import Configuration
import Utils, CSE
from helpers.BackgroundWorker import BackgroundWorkerPool
from resources.Resource import Resource

# TODO: removal policy (e.g. unsuccessful tries)
# TODO: no async notifications yet, no batches etc



class NotificationManager(object):

	def __init__(self) -> None:
		self.lockBatchNotification = Lock()	# Lock for batchNotifications

		if Configuration.get('cse.enableNotifications'):
			Logging.log('Notifications ENABLED')
		else:
			Logging.log('Notifications DISABLED')
		Logging.log('NotificationManager initialized')


	def shutdown(self) -> None:
		Logging.log('NotificationManager shut down')


	def addSubscription(self, subscription:Resource, originator:str) -> Result:
		if not Configuration.get('cse.enableNotifications'):
			return Result(status=False, rsc=RC.subscriptionVerificationInitiationFailed, dbg='notifications are disabled')
		Logging.logDebug('Adding subscription')
		if (res := self._getAndCheckNUS(subscription, originator=originator)).lst is None:	# verification requests happen here
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)
		return Result(status=True) if CSE.storage.addSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot add subscription to database')


	def removeSubscription(self, subscription: Resource) -> Result:
		""" Remove a subscription. Send the deletion notifications, if possible. """
		Logging.logDebug('Removing subscription')

		# This check does allow for removal of subscriptions
		if not Configuration.get('cse.enableNotifications'):
			return Result(status=False, rsc=RC.subscriptionVerificationInitiationFailed, dbg='notifications are disabled')

		# Send outstanding batchNotifications
		self._flushBatchNotifications(subscription)

		# Send a deletion request to the subscriberURI
		if (sus := self._getNotificationURLs([subscription['su']])) is not None:
			for su in sus:
				if not self._sendDeletionNotification(su, subscription.ri):
					Logging.logDebug('Deletion request failed: %s' % su) # but ignore the error

		# Send a deletion request to the associatedCrossResourceSub
		if (acrs := subscription['acrs']) is not None and (nus := self._getNotificationURLs(acrs)) is not None:
			for nu in nus:
				if not self._sendDeletionNotification(nu, subscription.ri):
					Logging.logDebug('Deletion request failed: %s' % nu) # but ignore the error
		
		# Finally remove subscriptions from storage
		return Result(status=True) if CSE.storage.removeSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot remove subscription from database')


	def updateSubscription(self, subscription:Resource, newJson:dict, previousNus:List[str], originator:str) -> Result:
		Logging.logDebug('Updating subscription')
		#previousSub = CSE.storage.getSubscription(subscription.ri)
		if (res := self._getAndCheckNUS(subscription, newJson, previousNus, originator=originator)).lst is None:	# verification/delete requests happen here
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)
		return Result(status=True) if CSE.storage.updateSubscription(subscription) else Result(status=False, rsc=RC.internalServerError, dbg='cannot update subscription in database')


	def checkSubscriptions(self, resource:Resource, reason:NotificationEventType, childResource:Resource=None, modifiedAttributes:dict=None) -> None:
		if not Configuration.get('cse.enableNotifications'):
			return

		if Utils.isVirtualResource(resource):
			return 

		ri = resource.ri

		# ATTN: The "subscription" returned here are NOT the <sub> resources,
		# but an internal representation from the 'subscription' DB !!!
		# Access to attributes is different bc the structure is flattened
		subs = CSE.storage.getSubscriptionsForParent(ri)
		if subs is None or len(subs) == 0:
			return

		Logging.logDebug('Checking subscription for: %s, reason: %d' % (ri, reason))
		for sub in subs:
			# Prevent own notifications for subscriptions 
			if childResource is not None and \
				sub['ri'] == childResource.ri and \
				reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:
					continue
			if reason not in sub['net']:	# check whether reason is actually included in the subscription
				continue
			if reason in [ NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]:	# reasons for child resources
				for nu in self._getNotificationURLs(sub['nus']):
					if not self._sendSubscriptionNotification(sub, nu, reason, childResource, modifiedAttributes=modifiedAttributes):
						pass
			else: # all other reasons that target the resource
				for nu in self._getNotificationURLs(sub['nus']):
					if not self._sendSubscriptionNotification(sub, nu, reason, resource, modifiedAttributes=modifiedAttributes):
						pass


	# def sendOutstandingNotifications(self, ri:str) -> None:
	# 	"""	Send outstanding Notifications for a subscription (for ri).
	# 	"""
	# 	subs = CSE.storage.getSubscriptions(ri)
	# 	if subs is None or len(subs) == 0:
	# 		return
	# 	for sub in subs:
	# 		for nu in self._getNotificationURLs(sub['nus']):
	# 			pass # TODO

	#########################################################################

	# Return resolved notification URLs, so also POA from referenced AE's etc
	def _getNotificationURLs(self, nus:Union[List[str], str], originator:str=None) -> List[str]:
		if nus is None:
			return []
		nusl = nus if isinstance(nus, list) else [ nus ]	# make a list out of it even when it is a single value
		result = []
		for nu in nusl:
			if nu is None:
				continue
			# check if it is a direct URL
			Logging.logDebug("Checking next notification target: %s" % nu)
			if Utils.isURL(nu):
				result.append(nu)
			else:
				if (resource := CSE.dispatcher.retrieveResource(nu).resource) is None:
					Logging.logWarn('Resource not found to get URL: %s' % nu)
					return None

				# If the Originator is the notification target then exclude it from the list of targets
				# Test for AE and CSE (CSE starts with a /)
				if originator is not None and (resource.ri == originator or resource.ri == '/%s' % originator):
					Logging.logDebug('Notification target is the originator, no verification request for: %s' % nu)
					continue
				if not CSE.security.hasAccess('', resource, Permission.NOTIFY):	# check whether AE/CSE may receive Notifications
					Logging.logWarn('No access to resource: %s' % nu)
					return None
				if (poa := resource.poa) is not None and isinstance(poa, list):	#TODO? check whether AE or CSEBase
					result += poa
		return result


	def _getAndCheckNUS(self, subscription:Resource, newJson:dict=None, previousNus:List[str]=None, originator:str=None) -> Result:
		newNus = []
		if newJson is None:	# If there is no new JSON structure, get the one from the subscription to work with
			newJson = subscription.asJSON()

		# Resolve the URI's in the previousNus.
		if previousNus is not None:
			if (previousNus := self._getNotificationURLs(previousNus, originator)) is None:
				# Fail if any of the NU's cannot be retrieved
				return Result(rsc=RC.subscriptionVerificationInitiationFailed, dbg='cannot retrieve all previous nu''s')

		# Are there any new URI's?
		if (nuAttribute := Utils.findXPath(newJson, 'm2m:sub/nu')) is not None:

			# Resolve the URI's for the new NU's
			if (newNus := self._getNotificationURLs(nuAttribute, originator)) is None:
				# Fail if any of the NU's cannot be retrieved
				return Result(rsc=RC.subscriptionVerificationInitiationFailed, dbg='cannot retrieve all new nu''s')

			# notify new nus (verification request). New ones are the ones that are not in the previousNU list
			for nu in newNus:
				if previousNus is None or (nu not in previousNus):
					if not self._sendVerificationRequest(nu, subscription.ri, originator=originator):
						Logging.logDebug('Verification request failed: %s' % nu)
						return Result(rsc=RC.subscriptionVerificationInitiationFailed, dbg='verification request failed for nu: %s' % nu)

		# notify removed nus (deletion notification) if nu = null
		if 'nu' in newJson: # if nu not present, nothing to do
			if previousNus is not None:
				for nu in previousNus:
					if nu not in newNus:
						if not self._sendDeletionNotification(nu, subscription.ri):
							Logging.logDebug('Deletion request failed') # but ignore the error

		return Result(lst=newNus)


	#########################################################################


	def _sendVerificationRequest(self, nu:str, ri:str, originator:str=None) -> bool:
		Logging.logDebug('Sending verification request to: %s' % nu)
	
		verificationRequest = {
			'm2m:sgn' : {
				'vrq' : True,
				'sur' : Utils.fullRI(ri)

			}
		}
		originator is not None and Utils.setXPath(verificationRequest, 'm2m:sgn/cr', originator)
		return self._sendRequest(nu, verificationRequest)


	def _sendDeletionNotification(self, nu:str, ri:str) -> bool:
		Logging.logDebug('Sending deletion notification to: %s' % nu)
	
		deletionNotification = {
			'm2m:sgn' : {
				'sud' : True,
				'sur' : Utils.fullRI(ri)
			}
		}
		
		return self._sendRequest(nu, deletionNotification)


	def _sendSubscriptionNotification(self, sub:dict, nu:str, reason:NotificationEventType, resource:Resource, modifiedAttributes:dict=None) ->  bool:
		Logging.logDebug('Sending notification to: %s, reason: %d' % (nu, reason))

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
		nct == NotificationContentType.all					and (data := resource.asJSON())
		nct == NotificationContentType.ri 					and (data := { 'm2m:uri' : Utils.fullRI(resource.ri) })
		nct == NotificationContentType.modifiedAttributes	and (data := { resource.tpe : modifiedAttributes })
		# TODO nct == NotificationContentType.triggerPayload

		# Add some values to the notification
		reason is not None 									and Utils.setXPath(notificationRequest, 'm2m:sgn/nev/net', reason)
		data is not None 									and Utils.setXPath(notificationRequest, 'm2m:sgn/nev/rep', data)

		if sub['bn'] is not None:
			return self._handleBatchNotification(nu, sub, notificationRequest)
		else:
			return self._sendRequest(nu, notificationRequest)


	def _sendRequest(self, nu:str, notificationRequest:dict) -> bool:
		"""	Actually send a Notification request.
		"""
		return CSE.httpServer.sendCreateRequest(nu, Configuration.get('cse.csi'), data=json.dumps(notificationRequest)).rsc == RC.OK


	def _flushBatchNotifications(self, subscription:Resource) -> None:
		ri = subscription.ri
		sub = CSE.storage.getSubscription(ri)

		for nu in self._getNotificationURLs(sub['nus']):
			self._stopNotificationBatchWorker(ri, nu)					# Stop a potential worker
			self._sendSubscriptionAggregatedBatchNotification(ri, nu)	# Send all remaining notifications


	def _handleBatchNotification(self, nu:str, sub:dict, notificationRequest:dict) -> bool:
		"""	Store a subscription's notification for later sending.
		"""
		# Rename key name
		if 'm2m:sgn' in notificationRequest:
			notificationRequest['sgn'] = notificationRequest.pop('m2m:sgn')

		# Alway add the notification first before doing the other handling
		ri = sub['ri']
		CSE.storage.addBatchNotification(ri, nu, notificationRequest)

		#  Check for actions
		if (num := Utils.findXPath(sub, 'bn/num')) is not None and (countBN := CSE.storage.countBatchNotifications(ri, nu)) >= num:
			self._stopNotificationBatchWorker(ri, nu)	# Stop the worker, not needed
			self._sendSubscriptionAggregatedBatchNotification(ri, nu)

		# Check / start Timer worker to guard the batch notification duration
		else:
			try:
				dur = isodate.parse_duration(Utils.findXPath(sub, 'bn/dur')).total_seconds()
			except Exception as e:
				return False
			self._startNewBatchNotificationWorker(ri, nu, dur)
		return True


	def _sendSubscriptionAggregatedBatchNotification(self, ri:str, nu:str) -> bool:
		"""	Send and remove(!) the available BatchNotifications for an ri & nu.
		"""
		with self.lockBatchNotification: # TODO check whether this is actually necessary
			Logging.log('Sending aggregated subscription notifications for ri: %s' % ri)
			# Collect the notifications	
			notifications = []		
			for notification in CSE.storage.getBatchNotifications(ri, nu):
				notifications.append(notification['request'])
			if len(notifications) == 0:	# This can happen when the subscription is deleted and there are no outstanding notifications
				return False

			# Aggregate and send
			notificationRequest = {
				'm2m:agn' : notifications
			}
			if not self._sendRequest(nu, notificationRequest):
				Logging.logWarn('Error sending aggregated batch notifications')
				return False

			# Delete old notifications
			if not CSE.storage.removeBatchNotifications(ri, nu):
				Logging.logWarn('Error removing aggregated batch notifications')
				return False

			return True


	def _startNewBatchNotificationWorker(self, ri:str, nu:str, dur:int) -> bool:
		if dur is None or dur < 1:
			Logging.logErr('BatchNotification duration is < 1')
			return False
		Logging.logDebug('Starting new batchNotificationsWorker. Duration : %d seconds' % dur)

		# Check and start a notification worker to send notifications after some time
		if len(BackgroundWorkerPool.findWorkers(self._workerID(ri, nu))) > 0:	# worker started, return
			return True
		BackgroundWorkerPool.newActor(dur, self._sendSubscriptionAggregatedBatchNotification, name=self._workerID(ri, nu)).start(ri=ri, nu=nu)
		return True


	def _stopNotificationBatchWorker(self, ri:str, nu:str) -> None:
		BackgroundWorkerPool.stopWorkers(self._workerID(ri, nu))


	def _workerID(self, ri:str, nu:str) -> str:
		return '%s;%s' % (ri, nu)

