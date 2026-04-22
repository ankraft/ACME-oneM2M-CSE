#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Group (GRP) Resource Type """

from __future__ import annotations
from typing import Optional, Any

from ..etc.Types import ResourceTypes, ConsistencyStrategy, JSON
from ..etc.ResponseStatusCodes import NOT_IMPLEMENTED
from ..helpers.PluginManager import requires
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..runtime import Factory as Factory	# attn: circular import
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


@requires(groupManager='acme.plugins.services.GroupManager', required=False)
class GRP(AnnounceableResource):
	""" Represents the Group resource. """

	groupManager: Optional[Any] = None

	def initialize(self, pi: str) -> None:
		self.setAttribute('mt', int(ResourceTypes.MIXED), overwrite=False)
		self.setAttribute('ssi', False, overwrite=True)
		self.setAttribute('cnm', 0, overwrite=False)	# calculated later
		self.setAttribute('mid', [], overwrite=False)			
		self.setAttribute('mtv', False, overwrite=False)
		self.setAttribute('csy', ConsistencyStrategy.abandonMember, overwrite=False)
		super().initialize(pi)

		# These attributes are not provided by default: mnm (no default), macp (no default)
		# optional set: spty, gn, nar


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)
		
		# add fanOutPoint
		L.isDebug and L.logDebug(f'Registering fanOutPoint resource for: {self.ri}')
		self.createChildResourceFromDict({ 'et': self.et }, ty=ResourceTypes.GRP_FOPT, originator=originator)		# rn is assigned by resource itself



	def validate(self, originator: Optional[str]=None, 
					   dct: Optional[JSON]=None, 
					   parentResource: Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)
		if not self.groupManager:
			raise NOT_IMPLEMENTED(L.logWarn('GroupManager plugin is disabled, cannot validate group.'))
		self.groupManager.validateGroup(self, originator)


