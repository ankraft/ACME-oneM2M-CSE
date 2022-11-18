#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from __future__ import annotations
from typing import Optional, cast

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON
from ..resources.Resource import Resource
from ..resources import Factory
from ..resources import PCH_PCU
from ..services import CSE
from ..services.Logging import Logging as L


# Tests for special access to PCH resource is done in SecurityManager.hasAccess()

class PCH(Resource):

	_parentOriginator = '__parentOriginator__'
	_pcuRI = '__pcuRI__'

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.PCH_PCU ]

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
		'rqag': None,
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		# PCH inherits from its parent, the <AE>
		super().__init__(ResourceTypes.PCH, dct, pi, create = create, inheritACP = True)

		# Add to internal attributes to ignore in validation etc
		self._addToInternalAttributes(self._parentOriginator)	
		self._addToInternalAttributes(self._pcuRI)

		# Set optional default for requestAggregation
		self.setAttribute('rqag', False, overwrite = False)	


	def activate(self, parentResource:Resource, originator:str) -> Result:
		# register pollingChannelURI PCU virtual resource before anything else, because
		# it will be needed during validation, 
		L.isDebug and L.logDebug(f'Registering <PCU> for: {self.ri}')
		dct = {
			'm2m:pcu' : {
				'rn' : 'pcu'
			}
		}
		pcu = Factory.resourceFromDict(dct, pi = self.ri, ty = ResourceTypes.PCH_PCU).resource	# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createLocalResource(pcu, originator = originator)).resource:
			return Result.errorResult(rsc = res.rsc, dbg = res.dbg)
		self.setAttribute(PCH._pcuRI, res.resource.ri)	# store own PCU ri

		# General activation + validation
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Store the parent's orginator/AE-ID/CSE-ID
		if parentResource.ty in [ ResourceTypes.CSEBase, ResourceTypes.AE]:
			self.setAttribute(PCH._parentOriginator, parentResource.getOriginator())
		else:
			return Result.errorResult(dbg = L.logWarn(f'PCH must be registered under CSE or AE, not {str(ResourceTypes(parentResource.ty))}'))

		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		
		return Result.successResult()


	def validate(self, originator:Optional[str] = None, 
					   create:Optional[bool] = False, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res

		# Set the aggregation state in the own PCU
		# This is done in activate and update
		if not (res := CSE.dispatcher.retrieveLocalResource(self.attribute(PCH._pcuRI))).status:
			return res
		pcu = cast(PCH_PCU.PCH_PCU, res.resource)
		pcu.setAggregate(self.rqag)
		pcu.dbUpdate()

		return Result.successResult()
		

	def getParentOriginator(self) -> str:
		"""	Return the <PCU>'s parent originator.
		
			Return:
				The <PCU>'s parent originator.
		"""
		return self.attribute(PCH._parentOriginator)