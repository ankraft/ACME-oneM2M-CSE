#
#	VirtualResource.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This module implements the base class for all oneM2M virtual resource types. """

from __future__ import annotations

from ..etc.Types import ResourceTypes, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, NOT_FOUND
from ..resources.Resource import Resource
from ..services import CSE

# TODO DOCs

class VirtualResource(Resource):
	""" Base class for all oneM2M virtual resource types. 
		It adds methods for virtual resources.
	"""

	def retrieveLatestOldest(self, request:CSERequest, 
								   originator:str, 
								   typ:ResourceTypes, 
								   oldest:bool) -> Result:

		if not (resource := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, typ, oldest = oldest)):
			raise NOT_FOUND(f'no instance for <{"oldest" if oldest else "latest"}>')

		# Take the resource, either a FCIN or self and check whether a blocking RETRIEVE
		# is necessary
		# EXPERIMENTAL
		CSE.notification.checkPerformBlockingRetrieve(resource, 
													  request, 
													  finished = lambda: self.dbReloadDict())

		# Then retrieve the latest instance resource again(!) because it might have changed during the 
		# blocking RETRIEVE
		if not (resource := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, typ, oldest = oldest)):
			raise NOT_FOUND(f'no instance for <{"oldest" if oldest else "latest"}>')
		
		# Do again some checks with the final resource, but no subscription checks! (we did this already)
		resource.willBeRetrieved(originator, request, subCheck = False)
		
		return Result(rsc = ResponseStatusCode.OK, resource = resource)

