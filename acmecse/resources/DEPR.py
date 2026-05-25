#
#	DEPR.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Dependency
#
""" Dependency (DEPR) resource type. """

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import JSON
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST, NOT_IMPLEMENTED
from ..helpers.PluginManager import requires
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource

if TYPE_CHECKING:
	from acmecse.plugins.services.ActionManager import ActionManager


@requires(actionManager='acmecse.plugins.services.ActionManager', required=False)
class DEPR(AnnounceableResource):
	""" Dependency (DEPR) resource type. """

	actionManager: ActionManager = None
	"""	Injected ActionManager instance. """

	def activate(self, parentResource: Resource, originator: str) -> None:

		super().activate(parentResource, originator)

		# Check that the evalCriteria and target resources are correct and accessible
		if not self.actionManager:
			raise NOT_IMPLEMENTED(L.logWarn('ActionManager is disabled, cannot check evalCriteria'))
		try:
			self.actionManager.checkEvalCriteria(self.evc, self.rri, originator)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)


	def update(self, dct: JSON=None, 
					 originator: Optional[str]=None,
					 doValidateAttributes: Optional[bool]=True) -> None:

		# get new or old rri and evc
		rri = self.getFinalResourceAttribute('rri', dct)
		evc = self.getFinalResourceAttribute('evc', dct)

		# Check that the evalCriteria and target resources are correct and accessible
		# Check the evc only if the evc attribute is present in the update request
		try:
			if not self.actionManager:
				raise NOT_IMPLEMENTED(L.logWarn('ActionManager is disabled, cannot check evalCriteria'))
			self.actionManager.checkEvalCriteria(evc, rri, originator, 'evc' in dct)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)

		super().update(dct, originator, doValidateAttributes)