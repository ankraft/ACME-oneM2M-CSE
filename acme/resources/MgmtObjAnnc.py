#
#	MgmtObjAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MgmtObj : Announceable variant
#

from copy import deepcopy
from ..etc.Types import ResourceTypes as T, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *


class MgmtObjAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ]


	def __init__(self, dct:JSON, pi:str, mgd:T, create:bool = False) -> None:
		# super().__init__(T.MGMTOBJAnnc, dct, pi, tpe = f'{mgd.tpe()}A', create = create)
		super().__init__(T.MGMTOBJAnnc, dct, pi, tpe = mgd.announced().tpe(), create = create)
		self.setAttribute('mgd', int(mgd), overwrite = True)

