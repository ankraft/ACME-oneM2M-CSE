#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from __future__ import annotations
from typing import Any
from ..etc.Types import AttributePolicyDict, ContentSerializationType, Operation, ResourceTypes as T, Result, JSON, Parameters
from ..etc import RequestUtils as RU
from ..resources.Resource import *
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L


class PCH(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.PCH_PCU ]

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

		# Resource attributes

		# TODO requestAggregation attribute as soon as it has been specified in TS-0004

	}


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		# PCH inherits from its parent, the <AE>
		super().__init__(T.PCH, dct, pi, create=create, inheritACP=True)


# TODO test Retrieve by AE only! Add new willBeRetrieved() function
# TODO continue with 10.2.5.14 Retrieve <pollingChannel>

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		
		# register pollingChannelURI virtual resource
		if L.isDebug: L.logDebug(f'Registering <PCU> for: {self.ri}')
		pcu = Factory.resourceFromDict(pi=self.ri, ty=T.PCH_PCU).resource	# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(pcu)).resource:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		return Result(status=True)


	def storeRequest(self, operation:Operation, originator:str, ty:T, data:Any, ct:ContentSerializationType, parameters:Parameters=None):

		# Fill various request attributes
		request 								= CSERequest()
		request.op 								= operation
		request.headers.originator				= originator
		request.headers.resourceType 			= ty
		request.headers.originatingTimestamp	= DateUtils.getResourceDate()
		request.headers.requestIdentifier		= Utils.uniqueRI()
		request.headers.releaseVersionIndicator	= CSE.releaseVersion
		if parameters:
			if C.hfcEC in parameters:				# Event Category
				request.parameters[C.hfEC] 		= parameters[C.hfcEC]

		# Add the request and the data
		result									= Result(dict=data, request=request)

		L.logErr(result)
	

