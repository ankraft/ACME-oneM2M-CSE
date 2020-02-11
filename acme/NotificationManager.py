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


	def addSubscription(self, subscription):
		if Configuration.get('cse.enableNotifications') is not True:
			return False
		Logging.logDebug('Adding subscription')
		if self._getAndCheckNUS(subscription) is None:	# verification requests happen here
			return False
		return CSE.storage.addSubscription(subscription)


	def removeSubscription(self, subscription):
		Logging.logDebug('Removing subscription')
		# This check does allow for removal of subscriptions
		if Configuration.get('cse.enableNotifications'):
			for nu in self._getNotificationURLs(subscription.nu):
				if not self._sendDeletionNotification(nu, subscription):
					Logging.logDebug('Deletion request failed') # but ignore the error
		return CSE.storage.removeSubscription(subscription)


	def updateSubscription(self, subscription):
		Logging.logDebug('Updating subscription')
		previousSub = CSE.storage.getSubscription(subscription.ri)
		if self._getAndCheckNUS(subscription, previousSub['nus']) is None:	# verification/delete requests happen here
			return False
		return CSE.storage.updateSubscription(subscription)


	def checkSubscriptions(self, resource, reason, childResource=None):
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
		result = []
		for nu in nus:
			# check if it is a direct URL
			if Utils.isURL(nu):
				result.append(nu)
			else:
				(r, _) = CSE.dispatcher.retrieveResource(nu)
				if r is None:
					continue
				if not CSE.security.hasAccess('', r, C.permNOTIFY):	# check whether AE/CSE may receive Notifications
					continue
				if (poa := r['poa']) is not None and isinstance(poa, list):	#TODO? check whether AE or CSEBase
					result += poa
		return result


	def _getAndCheckNUS(self, subscription, previousNus=None):
		newNus = self._getNotificationURLs(subscription['nu'])
		# notify removed nus (deletion notification)
		if previousNus is not None:
			for nu in previousNus:
				if nu not in newNus:
					if not self._sendDeletionNotification(nu, subscription):
						Logging.logDebug('Deletion request failed') # but ignore the error

		# notify new nus (verification request)
		for nu in newNus:
			if previousNus is None or (previousNus and nu not in previousNus):
				if not self._sendVerificationRequest(nu, subscription):
					Logging.logDebug('Verification request failed: %s' % nu)
					return None
		return newNus

	#########################################################################


	_verificationRequest = {
		'm2m:sgn' : {
			'vrq' : True,
			'sur' : ''
		}
	}

	def _sendVerificationRequest(self, nu, subscription):
		Logging.logDebug('Sending verification request to: %s' % nu)
		return self._sendRequest(nu, subscription['ri'], self._verificationRequest)


	_deletionNotification = {
		'm2m:sgn' : {
			'sud' : True,
			'sur' : ''
		}
	}

	def _sendDeletionNotification(self, nu, subscription):
		Logging.logDebug('Sending deletion notification to: %s' % nu)
		return self._sendRequest(nu, subscription['ri'], self._deletionNotification)


	_notificationRequest = {
		'm2m:sgn' : {
			'nev' : {
				'rep' : {},
				'net' : 0
			},
			'sur' : ''
		}
	}

	def _sendNotification(self, subscription, nu, reason, resource):
		Logging.logDebug('Sending notification to: %s, reason: %d' % (nu, reason))
		return self._sendRequest(nu, subscription['ri'], self._notificationRequest, reason, resource)


	def _sendRequest(self, nu, ri, jsn, reason=None, resource=None):
		Utils.setXPath(jsn, 'm2m:sgn/sur', Utils.fullRI(ri))
		if reason is not None:
			Utils.setXPath(jsn, 'm2m:sgn/nev/net', reason)
		if resource is not None:
			Utils.setXPath(jsn, 'm2m:sgn/nev/rep', resource.asJSON())				
		(_, rc) = CSE.httpServer.sendCreateRequest(nu, Configuration.get('cse.csi'), data=json.dumps(jsn))
		return rc in [C.rcOK]

