#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Group
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, ConsistencyStrategy, JSON
from ..services.Logging import Logging as L
from ..services import CSE
from ..resources import Factory as Factory	# attn: circular import
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class GRP(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.SMD, 
								   ResourceTypes.SUB, 
								   ResourceTypes.GRP_FOPT ]

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
		'mt': None,
		'spty': None,
		'cnm': None,
		'mnm': None,
		'mid': None,
		'macp': None,
		'mtv': None,
		'csy': None,
		'gn': None,
		'ssi': None,
		'nar': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   fcntType:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.GRP, dct, pi, create = create)

		self.setAttribute('mt', int(ResourceTypes.MIXED), overwrite = False)
		self.setAttribute('ssi', False, overwrite = True)
		self.setAttribute('cnm', 0, overwrite = False)	# calculated later
		self.setAttribute('mid', [], overwrite = False)			
		self.setAttribute('mtv', False, overwrite = False)
		self.setAttribute('csy', ConsistencyStrategy.abandonMember, overwrite = False)

		# These attributes are not provided by default: mnm (no default), macp (no default)
		# optional set: spty, gn, nar


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		# add fanOutPoint
		ri = self.ri
		L.isDebug and L.logDebug(f'Registering fanOutPoint resource for: {ri}')
		fanOutPointResource = Factory.resourceFromDict(pi = ri, ty = ResourceTypes.GRP_FOPT)
		CSE.dispatcher.createLocalResource(fanOutPointResource, self, originator)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		CSE.groupResource.validateGroup(self, originator)


