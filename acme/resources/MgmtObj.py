#
#	MgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ManagementObject (base class for specializations)
#

from __future__ import annotations

from ..etc.Types import ResourceTypes
from ..resources.AnnounceableResource import AnnounceableResource


class MgmtObj(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.SMD, 
								   ResourceTypes.SUB ]

