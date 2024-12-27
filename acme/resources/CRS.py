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

from ..etc.ACMEUtils import pureResource, toSPRelative, compareIDs
from ..etc.IDUtils import csiFromSPRelative
from ..helpers.TextTools import findXPath, setXPath
from ..helpers.ResourceSemaphore import criticalResourceSection, inCriticalSection
from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, TimeWindowType, EventEvaluationMode, CSERequest
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.ResponseStatusCodes import BAD_REQUEST, CROSS_RESOURCE_OPERATION_FAILURE
from ..resources.Resource import Resource, addToInternalAttributes
from ..runtime import CSE
from ..runtime.Logging import Logging as L


# add internal attribute to store the references to the created <sub> resources
# Add to internal attributes to ignore in validation etc
addToInternalAttributes(Constants.attrSubSratRIs)
addToInternalAttributes(Constants.attrSudRI)


class CRS(Resource):
	"""	This class implements the <crossResourceSubscription> resource type. """

	resourceType = ResourceTypes.CRS
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """


	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SCH ]

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
		'eem': None,	# EXPERIMENTAL
		'twt': None,
		'tws': None,
		'encs': None,
		'nse': None,
		'nsi': None,
	}


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute(Constants.attrSubSratRIs, {}, overwrite = False)	
		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		self.dbUpdate()	# Update in DB because we need some changes in other functions executed below
		L.isDebug and L.logDebug(f'Activating crossResourceSubscription: {self.ri}')

		# encs validation happens in validate()

		# Check owns NU's etc
		CSE.notification.addCrossResourceSubscription(self, originator)
		
		# Handle subscriptionResourcesAsTarget
		if (_srat := self.srat):
			for ri in _srat:
				try:
					self._addSratSubscription(ri, originator)
				except:
					self._deleteSubscriptions(originator)
					raise

		# Handle regularResourcesAsTarget
		if (_rrat := self.rrat):
			self.setAttribute('rrats', [ None ] * len(_rrat))	# add and initialize the rrats list
			_encs = self.attribute('encs/enc')
			for ri in _rrat:
				try:
					self._addRratSubscription(ri, _encs, _rrat.index(ri), originator)
				except:
					# Error? Then rollback: delete all created subscriptions so far and return with an error
					self._deleteSubscriptions(originator)
					raise
	
		# Start periodic window immediately if necessary
		if self.twt == TimeWindowType.PERIODICWINDOW:
			CSE.notification.startCRSPeriodicWindow(self.ri, self.tws, self._countSubscriptions(), self.eem)

		# "nsi" will be added later during the first stat recording
		
		# Set twi default if not present
		self.setAttribute('eem', EventEvaluationMode.ALL_EVENTS_PRESENT.value, False)

		self.dbUpdate()
	

	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		L.isDebug and L.logDebug(f'Updating crossResourceSubscription: {self.ri}')
		
		# We are validating the attributes already here because the actual update of the resource
		# (where this happens) is done only after other procedures hapened.
		CSE.validator.validateAttributes(dct, self.typeShortname, 
				   							  self.ty, 
											  self._attributes, 
											  create = False, 
											  createdInternally = self.isCreatedInternally(), 
											  isAnnounced = self.isAnnounced())

		# Handle update notificationStatsEnable attribute, but only if present in the resource.
		# This is important bc it can be set to True, False, or Null.
		if 'nse' in pureResource(dct)[0]:
			CSE.notification.updateOfNSEAttribute(self, findXPath(dct, 'm2m:crs/nse'))

		# Check new NU's
		previousNus = deepcopy(self.nu)
		if (newNus := findXPath(dct, 'm2m:crs/nu')):
			self.setAttribute('nu', newNus)
		
		# Update the CRS for notifications
		CSE.notification.updateCrossResourceSubscription(self, previousNus, originator)

		# Update TimeWindowType and TimeWindowSize
		oldTwt = self.twt
		newTwt = findXPath(dct, 'm2m:crs/twt')
		newTws = findXPath(dct, 'm2m:crs/tws')

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
		
		super().update(dct, originator, doValidateAttributes = False)	# Was vaildated before
	

	@criticalResourceSection(state = 'deactivate')
	def deactivate(self, originator:str, parentResource:Resource) -> None:

		# Deactivate time windows
		match self.twt:
			case TimeWindowType.PERIODICWINDOW:
				CSE.notification.stopCRSPeriodicWindow(self.ri)
			case TimeWindowType.SLIDINGWINDOW:
				CSE.notification.stopCRSSlidingWindow(self.ri)

		# Delete rrat and srat subscriptions
		self._deleteSubscriptions(originator)

		# Handle removing the csr by the notification manager
		CSE.notification.removeCrossResourceSubscription(self)

		super().deactivate(originator, parentResource)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		L.isDebug and L.logDebug(f'Validating crossResourceSubscription: {self.ri}')

		# Check that at least rrat or srat is present
		if self.rrat is None and self.srat is None:
			raise BAD_REQUEST(L.logDebug(f'At least one of regularResourcesAsTarget or subscriptionResourcesAsTarget attributes shall be present'))

		# Check when rrat is set that enc is correctly set and filled
		if self.rrat:
			if not self.encs or not self.attribute('encs/enc'):
				raise BAD_REQUEST(L.logDebug(f'eventNotificationCriteriaSet must not be empty when regularResourcesAsTarget is provided'))
			if (_l := len(self.attribute('encs/enc'))) != 1 and _l != len(self.rrat):
				raise BAD_REQUEST(L.logDebug(f'Number of entries in eventNotificationCriteriaSet must be 1 or the same number as regularResourcesAsTarget entries'))
		
		# EXPERIMENTAL
		# Check that if twt = SLIDINGWINDOW then eem is not set to ALL_OR_SOME_EVENTS_MISSING or ALL_EVENTS_MISSING
		if self.getFinalResourceAttribute('twt', dct) == TimeWindowType.SLIDINGWINDOW:
			eem = self.getFinalResourceAttribute('eem', dct)
			if eem is not None and eem in (EventEvaluationMode.ALL_OR_SOME_EVENTS_MISSING, 
										   EventEvaluationMode.ALL_EVENTS_MISSING):
				raise BAD_REQUEST(L.logDebug(f'eem = {eem} is not allowed with twt = SLIDINGWINDOW'))


	def childWillBeAdded(self, childResource: Resource, originator: str) -> None:
		super().childWillBeAdded(childResource, originator)
		if childResource.ty == ResourceTypes.SCH:
			if (rn := childResource._originalDict.get('rn')) is None:
				childResource.setResourceName('notificationSchedule')
			elif rn != 'notificationSchedule':
				raise BAD_REQUEST(L.logDebug(f'rn of <schedule> under <subscription> must be "notificationSchedule"'))
			

	def handleNotification(self, request:CSERequest, originator:str) -> None:
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
			return
		
		# Deletion request
		if (_sud := findXPath(request.pc, 'm2m:sgn/sud')) is not None and _sud == True:
			_sur = findXPath(request.pc, 'm2m:sgn/sur')
			if inCriticalSection(self.ri, 'deactivate'):
				L.isDebug and L.logDebug(f'Received subscription deletion notification from subscription: {_sur}. Already in delete. Ignored.')
				return
			L.isDebug and L.logDebug(f'Received subscription deletion request from: {_sur} to CRS resource')
			# Store the 'sur' to ignore that subscription resource during deletion
			self.setAttribute(Constants.attrSudRI, _sur)
			self.dbUpdate()

			# Delete self. Use the resource's creator for the creator
			CSE.dispatcher.deleteLocalResource(self, originator = self.getOriginator(), withDeregistration = True)
			return
		
		# Log any other notification
		if not (sur := findXPath(request.pc, 'm2m:sgn/sur')) :
			raise BAD_REQUEST(L.logWarn('No or empty "sur" attribute in notification'))

		# Test whether the received sur points to one of the rrat or srat resources	
		_subRIs = self.attribute(Constants.attrSubSratRIs)
		if (self.rrats and sur in self.rrats) or (self.srat and sur in self.srat) or (_subRIs.values() and sur in _subRIs.values()):
			CSE.notification.receivedCrossResourceSubscriptionNotification(sur, self)		
		else:
			L.isDebug and L.logDebug(f'Handling notification: sur: {sur} not in rrats: {self.rrats} or srat: {self.srat}')


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


	def _addRratSubscription(self, rrat:str, encs:list[dict], rratIndex:int, originator:str) -> None:
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
					'nu': 	[ (_spri := toSPRelative(self.ri)) ],
					'acrs': [ _spri ],
				}}
		setXPath(dct, 'm2m:sub/enc', encs[0] if len(encs) == 1 else encs[rratIndex] ) # position of rrat in the list of rrats
		# Add nec if present in <crs> resource
		if self.nec:
			setXPath(dct, 'm2m:sub/nec', self.nec)

		# create (possibly remote) subscription
		L.logDebug(f'Adding <sub> to {rrat}: ')
		try:
			tup = CSE.dispatcher.createResourceFromDict(dct, parentID = rrat, 
															 ty = ResourceTypes.SUB, 
															 originator = originator)
		except ResponseException as e:
			raise CROSS_RESOURCE_OPERATION_FAILURE(L.logWarn(f'Cannot create subscription for {rrat}: {e.dbg}'))
		
		subRi, subCsi, pID = tup # type: ignore [misc] # unpack
		# Add the created <sub>'s full RI to the correct position in the rrats list
		_rrats = self.rrats
		# _rrats[rratIndex] = f'{csiFromSPRelative(pri)}/{findXPath(res.request.pc, "m2m:sub/ri")}'
		_rrats[rratIndex] = f'{subCsi}/{subRi}'
		self.setAttribute('rrats', _rrats)


	def _addSratSubscription(self, srat:str, originator:str) -> None:
		"""	Update another subscription, pointed to by a *srat* entry, to
			notify this <crs> resource.
			
			Args:
				srat: The target <sub>'s uri.
				originator: The originator of the request.
			
			Raises:
			`CROSS_RESOURCE_OPERATION_FAILURE`: In case there is an error adding the *srat* subscription.
			`BAD_REQUEST`: In case the target resource is not a valid subscription.

		"""
		# Get subscription
		L.logDebug(f'Retrieving srat <sub>: {srat}')

		try:
			resource = CSE.dispatcher.retrieveResource((_sratSpRelative := toSPRelative(srat)), originator = originator)	# local or remote
		except ResponseException as e:
			self._deleteSubscriptions(originator)
			raise CROSS_RESOURCE_OPERATION_FAILURE(L.logWarn(f'Cannot retrieve subscription for {srat} uri: {_sratSpRelative}'))
		
		# Check whether the target is a subscription
		if resource.ty != ResourceTypes.SUB:
			self._deleteSubscriptions(originator)
			raise BAD_REQUEST(L.logWarn(f'Resource is not a subscription for {srat} uri: {_sratSpRelative}'))

		newDct:JSON = { 'm2m:sub': {} }	# new request dct

		# Add to the sub's nu
		if (nu := resource.nu) is None:
			nu = []		# Add nu if not present
		if (spRi := toSPRelative(self.ri)) not in nu:
			nu.append(spRi)
		setXPath(newDct, 'm2m:sub/nu', nu)

		# # Add to the sub's associatedCrossResourceSub
		if (acrs := resource.acrs) is None:
			acrs = []	# Add acrs if not present
		if spRi not in acrs:
			acrs.append(spRi)
		setXPath(newDct, 'm2m:sub/acrs', acrs)

		# # Send UPDATE request
		L.logDebug(f'Updating srat <sub>: {srat}')
		try:
			CSE.dispatcher.updateResourceFromDict(newDct, _sratSpRelative, originator = originator, resource =resource)
		except:
			self._deleteSubscriptions(originator)
			raise CROSS_RESOURCE_OPERATION_FAILURE(L.logWarn(f'Cannot update subscription for {srat} uri: {_sratSpRelative}'))

		# Add <sub>'s SP-relative ri to internal references
		_subRIs = self.attribute(Constants.attrSubSratRIs)
		_sratCsi = csiFromSPRelative(_sratSpRelative)
		_sratRi = resource.ri
		_subRIs[srat] = f'{_sratCsi}/{_sratRi}'
		self.setAttribute(Constants.attrSubSratRIs, _subRIs)


	def _deleteSubscriptions(self, originator:str) -> None:
		"""	Delete the created subscriptions.

			Args:
				originator: The originator to use for the DELETE requests.
		"""
		L.isDebug and L.logDebug(f'Deleting all subscriptions for <CRS>: {self.ri}')
		sudRI = self.attribute(Constants.attrSudRI)	# Optional RI given in a subscription deletion notification. Leave it out!

		# Remove subscriptions for rrat. For this use the RI stored in the rrats attribute
		if rrats := self.rrats:
			L.isDebug and L.logDebug(f'Deleting rrat subscriptions')
			for subRI in rrats:
				if not subRI:	# could be None!
					continue
				if sudRI and compareIDs(sudRI, subRI):	# Continue when this is the resource ID of a deletion notification
					L.isDebug and L.logDebug(f'Skipping deletion initiating subscription (from notification): {sudRI}')
					continue
				self._deleteSubscriptionForRrat(subRI, originator)
		
		# Remove self from successfully done srat subscriptions
		# This is the internal list, not srat, bc this list may be smaller
		if _subRIs := self.attribute(Constants.attrSubSratRIs):
			L.isDebug and L.logDebug(f'Removing from srat subscriptions')
			for subRI in list(_subRIs.keys()):
				if sudRI and compareIDs(sudRI, subRI):	# Continue when this is the resource ID of a deletion notification
					L.isDebug and L.logDebug(f'Skipping deletion initiating subscription (from notification): {sudRI}')
					continue
				self._deleteFromSubscriptionsForSrat(subRI, originator)


	def _deleteSubscriptionForRrat(self, subRI:str, originator:str) -> None:
		if subRI is not None:
			L.isDebug and L.logDebug(f'Deleting <sub>: {subRI}')
			try:
				CSE.dispatcher.deleteResource(subRI, originator = originator)
			except Exception as e:
				# ignore not found resources here
				L.logWarn(f'Cannot delete subscription for {subRI}: {e}')

			# To be sure: Set the RI in the rrats list to None
			_rrats = self.rrats
			_index = _rrats.index(subRI)
			_rrats[_index] = None
			self.setAttribute('rrats', _rrats)


	def _deleteFromSubscriptionsForSrat(self, srat:str, originator:str) -> None:
		_subRIs = self.attribute(Constants.attrSubSratRIs)
		if (subRI := _subRIs.get(srat)) is not None:
			try:
				resource = CSE.dispatcher.retrieveResource(subRI, originator = originator)
			except Exception as e:
				L.logWarn(f'Cannot retrieve subscription for {subRI}: {e}')

			newDct:JSON = { 'm2m:sub': {} }	# new request dct

			# remove from to the sub's nu
			if (nu := resource.nu) is not None:
				if (spRi := toSPRelative(self.ri)) in nu:
					nu.remove(spRi)
				setXPath(newDct, 'm2m:sub/nu', nu)

			# Add to the sub's associatedCrossResourceSub
			if (acrs := resource.acrs) is not None:
				if spRi in acrs:
					acrs.remove(spRi)
					if len(acrs) == 0:
						acrs = None
					setXPath(newDct, 'm2m:sub/acrs', acrs)

			# Send UPDATE request
			try:
				resource = CSE.dispatcher.updateResourceFromDict(newDct, subRI, originator = originator, resource = resource)
			except ResponseException as e:
				L.logWarn(f'Cannot update subscription for {srat} uri: {subRI}: {e} {e.dbg}')

			del _subRIs[srat]
			self.setAttribute(Constants.attrSubSratRIs, _subRIs)
