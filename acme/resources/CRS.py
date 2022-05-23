#
#	CRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CrossResourceSubscription
#

from __future__ import annotations

from ..etc.Utils import toSPRelative
from ..etc.Types import AttributePolicyDict, Operation, ResourceTypes as T, Result, JSON
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L


class CRS(Resource):

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


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if (res := super().activate(parentResource, originator)).status == False:
			return res
		
		# Handle regularResourcesAsTarget
		if self.rrat:
			rratCounter = 0
			for rrat in self.rrat:
				dct = { 'm2m:sub' : {
							'nu' : [ (_spri := Utils.toSPRelative(self.ri)) ],
							'acrs': [ _spri ],
						}}

				L.logWarn(Utils.findXPath(self.encs[0], 'enc'))
				if len(self.encs) == 1:
					Utils.setXPath(dct, 'm2m:sub/enc', Utils.findXPath(self.encs[0], 'enc'))
				else:
					Utils.setXPath(dct, 'm2m:sub/enc', Utils.findXPath(self.encs[rratCounter], 'enc'))
				if self.nec:
					Utils.setXPath(dct, 'm2m:sub/nec', self.nec)
				rratCounter += 1
				L.logDebug(f'Creating <sub> for {rrat}')
				res = CSE.request.sendCreateRequest((_uri := Utils.toSPRelative(rrat)), 
													originator = originator,
													ty = T.SUB,
													data = dct,
													appendID = _uri)
				if not res.status or res.rsc != RC.created:
					L.logDebug(f'Cannot create subscription for {rrat} uri: {_uri}: {res.resource}')

				# TODO rollback the subs until now!


				# L.log(dct)
				# L.log(res)

# If regularResourcesAsTarget is included, the Hosting CSE shall send a CREATE <subscription> request message to each target resource 
# indicated by regularResourcesAsTarget.
#	-i) In the new CREATE <subscription> request, the receiver shall use the From of the current CREATE request. 
# 		For this <subscription> to be created:
#		-1) eventNotificationCriteria attribute shall use the corresponding entry included in eventNotificationCriteriaSet attribute of the
# 			 <crossResourceSubscription> resource representation.
#		-2) notificationURI attribute shall be set to the resource identifier of this <crossResourceSubscription> resource being created.
#		- 3) associatedCrossResourceSub attribute shall be set to the resource identifier of this <crossResourceSubscription> resource being created.
#		-4) notificationEventCat attribute shall be set to the same value in the <crossResourceSubscription> resource representation.
#	ii) If any <subscription> for a target resource cannot be successfully created, the receiver shall send an unsuccessful response with a 
# 		"CROSS_RESOURCE_OPERATION_FAILURE" Response Status Code to the Originator; the receiver shall also delete already created <subscription> 
# 		resources at other target resources that were created based on the presence of regularResourcesAsTarget.

		return Result.successResult()


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
		if (_vrq := Utils.findXPath(request.pc, 'm2m:sgn/vrq')) is not None and _vrq == True:
			L.isDebug and L.logDebug('Received subscription verification request to CRS resource')
			return Result(status = True, rsc = RC.OK)
		
		# Deletion request
		if (_sud := Utils.findXPath(request.pc, 'm2m:sgn/sud')) is not None and _sud == True:
			L.isDebug and L.logDebug('Received subscription deletion request to CRS resource')
			return Result(status = True, rsc = RC.OK)
		
		return Result.errorResult( dbg = 'unknown notification')

