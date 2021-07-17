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
from Configuration import Configuration
from Types import ResourceTypes as T, Result, NotificationContentType, NotificationEventType as NET
import CSE
from Validator import constructPolicy
from .Resource import *
from Types import ResponseCode as RC, JSON
from Logging import Logging as L

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'cr', 'hld', 'acpi', 'daci', 'enc',
	'exc', 'nu', 'gpi', 'nfu', 'bn', 'rl', 'psn', 'pn', 'nsp', 'ln', 'nct', 'nec',
	'su', 'acrs'		#	primitiveProfileID missing in TS-0004
])

# LIMIT: Only http(s) requests in nu or POA is supported yet

class SUB(Resource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes:list[T] = [ ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.SUB, dct, pi, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate ], overwrite=False)

			# Apply the nct only on the first element of net. Do the combination checks later in validate()
			net = self['enc/net']
			if len(net) > 0:
				if net[0] in [ NET.resourceUpdate, NET.resourceDelete, NET.createDirectChild, NET.deleteDirectChild, NET.retrieveCNTNoChild ]:
					self.setAttribute('nct', NotificationContentType.all, overwrite=False)
				elif net[0] in [ NET.triggerReceivedForAE ]:
					self.setAttribute('nct', NotificationContentType.triggerPayload, overwrite=False)
				elif net[0] in [ NET.blockingUpdate ]:
					self.setAttribute('nct', NotificationContentType.modifiedAttributes, overwrite=False)
				elif net[0] in [ NET.reportOnGeneratedMissingDataPoints ]:
					self.setAttribute('nct', NotificationContentType.timeSeriesNotification, overwrite=False)

			if self.bn is not None:		# set batchNotify default attributes
				self.setAttribute('bn/dur', Configuration.get('cse.sub.dur'), overwrite=False)



# TODO expirationCounter
# TODO notificationForwardingURI

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (result := super().activate(parentResource, originator)).status:
			return result

		# check whether an observed child resource type is actually allowed by the parent
		if (chty := self['enc/chty']) is not None:
			if  not (res := self._checkAllowedCHTY(parentResource, chty)).status:
				return res

		return CSE.notification.addSubscription(self, originator)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)
		CSE.notification.removeSubscription(self)


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		previousNus = deepcopy(self.nu)
		newDict = deepcopy(dct)
		if not (res := super().update(dct, originator)).status:
			return res

		# check whether an observed child resource type is actually allowed by the parent
		if (chty := self['enc/chty']) is not None:
			if (parentResource := self.retrieveParentResource()) is None:
				L.logErr(dbg := f'cannot retrieve parent resource')
				return Result(status=False, rsc=RC.internalServerError, dbg=dbg)
			if  not (res := self._checkAllowedCHTY(parentResource, chty)).status:
				return res

		return CSE.notification.updateSubscription(self, newDict, previousNus, originator)

 
	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		L.isDebug and L.logDebug(f'Validating subscription: {self.ri}')

		# Check necessary attributes
		if (nu := self.nu) is None or not isinstance(nu, list):
			L.isDebug and L.logDebug(dbg := f'"nu" attribute missing for subscription: {self.ri}')
			return Result(status=False, rsc=RC.insufficientArguments, dbg=dbg)

		# check nct and net combinations
		if (nct := self.nct) is not None and (net := self['enc/net']) is not None:
			for n in net:
				if not NotificationEventType(n).isAllowedNCT(NotificationContentType(nct)):
					L.isDebug and L.logDebug(dbg := f'nct={nct} is not allowed for one or more values in enc/net={net}')
					return Result(status=False, rsc=RC.badRequest, dbg=dbg)
				# fallthough
			if n == NotificationEventType.reportOnGeneratedMissingDataPoints:
				# Check that parent is a TimeSeries
				if (parent := self.retrieveParentResource()) is None:
					L.logErr(dbg := f'cannot retrieve parent resource')
					return Result(status=False, rsc=RC.internalServerError, dbg=dbg)
				if parent.ty != T.TS:
					L.isDebug and L.logDebug(dbg := f'parent must be a <TS> resource for net==reportOnGeneratedMissingDataPoints')
					return Result(status=False, rsc=RC.badRequest, dbg=dbg)

				# Check missing data structure
				if (md := self['enc/md']) is None:
					L.isDebug and L.logDebug(dbg := f'net==reportOnGeneratedMissingDataPoints is set, but enc/md is missing')
					return Result(status=False, rsc=RC.badRequest, dbg=dbg)
				if not (res := CSE.validator.validateAttribute('num', md.get('num'))).status:
					L.isDebug and L.logDebug(res.dbg)
					return Result(status=False, rsc=RC.badRequest, dbg=res.dbg)
				if not (res := CSE.validator.validateAttribute('dur', md.get('dur'))).status:
					L.isDebug and L.logDebug(res.dbg)
					return Result(status=False, rsc=RC.badRequest, dbg=res.dbg)


		# TODO: Validate enc/missing/data
		# TODO: check missingData only if parent if TS. Add test for that

		
		# check other attributes
		self.normalizeURIAttribute('nfu')
		self.normalizeURIAttribute('nu')
		self.normalizeURIAttribute('su')

		return Result(status=True)

	def _checkAllowedCHTY(self, parentResource:Resource, chty:list[T]) -> Result:
		""" Check whether an observed child resource type is actually allowed by the parent. """
		for ty in self['enc/chty']:
			if ty not in parentResource.allowedChildResourceTypes:
				L.logDebug(dbg := f'ChildResourceType {T(ty).name} is not an allowed child resource of {T(parentResource.ty).name}')
				return Result(status=False, rsc=RC.badRequest, dbg=dbg)
		return Result(status=True)

