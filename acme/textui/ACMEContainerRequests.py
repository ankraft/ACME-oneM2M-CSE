#
#	ACMEContainerRequests.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Requests* view for the ACME text UI.
"""

from __future__ import annotations
from typing import Optional, List, cast, Any
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Center
from textual.binding import Binding
from textual.widgets import Static, Label, ListView, ListItem
from textual.widget import Widget
from rich.pretty import Pretty
from rich.syntax import Syntax
from ..etc.Types import JSONLIST, JSON, Operation
from ..etc.ResponseStatusCodes import ResponseStatusCode, isSuccessRSC
from ..etc.DateUtils import toISO8601Date
from ..etc.Utils import reverseEnumerate
from ..services import CSE
from ..helpers.TextTools import commentJson

idRequests = 'requests'


class ACMEContainerRequests(Container):

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idRequests)
		self.tuiApp = tuiApp
		self.requestsView = ACMEViewRequests()


	def compose(self) -> ComposeResult:
		with Container():
			with Vertical(id = 'requests-view'):
				yield self.requestsView


	def on_show(self) -> None:
		self.requestsView.onShow()
		self.requestsView.updateBindings()


class ACMEListItem(ListItem):
	# TODO own module?

	def __init__(self, *children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
		super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
		self._data:Any = None
	



class ACMEViewRequests(Vertical):

	BINDINGS = 	[ Binding('r', 'refresh_requests', 'Refresh'),
				  Binding('D', 'delete_requests', 'Delete ALL Requests', key_display = 'SHIFT+D'),
				  Binding('e', 'enable_requests', ''),
				  Binding('t', 'toggle_list_details', 'List Details'),
				  Binding('ctrl+t', 'toggle_comment_style', 'Comments Style'),
				]

	DEFAULT_CSS = """
#requests-view {
	overflow: auto auto;  
	width: 1fr;
	height: 1fr;
	/* background:red; */
}

#request-list-view {
	/* overflow: auto scroll; */
	width: 1fr;
	height: 1fr;
	/* background:red; */
}

#request-list-header {
	/* overflow: auto hidden; */
	width: 1fr;
	height: 1;
	align-vertical: middle;
	background: $panel;
}

#request-list-list {
	overflow: auto auto;  
	min-width: 100%;
	height: 2fr;
}

#request-list-details-header {
	overflow: auto;
	height: 1;
	align-vertical: middle;
	background: $panel;
}

#request-list-details {
	overflow: auto scroll;
	height: 3fr;
}	

#request-list-request {
	overflow: auto;  
	width: 1fr;
	min-height: 100%;
	padding: 1 1;
}

#request-list-response {
	overflow: auto;  
	width: 1fr;
	min-height: 100%;
	border-left: $panel;
	padding: 1 1;
}


