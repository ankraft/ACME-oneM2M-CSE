#
#	CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ContentInstance
#
""" ContentInstance (CIN) resource type.
"""

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes,  JSON, CSERequest
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.ACMEUtils import getAttributeSize
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime.Logging import Logging as L


class CIN(AnnounceableResource):
	""" ContentInstance resource type.
	"""

	resourceType = ResourceTypes.CIN
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SMD ]
	""" The allowed child-resource types. """

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
		'at': None,
		'aa': None,
		'ast': None,
		'ast': None,
		'daci': None,
		'st': None,
		'cr': None,
		'loc': None,


		# Resource attributes
		'cnf': None,
		'cs': None,
		'conr': None,
		'con': None,
		'or': None,
		'conr': None,
		'dcnt': None,
		'dgt': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def initialize(self, pi:str, originator:str) -> None:
		# Initializations must happen just after the resource is created
		# because the parent resource checks some of the attributes
		self.setAttribute('con', '', overwrite = False)
		self.setAttribute('cs', getAttributeSize(self.con))
		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# increment parent container's state tag
		parentResource = parentResource.dbReload()	# Read the resource again in case it was updated in the DB
		st = parentResource.st + 1
		parentResource.setAttribute('st',st)
		parentResource.dbUpdate(True)

		# Set stateTag attribute in self as well
		self.setAttribute('st', st)


	def willBeDeactivated(self, originator:str, parentResource:Resource) -> None:
		super().willBeDeactivated(originator, parentResource)
		
		# Check whether the parent container's *disableRetrieval* attribute is set to True.
		if parentResource.disr:
			raise OPERATION_NOT_ALLOWED(L.logWarn(f'Retrieval is disabled for the parent <container>'))
		
		# Check deletion Count: Update the cni and cbs attributes of the parent container
		# This actually happens in the parent container's childRemoved() method


	# Forbid updating
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		raise OPERATION_NOT_ALLOWED('updating CIN is forbidden')


	def willBeRetrieved(self, originator:str, 
							  request:Optional[CSERequest] = None, 
							  subCheck:Optional[bool] = True) -> None:
		super().willBeRetrieved(originator, request, subCheck = subCheck)

		# Check whether the parent container's *disableRetrieval* attribute is set to True.
		# "cnt" is a raw resource!
		if (cntRaw := self.retrieveParentResourceRaw()) and cntRaw.get('disr'):	# disr is either None, True or False. False means "not disabled retrieval"
			raise OPERATION_NOT_ALLOWED(L.logDebug(f'retrieval is disabled for the parent <container>'))
		
		# Check deletion Count
		if (dcnt := self.dcnt) is not None:	# dcnt is an innt
			L.isDebug and L.logDebug(f'Decreasing dcnt for <cin>, ri: {self.ri}, ({dcnt} -> {dcnt-1})')
			dcnt -= 1
			if dcnt > 0:	# still > 0 -> CIN is not deleted
				# We have to decrement this in the DB first, but increment it again
				self.setAttribute('dcnt', dcnt)
				self.dbUpdate()
				# Since this is handled as a post decrement we need to set-back the value of dcnt.
				# Attn: After this this value in the hold instance and in the DB are different !
				self.setAttribute('dcnt', dcnt+1)
			else:
				L.isDebug and L.logDebug(f'Deleting <cin>, ri: {self.ri} because dcnt reached 0')
				CSE.dispatcher.deleteLocalResource(self, originator = originator)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)

		# Check the format of the CNF attribute
		if cnf := self.cnf:
			CSE.validator.validateCNF(cnf)
		