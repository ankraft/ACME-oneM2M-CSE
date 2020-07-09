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
#from .Resource import *



class AnnouncedResource(Resource):

	def __init__(self, ty:T, jsn: dict, pi:str = None, create:bool = False) -> None:
		super().__init__(ty, jsn, pi, create=create, isAnnouncedResource=True)

		# TODO Link attribute
		# TODO registrationStatus (optiona)



		if self.json is not None:
			self.setAttribute('aei', Utils.uniqueAEI(), overwrite=False)
			self.setAttribute('rr', False, overwrite=False)





	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.ACP,
									   T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.SUB
									 ])