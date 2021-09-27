#
#	MgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ManagementObject (base class for specializations)
#

from copy import deepcopy
from ..etc.Types import ResourceTypes as T, JSON
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class MgmtObj(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ]

	def __init__(self, dct:JSON, pi:str, mgd:T, create:bool=False) -> None:
		super().__init__(T.MGMTOBJ, dct, pi, tpe=mgd.tpe(), create=create)
		self.setAttribute('mgd', int(mgd), overwrite=True)

