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
from ..etc.Types import JSONLIST, JSON, Operation
from ..etc.ResponseStatusCodes import ResponseStatusCode, isSuccessRSC
from ..etc.DateUtils import toISO8601Date
from ..services import CSE

idRequests = 'requests'


class ACMEContainerRequests(Container):

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idRequests)
		self.tuiApp = tuiApp
		self.requestsView = ACMEViewRequests()


	def compose(self) -> ComposeResult:
		yield Container(
			Vertical(self.requestsView, id = 'requests-view')
		)


	async def onShow(self) -> None:
		await self.requestsView.onShow()



class ACMEListItem(ListItem):
	# TODO own module?
	def __init__(self, *children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
		super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
		self._data:Any = None



class ACMEViewRequests(Vertical):

	BINDINGS = 	[ Binding('r', 'refresh_requests', 'Refresh Requests'),
				  Binding('D', 'delete_requests', 'Delete ALL Requests', key_display = 'SHIFT+D')]


	def __init__(self) -> None:
		super().__init__(id = 'request-list-view')

		self._currentRequests:List[JSON] = None
		self._currentRI:str = None

		# Request list view : header + list
		self.requestListHeader = Label(f'    [u b]#[/u b]  -  [u b]Timestamp[/u b]         [u b]Target[/u b]                      [u b]Originator[/u b]                  [u b]Operation[/u b]    [u b]Response Status[/u b]', 
									   id = 'request-list-header')
		self.requestListHeader.styles.height = 2
		self.requestList = ListView(id = 'request-list-list')

		# Request view: request + response

		self.requestListRequest = Static(id = 'request-list-request', expand = True)
		self.requestListResponse = Static(id = 'request-list-response', expand = True)
		self.requestListDetailsHeader = Horizontal(Center(Label('[u b]Request[/u b]')), 
												   Center(Label('[u b]Response[/u b]')),
												   id = 'request-list-details-header')
		self.requestListDetails = Horizontal(self.requestListRequest,
											 self.requestListResponse,
											 id = 'request-list-details')
		
	
	@property
	def currentRI(self) -> Optional[str]:
		return self._currentRI
	

	@currentRI.setter
	def currentRI(self, ri:str) -> None:
		self._currentRI = ri

		# Change the "delete" binding accordingly (all or one)
		self._bindings.bind('D', 'delete_requests', 'Delete Requests' if ri else 'Delete ALL Requests', key_display = 'SHIFT+D')

							
	def compose(self) -> ComposeResult:
		yield self.requestListHeader
		yield self.requestList
		yield self.requestListDetailsHeader
		yield self.requestListDetails
	

	async def onShow(self) -> None:
		self.updateRequests()
		self.requestList.focus()


	async def on_list_view_selected(self, selected:ListView.Selected) -> None:
		self.requestListRequest.update(Pretty(self._currentRequests[cast(ACMEListItem, selected.item)._data]['req']))
		self.requestListResponse.update(Pretty(self._currentRequests[cast(ACMEListItem, selected.item)._data]['rsp']))
	

	async def on_list_view_highlighted(self, selected:ListView.Highlighted) -> None:
		# self.tuiApp.bell()
		if selected and selected.item:
			self.requestListRequest.update(Pretty(self._currentRequests[cast(ACMEListItem, selected.item)._data]['req']))
			self.requestListResponse.update(Pretty(self._currentRequests[cast(ACMEListItem, selected.item)._data]['rsp']))


	def action_refresh_requests(self) -> None:
		self.updateRequests()


	def action_delete_requests(self) -> None:
		self.deleteRequests()


	def updateRequests(self) -> None:
			# TODO plantuml?

			def rscFmt(rsc:int) -> str:
				_rsc = ResponseStatusCode(rsc) if ResponseStatusCode.has(rsc) else ResponseStatusCode.UNKNOWN
				_c = 'green1' if isSuccessRSC(_rsc) else 'red'
				return f'[{_c}]{_rsc.name}[/{_c}]'

			self.requestList.clear()
			self.requestListRequest.update()
			self.requestListResponse.update()

			self._currentRequests = cast(JSONLIST, CSE.storage.getRequests(self._currentRI))

			for i, r in enumerate(self._currentRequests):
				_ts = toISO8601Date(r["ts"], readable = True).split('T')
				self.requestList.append(_l := ACMEListItem(
					Label(f' {i:4}  -  {_ts[1]}   {str(r["ri"]):25}   {str(r["org"]):25}   {Operation(r["op"]).name:10}   {rscFmt(r["rsc"])}\n          [dim]{_ts[0]}[/dim]        [dim]{str(r["srn"])}[/dim]')))
				_l._data = i
			if len(self._currentRequests):
				self.setIndex(0)
	
	
	def deleteRequests(self) -> None:
		CSE.storage.deleteRequests(self._currentRI)
		self.updateRequests()


	def setIndex(self, idx:int) -> None:
		if 0 <= idx < len(self._currentRequests):
			self.requestListRequest.update(Pretty(self._currentRequests[idx]['req']))
			self.requestListResponse.update(Pretty(self._currentRequests[idx]['rsp']))


