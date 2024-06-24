#
#	ACMEContainerUpdate.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Update* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast
import json
from copy import deepcopy

from textual.app import ComposeResult
from textual.containers import Container
from rich.syntax import Syntax
from .ACMEViewResponse import ACMEViewResponse
from .ACMEViewRequest import ACMEViewRequest
from ..etc.Types import Operation, ResponseStatusCode, RequestOptionality, JSON
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.DateUtils import getResourceDate
from ..etc.ACMEUtils import uniqueRI
from ..helpers.TextTools import removeCommentsFromJSON, flattenJSON, parseJSONDecodingError
from ..helpers.ResourceSemaphore import CriticalSection, inCriticalSection
from ..resources.Resource import Resource
from ..runtime import CSE

class ACMEContainerUpdate(Container):

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""
		from ..textui.ACMETuiApp import ACMETuiApp

		super().__init__(id = id)

		self.requestOriginator = CSE.cseOriginator
		"""	The request originator. """

		self.resource:Resource = None
		"""	The resource to delete. """

		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		self.requestView:ACMEViewRequest = ACMEViewRequest(id = 'request-update-request', 
													 	   title = 'UPDATE Request',
													 	   header = 'Add, modify, and remove resource attributes.',
														   originator = self.requestOriginator,
														   buttonLabel = 'UPDATE Resource',
														   callback = self.doUpdate)
		"""	The request view. """

		self.responseView:ACMEViewResponse = ACMEViewResponse(id = 'request-update-response')
		"""	The response view. """



	def compose(self) -> ComposeResult:
		"""	Build the *Update* view.
		"""
		yield self.requestView
		yield self.responseView


	def updateResource(self, resource:Resource) -> None:
		"""	Update the resource to update.

			Args:
				resource:	The resource to update.
		"""
		self.resource = resource

		# Check whether we are currently doing a resource update (below). If so, return and don't update the editor.
		if inCriticalSection('tuiUpdate'):
			return

		_resourceType = self.resource.ty

		# Update the request originator. Important for getting a default request originator
		# self.requestOriginator = self.resource.getOriginator()
		if self.requestOriginator:
			self.requestView.updateOriginator(self.requestOriginator, [CSE.cseOriginator, self.requestOriginator])
		else: # No originator, use CSE originator
			self.requestView.updateOriginator(CSE.cseOriginator, [CSE.cseOriginator])


		# TODO move this to a separate function (also for CREATE later)

		_resourceAttributes:JSON = cast(JSON, self.resource.asDict()[self.resource.tpe])

		_possibleResourceAttributes = deepcopy(self.resource._attributes)

		# Remove attributes that are not allowed to be updated from the resource
		for attr in list(_possibleResourceAttributes):
			_policy = CSE.validator.getAttributePolicy(_resourceType, attr)
			if _policy is None or _policy.optionalUpdate == RequestOptionality.NP:
				_possibleResourceAttributes.pop(attr)
				if attr in _resourceAttributes:
					_resourceAttributes.pop(attr)
			
			# remove to-be-processed attributes that are already in the resource
			elif attr in _resourceAttributes:
				_possibleResourceAttributes.pop(attr)
			
		# dump and format the remaining attributes
		_text = json.dumps({ self.resource.tpe: _resourceAttributes }, indent = 4)

		# add the not-yet present but possible resource attributes in the middle of the resource
		_result = [ f'        // "{attr}": {CSE.validator.getAttributeValueRepresentation(attr, _resourceType)}'
					for attr in _possibleResourceAttributes ]
		_t = _text.split('\n    }')
		_text = _t[0] + '\n\n' + ',\n'.join(_result) + '\n    }\n}'

		self.requestView.resource = _text
		self.responseView.clear()
	

	def doUpdate(self) -> None:
		"""	Handle the *Send UPDATE Request* button event.
		"""
		from .ACMETuiApp import ACMETuiApp

		# get pure JSON text without comments and flattened
		text = flattenJSON(removeCommentsFromJSON(self.requestView.resource))

		# Check the validity of the JSON by trying to parse it
		try:
			jsn = json.loads(text)
		except json.JSONDecodeError as e:
			self.responseView.error(f'JSON Error: {e.msg}\n{parseJSONDecodingError(e)}')
			return

		# Send the UPDATE request and handle the response
		try:			
			# Prepare request structure
			result = CSE.request.handleRequest( {
					'op': Operation.UPDATE,
					'fr': self.requestView.originator,
					'to': self.resource.ri, 
					'rvi': CSE.releaseVersion,
					'rqi': uniqueRI(), 
					'ot': getResourceDate(),
					'pc': jsn,
				})
			if result.rsc != ResponseStatusCode.UPDATED:
				raise ResponseException(result.rsc, result.dbg)
			else:

				# The following is a critical section, because the resource tree has to be updated
				# but we don't want to update the editor. The 'updateResource()' method would do that.
				# There is a check for the critical section in the 'updateResource()' method above.
				_resource = cast(Resource, result.resource)
				with CriticalSection('tuiUpdate', timeout = 0.0):
					self._app.containerTree.updateResource(_resource)
				
				self.responseView.success(Syntax(json.dumps(_resource.asDict(), indent = 4),
									 			 'json', 
												 theme = self._app.syntaxTheme),
										  result.rsc)
				# self.responseView.refresh()
		except ResponseException as e:
			self.responseView.error(e.dbg, e.rsc)
			