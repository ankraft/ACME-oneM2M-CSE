#
#	REQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Request
#

from typing import Dict, Any
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseStatusCode as RC, Result, RequestStatus, CSERequest, JSON
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services.Configuration import Configuration
from ..resources.Resource import *
from ..resources import Factory as Factory


class REQ(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ]

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
		'cstn': None,
		'acpi':None,
		'daci': None,

		# Resource attributes
		'op': None,
		'tg': None,
		'org': None,
		'rid': None,
		'mi': None,
		'pc': None,
		'rs': None,
		'ors': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.REQ, dct, pi, create = create)


	@staticmethod
	def createRequestResource(request:CSERequest) -> Result:
		"""	Create an initialized <request> resource.
		"""

		# Check if a an expiration ts has been set in the request
		if request.headers.requestExpirationTimestamp:
			et = request.headers.requestExpirationTimestamp	# This is already an ISO8601 timestamp
		
		# Check the rp(ts) argument
		elif request.args.rpts:
			et = request.args.rpts
		
		# otherwise calculate request et
		else:	
			et = DateUtils.getResourceDate(Configuration.get('cse.req.minet'))
			# minEt = DateUtils.getResourceDate(Configuration.get('cse.req.minet'))
			# maxEt = DateUtils.getResourceDate(Configuration.get('cse.req.maxet'))
			# if request.args.rpts:
			# 	et = request.args.rpts if request.args.rpts < maxEt else maxEt
			# else:
			# 	et = minEt


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
					'ot'	: DateUtils.getResourceDate(),
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
					'rvi'	: request.headers.releaseVersionIndicator if request.headers.releaseVersionIndicator else CSE.releaseVersion,
					'vsi'	: request.headers.vendorInformation,
				},
				'rs'	: RequestStatus.PENDING,
				# 'ors'	: {
				# }
		}}

		# add handlings, conditions and attributes from filter
		for k,v in { **request.args.handling, **request.args.conditions, **request.args.attributes}.items():
			Utils.setXPath(dct, f'm2m:req/mi/fc/{k}', v, True)

		# add content
		if request.pc and len(request.pc) > 0:
			Utils.setXPath(dct, 'm2m:req/pc', request.pc, True)

		# calculate and assign rtu for rt
		if (rtu := request.headers.responseTypeNUs) and len(rtu) > 0:
			Utils.setXPath(dct, 'm2m:req/mi/rt/nu', [ u for u in rtu if len(u) > 0] )

		if not (cseres := Utils.getCSE()).resource:
			return Result.errorResult(dbg = cseres.dbg)

		return Factory.resourceFromDict(dct, pi = cseres.resource.ri, ty = T.REQ)


