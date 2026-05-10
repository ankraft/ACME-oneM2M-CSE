#
#	NOD.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Node
#

from __future__ import annotations

from typing import TYPE_CHECKING

from ..etc.IDUtils import uniqueID
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..resources.Resource import Resource
	from ..services.Dispatcher import Dispatcher


# TODO Support cmdhPolicy
# TODO Support storage


@requires(dispatcher='acme.services.Dispatcher')
class NOD(AnnounceableResource):

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	def initialize(self, pi: str) -> None:
		self.setAttribute('ni', uniqueID(), overwrite=False)
		super().initialize(pi)


	def deactivate(self, originator: str, parentResource: Resource) -> None:
		super().deactivate(originator, parentResource)

		# Remove self from all hosted AE's (their node links)
		if not self['hael']:
			return
		ri = self['ri']
		for ae in self['hael']:
			self._removeNODfromAE(ae, ri)


	def _removeNODfromAE(self, aeRI: str, ri: str) -> None:
		""" Remove NOD.ri from AE node link. """
		if aeResource := self.dispatcher.retrieveResource(aeRI):
			if (nl := aeResource.nl) and isinstance(nl, str) and ri == nl:
				aeResource.delAttribute('nl')
				aeResource.dbUpdate(True)

