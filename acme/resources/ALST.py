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

from ..etc.Types import CSEType
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED 
from ..resources.Resource import Resource
from ..etc.Constants import RuntimeConstants as RC


class ALST(Resource):
	""" AEContactList (ALST) resource type. """
	pass

	# def activate(self, parentResource: Resource, originator: str) -> None:

	# 	# Check if we are running on an INCSE
	# 	if RC.cseType != CSEType.IN:
	# 		raise OPERATION_NOT_ALLOWED('ALST resource type is only allowed on an IN-CSE')
		
	# 	# Add RO attribute to the resource
	# 	self.setAttribute('nic', 0, overwrite=False)

	# 	return super().activate(parentResource, originator)
	# pass
