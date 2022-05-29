#
#	CRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CrossResourceSubscription
#

from __future__ import annotations
from ast import Subscript

from ..etc.Utils import toSPRelative, csiFromSPRelative, findXPath, setXPath
from ..etc.Types import AttributePolicyDict, Operation, ResourceTypes as T, Result, JSON
from ..resources.Resource import *
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L



class CRS(Resource):

	_subRratRIs = '__subRratRIs__'	# dict rrat-ri -> sub-ri
	_subSratRIs = '__subSratRIs__'	# dict srat-ri -> sub-ri

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
		'acpi': None,
		'lbl': None,
		'cr': None,
		'cstn': None,
		'daci': None,

		# Resource attributes
		'exc': None,
		'nu': None,
		'nec': None,
		'su': None,
		'rrat': None,
		'srat': None,
		'twt': None,
		'tws': None,
		'encs': None, 

	}

	# TODO notificationStatsEnable - nse  support
	# TODO notificationStatsInfo - nsi	support


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.CRS, dct, pi, create = create)


		# add internal attribute to store the references to the created <sub> resources
		# Add to internal attributes to ignore in validation etc
		self.internalAttributes.append(self._subRratRIs)
		self.internalAttributes.append(self._subSratRIs)
		self.setAttribute(self._subRratRIs, {}, overwrite = False)	
		self.setAttribute(self._subSratRIs, {}, overwrite = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if (res := super().activate(parentResource, originator)).status == False:
			return res
		
		# Handle regularResourcesAsTarget
		if self.rrat:
			for rrat in self.rrat:
				if not (res := self._addRratSubscription(rrat, self.encs, originator)).status:
					self._deleteSubscriptions(originator)
					return res
		
		# Handle subscriptionResourcesAsTarget
		if self.srat:
			for srat in self.srat:
				if not (res := self._addSratSubscription(srat, originator)).status:
					self._deleteSubscriptions(originator)
					return res



		# TODO ...
		# d)Once the <crossResourceSubscription> resource is created, the Hosting CSE shall start the time window if the 
		# 	timeWindowType=PERIODICWINDOW; if timeWindowType=SLIDINGWINDOW, the Hosting CSE shall start the time window after the 
		# 	first notification is received from a Target Resource Hosting CSE.


		self.dbUpdate()
		return Result.successResult()
	

	def update(self, dct:JSON = None, originator:str = None) -> Result:

		# Structures for rollback
		_createdRrat:list[str] = []
		_deletedRrat:list[str] = []

		# Update for regularResourcesAsTarget
		if newRrat := findXPath(dct, 'm2m:crs/rrat'):
			oldRrat = self.rrat
			_dctEncs = findXPath(dct, 'm2m:crs/encs')
			encs = _dctEncs if _dctEncs else self.encs
	
			# Add subscriptions for added rrats
			for rrat in newRrat:
				if rrat not in oldRrat:
					if not (res := self._addRratSubscription(rrat, encs, originator)).status:
						self._rollbackRrats(_createdRrat, _deletedRrat, originator)
						return res
					_createdRrat.append(rrat)
				
			# Delete subscriptions for removed rrats
			for rrat in oldRrat:
				if rrat not in newRrat:
					if not (res := self._deleteSubscriptionForRrat(rrat, originator)).status:
						self._rollbackRrats(_createdRrat, _deletedRrat, originator)
						return res
				_deletedRrat.append(rrat)
		
		# TODO ...

		# b) If subscriptionResourcesAsTarget is updated, the Hosting CSE shall perform the following tasks:
		#	iii) If a <subscription> resource has been removed in the new subscriptionResourcesAsTarget attribute value 
		# 		the Hosting CSE shall update the <subscription> resource using the procedure in clause 7.4.8.2.4 to
		# 		remove this <crossResourceSubscription> from the <subscription> resource's associatedCrossResourceSub attribute.
		#	iv) If the updated subscriptionResourcesAsTarget attribute value contains new a <subscription>resource, the Hosting
		# 		CSE shall add the resource identifier of this <crossResourceSubscription> resource to the associatedCrossResourceSub 
		# 		attribute of each <subscription> resource indicated in subscriptionResourcesAsTarget as described in clause 7.4.58.2.1.


		# c)If eventNotificationCriteriaSet is updated, the Hosting CSE shall update the eventNotificationCriteria of each previously 
		# 	created <subscription> child resource of the targets listed in the regularResourcesAsTarget attribute to reflect the received
		# 	eventNotificationCriteria content using the procedures in clause 7.4.8.2.3.
		# 
		# d)If timeWindowSize or timeWindowType is updated in the resource representation the receiver shall restart the timer as
		# 	 described in clause 7.4.58.2.1.
		# 
		# e)If any of the above Update procedures are unsuccessful the receiver shall send an unsuccessful response with a
		# 	 "CROSS_RESOURCE_OPERATION_FAILURE" Response Status Code to the Originator; the receiver shall also restore all resources to
		#  the states they were in prior to this request.

		
		return super().update(dct, originator)


	

	def deactivate(self, originator:str) -> None:

		# Delete rrat and srat subscriptions
		self._deleteSubscriptions(originator)

		# TODO deactivate timer
		

		return super().deactivate(originator)


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		L.isDebug and L.logDebug(f'Validating crossResourceSubscription: {self.ri}')

		# Check that at least rrat or srat is present
		if self.rrat is None and self.srat is None:
			return Result.errorResult(dbg = L.logDebug(f'At least one of regularResourcesAsTarget or subscriptionResourcesAsTarget attributes shall be present'))

		# Check when rrat is set that enc is correctly set and filled
		if self.rrat:
			if not self.encs:
				return Result.errorResult(dbg = L.logDebug(f'eventNotificationCriteriaSet must not be empty when regularResourcesAsTarget is provided'))
			if (_l := len(self
			.encs)) != 1 and _l != len(self.rrat):
				return Result.errorResult(dbg = L.logDebug(f'Number of entries in eventNotificationCriteriaSet must be 1 or the same number as regularResourcesAsTarget entries'))

		return Result.successResult()
	

	def handleNotification(self, request:CSERequest, originator:str) -> Result:
		"""	Handle a notification request to a CRS resource.

			Args:
				request: The notification request structure
				originator: Originator of the request
			Return:
				Result object
		"""
		L.isDebug and L.logDebug('Handling notification to CRS resource')

		# Verification request
		if (_vrq := findXPath(request.pc, 'm2m:sgn/vrq')) is not None and _vrq == True:
			L.isDebug and L.logDebug('Received subscription verification request to CRS resource')
			return Result(status = True, rsc = RC.OK)
		
		# Deletion request
		if (_sud := findXPath(request.pc, 'm2m:sgn/sud')) is not None and _sud == True:
			L.isDebug and L.logDebug('Received subscription deletion request to CRS resource')
			return Result(status = True, rsc = RC.OK)
		
		return Result.errorResult( dbg = 'unknown notification')


	def _addRratSubscription(self, rrat:str, encs:list[dict], originator:str) -> Result:
		"""	Add a single subscription for a rrat.
			
			Args:
				rrat: The target resource's uri.
				encs: eventNotificationCriteriaSet to add to the new <sub>.
				originator: The originator of the request.
			Return:
				Result object.
		"""
		dct = { 'm2m:sub' : {
					'nu' : [ (_spri := toSPRelative(self.ri)) ],
					'acrs': [ _spri ],
				}}
		if len(self.encs) == 1:
			setXPath(dct, 'm2m:sub/enc', findXPath(encs[0], 'enc'))
		else:
			setXPath(dct, 'm2m:sub/enc', findXPath(encs[self.rrat.index(rrat)], 'enc'))	# position of rrat in the list of rrats
		if self.nec:
			setXPath(dct, 'm2m:sub/nec', self.nec)
		# create (possibly remote) subscription
		L.logDebug(f'Adding <sub> to {rrat}')
		res = CSE.request.sendCreateRequest((_rratSpRelative := toSPRelative(rrat)), 
											originator = originator,
											ty = T.SUB,
											data = dct,
											appendID = _rratSpRelative)
		
		# Error? Then rollback: delete all created subscriptions so far and return with an error
		if not res.status or res.rsc != RC.created:
			return Result.errorResult(rsc = RC.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot create subscription for {rrat} uri: {_rratSpRelative}'))

		# Add <sub> to internal references
		_subRIs = self.attribute(self._subRratRIs)
		_subRIs[rrat] = f'{csiFromSPRelative(_rratSpRelative)}/{findXPath(res.request.pc, "m2m:sub/ri")}'
		self.setAttribute(self._subRratRIs, _subRIs)

		return Result.successResult()


	def _addSratSubscription(self, srat:str, originator:str) -> Result:
		"""	Update another subscription, pointed to by a srat entry, to
			notify this <crs> resource.
			
			Args:
				srat: The target <sub>'s uri.
				originator: The originator of the request.
			Return:
				Result object.
		"""

		# Get subscription
		L.logDebug(f'Retrieving srat <sub>: {srat}')
		res = CSE.request.sendRetrieveRequest((_sratSpRelative := toSPRelative(srat)), 
												originator = originator,
												appendID = _sratSpRelative)
		if not res.status or res.rsc != RC.OK:
			self._deleteSubscriptions(originator)
			return Result.errorResult(rsc = RC.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot retrieve subscription for {srat} uri: {_sratSpRelative}'))

		# Check whether the target is a subscription
		subDct:JSON = cast(JSON, res.data)
		if findXPath(subDct, 'm2m:sub') is None:
			self._deleteSubscriptions(originator)
			return Result.errorResult(dbg = L.logWarn(f'Resource is not a subscription for {srat} uri: {_sratSpRelative}'))

		newDct:JSON = { 'm2m:sub': {} }	# new request dct

		# Add to the sub's nu
		if (nu := findXPath(subDct, 'm2m:sub/nu')) is None:
			nu = [ ]
		if (spRi := toSPRelative(self.ri)) not in nu:
			nu.append(spRi)
		setXPath(newDct, 'm2m:sub/nu', nu)

		# Add to the sub's associatedCrossResourceSub
		if (acrs := findXPath(subDct, 'm2m:sub/acrs')) is None:
			acrs = [ ]
		if spRi not in acrs:
			acrs.append(spRi)
		setXPath(newDct, 'm2m:sub/acrs', acrs)

		# Send UPDATE request
		L.logDebug(f'Updating srat <sub>: {srat}')
		res = CSE.request.sendUpdateRequest(_sratSpRelative, 
											originator = originator,
											data = newDct,
											appendID = _sratSpRelative)
		if not res.status or res.rsc != RC.updated:
			self._deleteSubscriptions(originator)
			return Result.errorResult(rsc = RC.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot update subscription for {srat} uri: {_sratSpRelative}'))

		# Add <sub> to internal references
		_subRIs = self.attribute(self._subSratRIs)
		_subRIs[srat] = f'{csiFromSPRelative(_sratSpRelative)}/{srat}'
		self.setAttribute(self._subSratRIs, _subRIs)

		return Result.successResult()


	def _deleteSubscriptions(self, originator:str) -> Result:
		"""	Delete the created subscriptions.

			Args:
				originator: The originator to use for the DELETE requests.
		"""
		# rrat
		if _subRratRIs := self.attribute(self._subRratRIs):
			for rrat in list(_subRratRIs.keys()):
				if not (res := self._deleteSubscriptionForRrat(rrat, originator)).status:
					return res
		
		#srat
		if _subSratRIs := self.attribute(self._subSratRIs):
			for srat in list(_subSratRIs.keys()):
				if not (res := self._deleteFromSubscriptionsForSrat(srat, originator)).status:
					return res
		return Result.successResult()


	def _deleteSubscriptionForRrat(self, rrat:str, originator:str) -> Result:
		_subRIs = self.attribute(self._subRratRIs)
		if (subRI := _subRIs.get(rrat)) is not None:
			L.isDebug and L.logDebug(f'Deleting <sub>: {subRI} from rrat: {rrat}')
			if not (res := CSE.request.sendDeleteRequest(subRI, originator = originator)).status:
				return res
			del _subRIs[rrat]
			self.setAttribute(self._subRratRIs, _subRIs)
		return Result.successResult()


	def _deleteFromSubscriptionsForSrat(self, srat:str, originator:str) -> Result:
		_subRIs = self.attribute(self._subSratRIs)
		if (subRI := _subRIs.get(srat)) is not None:
			res = CSE.request.sendRetrieveRequest(subRI, 
												  originator = originator,
												  appendID = subRI)
			if not res.status or res.rsc != RC.OK:
				return Result.errorResult(rsc = RC.badRequest, dbg = L.logWarn(f'Cannot create subscription for {srat} uri: {subRI}'))
			
			subDct:JSON = cast(JSON, res.data)
			newDct:JSON = { 'm2m:sub': {} }	# new request dct

			# remove from to the sub's nu
			if (nu := findXPath(subDct, 'm2m:sub/nu')) is not None:
				if (spRi := toSPRelative(self.ri)) in nu:
					nu.remove(spRi)
				setXPath(newDct, 'm2m:sub/nu', nu)

			# Add to the sub's associatedCrossResourceSub
			if (acrs := findXPath(subDct, 'm2m:sub/acrs')) is not None:
				if spRi in acrs:
					acrs.remove(spRi)
					if len(acrs) == 0:
						acrs = None
					setXPath(newDct, 'm2m:sub/acrs', acrs)

			# Send UPDATE request
			res = CSE.request.sendUpdateRequest(subRI, 
												originator = originator,
												data = newDct,
												appendID = subRI)
			if not res.status or res.rsc != RC.updated:
				return Result.errorResult(dbg = L.logWarn(f'Cannot update subscription for {srat} uri: {subRI}'))

			del _subRIs[srat]
			self.setAttribute(self._subSratRIs, _subRIs)
		return Result.successResult()


	def _rollbackRrats(self, createdRrats:list[str], deletedRrats:list[str], originator:str) -> None:
		L.isDebug and L.logDebug('Rollback rrat additions and deletions')
		for rrat in createdRrats:	# delete those that are not in the original rrat list
			if rrat not in self.rrat:	# new, so delete <sub>
				self._deleteSubscriptionForRrat(rrat, originator)
		for rrat in deletedRrats:
			if rrat in self.rrat:		# exists, so re-add <sub>
				self._addRratSubscription(rrat, self.encs, originator)




