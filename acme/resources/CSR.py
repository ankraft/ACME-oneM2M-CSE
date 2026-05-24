#
#	CSR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: RemoteCSE
#
""" RemoteCSE resource class. """

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import ResourceTypes, JSON
from ..etc.ResponseStatusCodes import ORIGINATOR_HAS_NO_PRIVILEGE, BAD_REQUEST
from ..etc.IDUtils import originatorToID
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..resources.Resource import Resource
	from ..services.Dispatcher import Dispatcher

@requires(dispatcher='acme.services.Dispatcher')
class CSR(AnnounceableResource):
	""" RemoteCSE resource class."""

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	def initialize(self, pi: str) -> None:
		#self.setAttribute('csi', 'cse', overwrite=False)	# This shouldn't happen
		if self.csi:
			self.setAttribute('ri', originatorToID(self.csi))	# overwrite ri (only after /'s')
			self.setResourceName(originatorToID(self.csi))				# set the resource name to the csi of the remote CSE

		self.setAttribute('rr', False, overwrite=False)
		super().initialize(pi)


	def validate(self, originator: Optional[str]=None, 
					   dct: Optional[JSON]=None, 
					   parentResource: Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)

		# make sure that the poa attribute URIs are normalized
		self._normalizeURIAttribute('poa')


	def childWillBeAdded(self, childResource: Resource, originator: str) -> None:
		super().childWillBeAdded(childResource, originator)

		# Perform checks for <PCH>	
		if childResource.ty == ResourceTypes.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.csi != originator:
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator must be the parent <CSR>'))

			# check that there will only by one PCH as a child
			if self.dispatcher.countDirectChildResources(self.ri, ty=ResourceTypes.PCH) > 0:
				raise BAD_REQUEST(L.logDebug('Only one <PCH> per <CSR> is allowed'))
