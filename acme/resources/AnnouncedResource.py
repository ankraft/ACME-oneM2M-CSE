#
#	AnnouncedResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announced resources
#

from .Resource import *
import Utils
from Types import ResourceTypes as T


class AnnouncedResource(Resource):

	def __init__(self, ty:T, jsn: dict, pi:str = None, create:bool = False) -> None:
		super().__init__(ty, jsn, pi, create=create, isAnnouncedResource=True)

