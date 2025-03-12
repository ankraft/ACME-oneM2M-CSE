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

	resourceType = ResourceTypes.UNKNOWN
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	def __init__(self, dct:Optional[JSON], typeShortname:Optional[str], create:Optional[bool] = False) -> None:
		self.typeShortname = typeShortname
		super().__init__(dct, create = create)

