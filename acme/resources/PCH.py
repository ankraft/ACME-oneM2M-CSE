#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from __future__ import annotations
from typing import Any
from ..etc.Types import AttributePolicyDict, ContentSerializationType, Operation, RequestType, ResourceTypes as T, Result, JSON, Parameters
from ..etc import RequestUtils as RU
from ..resources.Resource import *
from ..resources import Factory as Factory
from ..resources import PCH_PCU as PCH_PCU
from ..services import CSE as CSE
from ..services.Logging import Logging as L


# Tests for special access to PCH resource is done in SecurityManager.hasAccess()

class PCH(Resource):

	_parentOriginator = '__parentOriginator__'
	_pcuRI = '__pcuRI__'

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.PCH_PCU ]

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

		# Resource attributes
		'pcra': None,
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		# PCH inherits from its parent, the <AE>
		super().__init__(T.PCH, dct, pi, create = create, inheritACP = True)

		# Add to internal attributes to ignore in validation etc
		self.internalAttributes.append(self._parentOriginator)	
		self.internalAttributes.append(self._pcuRI)

		# Set optional default for requestAggregation
		self.setAttribute('pcra', False, overwrite = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		# register pollingChannelURI PCU virtual resource before anything else, because
		# it will be needed during validation, 
		if L.isDebug: L.logDebug(f'Registering <PCU> for: {self.ri}')
		dct = {
			'm2m:pcu' : {
				'rn' : 'pcu'
			}
		}
		pcu = Factory.resourceFromDict(dct, pi = self.ri, ty = T.PCH_PCU).resource	# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(pcu, originator = originator)).resource:
			return Result.errorResult(rsc = res.rsc, dbg = res.dbg)
		self.setAttribute(PCH._pcuRI, res.resource.ri)	# store own PCU ri

		# General activation + validation
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Store the parent's orginator/AE-ID/CSE-ID
		if parentResource.ty in [ T.CSEBase, T.AE]:
			self.setAttribute(PCH._parentOriginator, parentResource.getOriginator())
		else:
			L.logWarn(dbg := f'PCH must be registered under CSE or AE, not {str(T(parentResource.ty))}')
			return Result.errorResult(dbg = dbg)

		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		
		return Result.successResult()


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res

		# Set the aggregation state in the own PCU
		# This is done in activate and update
		if not (res := CSE.dispatcher.retrieveLocalResource(self.attribute(PCH._pcuRI))).status:
			return res
		pcu = cast(PCH_PCU.PCH_PCU, res.resource)
		pcu.setAggregate(self.pcra)
		pcu.dbUpdate()

		return Result.successResult()
		

	def getParentOriginator(self) -> str:
		"""	Return the <PCU>'s parent originator.
		
			Return:
				The <PCU>'s parent originator.
		"""
		return self.attribute(PCH._parentOriginator)