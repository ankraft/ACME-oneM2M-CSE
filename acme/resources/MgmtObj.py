#
#	MgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" ManagementObject (MgmtObj) resource type. """

from __future__ import annotations

from ..etc.Types import ResourceTypes
from ..resources.AnnounceableResource import AnnounceableResource


class MgmtObj(AnnounceableResource):
	""" ManagementObject (MgmtObj) resource type. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SMD, 
								   ResourceTypes.SUB ]
	""" The allowed child-resource types. """