"""


	def __init__(self) -> None:
		super().__init__(id = 'request-list-view')

		self._currentRequests:List[JSON] = None
		self._currentRI:str = None

		# Request List
		self.requestList = ListView(id = 'request-list-list')
		self.listDetails = False

		# Request view: request + response
		self.requestListRequest = Static(id = 'request-list-request')
		self.requestListResponse = Static(id = 'request-list-response')
		self.commentsOneLine = True
		
	
	@property
	def currentRI(self) -> Optional[str]:
		return self._currentRI
	

	@currentRI.setter
	def currentRI(self, ri:str) -> None:
		self._currentRI = ri

		# Change some bindings
		self._bindings.bind('D', 'delete_requests', 'Delete Requests' if ri else 'Delete ALL Requests', key_display = 'SHIFT+D')
		self.updateBindings()

			
	def compose(self) -> ComposeResult:

		# Requests List Header
		with Horizontal(id = 'request-list-header'):
			yield Label(f'    [u b]#[/u b]  -  [u b]Timestamp UTC[/u b]     [u b]Operation[/u b]    [u b]Originator[/u b]                       [u b]Target[/u b]                           [u b]Response Status[/u b]')

		# Request List
		yield self.requestList

		# Details Header
		with Horizontal(id = 'request-list-details-header'):
			with Center():
				yield Label('[u b]Request[/u b]')
			with Center():
				yield Label('[u b]Response[/u b]')

		# Details
		with Horizontal(id = 'request-list-details'):
			yield self.requestListRequest
			yield self.requestListResponse
	

	def onShow(self) -> None:
		self.updateRequests()
		self.requestList.focus()


	async def on_list_view_selected(self, selected:ListView.Selected) -> None:
		self._showRequests(cast(ACMEListItem, selected.item))


	async def on_list_view_highlighted(self, selected:ListView.Highlighted) -> None:
		# self.tuiApp.bell()
		if selected and selected.item:
			self._showRequests(cast(ACMEListItem, selected.item))


	def _showRequests(self, item:ACMEListItem) -> None:
		""" Show the request and response of a request. 

			Args:
				item: The selected request item.
		"""
		# Get the request's json
		jsns = commentJson(self._currentRequests[cast(ACMEListItem, item)._data]['req'], 
					explanations = self.app.attributeExplanations,									# type: ignore [attr-defined]
					getAttributeValueName = CSE.validator.getAttributeValueName,					# type: ignore [attr-defined]
					width = None if self.commentsOneLine else self.requestListRequest.size[0] - 2)	# type: ignore [attr-defined]
		_l1 = jsns.count('\n')
		
		# Add syntax highlighting and explanations, and add to the view
		self.requestListRequest.update(Syntax(jsns, 'json', theme = self.app.syntaxTheme)) # type: ignore [attr-defined]

		# Get the response's json
		jsns = commentJson(self._currentRequests[cast(ACMEListItem, item)._data]['rsp'], 
					explanations = self.app.attributeExplanations,									# type: ignore [attr-defined]
					getAttributeValueName = CSE.validator.getAttributeValueName, 					# type: ignore [attr-defined]
					width = None if self.commentsOneLine else self.requestListRequest.size[0] - 2)	# type: ignore [attr-defined]
		_l2 = jsns.count('\n')

		# Make sure the response has the same number of lines as the request
		# (This is a hack to make sure the separator line covers the entire height of the view)
		if _l1 > _l2:
			jsns += '\n' * (_l1 - _l2)
			
		# Add syntax highlighting and explanations, and add to the view
		self.requestListResponse.update(Syntax(jsns, 'json', theme = self.app.syntaxTheme)) # type: ignore [attr-defined]


	def action_refresh_requests(self) -> None:
		self.updateRequests()


	def action_delete_requests(self) -> None:
		self.deleteRequests()
	

	def action_enable_requests(self) -> None:
		CSE.request.enableRequestRecording = True
		self.updateBindings()


	def action_disable_requests(self) -> None:
		CSE.request.enableRequestRecording = False
		self.updateBindings()
	

	def action_toggle_list_details(self) -> None:
		self.listDetails = not self.listDetails
		self.updateRequests()


	def action_toggle_comment_style(self) -> None:
		self.commentsOneLine = not self.commentsOneLine
		self.updateRequests()


	def updateBindings(self) -> None:
		#CSE.textUI.tuiApp.bell()

		if CSE.request.enableRequestRecording:
			self._bindings.bind('e', 'disable_requests', 'Record Requests: Enabled')
		else:
			self._bindings.bind('e', 'enable_requests', 'Record Requests: Disabled')
		
		# HACK: force footer refresh
		self.app.set_focus(None)
		self.requestList.focus()


	def updateRequests(self) -> None:
			# TODO plantuml?

		def rscFmt(rsc:int) -> str:
			_rsc = ResponseStatusCode(rsc) if ResponseStatusCode.has(rsc) else ResponseStatusCode.UNKNOWN
			# _c = 'green1' if isSuccessRSC(_rsc) else 'red'
			_c = 'green3' if isSuccessRSC(_rsc) else 'red'
			return f'[{_c}]{_rsc.name}[/{_c}]'

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
		CSE.storage.deleteRequests(self._currentRI)
		self.updateRequests()


	def setIndex(self, idx:int) -> None:
		if 0 <= idx < len(self._currentRequests):
			self.requestListRequest.update(Pretty(self._currentRequests[idx]['req']))
			self.requestListResponse.update(Pretty(self._currentRequests[idx]['rsp']))


