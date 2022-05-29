#
#	SUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Subscription
#

from __future__ import annotations
from copy import deepcopy
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, NotificationContentType, NotificationEventType as NET, ResponseStatusCode as RC, JSON
from ..services.Configuration import Configuration
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *


class SUB(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

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
		'ma': None,		# EXPERIMENTAL maxage
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.SUB, dct, pi, create = create)

		self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate.value ], overwrite = False)

		# Apply the nct only on the first element of net. Do the combination checks later in validate()
		net = self['enc/net']
		if len(net) > 0:
			if net[0] in [ NET.resourceUpdate, NET.resourceDelete, NET.createDirectChild, NET.deleteDirectChild, NET.retrieveCNTNoChild ]:
				self.setAttribute('nct', NotificationContentType.all, overwrite = False)
			elif net[0] in [ NET.triggerReceivedForAE ]:
				self.setAttribute('nct', NotificationContentType.triggerPayload, overwrite = False)
			elif net[0] in [ NET.blockingUpdate ]:
				self.setAttribute('nct', NotificationContentType.modifiedAttributes, overwrite = False)
			elif net[0] in [ NET.reportOnGeneratedMissingDataPoints ]:
				self.setAttribute('nct', NotificationContentType.timeSeriesNotification, overwrite = False)

		if self.bn:		# set batchNotify default attributes
			self.setAttribute('bn/dur', Configuration.get('cse.sub.dur'), overwrite = False)



# TODO notificationForwardingURI

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (result := super().activate(parentResource, originator)).status:
			return result

		# check whether an observed child resource type is actually allowed by the parent
		if chty := self['enc/chty']:
			if  not (res := self._checkAllowedCHTY(parentResource, chty)).status:
				return res

		return CSE.notification.addSubscription(self, originator)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)
		CSE.notification.removeSubscription(self)


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		previousNus = deepcopy(self.nu)
		if not (res := super().update(dct, originator)).status:
			return res

		# check whether an observed child resource type is actually allowed by the parent
		if chty := self['enc/chty']:
			if not (parentResource := self.retrieveParentResource()):
				L.logErr(dbg := f'cannot retrieve parent resource')
				return Result(status = False, rsc = RC.internalServerError, dbg = dbg)
			if  not (res := self._checkAllowedCHTY(parentResource, chty)).status:
				return res

		return CSE.notification.updateSubscription(self, previousNus, originator)

 
	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		L.isDebug and L.logDebug(f'Validating subscription: {self.ri}')

		# Check necessary attributes
		if not (nu := self.nu) or not isinstance(nu, list):
			return Result.errorResult(dbg = L.logDebug(f'"nu" attribute missing for subscription: {self.ri}'))
		
		# Check NotificationEventType
		if (net := self['enc/net']) is not None:
			if not NotificationEventType.has(net):
				return Result.errorResult(dbg = L.logDebug(f'enc/net={str(net)} is not an allowed or supported NotificationEventType'))

			# Check if blocking RETRIEVE or UPDATE is the only NET in the subscription, AND that there is no other NET for this resource
			if NotificationEventType.blockingUpdate in net or NotificationEventType.blockingRetrieve in net or NotificationEventType.blockingRetrieveDirectChild in net:
				if len(net) > 1:
					return Result.errorResult(dbg = L.logDebug(f'blockingRetrieve/blockingUpdate must be the only value in enc/net'))
				if CSE.notification.getSubscriptionsByNetChty(parentResource.ri, net = net):
					return Result.errorResult(dbg = L.logDebug(f'a subscription with blockingRetrieve/blockingUpdate already exsists for this resource'))
				
				if net[0] == NotificationEventType.blockingRetrieve:
					if CSE.notification.getSubscriptionsByNetChty(parentResource.ri, net = [ NotificationEventType.blockingRetrieve ]):
						return Result.errorResult(dbg = L.logDebug(f'a subscription with blockingRetrieve already exsists for this resource'))
				
				# TODO: check that only one NotificationEventType.blockingRetrieveDirectChild per chty. Or, if one without chty exists
				elif net[0] == NotificationEventType.blockingRetrieveDirectChild:
					...

				elif net[0] == NotificationEventType.blockingUpdate:
					if CSE.notification.getSubscriptionsByNetChty(parentResource.ri, net = [ NotificationEventType.blockingUpdate ]):
						return Result.errorResult(dbg = L.logDebug(f'a subscription with blockingUpdate already exsists for this resource'))

				if len(nu) > 1:
					return Result.errorResult(dbg = L.logDebug(f'nu must contain only one target for blockingRetrieve/blockingUpdate'))
				parentOriginator = parentResource.getOriginator()
				if net[0] != NotificationEventType.blockingUpdate:
					if not Utils.compareIDs(nu[0], parentOriginator):
						return Result.errorResult(dbg = L.logDebug(f'nu must target the parent resource\'s originator'))
				
		# Validate missingData
		L.logDebug(self['enc/md'])
		if (md := self['enc/md']) is not None:
			if len(md.keys() & {'dur', 'num'}) != 2:
				return Result.errorResult(dbg = L.logDebug(f'"dur" and/or "num" missing in "enc/md" attribute'))
			if parentResource is not None and parentResource.ty != T.TS:
				return Result.errorResult(dbg = L.logDebug(f'parent resource must be a TimeSeries resource when "enc/md" is provided'))

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
						return Result.errorResult(rsc = RC.internalServerError, dbg = L.logErr(f'cannot retrieve parent resource'))
					if parent.ty != T.TS:
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


		# TODO: Validate enc/missing/data
		# TODO: check missingData only if parent if TS. Add test for that

		
		# check other attributes
		self._normalizeURIAttribute('nfu')
		self._normalizeURIAttribute('nu')
		self._normalizeURIAttribute('su')

		return Result.successResult()

	def _checkAllowedCHTY(self, parentResource:Resource, chty:list[T]) -> Result:
		""" Check whether an observed child resource type is actually allowed by the parent. """
		for ty in chty:
			if ty not in parentResource._allowedChildResourceTypes:
				L.logDebug(dbg := f'ChildResourceType {T(ty).name} is not an allowed child resource of {T(parentResource.ty).name}')
				return Result.errorResult(dbg = dbg)
		return Result.successResult()

