#
#	ACMEContainerRequests.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Requests* view for the ACME text UI.
"""

from __future__ import annotations
import json

from typing import Optional, List, cast, Any
from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center, VerticalScroll
from textual.binding import Binding
from textual.widgets import Static, Label, ListView, ListItem
from textual.widget import Widget
from rich.pretty import Pretty
from rich.syntax import Syntax
from ..etc.Types import JSONLIST, JSON, Operation
from ..etc.ResponseStatusCodes import ResponseStatusCode, isSuccessRSC
from ..etc.DateUtils import toISO8601Date
from ..etc.Utils import reverseEnumerate
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..helpers.TextTools import commentJson, limitLines

class ACMEContainerRequests(Vertical):
	"""	Requests view for the ACME text UI.
	"""

	def __init__(self, id:str) -> None:
		""" Initialize the Requests view.

			Args:
				id: The ID of the view.
		"""
		super().__init__(id = id)
		self._requestsView = ACMEViewRequests(id = 'requests-view')
		"""	The requests view. """

	def compose(self) -> ComposeResult:
		""" Compose the view.

			Yields:
				The widgets of the view.
		"""
		yield self._requestsView


	def on_show(self) -> None:
		""" Called when the view is shown.
		"""
		self.requestsView.onShow()
		self.requestsView.updateBindings()


	@property
	def requestsView(self) -> ACMEViewRequests:
		""" The requests view.

			Returns:
				The requests view.
		"""
		return self._requestsView


class ACMEListItem(ListItem):
	"""	Generic list item for the ACME text UI.
	"""

	# TODO own module?

	def __init__(self, *children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
		"""	Initialize the list item.

			Args:
				children: The children of the list item.
				name: The name of the list item.
				id: The ID of the list item.
				classes: The classes of the list item.
				disabled: Whether the list item is disabled.
		"""
		super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
		self._data:Any = None
		"""	The data of the list item. """

class ACMEViewRequests(Vertical):
	"""	View to show the requests in the ACME text UI.
	"""

	BINDINGS = 	[ Binding('r', 'refresh_requests', 'Refresh'),
				  Binding('D', 'delete_requests', 'Delete ALL Requests', key_display = 'SHIFT+D'),
				  Binding('e', 'enable_requests', ''),
				  Binding('t', 'toggle_list_details', 'List Details'),
				  Binding('ctrl+t', 'toggle_comment_style', 'Comments Style'),
				]
	"""	The key bindings for the view. """


	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id: The ID of the view.
		"""
		super().__init__(id = id)

		self._currentRequests:List[JSON] = None
		"""	The current requests. """

		self._currentRI:str = None
		"""	The current resource ID. """

		self.currentRequest:JSON = None
		"""	The current request. """

		self.currentResponse:JSON = None
		"""	The current response. """

		self.listDetails = False
		"""Show list details."""

		self.commentsOneLine = True
		"""Show comments in requests and responses in one line."""

		# Some resources upfront
		self._requestListList = ListView(id = 'request-list-list')
		"""	The list of requests view. """
		self._requestListRequest = Static(id = 'request-list-request')
		"""	The request view. """

		self._requestListResponse = Static(id = 'request-list-response')
		"""	The response view. """

	
	@property
	def currentRI(self) -> Optional[str]:
		"""	The current resource ID.

			Returns:
				The current resource ID.
		"""
		return self._currentRI
	

	@currentRI.setter
	def currentRI(self, ri:str) -> None:
		"""	Set the current resource ID.

			Args:
				ri: The resource ID.
		"""
		self._currentRI = ri

		# Change some bindings
		self._bindings.bind('D', 'delete_requests', 'Delete Requests' if ri else 'Delete ALL Requests', key_display = 'SHIFT+D')
		self.updateBindings()


	@property
	def requestList(self) -> ListView:
		"""	The view for the list of requests.

			Returns:
				The list of requests.
		"""
		return self._requestListList


	@property
	def requestListRequest(self) -> Static:
		"""	The view for the list of requests.

			Returns:
				The view for the list of requests.
		"""
		return self._requestListRequest


	@property
	def requestListResponse(self) -> Static:
		"""	The view for the list of responses.

			Returns:
				The view for the list of responses.
		"""
		return self._requestListResponse

			
	def compose(self) -> ComposeResult:
		"""	Compose the view.

			Yields:
				The widgets of the view.
		"""

		# Requests List Header
		with Horizontal(id = 'request-list-header'):
			yield Label(f'    [u b]#[/u b]  -  [u b]Timestamp UTC[/u b]     [u b]Operation[/u b]    [u b]Originator[/u b]                       [u b]Target[/u b]                           [u b]Response Status[/u b]     ')

		# Request List
		yield self._requestListList

		# Details
		with Horizontal(id = 'request-list-details'):
			with (_c := VerticalScroll(classes = 'request-response')):
				_c.border_title = 'Request'
				yield self._requestListRequest
			with (_c := VerticalScroll(classes = 'request-response')):
				_c.border_title = 'Response'
				yield self._requestListResponse

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

	

	def onShow(self) -> None:
		""" Called when the view is shown.
		"""
		self.updateRequests()
	# 	self.requestList.focus()
		self.requestList.index = 0
	# 	self.requestList.action_select_cursor()



	def on_click(self, event:events.Click) -> None:
		"""Handle Click events. Copy the request or response to the clipboard.

			Args:
				event: The Click event.
		"""

		if self.currentRequest:
			match self.screen.get_widget_at(event.screen_x, event.screen_y)[0]:
				case self.requestListRequest:
					v = json.dumps(self.currentRequest, indent = 2)
					t = 'Request Copied'
				case self.requestListResponse:
					v = json.dumps(self.currentResponse, indent = 2)
					t = 'Response Copied'
				case _:
					return
			if self._app.copyToClipboard(v):
				self._app.showNotification(limitLines(v, 5), t, 'information')


	async def on_list_view_selected(self, selected:ListView.Selected) -> None:
		""" Handle the selection of a request in the list.
		
			Args:
				selected: The selected request.
		"""
		self._showRequests(cast(ACMEListItem, selected.item))


	async def on_list_view_highlighted(self, selected:ListView.Highlighted) -> None:
		""" Handle the highlighting of a request in the list.

			Args:
				selected: The highlighted request.
		"""
		# self.tuiApp.bell()
		if selected and selected.item:
			self._showRequests(cast(ACMEListItem, selected.item))


	def _showRequests(self, item:ACMEListItem) -> None:
		""" Show the request and response of a request. 

			Args:
				item: The selected request item.
		"""
		type = 'json'

		if not len(self._currentRequests):
			self.currentRequest = None
			return
		
		# Get the request's json
		self.currentRequest = self._currentRequests[cast(ACMEListItem, item)._data]['req']
		jsns = commentJson(	self.currentRequest, 
							explanations = self.app.attributeExplanations,									# type: ignore [attr-defined]
							getAttributeValueName = CSE.validator.getAttributeValueName,					# type: ignore [attr-defined]
							width = None if self.commentsOneLine else self.requestListRequest.size[0] - 2)	# type: ignore [attr-defined]
		if len(jsns) > Configuration.textui_maxRequestSize:
			jsns = 'Request is too large to display'
			type = 'text'

		# Add syntax highlighting and explanations, and add to the view
		self.requestListRequest.update(Syntax(jsns, type, theme = self.app.syntaxTheme)) # type: ignore [attr-defined]

		# Get the response's json
		self.currentResponse = self._currentRequests[cast(ACMEListItem, item)._data]['rsp']
		jsns = commentJson(	self.currentResponse, 
							explanations = self.app.attributeExplanations,									# type: ignore [attr-defined]
							getAttributeValueName = CSE.validator.getAttributeValueName, 					# type: ignore [attr-defined]
							width = None if self.commentsOneLine else self.requestListRequest.size[0] - 2)	# type: ignore [attr-defined]
		if len(jsns) > Configuration.textui_maxRequestSize:
			jsns = 'Response is too large to display'
			type = 'text'
		_l2 = jsns.count('\n')

		# Add syntax highlighting and explanations, and add to the view
		self.requestListResponse.update(Syntax(jsns, type, theme = self.app.syntaxTheme)) # type: ignore [attr-defined]


	def action_refresh_requests(self) -> None:
		""" Refresh the requests.
		"""
		self.updateRequests()


	def action_delete_requests(self) -> None:
		""" Delete the requests.
		"""
		self.deleteRequests()
	

	def action_enable_requests(self) -> None:
		""" Enable request recording.
		"""
		CSE.request.enableRequestRecording = True
		self.updateBindings()


	def action_disable_requests(self) -> None:
		""" Disable request recording.
		"""
		CSE.request.enableRequestRecording = False
		self.updateBindings()
	

	def action_toggle_list_details(self) -> None:
		""" Toggle the list details.
		"""
		self.listDetails = not self.listDetails
		self.updateRequests()


	def action_toggle_comment_style(self) -> None:
		""" Toggle the comment style.
		"""
		self.commentsOneLine = not self.commentsOneLine
		self.updateRequests()


	def updateBindings(self) -> None:
		""" Update the bindings.
		"""
		#CSE.textUI.tuiApp.bell()

		if CSE.request.enableRequestRecording:
			self._bindings.bind('e', 'disable_requests', 'Record Requests: Enabled')
		else:
			self._bindings.bind('e', 'enable_requests', 'Record Requests: Disabled')
		
		# HACK: force footer refresh
		self.app.set_focus(None)
		self.requestList.focus()


	def updateRequests(self) -> None:
		""" Update the requests.
		"""
			# TODO plantuml?

		def rscFmt(rsc:int) -> str:
			"""	Format the response status code.
			
				Args:
					rsc: The response status code.

				Returns:
					The formatted response status code.
			"""
			
			_rsc = ResponseStatusCode(rsc) if ResponseStatusCode.has(rsc) else ResponseStatusCode.UNKNOWN
			_c = 'green3' if isSuccessRSC(_rsc) else 'red'
			return f'[{_c}]{_rsc.name:30.30}[/{_c}]'

		self.requestList.clear()
		self.requestListRequest.update()
		self.requestListResponse.update()

		self._currentRequests = cast(JSONLIST, CSE.storage.getRequests(self._currentRI, sortedByOt = True))

		# Add the requests to the list in reverse order
		for i, r in reverseEnumerate(self._currentRequests):
			_ts = toISO8601Date(r["ts"], readable = True).split('T')
			_out = r['out']
			if _out:
				_to = r['req'].get('to', '')
			else:
				_to = r.get('ri', '')
			# _to = _to if _to else ''
			_srn = r.get('srn', '')
			# _srn = _srn if _srn else ''
			match self.listDetails:
				case True:
					_l = ACMEListItem(Label(f' {i:4}  -  {_ts[1]}   {Operation(r["op"]).name:10.10}   {str(r.get("org", "")):30.30}   {str(_to):30.30}   {rscFmt(r["rsc"])}\n          [dim]{_ts[0]}[/dim]                                                      [dim]{_srn}[/dim]'))
				case False:
					_l = ACMEListItem(Label(f' {i:4}  -  {_ts[1]}   {Operation(r["op"]).name:10.10}   {str(r.get("org", "")):30.30}   {str(_to):30.30}   {rscFmt(r["rsc"])}'))
				
			_l._data = i
			if r['out']:
				_l.set_class(True, '--outgoing')
			self.requestList.append(_l)
			# self.requestList.append(_l := ACMEListItem(
			# 	Label(f' {i:4}  -  {_ts[1]}   {Operation(r["op"]).name:10.10}   {str(r.get("org", "")):30.30}   {str(_to):30.30}   {rscFmt(r["rsc"])}\n          [dim]{_ts[0]}[/dim]                                                      [dim]{_srn}[/dim]')))


	def deleteRequests(self) -> None:
		""" Delete the requests from the storage.
		"""
		CSE.storage.deleteRequests(self._currentRI)
		self.updateRequests()


	# def setIndex(self, idx:int) -> None:
	# 	""" Set the index of the request list.

	# 		Args:
	# 			idx: The index to set.
	# 	"""
	# 	if 0 <= idx < len(self._currentRequests):
	# 		self.requestListRequest.update(Pretty(self._currentRequests[idx]['req']))
	# 		self.requestListResponse.update(Pretty(self._currentRequests[idx]['rsp']))
