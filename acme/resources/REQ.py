#
#	REQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Request
#

from __future__ import annotations
from typing import Optional, Dict, Any

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, RequestStatus, CSERequest, JSON
from ..etc import Utils, DateUtils
from ..services.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources import Factory
from ..services import CSE


class REQ(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SUB ]

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


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.REQ, dct, pi, create = create)


	@staticmethod
	def createRequestResource(request:CSERequest) -> Result:
		"""	Create an initialized <request> resource.
		"""

		# Check if a an expiration ts has been set in the request
		if request.rqet:
			et = request.rqet	# This is already an ISO8601 timestamp
		
		# Check the rp(ts) argument
		elif request._rpts:
			et = request._rpts
		
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
				'lbl'	: [ request.originator ],
				'op'	: request.op,
				'tg'	: request.id,
				'org'	: request.originator,
				'rid'	: request.rqi,
				'mi'	: {
					'ty'	: request.ty,
					'ot'	: DateUtils.getResourceDate(),
					'rqet'	: request.rqet,
					'rset'	: request.rset,
					'rt'	: { 
						'rtv' : request.rt
					},
					'rp'	: request.rp,
					'rcn'	: request.rcn,
					'fc'	: {
						'fu'	: request.fc.fu,
						'fo'	: request.fc.fo,
					},
					'drt'	: request.drt,
					'rvi'	: request.rvi if request.rvi else CSE.releaseVersion,
					'vsi'	: request.vsi,
					'sqi'	: request.sqi,
				},
				'rs'	: RequestStatus.PENDING,
				# 'ors'	: {
				# }
		}}

		# add handlings, conditions and attributes from filter
		for k,v in { **request.fc.criteriaAttributes(), **request.fc.attributes}.items():
			Utils.setXPath(dct, f'm2m:req/mi/fc/{k}', v, True)

		# add content
		if request.pc and len(request.pc) > 0:
			Utils.setXPath(dct, 'm2m:req/pc', request.pc, True)

		# calculate and assign rtu for rt
		if (rtu := request.rtu) and len(rtu) > 0:
			Utils.setXPath(dct, 'm2m:req/mi/rt/nu', [ u for u in rtu if len(u) > 0] )

		if not (cseres := Utils.getCSE()).resource:
			return Result.errorResult(dbg = cseres.dbg)

		return Factory.resourceFromDict(dct, pi = cseres.resource.ri, ty = ResourceTypes.REQ)


