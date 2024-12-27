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

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, CSERequest
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import BAD_REQUEST, ResponseException
from ..helpers.TextTools import findXPath
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources import Factory as Factory
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources.AnnounceableResource import AnnounceableResource


# internal attributes
addToInternalAttributes(Constants.attrDecodedDsp)


class SMD(AnnounceableResource):
	""" The <semanticDescriptor> resource is used to store a semantic description pertaining to a
		resource and potentially subresources.
	"""

	resourceType = ResourceTypes.SMD
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """


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

	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute(Constants.attrDecodedDsp, None, overwrite = False)	
		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		# Validation of CREATE is done in self.validate()
		
		# Perform Semantic validation process and add descriptor
		CSE.semantic.addDescriptor(self)
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
			CSE.semantic.validateSPARQL(soeNew)

		# Generic update and validation (with semantic procdures)
		super().update(dct, originator, doValidateAttributes)

		# Test whether vlde changed in the request from True to False, then set svd to False as well.
		if vldeOrg == True and vldeNew == False:
			self.setAttribute('svd', False)

		# Update the semantic graph 
		#CSE.semantic.updateDescription(self)

	
	def deactivate(self, originator:str, parentResource:Resource) -> None:
		CSE.semantic.removeDescriptor(self)
		return super().deactivate(originator, parentResource)


	def validate(self, originator:Optional[str] = None,
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		L.isDebug and L.logDebug(f'Validating semanticDescriptor: {self.ri}')
		super().validate(originator, dct, parentResource)
		
		# Validate validationEnable attribute
		CSE.semantic.validateValidationEnable(self)

		# Validate descriptor attribute
		try:
			CSE.semantic.validateDescriptor(self)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)
		
		# Perform Semantic validation process and add descriptor
		if findXPath(dct, 'm2m:smd/dsp') or dct is None:	# only on create or when descriptor is present in the UPDATE request
			CSE.semantic.addDescriptor(self)
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
