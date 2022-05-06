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

from ..etc.Types import ResourceTypes as T, JSON
from ..resources.Resource import Resource


class Unknown(Resource):

	def __init__(self, dct:JSON, tpe:str, pi:str = None, create:bool = False) -> None:
		super().__init__(T.UNKNOWN, dct, pi, tpe = tpe, create = create)

