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
from ..services.Logging import Logging as L
from ..etc.Utils import riFromID
from ..helpers.TextTools import findXPath
from ..services import CSE
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

		# Check existence and accessibility of the references resource in rri.
		try:
			resRri = CSE.dispatcher.retrieveResourceWithPermission(self.rri, originator, Permission.RETRIEVE)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)

		# Check existence of referenced subject attribute in the referenced resource.
		sbjt = self.evc['sbjt']
		if not resRri.hasAttributeDefined(sbjt):
			raise BAD_REQUEST(L.logDebug(f'sbjt - subject resource hasn\'t the attribute: {sbjt} defined: {resRri.ri}'))
		
		# Check the value space of the threshold attribute.
		dataType = CSE.action.checkAttributeThreshold(sbjt, self.evc['thld'])

		# Check evalCriteria operator
		CSE.action.checkAttributeOperator(EvalCriteriaOperator(self.evc['optr']), dataType, sbjt)


	def update(self, dct: JSON = None, 
					 originator: Optional[str] = None,
					 doValidateAttributes: Optional[bool] = True) -> None:

		# Check existence and accessibility of the references resource in rri.
		try:
			resRri = CSE.dispatcher.retrieveResourceWithPermission(self.getFinalResourceAttribute('rri', dct), originator, Permission.RETRIEVE)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)

		if (evc := findXPath(dct, 'm2m:depr/evc')) is not None:


			# Check existence of referenced subject attribute in the referenced resource.
			sbjt = evc['sbjt']
			if not resRri.hasAttributeDefined(sbjt):
				raise BAD_REQUEST(L.logDebug(f'sbjt - subject resource hasn\'t the attribute: {sbjt} defined: {resRri.ri}'))

			# Check the value space of the threshold attribute.
			dataType = CSE.action.checkAttributeThreshold(sbjt, self.evc['thld'])

			# Check evalCriteria operator
			CSE.action.checkAttributeOperator(EvalCriteriaOperator(self.evc['optr']), dataType, sbjt)

		super().update(dct, originator, doValidateAttributes)