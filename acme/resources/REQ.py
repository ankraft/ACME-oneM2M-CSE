#
#	REQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Request
#

from typing import Dict, Any
from Constants import Constants as C
from Types import ResourceTypes as T, Result, RequestArguments, RequestHeaders, Operation, RequestStatus
from Validator import constructPolicy, addPolicy
import Utils
from .Resource import *
from .AnnounceableResource import AnnounceableResource


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'daci', 
])
reqPolicies = constructPolicy([
	'op', 'tg', 'or', 'rid', 'mi', 'pc', 'rs', 'ors'
])
attributePolicies = addPolicy(attributePolicies, reqPolicies)



class REQ(Resource):

	def __init__(self, jsn:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.REQ, jsn, pi, create=create, attributePolicies=attributePolicies)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [ T.SUB ])


	@staticmethod
	def createRequestResource(arguments:RequestArguments, headers:RequestHeaders, operation:Operation, target:str, content:dict=None) -> Result:
		"""	Create an initialized <request> resource.
		"""
		# calculate request et
		minEt = Utils.getResourceDate(5) 	# TODO config
		maxEt = Utils.getResourceDate(20) 	# TODO config
		if arguments.rp is not None:
			et = arguments.rp if arguments.rp < maxEt else maxEt
		else:
			et = minEt

		jsn:Dict[str, Any] = {
			'm2m:req' : {
				'et'	: et,
				'lbl'	: [ headers.originator ],
				'op'	: operation,
				'tg'	: target,
				'or'	: headers.originator,
				'rid'	: headers.requestIdentifier,
				'mi'	: {
					'ty'	: headers.resourceType,
					'ot'	: Utils.getResourceDate(),
					'rqet'	: headers.requestExpirationTimestamp,
					'rset'	: headers.responseExpirationTimestamp,
					'rt'	: arguments.rt,
					'rp'	: arguments.rp,
					'rcn'	: arguments.rcn,
					'fc'	: {
						'fu'	: arguments.fu,
						'fo'	: arguments.fo,
					},
					'drt'	: arguments.drt,
					'rvi'	: headers.releaseVersionIndicator if headers.releaseVersionIndicator is not None else C.hfvRVI,
				},
				'rs'	: RequestStatus.PENDING,
				'ors'	: {
				}
		}}

		# add handlings, conditions and attributes from filter
		for k,v in { **arguments.handling, **arguments.conditions, **arguments.attributes}.items():
			Utils.setXPath(jsn, 'm2m:req/mi/fc/%s' % k, v, True)

		if content is not None:
			Utils.setXPath(jsn, 'm2m:req/pc', content, True)

		if (cseres := Utils.getCSE()).resource is None:
			return Result(rsc=RC.badRequest, dbg=cseres.dbg)
		return Utils.resourceFromJSON(jsn, pi=cseres.resource.ri, ty=T.REQ)


