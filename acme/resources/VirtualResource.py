#
#	VirtualResource.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This module implements the base class for all oneM2M virtual resource types. """

from __future__ import annotations

from ..etc.Types import ResourceTypes, Result, ResponseStatusCode, CSERequest
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
			return Result.errorResult(rsc = ResponseStatusCode.notFound, dbg = f'no instance for <{"oldest" if oldest else "latest"}>')

		# Take the resource, either a FCIN or self and check whether a blocking RETRIEVE
		# is necessary
		# EXPERIMENTAL
		if not (res := CSE.notification.checkPerformBlockingRetrieve(resource, 
																	 request, 
																	 finished = lambda: self.dbReloadDict())).status:
			return res

		# Then retrieve the latest instance resource again(!) because it might have changed during the 
		# blocking RETRIEVE
		if not (resource := CSE.dispatcher.retrieveLatestOldestInstance(self.pi, typ, oldest = oldest)):
			return Result.errorResult(rsc = ResponseStatusCode.notFound, dbg = f'no instance for <{"oldest" if oldest else "latest"}>')
		
		# Do again some checks with the final resource, but no subscription checks! (we did this already)
		if not (res := resource.willBeRetrieved(originator, request, subCheck = False)).status:
			return res
		
		return Result(status = True, rsc = ResponseStatusCode.OK, resource = resource)

