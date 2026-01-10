#
#	TGR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: TriggerRequest
#

""" TriggerRequest (TGR) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, EvalMode, ResourceTypes, JSON, Permission, EvalCriteriaOperator, Operation
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST
from ..etc.ACMEUtils import riFromID, compareIDs
from ..helpers.TextTools import findXPath
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration, ConfigurationError
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class TGR(AnnounceableResource):
	""" TriggerRequest (TGR) resource type. """

	resourceType = ResourceTypes.TGR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB
													 ]
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
		'lbl': None,
		'acpi':None,
		'et': None,
		'daci': None,
		'cstn': None,

		# Resource attributes
		'mei': None,
		'tri': None,
		'tpe': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)



	def update(self, dct: JSON=None,
					 originator: Optional[str]=None, 
					 doValidateAttributes: Optional[bool]=True) -> None:
		super().update(dct, originator, doValidateAttributes)
	


	def deactivate(self, originator: str, parentResource: Resource) -> None:
		# Unschedule the action
		return super().deactivate(originator, parentResource)
