#
#	AnnounceableResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announceable resources
#


from .Resource import *
import Utils
from Types import ResourceTypes as T
from Validator import addPolicy


class AnnounceableResource(Resource):

	def __init__(self, ty:Union[T, int], jsn:dict = None, pi:str = None, tpe:str = None, create:bool = False, inheritACP:bool = False, readOnly:bool = False, rn:str = None, attributePolicies:dict = None, isVirtual:bool = False) -> None:
		super().__init__(ty, jsn, pi, tpe=tpe, create=create, inheritACP=inheritACP, readOnly=readOnly, rn=rn, attributePolicies=attributePolicies, isVirtual=isVirtual)

		# # Indicate whether this is an announced resource
		# if isAnnouncedResource:
		# 	self.setAttribute(self._isAnnounced, isAnnouncedResource)



	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		# special case for FCNT, FCI
		if (additionalAttributes := CSE.validator.getAdditionalAttributesFor(self.tpe)) is not None:
			policies = addPolicy(self.resourceAttributePolicies.copy(), additionalAttributes)
			return super()._createAnnouncedJSON(policies), C.rcOK, None
		# Normal behaviour for other resources
		return super()._createAnnouncedJSON(self.resourceAttributePolicies), C.rcOK, None
