#
#	ALPC.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: AEContactListPerCSE
#

""" AEContactListPerCSE (ALPC) resource type. """

from __future__ import annotations

from ..etc.Types import CSEType
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED 
from ..resources.Resource import Resource
from ..etc.Constants import RuntimeConstants as RC


class ALPC(Resource):
	""" AEContactListPerCSE (ALPC) resource type. """

	# def activate(self, parentResource: Resource, originator: str) -> None:

	# 	# Check if we are running on an INCSE
	# 	if RC.cseType != CSEType.IN:
	# 		raise OPERATION_NOT_ALLOWED('ALPC resource type is only allowed on an IN-CSE')
		
	# 	return super().activate(parentResource, originator)
	pass


# Update. check if AE-IDList is empty, if yes, remove attribute