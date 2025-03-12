#
#	SUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	The <subscription> resource contains subscription information for its subscribed-to resource.
"""

from __future__ import annotations
from typing import Optional

from copy import deepcopy

from ..etc.ACMEUtils import pureResource
from ..helpers.TextTools import findXPath
from ..etc.Types import AttributePolicyDict, ResourceTypes, NotificationContentType
from ..etc.Types import NotificationEventType, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST, INTERNAL_SERVER_ERROR
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource


# TODO notificationForwardingURI
# TODO work on more NEC attributes


class SUB(Resource):

	resourceType = ResourceTypes.SUB
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SCH
						   							 ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'cstn': None,
		'acpi':None,
		'daci': None,
		'cr': None,

		# Resource attributes
		'enc': None,
		'exc': None,
		'nu': None,
		'gpi': None,
		'nfu': None,
		'bn': None,
		'rl': None,
		'psn': None,
		'pn': None,
		'nsp': None,
		'ln': None,
		'nct': None,
		'nec': None,
		'su': None,
		'acrs': None,
		'nse': None,
		'nsi': None,
		'eeno': None,
		'ma': None,		# EXPERIMENTAL maxage blocking retrieve
	}

	_disallowedBlockingAttributes = [
		'exc', 'gpi', 'nfu', 'bn', 'rl', 'psn',	'pn', 'nsp', 'ln',
		'nec', 'acrs',
	]
	"""	These attributes are not allowed in blocking-* subscription.
	"""

	_allowedENCAttributes = {
		'atr', 'net'
	}


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# set batchNotify default attributes
		if self.bn:		
			self.setAttribute('bn/dur', Configuration.resource_sub_batchNotifyDuration, overwrite = False)

		# Apply the nct only on the first element of net. Do the combination checks later in validate()
		net = self['enc/net']
		if net is not None and len(net) > 0:
			match net[0]:
				case NotificationEventType.resourceUpdate |\
					 NotificationEventType.resourceDelete |\
					 NotificationEventType.createDirectChild |\
					 NotificationEventType.deleteDirectChild |\
					 NotificationEventType.retrieveCNTNoChild:
					self.setAttribute('nct', NotificationContentType.allAttributes, overwrite = False)
				
				case NotificationEventType.triggerReceivedForAE:
					self.setAttribute('nct', NotificationContentType.triggerPayload, overwrite = False)

				case NotificationEventType.blockingUpdate:
					self.setAttribute('nct', NotificationContentType.modifiedAttributes, overwrite = False)

				case NotificationEventType.reportOnGeneratedMissingDataPoints:			
					self.setAttribute('nct', NotificationContentType.timeSeriesNotification, overwrite = False)

		# check whether an observed child resource type is actually allowed by the parent
		if chty := self['enc/chty']:
			self._checkAllowedCHTY(parentResource, chty)
		
		# "nsi" will be added later during the first stat recording

		CSE.notification.addSubscription(self, originator)

		# Increment the parent's subscription counter
		parentResource.incrementSubscriptionCounter()
		# L.logWarn(f'Incremented subscription counter for {parentResource.ri} to {parentResource.getSubscriptionCounter()}')



	def deactivate(self, originator:str, parentResource:Resource) -> None:
		super().deactivate(originator, parentResource)
		CSE.notification.removeSubscription(self, originator)
		parentResource.decrementSubscriptionCounter()
		# L.logWarn(f'Decremented subscription counter for {parentResource.ri} to {parentResource.getSubscriptionCounter()}')


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		previousNus = deepcopy(self.nu)

		# We are validating the attributes here already because this actual update of the resource
		# (where this happens) is done only after a lot of other stuff hapened.
		# So, the resource is validated twice in an update :()
		CSE.validator.validateAttributes(dct, 
										 self.typeShortname, 
										 self.ty, 
										 self._attributes, 
										 create = False, 
										 createdInternally = self.isCreatedInternally(),
										 isAnnounced = self.isAnnounced())


		# Handle update notificationStatsEnable attribute, but only if present in the resource.
		# This is important bc it can be set to True, False, or Null.
		pure = pureResource(dct)[0]
		if 'nse' in pure:
			CSE.notification.updateOfNSEAttribute(self, findXPath(dct, 'm2m:sub/nse'))

		# Reject updates with blocking *
		if (net := findXPath(pure, 'enc/net')) and self._hasBlockingNET(net):
			raise BAD_REQUEST(L.logDebug('Updates with any blocking Notification Event Type if not allowed.'))

		# Handle changes to acrs (send deletion notifications)
		if (newAcrs := findXPath(dct, 'm2m:sub/acrs')) is not None and self.acrs is not None:
			for crsRI in set(self.acrs) - set(newAcrs):
				L.isDebug and L.logDebug(f'Update of acrs: {crsRI} removed. Sending deletion notification')
				CSE.notification.sendDeletionNotification(crsRI, self.ri)	# TODO ignore result?

		# Do actual update
		super().update(dct, originator, doValidateAttributes = False)
		

		# check whether an observed child resource type is actually allowed by the parent
		if chty := self['enc/chty']:
			parentResource = self.retrieveParentResource()
			self._checkAllowedCHTY(parentResource, chty)

		CSE.notification.updateSubscription(self, previousNus, originator)

 
	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)

		L.isDebug and L.logDebug(f'Validating subscription: {self.ri}')
		attrs = self.dict if dct is None else pureResource(dct)[0]
		newEnc = attrs.get('enc')

		newNet = newEnc.get('net') if newEnc is not None else None
		newOm = newEnc.get('om') if newEnc is not None else None

		# Test whether notificationEventType and operationMonitor are specified together
		if newNet is not None and newOm is not None:
			raise BAD_REQUEST(L.logDebug('enc/net and enc/om cannot be specified together'))

		# Test whether operationMonitor is specified and is a valid value
		if newOm is not None:
			for om in newOm:
				if om.get('ops') is None and om.get('org') is None:
					raise BAD_REQUEST(L.logDebug('Entries in enc/om must contain at least one of "ops" or "org"'))
				
		# ensure that enc isalways present
		if self['enc'] is None:
			self.setAttribute('enc', {})	
		
		# Apply default enc/net value.
		if self['enc/net'] is None and self['enc/om'] is None:
			self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate.value ], overwrite = False)

		# Check NotificationEventType
		if (newNet := findXPath(attrs, 'enc/net')) is not None and not NotificationEventType.has(newNet):
			raise BAD_REQUEST(L.logDebug(f'enc/net={str(newNet)} is not an allowed or supported NotificationEventType'))

		# Check if blocking RETRIEVE or blocking UPDATE is the only NET in the subscription, 
		# AND that there is no other NET for this resource
		if newNet and self._hasBlockingNET(newNet):

			# only one entry in NET must exist per blocking subscription
			L.isWarn and L.logWarn(f'Blocking subscription: {newNet}')
			if len(newNet) > 1:
				raise BAD_REQUEST(L.logDebug(f'blockingRetrieve/blockingUpdate must be the only value in enc/net'))

			# Only one of each blocking UPDATE or RETRIEVE etc must exist for this resource
			# This works here in validate bc it is only allowed in CREATE/activate, and this resource has 
			# not been written to DB yet.
			if CSE.notification.getSubscriptionsByNetChty(parentResource.ri, net = newNet):
				raise BAD_REQUEST(L.logDebug(f'a subscription with blockingRetrieve/blockingUpdate/blockingRetrieveDirectChild already exsists for this resource'))

			# Only one NU is allowed for blocking UPDATE or RETRIEVE
			if len(self.nu) > 1:
				raise BAD_REQUEST(L.logDebug(f'nu must contain only one target for blockingRetrieve/blockingUpdate'))

			# Disallow other subscription-specific attributes if this is a blocking-* subscription
			if self._hasDisallowedBlockingAttributes(attrs):
				raise BAD_REQUEST(L.logDebug(f'disallowed attribute(s) in blocking-subscription'))

			# Disallow condition tags other than 'atr' (and perhaps 'chty')
			if newEnc and self._hasDisallowedENCAttributes(newEnc):
				raise BAD_REQUEST(L.logDebug(f'disallowed "enc" attribute(s) in blocking-subscription'))

			# TODO Where is it specified that the nu must target the parent's originator? -> Remove if not necessary
			# parentOriginator = parentResource.getOriginator()
			# if net[0] != NotificationEventType.blockingUpdate:
			# 	if not compareIDs(self.nu[0], parentOriginator):
			# 		return Result.errorResult(dbg = L.logDebug(f'nu must target the parent resource\'s originator for blocking notifications'))
		

		# Validate missingData
		if newNet and NotificationEventType.reportOnGeneratedMissingDataPoints in newNet:
			# missing data must be created only under a <TS> resource
			if parentResource is not None and parentResource.ty != ResourceTypes.TS:
				raise BAD_REQUEST(L.logDebug(f'parent resource must be a TimeSeries resource when "enc/md" is provided'))

			if (md := self['enc/md']) is not None:
				if len(md.keys() & {'dur', 'num'}) != 2:
					raise BAD_REQUEST(L.logDebug(f'"dur" and/or "num" missing in "enc/md" attribute'))
			else:
				raise BAD_REQUEST(L.logDebug(f'"enc/md" is missing in subscription for "reportOnGeneratedMissingDataPoints"'))
			
		# check nct and net combinations
		if (nct := self.nct) is not None and newNet is not None:
			for n in newNet:
				if not NotificationEventType(n).isAllowedNCT(NotificationContentType(nct)):
					raise BAD_REQUEST(L.logDebug(f'nct={nct} is not allowed for one or more values in enc/net={newNet}'))
				# fallthrough
				if n == NotificationEventType.reportOnGeneratedMissingDataPoints:
					# TODO is this necessary, parent resource should be provided
					# Check that parent is a TimeSeries
					if not (parent := self.retrieveParentResource()):
						raise INTERNAL_SERVER_ERROR(L.logErr(f'cannot retrieve parent resource'))
					if parent.ty != ResourceTypes.TS:
						raise BAD_REQUEST(L.logDebug(f'parent must be a <TS> resource for net==reportOnGeneratedMissingDataPoints'))

					# Check missing data structure
					if (md := self['enc/md']) is None:	# enc/md is a boolean
						raise BAD_REQUEST(L.logDebug(f'net==reportOnGeneratedMissingDataPoints is set, but enc/md is missing'))
					CSE.validator.validateAttribute('num', md.get('num'))
					CSE.validator.validateAttribute('dur', md.get('dur'))
		
		# if nct is not provided, check that net contains only event types that have the same default nct
		if nct is None and newNet is not None:
			if len(set([ NotificationEventType(t).defaultNCT() for t in newNet ])) > 1:
				raise BAD_REQUEST(L.logDebug(f'nct is not provided, and enc/net contains multiple NotificationEventTypes with different default NotificationContentType'))

		# check other attributes
		self._normalizeURIAttribute('nfu')
		self._normalizeURIAttribute('nu')
		self._normalizeURIAttribute('su')


	def childWillBeAdded(self, childResource: Resource, originator: str) -> None:
		super().childWillBeAdded(childResource, originator)
		if childResource.ty == ResourceTypes.SCH:
			if (rn := childResource._originalDict.get('rn')) is None:
				childResource.setResourceName('notificationSchedule')
			elif rn != 'notificationSchedule':
				raise BAD_REQUEST(L.logDebug(f'rn of <schedule> under <subscription> must be "notificationSchedule"'))


	def _checkAllowedCHTY(self, parentResource:Resource, chty:list[ResourceTypes]) -> None:
		""" Check whether an observed child resource types are actually allowed by the parent. 
		
			Args:
				parentResource: The resource to check.
				chty: A list of resource types to check.
			
			Raises:
				`BAD_REQUEST`: In case the observed child resource type is not allowed.
		"""
		for ty in chty:
			if ty not in parentResource._allowedChildResourceTypes:
				raise BAD_REQUEST(L.logDebug(f'ChildResourceType {ResourceTypes(ty).name} is not an allowed child resource of {ResourceTypes(parentResource.ty).name}'))


	def _hasBlockingNET(self, net:list[NotificationEventType]) -> bool:
		"""	Check whether a list of Notification Event Types contains at least one of the
			blocking notification event types.

			Args:
				net: List of Notification Event Types.
			
			Return:
				True, if the list contains at least one of the blocking NotificationEventType.
		"""
		return any([ n 
					 for n in [NotificationEventType.blockingUpdate, 
					 		   NotificationEventType.blockingRetrieve, 
							   NotificationEventType.blockingRetrieveDirectChild]
					 if n in net ])
	
	
	def _hasDisallowedBlockingAttributes(self, dct:JSON) -> bool:
		"""	Check whether a dictionary contains "disallowed" attributes. 
			"Disallowed" attributes are any of the resource specific attributes that
			are not allowed for the blocking Notification Event Types.
			
			Args:
				dct: Either a resource dict or an update dict.
			
			Return:
				True if the *dct* has any disallowed attributes.
		"""
		return any([ n
					 for n in self._disallowedBlockingAttributes
					 if n in dct
				])
	

	def _hasDisallowedENCAttributes(self, dct:JSON) -> bool:
		"""	Check whether a dictionary contains "disallowed" Event Notification Criteria
			attributes.This is used mainly to validate the blocking-* Notification
			Event Types.

			Args:
				dct: A Event Notification Criteria structure.
			
			Return:
				True if the *dct* has any disallowed attributes.
	
			"""
		return len(set(dct.keys()).difference(self._allowedENCAttributes)) > 0
	
