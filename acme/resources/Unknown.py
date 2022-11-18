#
#	Unknown.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Unknown
#
#	This is the default-capture class for all unknown resources. 
#	This is only for storing the resource, no further processing is done.
#
from __future__ import annotations
from typing import Optional

from ..etc.Types import ResourceTypes, JSON
from ..resources.Resource import Resource


class Unknown(Resource):

	def __init__(self, dct:Optional[JSON], 
					   tpe:Optional[str], 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.UNKNOWN, dct, pi, tpe = tpe, create = create)

