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
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ResponseStatusCode as RC, JSON, SemanticFormat
from ..etc import Utils, DateUtils
from ..services import CSE
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..resources import Factory as Factory
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class SMD(AnnounceableResource):
	""" The <semanticDescriptor> resource is used to store a semantic description pertaining to a
		resource and potentially subresources.
	"""

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ]

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


# TODO Annc version
# TODO Factory
# TODO SOE cannot be retrieved
# TODO Implement base64 basic type
# TODO clarify: or is RW or WO?
# TODO TEST write correct and wrong base64 in dsp



	def __init__(self, dct:JSON = None, pi:str = None, fcntType:str = None, create:bool = False) -> None:
		super().__init__(T.SMD, dct, pi, tpe = fcntType, create = create)


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		# Validation of CREATE is done in self.validate()

		return Result.successResult()


	def update(self, dct: JSON = None, originator: str = None, doValidateAttributes: bool = True) -> Result:

		# Some checks before the general validation that are necessary only in an UPDATE

		# TODO 
		# a) If both semanticOpExec and descriptor attributes exist, the Receiver shall generate a
		# Response Status Code indicating a "BAD_REQUEST" error.
		# b) If semanticOpExec attribute exists in the Request check that the syntax of its content corresponds
		#  to a valid SPARQL query request [33]. If the content does not correspond to a valid SPARQL query request,
		#  the Receiver shall generate a Response Status Code indicating an "INVALID_SPARQL_QUERY" error.


		if not (res := super().update(dct, originator, doValidateAttributes)).status:
			return res

		# TODO 
		#  If validationEnable attribute is changed from true to false, then the hosting CSE shall set the semanticValidated
		#  attribute of the addressed <semanticDescriptor> resource as false.

		return Result.successResult()


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		L.isDebug and L.logDebug(f'Validating semanticDescriptor: {self.ri}')
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res
		
		# Validate descriptor attribute
		if not (res := CSE.semantic.validateDescriptor(self)).status:
			res.rsc = RC.badRequest
			return res
		
		# Validate validationEnable attribute
		if not (res := CSE.semantic.validateValidationEnable(self)).status:
			res.rsc = RC.badRequest
			return res
		
		# The above procedures might have updated this instance.		
		self.dbUpdate()
		
		return Result.successResult()


	def willBeRetrieved(self, originator:str, request:CSERequest = None, subCheck:bool = True) -> Result:
		if (res := super().willBeRetrieved(originator, request, subCheck)).status == False:
			return res

		# Remove semanticOpExec from result
		self.delAttribute('soe')

		return Result.successResult()
