#
#	REQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Request
#

from typing import Dict, Any
from etc.Types import ResourceTypes as T, ResponseCode as RC, Result, RequestStatus, CSERequest, JSON
import etc.Utils as Utils
from resources.Resource import *
import resources.Factory as Factory
from services.Configuration import Configuration
from services.Validator import constructPolicy, addPolicy


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'daci', 'hld',
])
reqPolicies = constructPolicy([
	'op', 'tg', 'org', 'rid', 'mi', 'pc', 'rs', 'ors'
])
attributePolicies = addPolicy(attributePolicies, reqPolicies)


class REQ(Resource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.REQ, dct, pi, create=create, attributePolicies=attributePolicies)


	@staticmethod
	def createRequestResource(request:CSERequest) -> Result:
		"""	Create an initialized <request> resource.
		"""

		# Check if a an expiration ts has been set in the request
		if request.headers.requestExpirationTimestamp is not None:
			et = request.headers.requestExpirationTimestamp	# This is already an ISO8601 timestamp
		
		# Check the rp(ts) argument
		elif request.args.rpts is not None:
			et = request.args.rpts
		
		# otherwise calculate request et
		else:	
			minEt = Utils.getResourceDate(Configuration.get('cse.req.minet'))
			maxEt = Utils.getResourceDate(Configuration.get('cse.req.maxet'))
			if request.args.rpts is not None:
				et = request.args.rpts if request.args.rpts < maxEt else maxEt
			else:
				et = minEt


		dct:Dict[str, Any] = {
			'm2m:req' : {
				'et'	: et,
				'lbl'	: [ request.headers.originator ],
				'op'	: request.op,
				'tg'	: request.id,
				'org'	: request.headers.originator,
				'rid'	: request.headers.requestIdentifier,
				'mi'	: {
					'ty'	: request.headers.resourceType,
					'ot'	: Utils.getResourceDate(),
					'rqet'	: request.headers.requestExpirationTimestamp,
					'rset'	: request.headers.resultExpirationTimestamp,
					'rt'	: { 
						'rtv' : request.args.rt
					},
					'rp'	: request.args.rp,
					'rcn'	: request.args.rcn,
					'fc'	: {
						'fu'	: request.args.fu,
						'fo'	: request.args.fo,
					},
					'drt'	: request.args.drt,
					'rvi'	: request.headers.releaseVersionIndicator if request.headers.releaseVersionIndicator is not None else Configuration.get('cse.releaseVersion'),
					'vsi'	: request.headers.vendorInformation,
				},
				'rs'	: RequestStatus.PENDING,
				'ors'	: {
				}
		}}

		# add handlings, conditions and attributes from filter
		for k,v in { **request.args.handling, **request.args.conditions, **request.args.attributes}.items():
			Utils.setXPath(dct, f'm2m:req/mi/fc/{k}', v, True)

		# add content
		if request.dict is not None and len(request.dict) > 0:
			Utils.setXPath(dct, 'm2m:req/pc', request.dict, True)

		# calculate and assign rtu for rt
		if (rtu := request.headers.responseTypeNUs) is not None and len(rtu) > 0:
			Utils.setXPath(dct, 'm2m:req/mi/rt/nu', [ u for u in rtu if len(u) > 0] )

		if (cseres := Utils.getCSE()).resource is None:
			return Result(rsc=RC.badRequest, dbg=cseres.dbg)

		return Factory.resourceFromDict(dct, pi=cseres.resource.ri, ty=T.REQ)


