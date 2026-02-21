#
#	ALST.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: AEContactList
#

""" AEContactList (ALST) resource type. """

from __future__ import annotations
from typing import Optional, Tuple

from ..etc.Types import CSEType, EvalMode, JSON, Permission, Operation
from ..etc.ResponseStatusCodes import ResponseException, OPERATION_NOT_ALLOWED 
from ..etc.ACMEUtils import riFromID, compareIDs
from ..helpers.TextTools import findXPath
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.Constants import RuntimeConstants as RC


class ALST(Resource):
	""" AEContactList (ALST) resource type. """

	def activate(self, parentResource: Resource, originator: str) -> None:

		# Check if we are running on an INCSE
		if RC.cseType != CSEType.IN:
			raise OPERATION_NOT_ALLOWED('ALST resource type is only allowed on an IN-CSE')
		
		# Add RO attribute to the resource
		self.setAttribute('nic', 0, overwrite=False)
		
		return super().activate(parentResource, originator)
	pass
