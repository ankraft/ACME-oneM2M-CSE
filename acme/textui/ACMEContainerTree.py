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
from datetime import datetime
from textual import events
from textual.app import ComposeResult
from textual.widgets import Tree as TextualTree, Static, TabbedContent, TabPane, Markdown, Label, Button
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.binding import Binding
from rich.syntax import Syntax
from ..services import CSE
from ..resources.Resource import Resource
from ..textui.ACMEContainerRequests import ACMEViewRequests
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.Types import ResourceTypes
from ..etc.DateUtils import fromAbsRelTimestamp
from ..helpers.TextTools import commentJson
from .ACMEContainerDelete import ACMEContainerDelete
from .ACMEContainerDiagram import ACMEContainerDiagram


idTree = 'tree'


class ACMEResourceTree(TextualTree):

	parentContainer:ACMEContainerTree = None

	def _update_tree(self) -> None:
		self.clear()
		self.auto_expand = False
		self.select_node(None)
		for r in self._retrieve_resource_children(CSE.cseRi):
			self.root.add(r[0].rn, data = r[0].ri, allow_expand = r[1])
		self._update_content(self.cursor_node.data)


	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		try:
			self._update_content(node.node.data)
		except ResponseException as e:
			self.parentContainer.resourceView.update(f'ERROR: {e.dbg}')


	def on_tree_node_expanded(self, node:TextualTree.NodeSelected) -> None:
		node.node._children = []	# no available method?
		for r in self._retrieve_resource_children(node.node.data):
			node.node.add(r[0].rn, data = r[0].ri, allow_expand = r[1])
	

	def on_tree_node_hover(self, event:events.MouseMove) -> None:
		self.parentContainer.header.update('## Resources')


	_virtualResourcesParameter = {
		ResourceTypes.CNT_LA: (ResourceTypes.CIN, False),
		ResourceTypes.CNT_OL: (ResourceTypes.CIN, True),
		ResourceTypes.FCNT_LA: (ResourceTypes.FCI, False),
		ResourceTypes.FCNT_OL: (ResourceTypes.FCI, True),
		ResourceTypes.TS_OL: (ResourceTypes.TSI, True),
		ResourceTypes.TS_LA: (ResourceTypes.TSI, False),
	}

	def _update_content(self, ri:str) -> None:
		try:
			resource = CSE.dispatcher.retrieveLocalResource(ri)

			# retrieve the latest/oldest instance of some virtual resources
			if (_params := self._virtualResourcesParameter.get(resource.ty)):
				if (_r := CSE.dispatcher.retrieveLatestOldestInstance(resource.pi, _params[0], oldest = _params[1])):
					resource = _r
				else:
					resource = None
		except ResponseException as e:
			self._update_tree()
			return
		
		# Update the resource view and other views
		self.parentContainer.updateResource(resource)

		# Update the header
		self.parentContainer.header.update(f'## {ResourceTypes.fullname(resource.ty)}' if resource else '## &nbsp;')



	def _retrieve_resource_children(self, ri:str) -> List[Tuple[Resource, bool]]:
		result:List[Tuple[Resource, bool]] = []
		chs = [ x for x in CSE.dispatcher.retrieveDirectChildResources(ri) if not x.ty in [ ResourceTypes.GRP_FOPT, ResourceTypes.PCH_PCU ]]
		# chs = [ x for x in CSE.dispatcher.directChildResources(ri) if not x.isVirtual() ]
		# chs = [ x for x in CSE.dispatcher.directChildResources(ri) if not x.isVirtual() ]
		for r in chs:
			result.append((r, len([ x for x in CSE.dispatcher.retrieveDirectChildResources(r.ri)  ]) > 0))
			# result.append((r, len([ x for x in CSE.dispatcher.directChildResources(r.ri) if not x.isVirtual() ]) > 0))
		return result


