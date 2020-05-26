#
#	NotificationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles subscriptions and sending of notifications. 
#

from Logging import Logging
from Constants import Constants as C
from Configuration import Configuration
import Utils, CSE
import requests, json


# TODO: removal policy (e.g. unsuccessful tries)
# TODO: no async notifications yet, no batches etc



class NotificationManager(object):

	def __init__(self):
		Logging.log('NotificationManager initialized')
		if Configuration.get('cse.enableNotifications'):
			Logging.log('Notifications ENABLED')
		else:
			Logging.log('Notifications DISABLED')


	def shutdown(self):
		Logging.log('NotificationManager shut down')


	def addSubscription(self, subscription, originator):
		if Configuration.get('cse.enableNotifications') is not True:
			return (False, C.rcSubscriptionVerificationInitiationFailed)
		Logging.logDebug('Adding subscription')
		if (result := self._getAndCheckNUS(subscription, originator=originator))[0] is None:	# verification requests happen here
			return (False, result[1])
		return (True, C.rcOK) if CSE.storage.addSubscription(subscription) else (False, C.rcSubscriptionVerificationInitiationFailed)


	def removeSubscription(self, subscription):
		""" Remove a subscription. Send the deletion notifications, if possible. """
		Logging.logDebug('Removing subscription')

		# This check does allow for removal of subscriptions
		if Configuration.get('cse.enableNotifications'):

			# Send a deletion request to the subscriberURI
			for su in self._getNotificationURLs(subscription['su']):
				if not self._sendDeletionNotification(su, subscription):
					Logging.logDebug('Deletion request failed: %s' % su) # but ignore the error

			# Send a deletion request to the associatedCrossResourceSub
			for nu in self._getNotificationURLs(subscription['acrs']):
				if not self._sendDeletionNotification(nu, subscription):
					Logging.logDebug('Deletion request failed: %s' % nu) # but ignore the error
		
		return (True, C.rcOK) if CSE.storage.removeSubscription(subscription) else (False, C.rcInternalServerError)



	def updateSubscription(self, subscription):
		Logging.logDebug('Updating subscription')
		previousSub = CSE.storage.getSubscription(subscription.ri)
		if (result := self._getAndCheckNUS(subscription, previousSub['nus']))[0] is None:	# verification/delete requests happen here
			return (False, result[1])
		return (True, C.rcOK) if CSE.storage.updateSubscription(subscription) else (False, result[1])


	def checkSubscriptions(self, resource, reason, childResource=None):
		Logging.logDebug('Check subscription')
		if Configuration.get('cse.enableNotifications') is not True:
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
					if not self._sendNotification(sub, nu, reason, childResource):
						pass
			else: # all other reasons that target the resource
				for nu in self._getNotificationURLs(sub['nus']):
					if not self._sendNotification(sub, nu, reason, resource):
						pass


	#########################################################################

	# Return resolved notification URLs, so also POA from referenced AE's etc
	def _getNotificationURLs(self, nus):
		if nus is None:
			return []
		nusl = nus if isinstance(nus, list) else [ nus ]	# make a list out of it even when it is a single value
		result = []
		for nu in nusl:
			# check if it is a direct URL
			if Utils.isURL(nu):
				result.append(nu)
			else:
				(r, _) = CSE.dispatcher.retrieveResource(nu)
				if r is None:
					Logging.logWarn('Resource not found to get URL: %s' % nu)
					return None
				if not CSE.security.hasAccess('', r, C.permNOTIFY):	# check whether AE/CSE may receive Notifications
					Logging.logWarn('No access to resource: %s' % nu)
					return None
				if (poa := r['poa']) is not None and isinstance(poa, list):	#TODO? check whether AE or CSEBase
					result += poa
		return result


	def _getAndCheckNUS(self, subscription, previousNus=None, originator=None):
		if (newNus := self._getNotificationURLs(subscription['nu'])) is None:
			# Fail if any of the NU's cannot be retrieved
			return (None, C.rcSubscriptionVerificationInitiationFailed)	

		# notify removed nus (deletion notification)
		if previousNus is not None:
			for nu in previousNus:
				if nu not in newNus:
					if not self._sendDeletionNotification(nu, subscription):
						Logging.logDebug('Deletion request failed') # but ignore the error

		# notify new nus (verification request)
		for nu in newNus:
			if previousNus is None or (previousNus and nu not in previousNus):
				if not self._sendVerificationRequest(nu, subscription, originator=originator):
					Logging.logDebug('Verification request failed: %s' % nu)
					return (None, C.rcSubscriptionVerificationInitiationFailed)	
		return (newNus, C.rcOK)


	#########################################################################




	def _sendVerificationRequest(self, nu, subscription, originator=None):
		Logging.logDebug('Sending verification request to: %s' % nu)
	
		verificationRequest = {
			'm2m:sgn' : {
				'vrq' : True,
				'sur' : ''
			}
		}
	
		return self._sendRequest(nu, subscription['ri'], verificationRequest, originator=originator)


	def _sendDeletionNotification(self, nu, subscription):
		Logging.logDebug('Sending deletion notification to: %s' % nu)
	
		deletionNotification = {
			'm2m:sgn' : {
				'sud' : True,
				'sur' : ''
			}
		}
		
		return self._sendRequest(nu, subscription['ri'], deletionNotification)


	def _sendNotification(self, subscription, nu, reason, resource):
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

		return self._sendRequest(nu, subscription['ri'], notificationRequest, reason, resource)


	def _sendRequest(self, nu, ri, jsn, reason=None, resource=None, originator=None):
		Utils.setXPath(jsn, 'm2m:sgn/sur', Utils.fullRI(ri))

		# Add some values to the notification
		if reason is not None:
			Utils.setXPath(jsn, 'm2m:sgn/nev/net', reason)
		if resource is not None:
			Utils.setXPath(jsn, 'm2m:sgn/nev/rep', resource.asJSON())
		if originator is not None:
			Utils.setXPath(jsn, 'm2m:sgn/cr', originator)

		(_, rc) = CSE.httpServer.sendCreateRequest(nu, Configuration.get('cse.csi'), data=json.dumps(jsn))
		return rc in [C.rcOK]

