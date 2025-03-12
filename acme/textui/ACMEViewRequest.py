#
#	ACMEViewRequest.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines a view to display requests.
"""

from __future__ import annotations
from typing import cast, Optional, Callable
from copy import deepcopy
import json

from rich.syntax import Syntax
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container
from textual.widgets import Label, Button, TextArea, Select
from textual.widgets.button import ButtonVariant
from textual.binding import Binding

from .ACMEFieldOriginator import ACMEFieldOriginator
from .ACMEContentDialog import ACMEContentDialog
from .ACMEViewResponse import ACMEViewResponse
from ..runtime import CSE
from ..etc.Types import ResourceTypes, JSON, RequestOptionality, Operation, ResponseStatusCode, Result
from ..etc.IDUtils import uniqueRI
from ..etc.RequestUtils import curlFromRequest
from ..etc.Constants import RuntimeConstants as RC
from ..helpers.TextTools import removeCommentsFromJSON, flattenJSON, parseJSONDecodingError
from ..resources.Resource import Resource
from ..resources.Factory import resourceFromDict
from ..runtime.Configuration import Configuration


class ACMETextArea(TextArea):
	"""	An extended text area.
	"""

	BINDINGS = [
		Binding('ctrl+p', 'copy_to_clipboard', 'copy', key_display = 'CTRL-p'),
		Binding('cmd+c', 'copy_to_clipboard'),
		Binding('ctrl+v', 'paste_from_clipboard', 'paste', key_display = 'CTRL-v'),
	]
	"""	The key bindings for the text area. """


	def action_copy_to_clipboard(self) -> None:
		"""	Action callback: Copy the selected text to the clipboard.
		"""
		from ..textui.ACMETuiApp import ACMETuiApp
		cast(ACMETuiApp, self.app).copyToClipboard(self.selected_text)

	
	def action_paste_from_clipboard(self) -> None:
		"""	Action callback: Paste the clipboard content to the cursor position.
		"""
		self.begin_capture_print()
		from ..textui.ACMETuiApp import ACMETuiApp
		v = cast(ACMETuiApp, self.app).pasteFromClipboard()
		v = v if v is not None else ''
		self.replace(
			v,
			self.selection.start,
			self.selection.end,
		)


class ACMEViewRequest(VerticalScroll):
	"""	View to display request.
	"""

	def __init__(self, id:str, 
			  		   title:str,
			  		   header:str, 
					   originator:str,
					   buttonLabel:str, 
					   buttonVariant:Optional[ButtonVariant] = 'primary',
					   callback:Optional[Callable] = None,
					   enableEditor:bool = True,
					   operation:Operation = Operation.CREATE,
					   selectCallback:Optional[Callable] = None,
					   responseView:Optional[ACMEViewResponse] = None
					   ):
		"""	Initialize the view.

			Args:
				id:	The view ID.
				title: The title of the view.
				header: The header text.
				originator: The originator.
				buttonLabel: The label of the button.
				buttonVariant: The button variant.
				callback: The callback for the button action
				enableEditor: Enable the editor.
				operation: The operation for the request.
				selectCallback: The callback for the select change.
				responseView: The response view.
		"""
		super().__init__(id = id, classes = 'request-view')

		self.header = Label(header, classes = 'request-header-label')
		"""	The header label. """

		self.button = Button(buttonLabel, 
					   		 variant = buttonVariant, 
							 id = 'request-button', 
							 classes = 'request-button',
							 disabled = operation == Operation.CREATE)	# start disabled when CREATE operation
		"""	The button to submit the request. """
		
		self.childResources = Select([('None', 0), ('some', 1)], 
							   		 prompt = 'Select resource type', 
									 id = 'request-child-resources-select', 
									 classes = 'request-child-resources-select'	)
		"""	The child resource select view. """

		self.inputOriginator = ACMEFieldOriginator(originator, suggestions = [RC.cseOriginator, originator])
		"""	The input originator. """

		self.resourceTextArea = ACMETextArea('', 
						 	 				 classes = 'request-resource-textarea', 
											 language = 'json' if Configuration.textui_enableTextEditorSyntaxHighlighting else None,
											 soft_wrap = False,
											 tab_behavior = 'indent',
				  							 show_line_numbers = True,
											 disabled = operation == Operation.CREATE,	# start disabled for CREATE operation
											 theme = 'monokai')
		"""	The resource text area. """

		self.border_title = title
		"""	The border title. Inherited from the parent class. """

		self.callback = callback
		"""	The callback for the button action. """

		self.enableEditor = enableEditor
		"""	Enable the editor. """

		self.operation = operation
		"""	The operation for the request. """

		self.selectCallback = selectCallback
		"""	The callback for the select change. """

		self.responseView = responseView
		"""	The response view. """


	def compose(self) -> ComposeResult:
		"""	Compose the view.

			Yields:
				The view content.
		"""

		with Horizontal(classes = 'request-header'):
			yield self.header
			yield self.button

		if self.operation == Operation.CREATE:
			with Horizontal(classes = 'request-child-resources-container'):
				yield Label('[b]Resource type[/b]', classes = 'request-child-resources-label')
				yield self.childResources

		with Container(classes = 'request-originator'):
			yield self.inputOriginator
		if self.enableEditor:
			yield self.resourceTextArea

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """



	@property
	def originator(self) -> str:
		"""	Return the originator.

			Returns:
				The originator.
		"""
		return self.inputOriginator.value


	def updateOriginator(self, originator:str, suggestions:list[str] = []) -> None:
		"""	Update the originator.

			Args:
				originator: The originator.
				suggestions: The suggestions.
		"""
		self.inputOriginator.update(originator, suggestions = suggestions)


	@property
	def resourceText(self) -> str:
		"""	Return the resource text.

			Returns:
				The resource text.
		"""
		return self.resourceTextArea.text
	

	@resourceText.setter
	def resourceText(self, resource:str) -> None:
		"""	Set the resource text.

			Args:
				resource: The resource text.
		"""
		self.resourceTextArea.text = resource

	
	@property
	def childResourceType(self) -> Optional[ResourceTypes]:
		"""	Return the selected child resource type.

			Returns:
				The selected child resource type.
		"""
		if self.childResources.is_blank():
			return None									# type: ignore [return-value]
		return ResourceTypes(self.childResources.value)	# type: ignore [arg-type]
	

	@on(Button.Pressed, '#request-button')
	def buttonExecute(self) -> None:
		"""	Execute the callback.
		"""
		if self.callback:
			self.callback()


	@on(Select.Changed)
	def selectChanged(self, event: Select.Changed) -> None:
		"""	Handle the select change.

			Args:
				event: The select change event.
		"""
		if self.selectCallback:
			self.selectCallback(event.value)
		if self.operation == Operation.CREATE:
			self.resourceTextArea.disabled = not self.childResourceType
		self.button.disabled = not self.childResourceType
		if self.responseView:
			self.responseView.clear()


	def updateResourceView(self, 
						   resource:Resource, 
						   resourceType:ResourceTypes,
						   requestOriginator:Optional[str] = None) -> None:
		"""	Update the selected resource.

			Args:
				resource:	The selected resource.
		"""

		# Update the request originator. Important for getting a default request originator
		if requestOriginator:
			self.updateOriginator(requestOriginator, [RC.cseOriginator, requestOriginator])
		else: # No originator, use CSE originator
			self.updateOriginator(RC.cseOriginator, [RC.cseOriginator])

		_resourceAttributes:JSON = {}
		match self.operation:
			case Operation.CREATE:
				resource = None
				if resourceType is not None:
					# Create a template resource
					resource = resourceFromDict(ty = resourceType, template = True)
			
			case _:
				# Copy the original an used attributes 
				_resourceAttributes = cast(JSON, resource.asDict()[resource.typeShortname])


		if resource is not None:
			_possibleResourceAttributes = deepcopy(resource._attributes)

			# Remove attributes that are not allowed to be updated from the resource
			for attr in list(_possibleResourceAttributes):
				_policy = CSE.validator.getAttributePolicy(resourceType, attr)
				if _policy is None or \
					(self.operation == Operation.CREATE and _policy.optionalCreate == RequestOptionality.NP) or \
					(self.operation == Operation.UPDATE and _policy.optionalUpdate == RequestOptionality.NP):

					_possibleResourceAttributes.pop(attr)
					if attr in _resourceAttributes:
						_resourceAttributes.pop(attr)
				
				elif self.operation == Operation.CREATE and _policy.optionalCreate == RequestOptionality.M:
					# set the default value
					_resourceAttributes[attr] = None
				
				# remove to-be-processed attributes that are already in the resource
				elif attr in _resourceAttributes:
					_possibleResourceAttributes.pop(attr)
				
			# dump and format the remaining attributes
			_text = json.dumps({ resource.typeShortname: _resourceAttributes }, indent = 4)

			# Replace all None values with an indication that the value is not yet present and must be added
			_text = _text.replace('null', '... // mandatory attribute')
		
			# add the not-yet present but possible resource attributes in the middle of the resource
			_result = [ f'        // "{attr}": {CSE.validator.getAttributeValueRepresentation(attr, resourceType)}'
						for attr in _possibleResourceAttributes ]
			
			if self.operation == Operation.CREATE:
				_t = _text.split('}\n}')
			else:
				_t = _text.split('\n    }')
			_text = _t[0] + '\n\n' + ',\n'.join(_result) + '\n    }\n}'

		else:
			_text = ''

		self.resourceText = _text


	def prepareRequest(self, targetResource:Resource) -> Optional[JSON]:
		"""	Prepare the request for an operation.

			Args:
				targetResource: The resource to target.

			Returns:
				The request structure.
		"""

		match self.operation:
			case Operation.CREATE:
				# get pure JSON text without comments and flattened
				text = flattenJSON(removeCommentsFromJSON(self.resourceText))
				# Check the validity of the JSON by trying to parse it
				jsn = json.loads(text)
				# Create and return the request structure
				return {
						'op': self.operation,
						'fr': self.originator,
						'ty': self.childResourceType.value,
						'to': targetResource.ri, 
						'csz': 'application/json',
						'rvi': RC.releaseVersion,
						'rqi': uniqueRI(), 
						'pc': jsn,
					}
			case Operation.UPDATE:
				# get pure JSON text without comments and flattened
				text = flattenJSON(removeCommentsFromJSON(self.resourceText))
				# Check the validity of the JSON by trying to parse it
				jsn = json.loads(text)
				# Create and return the request structure
				return {
						'op': Operation.UPDATE,
						'fr': self.originator,
						'to': targetResource.ri, 
						'csz': 'application/json',
						'rvi': RC.releaseVersion,
						'rqi': uniqueRI(), 
						'pc': jsn,
					}
			case Operation.DELETE:
				# Create and return the request structure
				return {
						'op': self.operation,
						'fr': self.originator,
						'to': targetResource.ri, 
						'rvi': RC.releaseVersion,
						'rqi': uniqueRI(), 
					}
		
			case _:
				return None


	def runRequest(self, resource:Resource) -> Optional[Result]:
		"""	Run the request on a resource.
		
			Args:
				resource: The resource to target.
				
			Returns:
				The result.
		"""
		# Send the request and handle the response

		try:
			# Prepare request structure
			if not (_r := self.prepareRequest(resource)):
				return None
			result = CSE.request.handleRequest(_r)

			# handle the response
			match self.operation:
				case Operation.CREATE:
					if result.rsc != ResponseStatusCode.CREATED:
						if self.responseView:
							self.responseView.error(result.dbg, result.rsc, 'CREATE Resource - ERROR')
						return None
					self._app.showNotification(f'Resource {result.resource["ri"]} created', 'CREATE Resource', 'information')

				case Operation.UPDATE:
					if result.rsc != ResponseStatusCode.UPDATED:
						if self.responseView:
							self.responseView.error(result.dbg, result.rsc, 'UPDATE Resource - ERROR')
						return None
					self._app.showNotification(f'Resource {resource.ri} updated', 'UPDATE Resource', 'information')
				
				case Operation.DELETE:
					if result.rsc != ResponseStatusCode.DELETED:
						if self.responseView:
							self.responseView.error(result.dbg, result.rsc, 'DELETE Resource - ERROR')
						return None
					self._app.showNotification(f'Resource {resource.ri} deleted', 'DELETE Resource', 'information')

			# print the result resource
			if self.operation in ( Operation.UPDATE, Operation.CREATE ) and self.responseView:
				
				from ..helpers.TextTools import commentJson

				jsns = commentJson(result.resource.asDict(sort = True), 
									explanations = self.app.attributeExplanations,	# type: ignore [attr-defined]
									getAttributeValueName = lambda a, v: CSE.validator.getAttributeValueName(a, v, result.resource.ty if result.resource else None))	# type: ignore [attr-defined]
				self.responseView.success(Syntax(jsns,
												'json', 
												theme = self._app.syntaxTheme),
										result.rsc)


		except json.JSONDecodeError as e:
			if self.responseView:
				self.responseView.error(f'JSON Error: {e.msg}\n{parseJSONDecodingError(e)}')
			return None

		return result
		

	def showCurlDialog(self, resource:Resource) -> None:
		"""	Show the current request as cURL command.
		"""
		try:
			self.app.push_screen(
				ACMEContentDialog(
					curlFromRequest(self.prepareRequest(resource)),
					'cURL Command'))
		except json.JSONDecodeError as e:
			if self.responseView:
				self.responseView.error(f'JSON Error: {e.msg}\n{parseJSONDecodingError(e)}')

