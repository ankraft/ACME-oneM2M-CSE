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
from typing import Optional, Any

from ..etc.Types import JSON, CSERequest
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import BAD_REQUEST, ResponseException, NOT_IMPLEMENTED
from ..helpers.TextTools import findXPath
from ..helpers.PluginManager import requires
from ..runtime.Logging import Logging as L
from ..runtime import Factory as Factory
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources.AnnounceableResource import AnnounceableResource


# internal attributes
addToInternalAttributes(Constants.attrDecodedDsp)


@requires(semanticManager='acme.plugins.services.SemanticManager', required=False)
class SMD(AnnounceableResource):
	""" The <semanticDescriptor> resource is used to store a semantic description pertaining to a
		resource and potentially subresources.
	"""

	semanticManager: Optional[Any] = None

# TODO SOE cannot be retrieved. Also in Updates?
# TODO clarify: or is RW or WO?

	def initialize(self, pi: str) -> None:
		self.setAttribute(Constants.attrDecodedDsp, None, overwrite=False)	
		super().initialize(pi)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		# Validation of CREATE is done in self.validate()
		
		# Perform Semantic validation process and add descriptor
		if not self.semanticManager:
			raise NOT_IMPLEMENTED(L.logWarn('SemanticManager is disabled, cannot add descriptor to graph'))
		self.semanticManager.addDescriptor(self)
		self.setAttribute('svd', True)



	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None,
					 doValidateAttributes:Optional[bool] = True) -> None:

		# Some checks before the general validation that are necessary only in an UPDATE
		soeNew = findXPath(dct, '{*}/soe')
		dspNew = findXPath(dct, '{*}/dsp')
		vldeOrg = self.vlde # store for later
		vldeNew = findXPath(dct, '{*}/vlde')

		# soe and dsp cannot updated together
		if soeNew and dspNew:
			raise BAD_REQUEST('Updating soe and dsp in one request is not allowed')
		
		# If soe exists then validate it
		if soeNew:
			if not self.semanticManager:
				raise NOT_IMPLEMENTED(L.logWarn('SemanticManager is disabled, cannot validate SPARQL query for soe attribute'))
			self.semanticManager.validateSPARQL(soeNew)

		# Generic update and validation (with semantic procdures)
		super().update(dct, originator, doValidateAttributes)

		# Test whether vlde changed in the request from True to False, then set svd to False as well.
		if vldeOrg == True and vldeNew == False:
			self.setAttribute('svd', False)

		# Update the semantic graph 
		#CSE.semantic.updateDescription(self)

	
	def deactivate(self, originator:str, parentResource:Resource) -> None:
		if not self.semanticManager:
			raise NOT_IMPLEMENTED(L.logWarn('SemanticManager is disabled, cannot remove descriptor from graph'))
		self.semanticManager.removeDescriptor(self)
		return super().deactivate(originator, parentResource)


	def validate(self, originator:Optional[str] = None,
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		L.isDebug and L.logDebug(f'Validating semanticDescriptor: {self.ri}')
		super().validate(originator, dct, parentResource)
		
		# Validate validationEnable attribute
		if self.semanticManager:
			self.semanticManager.validateValidationEnable(self)
		else:
			raise NOT_IMPLEMENTED(L.logWarn('SemanticManager is disabled, cannot validate vlde attribute'))

		# Validate descriptor attribute
		try:
			if self.semanticManager:
				self.semanticManager.validateDescriptor(self)
			else:
				raise NOT_IMPLEMENTED(L.logWarn('SemanticManager is disabled, cannot validate dcrp attribute'))
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)
		
		# Perform Semantic validation process and add descriptor
		if findXPath(dct, 'm2m:smd/dsp') or dct is None:	# only on create or when descriptor is present in the UPDATE request
			if self.semanticManager:
				self.semanticManager.addDescriptor(self)
			else:
				raise NOT_IMPLEMENTED(L.logWarn('SemanticManager is disabled, cannot add descriptor to graph'))
		self.setAttribute('svd', True)
		
		# The above procedures might have updated this instance.		
		self.dbUpdate(True)
		

	def willBeRetrieved(self, originator:str, 
							  request:Optional[CSERequest] = None, 
							  subCheck:Optional[bool] = True) -> None:
		super().willBeRetrieved(originator, request, subCheck)

		# Remove semanticOpExec from result
		self.delAttribute('soe')


	def setDecodedDSP(self, dsp:str) -> None:
		""" Set the decoded DSP internal attribute.
		"""
		self.setAttribute(Constants.attrDecodedDsp, dsp)


	def getDecodeDSP(self) -> str:
		""" Get the decoded DSP internal attribute.
		"""
		return self.attribute(Constants.attrDecodedDsp)
