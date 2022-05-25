#
#	CRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CrossResourceSubscription
#

from __future__ import annotations

from ..etc.Utils import toSPRelative, csiFromSPRelative, findXPath, setXPath
from ..etc.Types import AttributePolicyDict, Operation, ResourceTypes as T, Result, JSON
from ..resources.Resource import *
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L



class CRS(Resource):

	_subRIs = '__subRIs__'	# dict rrat-ri -> sub-ri

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
		self.internalAttributes.append(self._subRIs)
		self.setAttribute(self._subRIs, {}, overwrite = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if (res := super().activate(parentResource, originator)).status == False:
			return res
		
		# Handle regularResourcesAsTarget
		if self.rrat:
			for rrat in self.rrat:
				if not (res := self._addSubscription(rrat, originator)).status:
					return res

		# TODO ...
		# c) If subscriptionResourcesAsTarget is included, the Hosting CSE shall add the resource identifier of this
		#  <crossResourceSubscription> resource to the associatedCrossResourceSub attribute of each <subscription> resource 
		# indicated in subscriptionResourcesAsTarget by issuing an UPDATE request to the <subscription> resource host.
		# 	iii) In the UPDATE request, the receiver shall use the From parameter from the current CREATE request.
		# 	iv) notificationURI attribute shall be updated to include the resource identifier of this <crossResourceSubscription>
		# 		 resource being created.
		# 	v) If any <subscription> for a target resource cannot be successfully updated, the receiver shall send an unsuccessful 
		# 		response with a "CROSS_RESOURCE_OPERATION_FAILURE" Response Status Code to the Originator; the Hosting CSE shall also
		# 		 remove itself from any already successfully associated <subscription> resources using the procedures in clause 7.4.8.2.4 and also delete any already-created <subscription> resources at other target resources.
		# 
		# d)Once the <crossResourceSubscription> resource is created, the Hosting CSE shall start the time window if the 
		# 	timeWindowType=PERIODICWINDOW; if timeWindowType=SLIDINGWINDOW, the Hosting CSE shall start the time window after the 
		# 	first notification is received from a Target Resource Hosting CSE.
		# e) If the notificationStatsEnable attribute is set to true, the Hosting CSE shall start recording notification statistics in
		# 	 the notificationStatsInfo attribute once the <crossResourceSubscription> resource is created.

		self.dbUpdate()
		return Result.successResult()
	

	def update(self, dct:JSON = None, originator:str = None) -> Result:

		# Update for regularResourcesAsTarget
		if newRrat := findXPath(dct, 'm2m:crs/rrat'):
			oldRrat = self.rrat
	
			# Add subscriptions for added rrats
			for rrat in newRrat:
				if rrat not in oldRrat:
					if not (res := self._addSubscription(rrat, originator)).status:
						return res
			
			# Delete subscriptions for removed rrats
			for rrat in oldRrat:
				if rrat not in newRrat:
					self._deleteSubscriptionForRrat(rrat, originator)
		
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
		# 
		# f)If the notificationStatsEnable attribute in the resource is true and the notificationStatsEnable attribute in the request
		#  is false, the Hosting CSE shall stop collecting notification statistics for the <crossResourceSubscription> resource. 
		#  The Hosting CSE shall maintain the current value of the notificationStatsInfo attribute.
		#
		# g)If the notificationStatsEnable attribute in the resource is false and the notificationStatsEnable attribute in the request is
		#  true, the Hosting CSE shall update the value of the notificationStatsEnable attribute in the resource to true, delete any
		# values stored in the notificationStatsInfo attribute of the resource and then start recording notification statistics.
		
		return super().update(dct, originator)


	

	def deactivate(self, originator:str) -> None:

		# Delete rrat subscriptions
		if self.rrat:
			self._deleteSubscriptions(originator)
		
		# TODO Remove self from nu of srat subscriptions
		# b) The Hosting CSE shall UPDATE the <subscription> resource of each target resource indicated in the 
		# subscriptionResourcesAsTarget attribute using the procedure in clause 7.4.8.2.3 to remove the
		# resource identifier of this <crossResourceSubscription> from the <subscription> resource's 
		# associatedCrossResourceSub attribute. The Receiver shall use the From of the current request for these requests.
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


	def _addSubscription(self, rrat:str, originator:str) -> Result:
		"""	Add a single subscription for a rrat.
			
			Args:
				rrat: The target resource's uri.
				originator: The originator of the request.
			Return:
				Result object.
		"""
		
		dct = { 'm2m:sub' : {
					'nu' : [ (_spri := toSPRelative(self.ri)) ],
					'acrs': [ _spri ],
				}}
		if len(self.encs) == 1:
			setXPath(dct, 'm2m:sub/enc', findXPath(self.encs[0], 'enc'))
		else:
			setXPath(dct, 'm2m:sub/enc', findXPath(self.encs[rratCounter], 'enc'))
		if self.nec:
			setXPath(dct, 'm2m:sub/nec', self.nec)
		# create (possibly remote) subscription
		L.logDebug(f'Creating <sub> for {rrat}')
		res = CSE.request.sendCreateRequest((_rratSpRelative := toSPRelative(rrat)), 
											originator = originator,
											ty = T.SUB,
											data = dct,
											appendID = _rratSpRelative)
		
		# Error? Then rollback: delete all created subscriptions so far and return with an error
		if not res.status or res.rsc != RC.created:
			self._deleteSubscriptions(originator)
			return Result.errorResult(rsc = RC.crossResourceOperationFailure, dbg = L.logWarn(f'Cannot create subscription for {rrat} uri: {_rratSpRelative}'))

		# Add <sub> to internal references
		_subRIs = self.attribute(self._subRIs)
		_subRIs[rrat] = f'{csiFromSPRelative(_rratSpRelative)}/{findXPath(res.request.pc, "m2m:sub/ri")}'
		self.setAttribute(self._subRIs, _subRIs)

		return Result.successResult()


	def _deleteSubscriptions(self, originator:str) -> None:
		"""	Delete the created subscriptions.

			Args:
				originator: The originator to use for the DELETE requests.
		"""
		if _subRIs := self._subRIs:
			for rrat in list(self.attribute(_subRIs).keys()):
				self._deleteSubscriptionForRrat(rrat, originator)


	def _deleteSubscriptionForRrat(self, rrat:str, originator:str) -> None:
		_subRIs = self.attribute(self._subRIs)
		if (subRI := _subRIs.get(rrat)) is not None:
			CSE.request.sendDeleteRequest(subRI, originator = originator)
			del _subRIs[rrat]
			self.setAttribute(self._subRIs, _subRIs)





