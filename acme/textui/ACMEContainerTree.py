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
from textual.widgets import Tree as TextualTree, Static, TabbedContent, TabPane, Label
from textual.containers import Container, Vertical, ScrollableContainer
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
		self.auto_expand = False
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
		chs = [ x for x in CSE.dispatcher.directChildResources(ri) if not x.isVirtual() ]
		for r in chs:
			result.append((r, len([ x for x in CSE.dispatcher.directChildResources(r.ri) if not x.isVirtual() ]) > 0))
		return result


class ACMEContainerTree(Container):

	resourceTree:ACMEResourceTree

	BINDINGS = 	[ Binding('r', 'refresh_resources', 'Refresh') 
				
				# TODO copy resource
				# TODO delete

				# delete requests
				]

	def __init__(self) -> None:
		super().__init__(id = idTree)
		self.resourceTree = ACMEResourceTree(CSE.cseRn, data = CSE.cseRi, id = 'tree-view')
		self.resourceTree.parentContainer = self

		# Tabs
		self.tabs = TabbedContent()

		# Resource and Request views
		self.resourceView = Static(id = 'resource-view', expand = True)
		self.requestView = ACMEViewRequests()

	def compose(self) -> ComposeResult:
		self.resourceTree.focus()

		with Container():
			yield self.resourceTree
			with self.tabs:
				with TabPane('Resource', id = 'tree-tab-resource'):
					yield self.resourceView
				with TabPane('Requests', id = 'tree-tab-requests'):
					yield self.requestView
	

	def action_refresh_resources(self) -> None:
		# _textUI.tuiApp.bell()
		self.resourceTree._update_tree()


	async def onShow(self) -> None:
		self.resourceTree.focus()
		self._update_requests()


	async def on_tabbed_content_tab_activated(self, event:TabbedContent.TabActivated) -> None:
	#async def on_tabs_tab_activated(self, event:Tabs.TabActivated) -> None:
		"""Handle TabActivated message sent by Tabs."""
		# self.app.debugConsole.update(event.tab.id)

		if self.tabs.active == 'tree-tab-requests':
			self._update_requests()
			self.requestView.updateBindings()
		self.app.updateFooter()	# type:ignore[attr-defined]


	def _update_requests(self, ri:Optional[str] = None) -> None:
		if self.tabs.active == 'tree-tab-requests':
			self.requestView.currentRI = ri if ri else self.resourceTree.cursor_node.data
			self.requestView.updateRequests()
			self.requestView.requestList.focus()