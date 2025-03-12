#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#
"""	This module implements the PollingChannel (PCH) resource.
"""

from __future__ import annotations
from typing import Optional, cast

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.Constants import Constants
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources import Factory		# attn: circular import
from ..resources import PCH_PCU
from ..runtime import CSE
from ..runtime.Logging import Logging as L


# Add to internal attributes
addToInternalAttributes(Constants.attrParentOriginator)	
addToInternalAttributes(Constants.attrPCURI)


# Tests for special access to PCH resource is done in SecurityManager.hasAccess()

class PCH(Resource):
	"""	PollingChannel resource class.
	"""

	resourceType = ResourceTypes.PCH
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """


	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.PCH_PCU ]
	"""	Allowed child-resource types. """

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
	"""	Attributes and Attribute policies for this Resource Class. """


	def initialize(self, pi:str, originator:str) -> None:
		# Set optional default for requestAggregation
		self.setAttribute('rqag', False, overwrite = False)	
		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		"""	Activate the PCH resource. Create the PCU resource and set the parent's originator.

			Args:
				parentResource:	The parent resource.
				originator:		The originator of the request.
		"""
		# register pollingChannelURI PCU virtual resource before anything else, because
		# it will be needed during validation, 
		L.isDebug and L.logDebug(f'Registering <PCU> for: {self.ri}')
		dct = {
			'm2m:pcu' : {
				'rn' : 'pcu'
			}
		}
		pcu = Factory.resourceFromDict(dct, 
								 	   pi = self.ri, 
									   ty = ResourceTypes.PCH_PCU,
									   create = True,
									   originator = originator)	# rn is assigned by resource itself
		
		resource = CSE.dispatcher.createLocalResource(pcu, self, originator = originator)
		self.setAttribute(Constants.attrPCURI, resource.ri)	# store own PCU ri

		# General activation + validation
		super().activate(parentResource, originator)

		# Store the parent's orginator/AE-ID/CSE-ID
		if parentResource.ty in [ ResourceTypes.CSEBase, ResourceTypes.AE]:
			self.setAttribute(Constants.attrParentOriginator, parentResource.getOriginator())
		else:
			raise BAD_REQUEST(L.logWarn(f'PCH must be registered under CSE or AE, not {str(ResourceTypes(parentResource.ty))}'))

		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		

	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		"""	Validate the PCH resource.
		
			Args:
				originator:		The originator of the request.
				dct:			The dictionary containing the resource data.
				parentResource:	The parent resource.
		"""
		super().validate(originator, dct, parentResource)

		# Set the aggregation state in the own PCU
		# This is done in activate and update
		resource = CSE.dispatcher.retrieveLocalResource(self.attribute(Constants.attrPCURI))
		pcu = cast(PCH_PCU.PCH_PCU, resource)
		pcu.setAggregate(self.rqag)
		pcu.dbUpdate(True)
		

	def getParentOriginator(self) -> str:
		"""	Return the <PCU>'s parent originator.
		
			Return:
				The <PCU>'s parent originator.
		"""
		return self.attribute(Constants.attrParentOriginator)