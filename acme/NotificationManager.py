#
#	NotificationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles subscriptions and sending of notifications. 
#

import requests, json
from typing import List, Tuple, Union
from Logging import Logging
from Constants import Constants as C
from Configuration import Configuration
import Utils, CSE
from resources.Resource import Resource

# TODO: removal policy (e.g. unsuccessful tries)
# TODO: no async notifications yet, no batches etc



class NotificationManager(object):

	def __init__(self) -> None:
		Logging.log('NotificationManager initialized')
		if Configuration.get('cse.enableNotifications'):
			Logging.log('Notifications ENABLED')
		else:
			Logging.log('Notifications DISABLED')


	def shutdown(self) -> None:
		Logging.log('NotificationManager shut down')


	def addSubscription(self, subscription: Resource, originator: str) -> Tuple[bool, int, str]:
		if not Configuration.get('cse.enableNotifications'):
			return False, C.rcSubscriptionVerificationInitiationFailed, 'notifications are disabled'
		Logging.logDebug('Adding subscription')
		if (result := self._getAndCheckNUS(subscription, originator=originator))[0] is None:	# verification requests happen here
			return False, result[1], result[2]
		return (True, C.rcOK, None) if CSE.storage.addSubscription(subscription) else (False, C.rcInternalServerError, 'cannot add subscription to database')


	def removeSubscription(self, subscription: Resource) -> Tuple[bool, int, str]:
		""" Remove a subscription. Send the deletion notifications, if possible. """
		Logging.logDebug('Removing subscription')

		# This check does allow for removal of subscriptions
		if not Configuration.get('cse.enableNotifications'):
			return False, C.rcSubscriptionVerificationInitiationFailed, 'notifications are disabled'

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
		
		return (True, C.rcOK, None) if CSE.storage.removeSubscription(subscription) else (False, C.rcInternalServerError, 'cannot remove subscription from database')



	def updateSubscription(self, subscription: Resource, newJson: dict, previousNus: List[str], originator: str) -> Tuple[bool, int, str]:
		Logging.logDebug('Updating subscription')
		#previousSub = CSE.storage.getSubscription(subscription.ri)
		if (result := self._getAndCheckNUS(subscription, newJson, previousNus, originator=originator))[0] is None:	# verification/delete requests happen here
			return False, result[1], result[2]
		return (True, C.rcOK, None) if CSE.storage.updateSubscription(subscription) else (False, C.rcInternalServerError, 'cannot update subscription in database')


	def checkSubscriptions(self, resource: Resource, reason: int, childResource: Resource = None) -> None:
		if not Configuration.get('cse.enableNotifications'):
			return

		if Utils.isVirtualResource(resource):
			return 

		ri = resource.ri
		subs = CSE.storage.getSubscriptionsForParent(ri)
		if subs is None or len(subs) == 0:
			return

		Logging.logDebug('Checking subscription for: %s, reason: %d' % (ri, reason))
		for sub in subs:
			# Prevent own notifications for subscriptions 
			if childResource is not None and \
				sub['ri'] == childResource.ri and \
				reason in [C.netCreateDirectChild, C.netDeleteDirectChild]:
					continue
			if reason not in sub['net']:	# check whether reason is actually included in the subscription
				continue
			if reason in [C.netCreateDirectChild, C.netDeleteDirectChild]:	# reasons for child resources
				for nu in self._getNotificationURLs(sub['nus']):
					if not self._sendNotification(sub['ri'], nu, reason, childResource):
						pass
			else: # all other reasons that target the resource
				for nu in self._getNotificationURLs(sub['nus']):
					if not self._sendNotification(sub['ri'], nu, reason, resource):
						pass


	#########################################################################

	# Return resolved notification URLs, so also POA from referenced AE's etc
	def _getNotificationURLs(self, nus: Union[List[str], str], originator: str = None) -> List[str]:
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
				r, _, _ = CSE.dispatcher.retrieveResource(nu)
				if r is None:
					Logging.logWarn('Resource not found to get URL: %s' % nu)
					return None

				# If the Originator is the notification target then exclude it from the list of targets
				# Test for AE and CSE (CSE starts with a /)
				if originator is not None and (r.ri == originator or r.ri == '/%s' % originator):
					Logging.logDebug('Notification target is the originator, no verification request for: %s' % nu)
					continue
				if not CSE.security.hasAccess('', r, C.permNOTIFY):	# check whether AE/CSE may receive Notifications
					Logging.logWarn('No access to resource: %s' % nu)
					return None
				if (poa := r['poa']) is not None and isinstance(poa, list):	#TODO? check whether AE or CSEBase
					result += poa
		return result


	def _getAndCheckNUS(self, subscription: Resource, newJson: dict = None, previousNus: List[str] = None, originator: str = None) -> Tuple[List[str], int, str]:
		newNus = []
		if newJson is None:	# If there is no new JSON structure, get the one from the subscription to work with
			newJson = subscription.asJSON()

		# Resolve the URI's in the previousNus.
		if previousNus is not None:
			if (previousNus := self._getNotificationURLs(previousNus, originator)) is None:
				# Fail if any of the NU's cannot be retrieved
				return None, C.rcSubscriptionVerificationInitiationFailed, 'cannot retrieve all previous nu''s'

		# Are there any new URI's?
		if (nuAttribute := Utils.findXPath(newJson, 'm2m:sub/nu')) is not None:

			# Resolve the URI's for the new NU's
			if (newNus := self._getNotificationURLs(nuAttribute, originator)) is None:
				# Fail if any of the NU's cannot be retrieved
				return None, C.rcSubscriptionVerificationInitiationFailed, 'cannot retrieve all new nu''s'

			# notify new nus (verification request). New ones are the ones that are not in the previousNU list
			for nu in newNus:
				if previousNus is None or (nu not in previousNus):
					if not self._sendVerificationRequest(nu, subscription.ri, originator=originator):
						Logging.logDebug('Verification request failed: %s' % nu)
						return None, C.rcSubscriptionVerificationInitiationFailed, 'verification request failed for nu: %s' % nu

		# notify removed nus (deletion notification) if nu = null
		if 'nu' in newJson: # if nu not present, nothing to do
			if previousNus is not None:
				for nu in previousNus:
					if nu not in newNus:
						if not self._sendDeletionNotification(nu, subscription.ri):
							Logging.logDebug('Deletion request failed') # but ignore the error

		return newNus, C.rcOK, None


	#########################################################################




	def _sendVerificationRequest(self, nu: str, ri: str, originator: str = None) -> bool:
		Logging.logDebug('Sending verification request to: %s' % nu)
	
		verificationRequest = {
			'm2m:sgn' : {
				'vrq' : True,
				'sur' : ''
			}
		}
	
		return self._sendRequest(nu, ri, verificationRequest, originator=originator)


	def _sendDeletionNotification(self, nu: str, ri: str) -> bool:
		Logging.logDebug('Sending deletion notification to: %s' % nu)
	
		deletionNotification = {
			'm2m:sgn' : {
				'sud' : True,
				'sur' : ''
			}
		}
		
		return self._sendRequest(nu, ri, deletionNotification)


	def _sendNotification(self, ri: str, nu: str, reason: int, resource: Resource) ->  bool:
		Logging.logDebug('Sending notification to: %s, reason: %d' % (nu, reason))

		notificationRequest = {
			'm2m:sgn' : {
				'nev' : {
					'rep' : {},
					'net' : 0
				},
				'sur' : ''
			}
		}

		return self._sendRequest(nu, ri, notificationRequest, reason, resource)


	def _sendRequest(self, nu: str, ri: str, jsn: dict, reason: int = None, resource: Resource = None, originator: str = None) -> bool:
		Utils.setXPath(jsn, 'm2m:sgn/sur', Utils.fullRI(ri))

		# Add some values to the notification
		# TODO: switch statement:  (x is not None and bla())
		if reason is not None:
			Utils.setXPath(jsn, 'm2m:sgn/nev/net', reason)
		if resource is not None:
			Utils.setXPath(jsn, 'm2m:sgn/nev/rep', resource.asJSON())
		if originator is not None:
			Utils.setXPath(jsn, 'm2m:sgn/cr', originator)

		_, rc, _ = CSE.httpServer.sendCreateRequest(nu, Configuration.get('cse.csi'), data=json.dumps(jsn))
		return rc in [C.rcOK]

