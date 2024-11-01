#
#	DEPR.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Dependency
#

from __future__ import annotations
from typing import Optional, Tuple, Any, cast

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON, Permission, EvalCriteriaOperator
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST
from ..runtime.Logging import Logging as L
from ..helpers.TextTools import findXPath
from ..runtime import CSE
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class DEPR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB ] 
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
		'at': None,
		'aa': None,
		'ast': None,
		'cstn': None,
		'cr': None,

		# Resource attributes
		'sfc': None,
		'evc': None,
		'rri': None,
	}


	def __init__(self, dct:Optional[JSON] = None, pi:Optional[str] = None, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.DEPR, dct, pi, create = create)


	def activate(self, parentResource: Resource, originator: str) -> None:

		super().activate(parentResource, originator)

		# Check that the evalCriteria and target resources are correct and accessible
		try:
			CSE.action.checkEvalCriteria(self.evc, self.rri, originator)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)


	def update(self, dct: JSON = None, 
					 originator: Optional[str] = None,
					 doValidateAttributes: Optional[bool] = True) -> None:

		# get new or old rri and evc
		rri = self.getFinalResourceAttribute('rri', dct)
		evc = self.getFinalResourceAttribute('evc', dct)

		# Check that the evalCriteria and target resources are correct and accessible
		# Check the evc only if the evc attribute is present in the update request
		try:
			CSE.action.checkEvalCriteria(evc, rri, originator, 'evc' in dct)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)

		super().update(dct, originator, doValidateAttributes)