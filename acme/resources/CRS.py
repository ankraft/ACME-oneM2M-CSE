#
#	CRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CrossResourceSubscription
#

from __future__ import annotations
from copy import deepcopy

from ..etc.Utils import toSPRelative, csiFromSPRelative, findXPath, setXPath
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, JSON, TimeWindowType
from ..resources.Resource import *
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L



class CRS(Resource):

	_subRratRIs = '__subRratRIs__'	# dict rrat-ri -> sub-ri
	_subSratRIs = '__subSratRIs__'	# dict srat-ri -> sub-ri
	_sudRI		= '__sudRI__'		# Reference when the resource is been deleted because of the deletion of a rrat or srat subscription. Usually empty

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

	# TODO Restart support (in NotificationManager)


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.CRS, dct, pi, create = create)


		# add internal attribute to store the references to the created <sub> resources
		# Add to internal attributes to ignore in validation etc
		self._addToInternalAttributes(self._subRratRIs)
		self._addToInternalAttributes(self._subSratRIs)
		self._addToInternalAttributes(self._sudRI)
		self.setAttribute(self._subRratRIs, {}, overwrite = False)	
		self.setAttribute(self._subSratRIs, {}, overwrite = False)	

		# TODO NSE to False


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if (res := super().activate(parentResource, originator)).status == False:
			return res
		L.isDebug and L.logDebug(f'Activating crossResourceSubscription: {self.ri}')

		# Check NU's etc
		if not (res := CSE.notification.addCrossResourceSubscription(self, originator)).status:
			return res
		
		# Handle regularResourcesAsTarget
		if self.rrat:
			for rrat in self.rrat:
				if not (res := self._addRratSubscription(rrat, self.attribute('encs/enc'), self.rrat, originator)).status:
					self._deleteSubscriptions(originator)
					return res
		
		# Handle subscriptionResourcesAsTarget
		if self.srat:
			for srat in self.srat:
				if not (res := self._addSratSubscription(srat, originator)).status:
					self._deleteSubscriptions(originator)
					return res

		if self.twt == TimeWindowType.PERIODICWINDOW:
			CSE.notification.startCRSPeriodicWindow(self.ri, self.tws, self._countSubscriptions())

		self.dbUpdate()
		return Result.successResult()
	

	def update(self, dct:JSON = None, originator:str = None, doValidateAttributes:bool = True) -> Result:
		L.isDebug and L.logDebug(f'Updating crossResourceSubscription: {self.ri}')
		# We are validating the attributes here already because this actual update of the resource
		# (where this happens) is done only after a lot of other stuff hapened.
		# So, the resource is validated twice in an update :()
		if not (res := CSE.validator.validateAttributes(dct, self.tpe, self.ty, self._attributes, create = False, createdInternally = self.isCreatedInternally(), isAnnounced = self.isAnnounced())).status:
			return res


		# Check NU's etc
		if (newNus := findXPath(dct, 'm2m:crs/nu')):
			if not (res := CSE.notification.updateCrossResourceSubscription(self.ri, newNus, self.nu, originator)).status:
				return res
		
		# Structures for rollbacks
		_createdRrat:list[str] = []
		_deletedRrat:list[str] = []
		_createdSrat:list[str] = []
		_deletedSrat:list[str] = []

		# Check the state of enc first before doing any more complicated changes
		# take the rrat to work with from the update, otherwise from the current resource
		_dctRrats = findXPath(dct, 'm2m:crs/rrat')
		rrats = _dctRrats if _dctRrats else self.rrat	

		# Check enc attribute from the update, otherwise from the current resource
		_dctEncs = findXPath(dct, 'm2m:crs/encs/enc')
		encs = _dctEncs if _dctEncs else self.attribute('encs/enc')
		if rrats and not encs:
			return Result.errorResult(dbg = L.logDebug(f'"encs" must not be empty when "rrat" is provided'))
		if encs and len(encs) != 1 and len(encs) != len(rrats):
			return Result.errorResult(dbg = L.logDebug(f'Length of "encs" must be 1 or equal to length of "rrat"'))
			

		# Update for regularResourcesAsTarget
		if newRrat := findXPath(dct, 'm2m:crs/rrat'):

			# More preparations
			oldRrat =  deepcopy(self.rrat)

			# Add subscriptions for added rrats
			for rrat in newRrat:
				if not oldRrat or rrat not in oldRrat:	# when oldRrat does not exist, OR when rrat is not in oldRrat
					L.isDebug and L.logDebug(f'Adding rrat: {rrat}')
					if not (res := self._addRratSubscription(rrat, encs, rrats, originator)).status:
						self._rollbackRrats(_createdRrat, _deletedRrat, originator)
						return res
					_createdRrat.append(rrat)
				
			# Delete subscriptions for removed rrats
			if oldRrat:
				for rrat in oldRrat:
					if rrat not in newRrat:
						L.isDebug and L.logDebug(f'Removing rrat: {rrat}')
						if not (res := self._deleteSubscriptionForRrat(rrat, originator)).status:
							self._rollbackRrats(_createdRrat, _deletedRrat, originator)
							return res
					_deletedRrat.append(rrat)
		

		# Update for subscriptionResourcesAsTarget
		if newSrat := findXPath(dct, 'm2m:crs/srat'):
			oldSrat = deepcopy(self.srat)

			# Delete subscriptions for removed srats
			for srat in oldSrat:
				if srat not in newSrat:
					L.isDebug and L.logDebug(f'Removing srat: {srat}')
					if not (res := self._deleteFromSubscriptionsForSrat(srat, originator)).status:
						self._rollbackRrats(_createdRrat, _deletedRrat, originator)
						self._rollbackSrats(_createdSrat, _deletedSrat, originator)
						return res
				_deletedSrat.append(srat)

			# Add subscriptions for added srats
			if oldSrat:
				for srat in newSrat:
					if not oldSrat or srat not in oldSrat:	# when oldSrat does not exist, OR when srat is not in oldSrat
						L.isDebug and L.logDebug(f'Adding srat: {srat}')
						if not (res := self._addSratSubscription(srat, originator)).status:
							self._rollbackRrats(_createdRrat, _deletedRrat, originator)
							self._rollbackSrats(_createdSrat, _deletedSrat, originator)
							return res
						_createdSrat.append(srat)
		
		# Update of the eventNotificationCriteriaSet
		if newEncs := findXPath(dct, 'm2m:crs/encs/enc'):
			# Check of the correct encs length is done above already

			# Update all in rrats (either existing, or provided in the update)
			for rrat in rrats:
				if not (res := self._updateRratSubscription(rrat, newEncs, rrats, originator)).status:
					self._rollbackRrats(_createdRrat, _deletedRrat, originator)
					self._rollbackSrats(_createdSrat, _deletedSrat, originator)
					self._rollbackEncs(originator)
					return res

		# Update TimeWindowType and TimeWindowSize
		oldTwt = self.twt
		newTwt = findXPath(dct, 'm2m:crs/twt')
		oldTws = self.tws
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
		
		return super().update(dct, originator, doValidateAttributes = False)
	

	def deactivate(self, originator:str) -> None:

		# Delete rrat and srat subscriptions
		self._deleteSubscriptions(originator)

		# Deactivate windows
		if self.twt == TimeWindowType.PERIODICWINDOW:
			CSE.notification.stopCRSPeriodicWindow(self.ri)
		elif self.twt == TimeWindowType.SLIDINGWINDOW:
			CSE.notification.stopCRSSlidingWindow(self.ri)

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
		if (_vrq := findXPath(request.pc, 'm2m:sgn/vrq')) is not None and _vrq == True:
			L.isDebug and L.logDebug('Received subscription verification request to CRS resource')
			return Result(status = True, rsc = RC.OK)
		
		# Deletion request
		if (_sud := findXPath(request.pc, 'm2m:sgn/sud')) is not None and _sud == True:
			_sur = findXPath(request.pc, 'm2m:sgn/sur')
			L.isDebug and L.logDebug(f'Received subscription deletion request from: {_sur} to CRS resource')
			# Store the 'sur' to leave it out during deletion
			self.setAttribute(self._sudRI, _sur)
			self.dbUpdate()

			# TODO originator = original creator of the <crs> resource? 
			
			CSE.dispatcher.deleteResource(self, withDeregistration = True)
			return Result(status = True, rsc = RC.OK)
		
		# Log any other notification
		if not (sur := findXPath(request.pc, 'm2m:sgn/sur')) :
			return Result.errorResult(dbg = L.logWarn('No or empty "sur" attribute in notification'))
		if sur in self.attribute(self._subRratRIs).values() or sur in self.attribute(self._subSratRIs).values():
			CSE.notification.receivedCrossResourceSubscriptionNotification(sur, self)
		
		return Result(status = True, rsc = RC.OK)


	#########################################################################

	def _countSubscriptions(self) -> int:
		"""	Return the number of subscriptions created by this <crs>.
		
			Return:
				Integer value, the number of subscriptions.
		"""
		return len(self.attribute(self._subRratRIs)) + len(self.attribute(self._subSratRIs))


	def _addRratSubscription(self, rrat:str, encs:list[dict], rrats:list[str], originator:str) -> Result:
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
		setXPath(dct, 'm2m:sub/enc', encs[0] if len(encs) == 1 else encs[rrats.index(rrat)] ) # position of rrat in the list of rrats
		if self.nec:
			setXPath(dct, 'm2m:sub/nec', self.nec)
		# create (possibly remote) subscription
		L.logDebug(f'Adding <sub> to {rrat}: ')
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


	def _updateRratSubscription(self, rrat:str, encs:list[dict], rrats:list[str], originator:str) -> Result:
		dct:JSON = { 'm2m:sub' : {
				}}

		setXPath(dct, 'm2m:sub/enc', encs[0] if len(encs) == 1 else encs[rrats.index(rrat)] )	# position of rrat in the list of rrats

		# update (possibly remote) subscription
		subRI = self.attribute(self._subRratRIs).get(rrat)
		L.logDebug(f'Updating <sub> to {rrat} -> ri:{subRI}')
		res = CSE.request.sendUpdateRequest(subRI, 
											originator = originator,
											data = dct,
											appendID = subRI)
		
		# Error? Then rollback: delete all created subscriptions so far and return with an error
		if not res.status or res.rsc != RC.updated:
			return Result.errorResult(rsc = RC.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot update subscription for {rrat} uri: {subRI}: {res.data}'))

		return Result.successResult()


	def _deleteSubscriptions(self, originator:str) -> Result:
		"""	Delete the created subscriptions.

			Args:
				originator: The originator to use for the DELETE requests.
		"""
		sudRI = self.attribute(self._sudRI)	# Optional RI given in a subscription deletion notification. Leave it out!
		# rrat
		if _subRratRIs := self.attribute(self._subRratRIs):
			for rrat in list(_subRratRIs.keys()):
				if sudRI and sudRI == rrat:	# Continue when this is the resource ID of a deletion notification
					continue
				if not (res := self._deleteSubscriptionForRrat(rrat, originator)).status:
					return res
		
		#srat
		if _subSratRIs := self.attribute(self._subSratRIs):
			for srat in list(_subSratRIs.keys()):
				if sudRI and sudRI == srat:	# Continue when this is the resource ID of a deletion notification
					continue
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
		"""	Rollback of changes done for rrat updates.
		
			Args:
				createdRrats: List of created rrat resources.
				deletedRrats: List of deleted rrat resources.
				originator: originator of the request.
			"""
		L.isDebug and L.logDebug('Rollback rrat additions and deletions')
		if self.rrat:
			for rrat in createdRrats:	# delete those that are not in the original rrat list
				if rrat not in self.rrat:	# new, so delete <sub>
					self._deleteSubscriptionForRrat(rrat, originator)
			for rrat in deletedRrats:
				if rrat in self.rrat:		# originally exists, so re-add <sub>
					self._addRratSubscription(rrat, self.attribute('encs/enc'), self.rrat, originator)


	def _rollbackSrats(self, createdSrats:list[str], deletedSrats:list[str], originator:str) -> None:
		"""	Rollback of changes done for srat updates.
		
			Args:
				createdSrats: List of created srat resources.
				deletedSrats: List of deleted srat resources.
				originator: originator of the request.
			"""
		L.isDebug and L.logDebug('Rollback rrat additions and deletions')
		if self.srat:
			for srat in createdSrats:	# delete those that are not in the original srat list
				if srat not in self.srat:	# new, so delete <sub>
					self._deleteFromSubscriptionsForSrat(srat, originator)
			for srat in deletedSrats:
				if srat in self.srat:		# originally exists, so re-add <sub>
					self._addSratSubscription(srat, originator)


	def _rollbackEncs(self, originator:str) -> None:
		"""	Rollback the encs changes made to remote subscriptions.
		
			Args:
				originator: originator of the request.
		"""
		L.isDebug and L.logDebug('Rollback encs updates')
		if self.rrat:
			for rrat in self.rrat:
				# rollback to the current resource values
				self._updateRratSubscription(rrat, self.attribute('encs/enc'), self.rrat, originator)	# ignore results. What should we do?