class ACMEContainerTree(Container):

	resourceTree:ACMEResourceTree

	BINDINGS = 	[ Binding('r', 'refresh_resources', 'Refresh'),
				#   Binding('o', 'overlay', 'Overlay'),
		  
				
				# TODO copy resource
				# TODO delete

				# delete requests
				]

	DEFAULT_CSS = '''
#resource-view {
	/* overflow: hidden scroll;   */
	/* width: 1fr;
	height: 1fr; */
	width: auto;
	height: auto;
	margin: 0 0 0 1;
	/* background:red; */
}

#tree-tab-resource {
	overflow: hidden auto;  
	/* height: 1fr; */
	height: 100%;
	/* padding: 1 1; */

	/* background:red; */
	/* TODO try to get padding working with later released of textualize */
}



'''

	def __init__(self) -> None:
		super().__init__(id = idTree)
		self.resourceTree = ACMEResourceTree(CSE.cseRn, data = CSE.cseRi, id = 'tree-view')
		self.resourceTree.parentContainer = self

		self.resource:Resource = None

		# Tabs
		self.tabs = TabbedContent()

		# Various Resource and Request views
		self.deleteView = ACMEContainerDelete()
		self.diagram = ACMEContainerDiagram(refreshCallback = lambda: self.updateResource())

		# For some reason, the markdown header is not refreshed the very first time
		self.header = Markdown('')
		self.resourceView = Static(id = 'resource-view', expand = True)
		self.requestView = ACMEViewRequests()
		self.commentsOneLine = True



	def compose(self) -> ComposeResult:
		self.resourceTree.focus()

		with Container():
			yield self.resourceTree
			with self.tabs:
				with TabPane('Resource', id = 'tree-tab-resource'):
					yield self.header
					yield self.resourceView
				with TabPane('Requests', id = 'tree-tab-requests'):
					yield self.requestView

				with TabPane('Diagram', id = 'tree-tab-diagram'):
					yield self.diagram

				# with TabPane('CREATE', id = 'tree-tab-create', disabled = True):
				# 	yield Markdown('## Send CREATE Request')
				# 	yield Label('TODO')
				# with TabPane('RETRIEVE', id = 'tree-tab-retrieve', disabled = True):
				# 	yield Markdown('## Send RETRIEVE Request')
				# 	yield Label('TODO')
				# with TabPane('UPDATE', id = 'tree-tab-update', disabled = True):
				# 	yield Markdown('## Send UPDATE Request')
				# 	yield Label('TODO')
				
				with TabPane('DELETE', id = 'tree-tab-delete'):
					yield Markdown('## Send DELETE Request')
					yield self.deleteView
				
				

	def on_mount(self) -> None:
		self.update()


	def on_show(self) -> None:
		self.resourceTree.focus()
		# self.resourceTree._update_tree()
		# self._update_requests()


	def action_refresh_resources(self) -> None:
		self.update()

			
	# async def action_overlay(self) -> None:
	# 	"""	Show the overlay with the key bindings.
	# 	"""
	# 	self.app.push_screen(ACMEDialog())
	

	def update(self) -> None:
		self.resourceTree._update_tree()


	def updateResource(self, resource:Optional[Resource] = None) -> None:
		if resource:
			# Store the resource for later
			self.resource = resource
		else:
			# Otherwise use the old / current resource
			resource = self.resource

		# Add attribute explanations
		if resource:
			jsns = commentJson(resource.asDict(sort = True), 
							explanations = self.app.attributeExplanations,	# type: ignore [attr-defined]
							getAttributeValueName = lambda a, v: CSE.validator.getAttributeValueName(a, v, resource.ty if resource else None),		# type: ignore [attr-defined]
							width = None if self.commentsOneLine else self.requestListRequest.size[0] - 2)	# type: ignore [attr-defined]
			
			# Update the requests view
			self._update_requests(resource.ri)

			# Update DELETE view
			self.deleteView.updateResource(resource)
			self.deleteView.disabled = False

			# Update Diagram view
			try:
				if resource.ty in (ResourceTypes.CNT, ResourceTypes.TS):
					instances = CSE.dispatcher.retrieveDirectChildResources(resource.ri, [ResourceTypes.CIN, ResourceTypes.TSI])
					
					# The following line may fail if the content cannot be converted to a float.
					# This is expected! This just means that any content is not a number and we cannot raw a diagram.
					# The exception is caught below and the diagram view is hidden.
					values = [float(r.con) for r in instances]

					dates = [r.ct for r in instances]
					# values = [float(r.con)
					# 		for r in instances
					# 		if r.ty in (ResourceTypes.CIN, ResourceTypes.TSI)]
					# dates = [r.ct
					# 		for r in instances
					# 		if r.ty in (ResourceTypes.CIN, ResourceTypes.TSI)]

					self.diagram.setData(values, dates)
					self.tabs.show_tab('tree-tab-diagram') 
				else:
					self.tabs.hide_tab('tree-tab-diagram') 
			except:
				self.tabs.hide_tab('tree-tab-diagram')

		else:
			jsns = ''

			# Disable the delete view
			self.deleteView.disabled = True

			# Update the requests view with an empty string
			self._update_requests('')
			
		# Add syntax highlighting and add to the view
		self.resourceView.update(Syntax(jsns, 'json', theme = self.app.syntaxTheme))	# type: ignore [attr-defined]


		# TODO update the create, retrieve, update, delete views

	
	async def on_tabbed_content_tab_activated(self, event:TabbedContent.TabActivated) -> None:
	#async def on_tabs_tab_activated(self, event:Tabs.TabActivated) -> None:
		"""Handle TabActivated message sent by Tabs."""
		# self.app.debugConsole.update(event.tab.id)

		match self.tabs.active:
			case 'tree-tab-requests':
				self._update_requests()
				self.requestView.updateBindings()
			case 'tree-tab-resource':
				pass
			case 'tree-tab-delete':
				pass

		self.app.updateFooter()	# type:ignore[attr-defined]


	def _update_requests(self, ri:Optional[str] = None) -> None:
		if self.tabs.active == 'tree-tab-requests':
			self.requestView.currentRI = ri if ri else self.resourceTree.cursor_node.data
			self.requestView.updateRequests()
			self.requestView.requestList.focus()
	

