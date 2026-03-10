#
#	TSI.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: timeSeriesInstance
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED
from ..etc.ACMEUtils import getAttributeSize
from ..resources.AnnounceableResource import AnnounceableResource


class TSI(AnnounceableResource):

	def initialize(self, pi: str) -> None:
		self.setAttribute('cs', getAttributeSize(self['con']))       # Set contentSize
		super().initialize(pi)


	# Forbid updating
	def update(self, dct: Optional[JSON]=None, 
					 originator: Optional[str]=None, 
					 doValidateAttributes: Optional[bool]=True) -> None:
		raise OPERATION_NOT_ALLOWED('updating TSI is forbidden')

