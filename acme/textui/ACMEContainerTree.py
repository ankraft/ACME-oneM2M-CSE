#
#	ACMEContainerTree.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Resources* view for the ACME text UI.
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from textual.app import ComposeResult
from textual.widgets import Tree as TextualTree, Static, Tabs, Tab, ContentSwitcher
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.pretty import Pretty
from ..services import CSE
from ..resources.Resource import Resource
from ..textui.ACMEContainerRequests import ACMEViewRequests
from ..etc.ResponseStatusCodes import ResponseException


idTree = 'tree'


class ACMEResourceTree(TextualTree):

	parentContainer:ACMEContainerTree = None

	async def _on_compose(self) -> None:
		self._update_tree()
		return await super()._on_compose()

	def _update_tree(self) -> None:
		self.clear()
		for r in self._retrieve_children(CSE.cseRi):
			self.root.add(r[0].rn, data = r[0].ri, allow_expand = r[1])
	

	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		try:
			resource = CSE.dispatcher.retrieveLocalResource(node.node.data)
			self.parentContainer.resourceView.update(Pretty(resource.asDict()))
		except ResponseException as e:
			self.parentContainer.resourceView.update(f'ERROR: {e.dbg}')

	def on_tree_node_selected(self, node:TextualTree.NodeSelected) -> None:
		try:
			resource = CSE.dispatcher.retrieveLocalResource(node.node.data)
			# _textUI.tuiApp.resourceView.update(Pretty(_r.resource.asDict()))
			self.parentContainer.resourceView.update(Pretty(resource.asDict(), expand_all = True))
			self.parentContainer._update_requests(resource.ri)
		except ResponseException as e:
			self.parentContainer.resourceView.update('[red]Resource not found')


	def on_tree_node_expanded(self, node:TextualTree.NodeSelected) -> None:
		node.node._children = []	# no available method?
		for r in self._retrieve_children(node.node.data):
			node.node.add(r[0].rn, data = r[0].ri, allow_expand = r[1])


	def _retrieve_children(self, ri:str) -> List[Tuple[Resource, bool]]:
		result:List[Tuple[Resource, bool]] = []
		# for r in CSE.dispatcher.directChildResources(ri):
		chs = [ x for x in CSE.dispatcher.directChildResources(ri) if not x.isVirtual() ]
		for r in chs:
			#_r = filter(lambda x: not x.isVirtual(), CSE.dispatcher.directChildResources(r.ri))
			# result.append((r, len(CSE.dispatcher.directChildResources(r.ri)) > 0))
			result.append((r, len([ x for x in CSE.dispatcher.directChildResources(r.ri) if not x.isVirtual() ]) > 0))
		return result


class ACMEContainerTree(Container):

	resourceTree:ACMEResourceTree

	BINDINGS = 	[ Binding('r', 'refresh_resources', 'Refresh Resources') 
				
				# TODO copy resource
				# TODO delete

				# delete requests
				]

	def __init__(self) -> None:
		super().__init__(id = idTree)
		self.resourceTree = ACMEResourceTree(CSE.cseRn, data = CSE.cseRi, id = 'tree-view')
		self.resourceTree.parentContainer = self
		
		# Resource view
		self.resourceView = Static(id = 'resource-view', expand = True)

		# Request list view : header + list
		# self.requestListHeader = Label(f'    [u b]#[/u b]  -  [u b]Timestamp[/u b]                       [u b]Originator[/u b]             [u b]Operation[/u b]    [u b]Response Status[/u b]')
		# self.requestListHeader.styles.height = 2
		# self.requestList = ListView(id = 'request-list-list')

		# # Request view: request + response
		# self.requestListRequest = Static(id = 'request-list-request')
		# self.requestListResponse = Static(id = 'request-list-response')
		# self.requestListDetails = Horizontal(self.requestListRequest, 
		# 									 self.requestListResponse,
		# 									 id = 'request-list-details')

		# # Combine request views
		# self.requestView = Vertical(self.requestListHeader, 
		# 							self.requestList, 
		# 							self.requestListDetails,
		# 							id = 'request-list-view')
		self.requestView = ACMEViewRequests()

		# Tabs for the content view
		self.treeInfoTabs = Tabs(
			Tab('Resource', id = 'tree-tab-resource'),
			Tab('Requests', id = 'tree-tab-requests'))

		# Build the content view for the tabs
		self.contentView = ContentSwitcher(
			self.resourceView,
			self.requestView,
			initial = 'resource-view')


	def compose(self) -> ComposeResult:
		self.resourceTree.focus()

		yield Container(
			self.resourceTree,
			#Vertical(self.resourceView, id = 'resource-view'),
			Vertical(self.treeInfoTabs,
					 self.contentView))
	

	def action_refresh_resources(self) -> None:
		# _textUI.tuiApp.bell()
		self.resourceTree._update_tree()


	async def onShow(self) -> None:
		#self.resourceTree._update_tree()
		self.resourceTree.focus()
		self._update_requests()


	async def on_tabs_tab_activated(self, event:Tabs.TabActivated) -> None:
		"""Handle TabActivated message sent by Tabs."""
		if event.tab.id == 'tree-tab-resource':
			#await self.containerTree.onShow()
			self.contentView.current = 'resource-view'
		elif event.tab.id == 'tree-tab-requests':
			#await self.containerTree.onShow()
			#self.contentView.current = 'requests-view'
			self.contentView.current = 'request-list-view'
			self._update_requests()


	def _update_requests(self, ri:Optional[str] = None) -> None:
		# TODO nicer representation
		if self.contentView.current == 'request-list-view':
			self.requestView.currentRI = ri if ri else self.resourceTree.cursor_node.data
			self.requestView.updateRequests()
			self.requestView.requestList.focus()