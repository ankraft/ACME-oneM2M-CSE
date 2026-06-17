#
#	RequestPostProcessingInterceptor.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Interceptor for responses to incoming requests. Responses are intercepted after they are processed by the CSE. 
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from acmecse.runtime.PluginSupport import *
from acmecse.runtime.Logging import Logging as L

if TYPE_CHECKING:
	from acmecse.services.RequestManager import RequestManager

@requires(requestManager='acmecse.services.RequestManager')
@plugin(tags=['acme', 'interceptor'])
class RequestInterceptor(Interceptor):
	"""	Interceptor for responses to incoming requests. Responses are intercepted after they are processed by the CSE.

		This interceptor records the request and its response in the requests database after the request 
		has been processed by the CSE.
	"""

	requestManager: RequestManager = None
	""" Injected RequestManager instance. """


	@intercept(Phase.REQUEST_POST_PROCESSING, Operation.ALL, ResourceTypes.ALL, priority=10)
	def postRequestInterceptor(self, request:CSERequest, response:Result) -> None:
		"""	Post-processing interceptor for incoming requests. 
		
			This interceptor will be called after the request has been processed by the CSE and the 
			response is ready to be sent.

			Args:
				request: The incoming CSERequest object that is being processed.
				response: The Result object that is the response to the request.
		"""
		L.isDebug and L.logDebug('Interception: Request post-processing')

		# Add to requests database
		self.requestManager.recordRequest(request, response)

