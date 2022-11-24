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
from ..etc import Utils
from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, NotificationContentType
from ..etc.Types import NotificationEventType, ResponseStatusCode, JSON
from ..services.Configuration import Configuration
from ..services import CSE
from ..services.Logging import Logging as L
from ..resources.Resource import Resource


# TODO notificationForwardingURI
# TODO work on more NEC attributes


class SUB(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

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

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.SUB, dct, pi, create = create)

		# Set defaults for some attribute
		self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate.value ], overwrite = False)
		

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (result := super().activate(parentResource, originator)).status:
			return result

		# set batchNotify default attributes
		if self.bn:		
			self.setAttribute('bn/dur', Configuration.get('cse.sub.dur'), overwrite = False)

		# Apply the nct only on the first element of net. Do the combination checks later in validate()
		net = self['enc/net']
		if len(net) > 0:
			if net[0] in [ NotificationEventType.resourceUpdate, NotificationEventType.resourceDelete, 
						   NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild, 
						   NotificationEventType.retrieveCNTNoChild ]:
				self.setAttribute('nct', NotificationContentType.all, overwrite = False)
			elif net[0] in [ NotificationEventType.triggerReceivedForAE ]:
				self.setAttribute('nct', NotificationContentType.triggerPayload, overwrite = False)
			elif net[0] in [ NotificationEventType.blockingUpdate ]:
				self.setAttribute('nct', NotificationContentType.modifiedAttributes, overwrite = False)
			elif net[0] in [ NotificationEventType.reportOnGeneratedMissingDataPoints ]:
				self.setAttribute('nct', NotificationContentType.timeSeriesNotification, overwrite = False)
	
		# check whether an observed child resource type is actually allowed by the parent
		if chty := self['enc/chty']:
			if  not (res := self._checkAllowedCHTY(parentResource, chty)).status:
				return res
		
		# nsi is at least an empty list if nse is present, otherwise it must not be present
		if self.nse is not None:
			self.setAttribute('nsi', [], overwrite = False)
			CSE.notification.validateAndConstructNotificationStatsInfo(self)

		return CSE.notification.addSubscription(self, originator)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)
		CSE.notification.removeSubscription(self, originator)


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		previousNus = deepcopy(self.nu)

		# We are validating the attributes here already because this actual update of the resource
		# (where this happens) is done only after a lot of other stuff hapened.
		# So, the resource is validated twice in an update :()
		if not (res := CSE.validator.validateAttributes(dct, 
														self.tpe, 
														self.ty, 
														self._attributes, 
														create = False, 
														createdInternally = self.isCreatedInternally(),
														isAnnounced = self.isAnnounced())).status:
			return res


		# Handle update notificationStatsEnable attribute, but only if present in the resource.
		# This is important bc it can be set to True, False, or Null.
		pure = Utils.pureResource(dct)[0]
		if 'nse' in pure:
			CSE.notification.updateOfNSEAttribute(self, Utils.findXPath(dct, 'm2m:sub/nse'))

		# Reject updates with blocking *
		if (net := Utils.findXPath(pure, 'enc/net')) and self._hasBlockingNET(net):
			return Result.errorResult(dbg = L.logDebug('Updates with any blocking Notification Event Type if not allowed.'))

		# Handle changes to acrs (send deletion notifications)
		if (newAcrs := Utils.findXPath(dct, 'm2m:sub/acrs')) is not None and self.acrs is not None:
			for crsRI in set(self.acrs) - set(newAcrs):
				L.isDebug and L.logDebug(f'Update of acrs: {crsRI} removed. Sending deletion notification')
				CSE.notification.sendDeletionNotification(crsRI, self.ri)	# TODO ignore result?

		# Do actual update
		if not (res := super().update(dct, originator, doValidateAttributes = False)).status:
			return res
		
		# Check whether 'enc' is removed in the update
		if 'enc' in dct['m2m:sub'] and dct['m2m:sub']['enc'] is None:
			self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate.value ])


		# check whether an observed child resource type is actually allowed by the parent
		if chty := self['enc/chty']:
			if not (parentResource := self.retrieveParentResource()):
				return Result(status = False, rsc = ResponseStatusCode.internalServerError, dbg = L.logErr(f'cannot retrieve parent resource'))
			if  not (res := self._checkAllowedCHTY(parentResource, chty)).status:
				return res

		return CSE.notification.updateSubscription(self, previousNus, originator)

 
	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res

		L.isDebug and L.logDebug(f'Validating subscription: {self.ri}')
		attrs = self.dict if create else Utils.pureResource(dct)[0]
		enc = attrs.get('enc')

		# Check NotificationEventType
		if (net := Utils.findXPath(attrs, 'enc/net')) is not None:
			if not NotificationEventType.has(net):
				return Result.errorResult(dbg = L.logDebug(f'enc/net={str(net)} is not an allowed or supported NotificationEventType'))

		# Check if blocking RETRIEVE or blocking UPDATE is the only NET in the subscription, 
		# AND that there is no other NET for this resource
		if net and self._hasBlockingNET(net):

			# only one entry in NET must exist per blocking subscription
			if len(net) > 1:
				return Result.errorResult(dbg = L.logDebug(f'blockingRetrieve/blockingUpdate must be the only value in enc/net'))

			# Only one of each blocking UPDATE or RETRIEVE etc must exist for this resource
			# This works here in validate bc it is only allowed in CREATE/activate, and this resource has 
			# not been written to DB yet.
			if CSE.notification.getSubscriptionsByNetChty(parentResource.ri, net = net):
				return Result.errorResult(dbg = L.logDebug(f'A subscription with blockingRetrieve/blockingUpdate/blockingRetrieveDirectChild already exsists for this resource'))

			# Only one NU is allowed for blocking UPDATE or RETRIEVE
			if len(self.nu) > 1:
				return Result.errorResult(dbg = L.logDebug(f'nu must contain only one target for blockingRetrieve/blockingUpdate'))

			# Disallow other subscription-specific attributes if this is a blocking-* subscription
			if self._hasDisallowedBlockingAttributes(attrs):
				return Result.errorResult(dbg = L.logDebug(f'Disallowed attribute(s) in blocking-subscription'))

			# Disallow condition tags other than 'atr' (and perhaps 'chty')
			if enc and self._hasDisallowedENCAttributes(enc):
				return Result.errorResult(dbg = L.logDebug(f'Disallowed "enc" attribute(s) in blocking-subscription'))

			# TODO Where is it specified that the nu must target the parent's originator? -> Remove if not necessary
			# parentOriginator = parentResource.getOriginator()
			# if net[0] != NotificationEventType.blockingUpdate:
			# 	if not Utils.compareIDs(self.nu[0], parentOriginator):
			# 		return Result.errorResult(dbg = L.logDebug(f'nu must target the parent resource\'s originator for blocking notifications'))
		

		# Validate missingData
		if net and NotificationEventType.reportOnGeneratedMissingDataPoints in net:
			# missing data must be created only under a <TS> resource
			if parentResource is not None and parentResource.ty != ResourceTypes.TS:
				return Result.errorResult(dbg = L.logDebug(f'parent resource must be a TimeSeries resource when "enc/md" is provided'))

			if (md := self['enc/md']) is not None:
				if len(md.keys() & {'dur', 'num'}) != 2:
					return Result.errorResult(dbg = L.logDebug(f'"dur" and/or "num" missing in "enc/md" attribute'))
			else:
				return Result.errorResult(dbg = L.logDebug(f'"enc/md" is missing in subscription for "reportOnGeneratedMissingDataPoints"'))
			
		# check nct and net combinations
		if (nct := self.nct) is not None and net is not None:
			for n in net:
				if not NotificationEventType(n).isAllowedNCT(NotificationContentType(nct)):
					return Result.errorResult(dbg = L.logDebug(f'nct={nct} is not allowed for one or more values in enc/net={net}'))
				# fallthrough
				if n == NotificationEventType.reportOnGeneratedMissingDataPoints:
					# TODO is this necessary, parent resource should be provided
					# Check that parent is a TimeSeries
					if not (parent := self.retrieveParentResource()):
						return Result.errorResult(rsc = ResponseStatusCode.internalServerError, dbg = L.logErr(f'cannot retrieve parent resource'))
					if parent.ty != ResourceTypes.TS:
						return Result.errorResult(dbg = L.logDebug(f'parent must be a <TS> resource for net==reportOnGeneratedMissingDataPoints'))

					# Check missing data structure
					if (md := self['enc/md']) is None:	# enc/md is a boolean
						return Result.errorResult(dbg = L.logDebug(f'net==reportOnGeneratedMissingDataPoints is set, but enc/md is missing'))
					if not (res := CSE.validator.validateAttribute('num', md.get('num'))).status:
						L.isDebug and L.logDebug(res.dbg)
						return Result.errorResult(dbg = res.dbg)
					if not (res := CSE.validator.validateAttribute('dur', md.get('dur'))).status:
						L.isDebug and L.logDebug(res.dbg)
						return Result.errorResult(dbg = res.dbg)

		# check other attributes
		self._normalizeURIAttribute('nfu')
		self._normalizeURIAttribute('nu')
		self._normalizeURIAttribute('su')

		return Result.successResult()


	def _checkAllowedCHTY(self, parentResource:Resource, chty:list[ResourceTypes]) -> Result:
		""" Check whether an observed child resource types are actually allowed by the parent. 
		
			Args:
				parentResource: The resource to check.
				chty: A list of resource types to check.
			
			Return:
				Result object. Success result if the resource types are allowed.
		"""
		for ty in chty:
			if ty not in parentResource._allowedChildResourceTypes:		
				return Result.errorResult(dbg = L.logDebug(f'ChildResourceType {ResourceTypes(ty).name} is not an allowed child resource of {ResourceTypes(parentResource.ty).name}'))
		return Result.successResult()


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