#
#	AnnouncedResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announced resources
#

from .Resource import *
from Types import ResourceTypes as T, JSON, AttributePolicies


class AnnouncedResource(Resource):

	def __init__(self, ty:T, dct:JSON, pi:str=None, tpe:str=None, create:bool=False, attributePolicies:AttributePolicies=None, isRemote:bool=False) -> None:
		super().__init__(ty, dct, pi, tpe=tpe, create=create, attributePolicies=attributePolicies, isAnnounced=True, isRemote=isRemote)
