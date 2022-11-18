#
#	SMD.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: SemanticDescriptor
#

""" The <semanticDescriptor> resource is used to store a semantic description pertaining to a
	resource and potentially subresources.
"""

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, ResponseStatusCode, JSON, CSERequest
from ..etc import Utils
from ..services import CSE
from ..services.Logging import Logging as L
from ..resources import Factory as Factory
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource



class SMD(AnnounceableResource):
	""" The <semanticDescriptor> resource is used to store a semantic description pertaining to a
		resource and potentially subresources.
	"""

	_decodedDsp = '__decodedDsp__'
	""" Name of an internal string attribute that holds the description after base64 decode. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SUB ]

#AE, container, contentInstance, group, node, flexContainer, timeSeries, mgmtObj

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
		'at': None,
		'aa': None,
		'ast': None,
		'daci': None,
		'cr': None,

		# Resource attributes
		'dcrp': None,
		'soe': None,
		'dsp': None,
		'or': None,
		'rels': None,
		'svd': None,
		'vlde': None,
	}


# TODO SOE cannot be retrieved. Also in Updates?
# TODO clarify: or is RW or WO?



	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   fcntType:Optional[str] = None,
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.SMD, dct, pi, tpe = fcntType, create = create)
		self._addToInternalAttributes(self._decodedDsp)
		self.setAttribute(self._decodedDsp, None, overwrite = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		# Validation of CREATE is done in self.validate()
		
		# Perform Semantic validation process and add descriptor
		if not (res := CSE.semantic.addDescriptor(self)).status:
			return res
		self.setAttribute('svd', True)

		return Result.successResult()


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None,
					 doValidateAttributes:Optional[bool] = True) -> Result:

		# Some checks before the general validation that are necessary only in an UPDATE
		soeNew = Utils.findXPath(dct, '{*}/soe')
		dspNew = Utils.findXPath(dct, '{*}/dsp')
		vldeOrg = self.vlde # store for later
		vldeNew = Utils.findXPath(dct, '{*}/vlde')

		# soe and dsp cannot updated together
		if soeNew and dspNew:
			return Result(status = False, rsc = ResponseStatusCode.badRequest, dbg = 'Updating soe and dsp in one request is not allowed')
		
		# If soe exists then validate it
		if soeNew and not (res := CSE.semantic.validateSPARQL(soeNew)).status:
			return res

		# Generic update and validation (with semantic procdures)
		if not (res := super().update(dct, originator, doValidateAttributes)).status:
			return res

		# Test whether vlde changed in the request from True to False, then set svd to False as well.
		if vldeOrg == True and vldeNew == False:
			self.setAttribute('svd', False)

		# Update the semantic graph 
		#CSE.semantic.updateDescription(self)

		return Result.successResult()

	
	def deactivate(self, originator:str) -> None:
		CSE.semantic.removeDescriptor(self)
		return super().deactivate(originator)


	def validate(self, originator:Optional[str] = None,
					   create:Optional[bool] = False,
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		L.isDebug and L.logDebug(f'Validating semanticDescriptor: {self.ri}')
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		
		# Validate validationEnable attribute
		if not (res := CSE.semantic.validateValidationEnable(self)).status:
			res.rsc = ResponseStatusCode.badRequest
			return res

		# Validate descriptor attribute
		if not (res := CSE.semantic.validateDescriptor(self)).status:
			res.rsc = ResponseStatusCode.badRequest
			return res
		
		# Perform Semantic validation process and add descriptor
		if Utils.findXPath(dct, 'm2m:smd/dsp') or create:	# only on create or when descriptor is present in the UPDATE request
			if not (res := CSE.semantic.addDescriptor(self)).status:
				return res
		self.setAttribute('svd', True)
		
		# The above procedures might have updated this instance.		
		self.dbUpdate()
		
		return Result.successResult()


	def willBeRetrieved(self, originator:str, 
							  request:Optional[CSERequest] = None, 
							  subCheck:Optional[bool] = True) -> Result:
		if (res := super().willBeRetrieved(originator, request, subCheck)).status == False:
			return res

		# Remove semanticOpExec from result
		self.delAttribute('soe')

		return Result.successResult()
