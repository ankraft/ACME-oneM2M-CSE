#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Group (GRP) Resource Type """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, ConsistencyStrategy, JSON
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..resources import Factory as Factory	# attn: circular import
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class GRP(AnnounceableResource):
	""" Represents the Group resource. """

	resourceType = ResourceTypes.GRP
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.SMD, 
								   ResourceTypes.SUB, 
								   ResourceTypes.GRP_FOPT ]
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
	"""	Attributes and `AttributePolicy` for this resource type. """


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('mt', int(ResourceTypes.MIXED), overwrite = False)
		self.setAttribute('ssi', False, overwrite = True)
		self.setAttribute('cnm', 0, overwrite = False)	# calculated later
		self.setAttribute('mid', [], overwrite = False)			
		self.setAttribute('mtv', False, overwrite = False)
		self.setAttribute('csy', ConsistencyStrategy.abandonMember, overwrite = False)
		super().initialize(pi, originator)

		# These attributes are not provided by default: mnm (no default), macp (no default)
		# optional set: spty, gn, nar


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		# add fanOutPoint
		ri = self.ri
		L.isDebug and L.logDebug(f'Registering fanOutPoint resource for: {ri}')
		fanOutPointResource = Factory.resourceFromDict(pi = ri, 
												 	   ty = ResourceTypes.GRP_FOPT,
													   create = True,
													   originator = originator)
		CSE.dispatcher.createLocalResource(fanOutPointResource, self, originator)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		CSE.groupResource.validateGroup(self, originator)


