#
#	CRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CrossResourceSubscription
#

"""	<crossResourceSubscription> submodule. """

from __future__ import annotations
from typing import Optional

from copy import deepcopy
from ..etc import Utils
from ..helpers.ResourceSemaphore import resourceState, getResourceState
from ..etc.Types import AttributePolicyDict, ResourceTypes, ResponseStatusCode, Result, JSON, TimeWindowType, CSERequest
from ..resources.Resource import Resource
from ..services import CSE
from ..services.Logging import Logging as L



class CRS(Resource):
	"""	This class implements the <crossResourceSubscription> resource type. """

	_subSratRIs = '__subSratRIs__'	# dict of really modified <sub> resources
	_sudRI		= '__sudRI__'		# Reference when the resource is been deleted because of the deletion of a rrat or srat subscription. Usually empty

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
		'rrats': None,
		'twt': None,
		'tws': None,
		'encs': None,
		'nse': None,
		'nsi': None,
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.CRS, dct, pi, create = create)


		# add internal attribute to store the references to the created <sub> resources
		# Add to internal attributes to ignore in validation etc
		self._addToInternalAttributes(self._subSratRIs)
		self._addToInternalAttributes(self._sudRI)
		self.setAttribute(self._subSratRIs, {}, overwrite = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if (res := super().activate(parentResource, originator)).status == False:
			return res
		self.dbUpdate()	# Update in DB because we need some changes in other functions executed below
		L.isDebug and L.logDebug(f'Activating crossResourceSubscription: {self.ri}')

		# encs validation happens in validate()

		# Check owns NU's etc
		if not (res := CSE.notification.addCrossResourceSubscription(self, originator)).status:
			return res
		
		# Handle subscriptionResourcesAsTarget
		if (_srat := self.srat):
			for ri in _srat:
				if not (res := self._addSratSubscription(ri, originator)).status:
					self._deleteSubscriptions(originator)
					return res

		# Handle regularResourcesAsTarget
		if (_rrat := self.rrat):
			self.setAttribute('rrats', [ None ] * len(_rrat))	# add and initialize the rrats list
			_encs = self.attribute('encs/enc')
			for ri in _rrat:
				if not (res := self._addRratSubscription(ri, _encs, _rrat.index(ri), originator)).status:
					self._deleteSubscriptions(originator)
					return res
	
		# Start periodic window immediately if necessary
		if self.twt == TimeWindowType.PERIODICWINDOW:
			CSE.notification.startCRSPeriodicWindow(self.ri, self.tws, self._countSubscriptions())

		# nsi is at least an empty list if nse is present, otherwise it must not be present
		if self.nse is not None:
			self.setAttribute('nsi', [], overwrite = False)
			CSE.notification.validateAndConstructNotificationStatsInfo(self)


		self.dbUpdate()
		return Result.successResult()
	

	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> Result:
		L.isDebug and L.logDebug(f'Updating crossResourceSubscription: {self.ri}')
		
		# We are validating the attributes already here because the actual update of the resource
		# (where this happens) is done only after other procedures hapened.
		if not (res := CSE.validator.validateAttributes(dct, self.tpe, self.ty, self._attributes, create = False, createdInternally = self.isCreatedInternally(), isAnnounced = self.isAnnounced())).status:
			return res

		# Handle update notificationStatsEnable attribute, but only if present in the resource.
		# This is important bc it can be set to True, False, or Null.
		if 'nse' in Utils.pureResource(dct)[0]:
			CSE.notification.updateOfNSEAttribute(self, Utils.findXPath(dct, 'm2m:crs/nse'))

		# Check new NU's
		previousNus = deepcopy(self.nu)
		if (newNus := Utils.findXPath(dct, 'm2m:crs/nu')):
			self.setAttribute('nu', newNus)
		
		# Update the CRS for notifications
		if not (res := CSE.notification.updateCrossResourceSubscription(self, previousNus, originator)).status:
			return res

		# Update TimeWindowType and TimeWindowSize
		oldTwt = self.twt
		newTwt = Utils.findXPath(dct, 'm2m:crs/twt')
		newTws = Utils.findXPath(dct, 'm2m:crs/tws')

		if newTwt is not None or newTws is not None:
			if oldTwt == TimeWindowType.PERIODICWINDOW:
				CSE.notification.stopCRSPeriodicWindow(self.ri)
			else:
				CSE.notification.stopCRSSlidingWindow(self.ri)
			
			# Start periodic window with new tws if given, and when twt is still periodic
			# Sliding window will be activated when first notification is received
			if (newTwt is not None and newTwt == TimeWindowType.PERIODICWINDOW) or \
			   (newTwt is None     and oldTwt == TimeWindowType.PERIODICWINDOW):
				CSE.notification.startCRSPeriodicWindow(self.ri, self.tws if newTws is None else newTws, self._countSubscriptions())
		
		return super().update(dct, originator, doValidateAttributes = False)	# Was vaildated before
	

	@resourceState('deactivate')
	def deactivate(self, originator:str) -> None:

		# Deactivate time windows
		if self.twt == TimeWindowType.PERIODICWINDOW:
			CSE.notification.stopCRSPeriodicWindow(self.ri)
		elif self.twt == TimeWindowType.SLIDINGWINDOW:
			CSE.notification.stopCRSSlidingWindow(self.ri)

		# Delete rrat and srat subscriptions
		self._deleteSubscriptions(originator)

		# Handle removing the csr by the notification manager
		CSE.notification.removeCrossResourceSubscription(self)

		return super().deactivate(originator)


	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		L.isDebug and L.logDebug(f'Validating crossResourceSubscription: {self.ri}')

		# Check that at least rrat or srat is present
		if self.rrat is None and self.srat is None:
			return Result.errorResult(dbg = L.logDebug(f'At least one of regularResourcesAsTarget or subscriptionResourcesAsTarget attributes shall be present'))

		# Check when rrat is set that enc is correctly set and filled
		if self.rrat:
			if not self.encs or not self.attribute('encs/enc'):
				return Result.errorResult(dbg = L.logDebug(f'eventNotificationCriteriaSet must not be empty when regularResourcesAsTarget is provided'))
			if (_l := len(self.attribute('encs/enc'))) != 1 and _l != len(self.rrat):
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
		if (_vrq := Utils.findXPath(request.pc, 'm2m:sgn/vrq')) is not None and _vrq == True:
			L.isDebug and L.logDebug('Received subscription verification request to CRS resource')
			return Result(status = True, rsc = ResponseStatusCode.OK)
		
		# Deletion request
		if (_sud := Utils.findXPath(request.pc, 'm2m:sgn/sud')) is not None and _sud == True:
			_sur = Utils.findXPath(request.pc, 'm2m:sgn/sur')
			if getResourceState(self.ri) in ['deactivate']:
				L.isDebug and L.logDebug(f'Received subscription deletion notification from subscription: {_sur}. Already in delete. Ignored.')
				return Result(status = True, rsc = ResponseStatusCode.OK)
			L.isDebug and L.logDebug(f'Received subscription deletion request from: {_sur} to CRS resource')
			# Store the 'sur' to ignore that subscription resource during deletion
			self.setAttribute(self._sudRI, _sur)
			self.dbUpdate()

			# Delete self. Use the resource's creator for the creator
			CSE.dispatcher.deleteLocalResource(self, originator = self.getOriginator(), withDeregistration = True)
			return Result(status = True, rsc = ResponseStatusCode.OK)
		
		# Log any other notification
		if not (sur := Utils.findXPath(request.pc, 'm2m:sgn/sur')) :
			return Result.errorResult(dbg = L.logWarn('No or empty "sur" attribute in notification'))

		# Test whether the received sur points to one of the rrat or srat resources	
		_subSratRIs = self.attribute(self._subSratRIs)
		if (self.rrats and sur in self.rrats) or (self.srat and sur in self.srat) or (_subSratRIs.values() and sur in _subSratRIs.values()):
			CSE.notification.receivedCrossResourceSubscriptionNotification(sur, self)		
		else:
			L.isDebug and L.logDebug(f'Handling notification: sur: {sur} not in rrats: {self.rrats} or srat: {self.srat}')

		return Result(status = True, rsc = ResponseStatusCode.OK)


	#########################################################################

	def _countSubscriptions(self) -> int:
		"""	Return the number of subscriptions created by this <crs>. This is the
			sum of the subscriptions in rrat and and srat.
		
			Return:
				The number of subscriptions.
		"""
		_rrat = self.rrat
		_srat = self.srat
		return (len(_rrat) if _rrat else 0) + (len(_srat) if _srat else 0)


	def _addRratSubscription(self, rrat:str, encs:list[dict], rratIndex:int, originator:str) -> Result:
		"""	Add a single subscription for a rrat.
			
			Args:
				rrat: The target resource's uri.
				encs: eventNotificationCriteriaSet to add to the new <sub>.
				rratIndex: The index of *rrat* in the list.
				originator: The originator of the request.
			Return:
				Result object.
		"""
		dct = { 'm2m:sub' : {
					'et':	self.et,		# set <sub>'s et to the same value as self
					'nu': 	[ (_spri := Utils.toSPRelative(self.ri)) ],
					'acrs': [ _spri ],
				}}
		Utils.setXPath(dct, 'm2m:sub/enc', encs[0] if len(encs) == 1 else encs[rratIndex] ) # position of rrat in the list of rrats
		# Add nec if present in <crs> resource
		if self.nec:
			Utils.setXPath(dct, 'm2m:sub/nec', self.nec)

		# create (possibly remote) subscription
		L.logDebug(f'Adding <sub> to {rrat}: ')
		if not (res := CSE.dispatcher.createResourceFromDict(dct, parentID = rrat, ty = ResourceTypes.SUB, originator = originator)).status:
			return Result.errorResult(rsc = ResponseStatusCode.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot create subscription for {rrat}: {res.dbg}'))
		
		# Error? Then rollback: delete all created subscriptions so far and return with an error
		if not res.status or res.rsc != ResponseStatusCode.created:
			return Result.errorResult(rsc = ResponseStatusCode.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot create subscription for: {rrat}: {res.dbg}'))
		subRi, subCsi, pID = res.data # type: ignore [misc] # unpack

		# Add the created <sub>'s full RI to the correct position in the rrats list
		_rrats = self.rrats
		# _rrats[rratIndex] = f'{csiFromSPRelative(pri)}/{findXPath(res.request.pc, "m2m:sub/ri")}'
		_rrats[rratIndex] = f'{subCsi}/{subRi}'
		self.setAttribute('rrats', _rrats)

		return Result.successResult()


	def _addSratSubscription(self, srat:str, originator:str) -> Result:
		"""	Update another subscription, pointed to by a *srat* entry, to
			notify this <crs> resource.
			
			Args:
				srat: The target <sub>'s uri.
				originator: The originator of the request.
			Return:
				Result object.
		"""
		# Get subscription
		L.logDebug(f'Retrieving srat <sub>: {srat}')
		res = CSE.dispatcher.retrieveResource((_sratSpRelative := Utils.toSPRelative(srat)), originator = originator)	# local or remote
		if not res.status or res.rsc != ResponseStatusCode.OK:
			self._deleteSubscriptions(originator)
			return Result.errorResult(rsc = ResponseStatusCode.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot retrieve subscription for {srat} uri: {_sratSpRelative}'))
		
		resource = res.resource
		
		# Check whether the target is a subscription
		if resource.ty != ResourceTypes.SUB:
			self._deleteSubscriptions(originator)
			return Result.errorResult(dbg = L.logWarn(f'Resource is not a subscription for {srat} uri: {_sratSpRelative}'))

		newDct:JSON = { 'm2m:sub': {} }	# new request dct

		# Add to the sub's nu
		if (nu := resource.nu) is None:
			nu = []		# Add nu if not present
		if (spRi := Utils.toSPRelative(self.ri)) not in nu:
			nu.append(spRi)
		Utils.setXPath(newDct, 'm2m:sub/nu', nu)

		# # Add to the sub's associatedCrossResourceSub
		if (acrs := resource.acrs) is None:
			acrs = []	# Add acrs if not present
		if spRi not in acrs:
			acrs.append(spRi)
		Utils.setXPath(newDct, 'm2m:sub/acrs', acrs)

		# # Send UPDATE request
		L.logDebug(f'Updating srat <sub>: {srat}')
		res = CSE.dispatcher.updateResourceFromDict(newDct, _sratSpRelative, originator = originator, resource =resource)
		if not res.status or res.rsc != ResponseStatusCode.updated:
			self._deleteSubscriptions(originator)
			return Result.errorResult(rsc = ResponseStatusCode.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot update subscription for {srat} uri: {_sratSpRelative}'))

		# Add <sub>'s SP-relative ri to internal references
		_subRIs = self.attribute(self._subSratRIs)
		_sratCsi = Utils.csiFromSPRelative(_sratSpRelative)
		_sratRi = resource.ri
		_subRIs[srat] = f'{_sratCsi}/{_sratRi}'
		self.setAttribute(self._subSratRIs, _subRIs)

		return Result.successResult()


	def _deleteSubscriptions(self, originator:str) -> Result:
		"""	Delete the created subscriptions.

			Args:
				originator: The originator to use for the DELETE requests.
		"""
		L.isDebug and L.logDebug(f'Deleting all subscriptions for <CRS>: {self.ri}')
		sudRI = self.attribute(self._sudRI)	# Optional RI given in a subscription deletion notification. Leave it out!

		# Remove subscriptions for rrat. For this use the RI stored in the rrats attribute
		if rrats := self.rrats:
			L.isDebug and L.logDebug(f'Deleting rrat subscriptions')
			for subRI in rrats:
				if not subRI:	# could be None!
					continue
				if sudRI and Utils.compareIDs(sudRI, subRI):	# Continue when this is the resource ID of a deletion notification
					L.isDebug and L.logDebug(f'Skipping deletion initiating subscription (from notification): {sudRI}')
					continue
				if not (res := self._deleteSubscriptionForRrat(subRI, originator)).status:
					return res
		
		# Remove self from successfully done srat subscriptions
		# This is the internal list, not srat, bc this list may be smaller
		if _subSratRIs := self.attribute(self._subSratRIs):
			L.isDebug and L.logDebug(f'Removing from srat subscriptions')
			for subRI in list(_subSratRIs.keys()):
				if sudRI and Utils.compareIDs(sudRI, subRI):	# Continue when this is the resource ID of a deletion notification
					L.isDebug and L.logDebug(f'Skipping deletion initiating subscription (from notification): {sudRI}')
					continue
				if not (res := self._deleteFromSubscriptionsForSrat(subRI, originator)).status:
					return res
		return Result.successResult()


	def _deleteSubscriptionForRrat(self, subRI:str, originator:str) -> Result:
		if subRI is not None:
			L.isDebug and L.logDebug(f'Deleting <sub>: {subRI}')
			if not (res := CSE.dispatcher.deleteResource(subRI, originator = originator)).status:
				return res

			# To be sure: Set the RI in the rrats list to None
			_rrats = self.rrats
			_index = _rrats.index(subRI)
			_rrats[_index] = None
			self.setAttribute('rrats', _rrats)
		return Result.successResult()


	def _deleteFromSubscriptionsForSrat(self, srat:str, originator:str) -> Result:
		_subRIs = self.attribute(self._subSratRIs)
		if (subRI := _subRIs.get(srat)) is not None:
			res = CSE.dispatcher.retrieveResource(subRI, originator = originator)
			if not res.status or res.rsc != ResponseStatusCode.OK:
				return Result.errorResult(rsc = ResponseStatusCode.badRequest, dbg = L.logWarn(f'Cannot retrieve subscription for {srat} uri: {subRI}'))
			resource = res.resource

			newDct:JSON = { 'm2m:sub': {} }	# new request dct

			# remove from to the sub's nu
			if (nu := resource.nu) is not None:
				if (spRi := Utils.toSPRelative(self.ri)) in nu:
					nu.remove(spRi)
				Utils.setXPath(newDct, 'm2m:sub/nu', nu)

			# Add to the sub's associatedCrossResourceSub
			if (acrs := resource.acrs) is not None:
				if spRi in acrs:
					acrs.remove(spRi)
					if len(acrs) == 0:
						acrs = None
					Utils.setXPath(newDct, 'm2m:sub/acrs', acrs)

			# Send UPDATE request
			res = CSE.dispatcher.updateResourceFromDict(newDct, subRI, originator = originator, resource = resource)
			if not res.status or res.rsc != ResponseStatusCode.updated:
				return Result.errorResult(dbg = L.logWarn(f'Cannot update subscription for {srat} uri: {subRI}'))

			del _subRIs[srat]
			self.setAttribute(self._subSratRIs, _subRIs)
		return Result.successResult()