# TODO move the following to a more generic dialog module
class ACMEDialog(ModalScreen):
	BINDINGS = [('escape', 'pop_dialog', 'Close')]

	DEFAULT_CSS = '''

/* The CSS for ACMERequest is in .css file. The transparency
   doesn't work if it is in the DEFAULT_CSS. */

#confirm {
	width: 80%;
	padding: 1;
	height: 8;
	border: heavy $accent;
	background: $surface;
}

#confirm-label {
	content-align: center middle;
	width: 100%;
}

#confirm-buttons {
	margin-top: 2;
	align: center middle;
}

#confirm-buttons Button {
	min-width: 12;
	border-top: none;
	border-bottom: none;
	height: 1;
	margin-left: 1;
	margin-right: 1;
	align: center middle;
}

#confirm-ok {
	border-left: tall $success-lighten-2;
	border-right: tall $success-darken-3;
}

#confirm-cancel {
	border-left: tall $primary-lighten-2;
	border-right: tall $primary-darken-3;
}

'''

	def __init__(self, message:str = 'Really?', buttonOK:str = 'OK', buttonCancel:str = 'Cancel') -> None:
		super().__init__()
		self.message = message
		self.buttonOK = buttonOK
		self.buttonCancel = buttonCancel
		self.width = len(self.message) + 10 if len(self.message) + 10 > 50 else 50


	def compose(self) -> ComposeResult:
		with (_v := Vertical(id = 'confirm')):
			yield Label(self.message, id = 'confirm-label')
			with Horizontal(id = 'confirm-buttons'):
				yield Button(self.buttonOK, variant = 'success', id = 'confirm-ok')
				yield (_b := Button(self.buttonCancel, variant = 'primary', id = 'confirm-cancel'))
		_b.focus()
		_v.styles.width = self.width


	def action_pop_dialog(self) -> None:
		self.dismiss(False)


	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'confirm-ok':
			self.dismiss(True)
		else:
			self.dismiss(False)
