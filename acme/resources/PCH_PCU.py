#
#	PCH_PCU.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannelURI for PollingChannel
#

from __future__ import annotations
from typing import cast, Optional

from ..etc.Types import AttributePolicyDict, Operation, RequestType, ResourceTypes, JSON, CSERequest, Result
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import BAD_REQUEST, OPERATION_NOT_ALLOWED, INTERNAL_SERVER_ERROR, REQUEST_TIMEOUT
from ..resources.VirtualResource import VirtualResource
from ..resources.Resource import addToInternalAttributes
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..etc.DateUtils import timeUntilTimestamp
from ..etc.ResponseStatusCodes import ResponseStatusCode


# Add to internal attributes to ignore in validation etc
addToInternalAttributes(Constants.attrPCUAggregate)	


class PCH_PCU(VirtualResource):

	resourceType = ResourceTypes.PCH_PCU
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	resourceName = 'pcu'
	""" Possibility for virtual sub-classes to provide a specific resource name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute(Constants.attrPCUAggregate, False, overwrite = False)
		super().initialize(pi, originator)
		
	
	def handleRetrieveRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
		""" Handle a RETRIEVE request. Return resource or block until available. At the PCU, only received requests are retrieved, otherwise
			this function does not return until a reqeust timeout occurs. Only the AE's originator has access to this virtual resource.

			Args:
				request: Mandatory for PCU. The original RETRIEVE request.
				originator: Request originator.
			Return:
				Result instance, with the response set to *embeddedRequest*.
		"""
		L.isDebug and L.logDebug(f'RETRIEVE request for polling channel. Originator: {originator}')

		# A retrieve of PCU requires the original retrieve request
		if not request:
			raise INTERNAL_SERVER_ERROR(L.logErr('Missing request in call to PCU'))

		# Determine the request's timeout
		if request.rqet:
			ret = timeUntilTimestamp(request._rqetUTCts)
			L.isDebug and L.logDebug(f'Polling timeout: {ret} seconds')
		else:
			ret = CSE.request.requestExpirationDelta
			L.isDebug and L.logDebug(f'Polling timeout: indefinite')

		# Return the response or time out
		try:
			res = CSE.request.waitForPollingRequest(originator, None, timeout = ret, aggregate = self.getAggregate())
		except REQUEST_TIMEOUT:
			raise REQUEST_TIMEOUT(L.logWarn(f'Request Expiration Timestamp reached. No request queued for originator: {self.getOriginator()}'))
		
		return Result(rsc = ResponseStatusCode.OK, resource = res.resource, request = request, embeddedRequest = res.request)


	def handleNotifyRequest(self, request:CSERequest, originator:str) -> None:
		"""	Handle a NOTIFY request to a PCU resource. At the PCU, only Responses are delivered. This method is called
			when a notification is directed to a non-request-reachable target.
		"""
		L.isDebug and L.logDebug(f'NOTIFY request for polling channel. Originator: {originator}')

		# Check whether the request is allowed by this originator was done in the dispatcher

		# Check content
		if request.pc is None:
			raise BAD_REQUEST(f'Missing content/request in notification')
		
		# Validate the response
		CSE.validator.validatePrimitiveContent(request.pc)

		if (innerPC := cast(JSON, request.pc.get('m2m:rsp'))) is None:
			raise BAD_REQUEST(L.logDebug(f'Notification to PCU must contain a Response (m2m:rsp)'))
		
		if not innerPC.get('fr'):
			L.isDebug and L.logDebug(f'Adding originator: {request.originator} to request')
			innerPC['fr'] = request.originator

		nrequest = CSERequest()
		nrequest.originalRequest = innerPC
		nrequest.pc = innerPC.get('pc')

		response = CSE.request.fillAndValidateCSERequest(nrequest, isResponse = True)
		# L.logWarn(response)
		# L.logWarn(innerPC)

		# Enqueue the reqeust
		CSE.request.queueRequestForPCH(operation = Operation.NOTIFY,
									   pchOriginator = self.getOriginator(), 
									   request = response, 
									   reqType = RequestType.RESPONSE)	# A Notification to PCU always contains a response to a previous request
		

	def handleCreateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a CREATE request. Fail with error code. 
		"""
		raise OPERATION_NOT_ALLOWED('CREATE operation not allowed for <pollingChanelURI> resource type')


	def handleUpdateRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle an UPDATE request. Fail with error code. 
		"""
		raise OPERATION_NOT_ALLOWED('UPDATE operation not allowed for <pollingChanelURI> resource type')


	def handleDeleteRequest(self, request:CSERequest, id:str, originator:str) -> Result:
		""" Handle a DELETE request. Delete the latest resource. 
		"""
		raise OPERATION_NOT_ALLOWED('DELETE operation not allowed for <pollingChanelURI> resource type')


	def setAggregate(self, aggregate:bool) -> None:
		"""	Set the aggregated state for a polling channel. This usually reflects the state of the PCU's parent resource, and
			is maintained by it.
			This attribute is handled as an internal attribute.

			Args:
				aggregate: Boolean indicating whether requests shall be aggregated in a response.
		"""
		self.setAttribute(Constants.attrPCUAggregate, aggregate)
		

	def getAggregate(self) -> bool:
		"""	Return the aggregated state internal attribute.

			Return:
				Boolean, the agregated state.
		"""
		return self.attribute(Constants.attrPCUAggregate)