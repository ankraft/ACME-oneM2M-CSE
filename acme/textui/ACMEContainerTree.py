#
#	ACMEContainerTree.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Resources* view for the ACME text UI.
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Any, cast

from textual import events
from textual.app import ComposeResult
from textual.widgets import Tree as TextualTree, Static, TabbedContent, TabPane, Markdown, Label, Button
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.binding import Binding
from rich.syntax import Syntax
from ..runtime import CSE
from ..resources.Resource import Resource
from ..textui.ACMEContainerRequests import ACMEViewRequests
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.Types import ResourceTypes
from ..helpers.TextTools import commentJson
from .ACMEContainerDelete import ACMEContainerDelete
from .ACMEContainerDiagram import ACMEContainerDiagram
from .ACMEContainerResourceServices import ACMEContainerResourceServices


class ACMEResourceTree(TextualTree):


	def __init__(self, *args:Any, **kwargs:Any) -> None:
		self.parentContainer = kwargs.pop('parentContainer', None)
		super().__init__(*args, **kwargs)

	
	def on_mount(self) -> None:
		self.root.expand()

		
	def _update_tree(self) -> None:
		self.clear()
		self.auto_expand = False
		self.select_node(None)
		prevType = ''
		for resource in self._retrieve_resource_children(CSE.cseRi):
			ty = resource[0].ty
			if ty != prevType and not ResourceTypes.isVirtualResource(ty):
				self.root.add(f'[{CSE.textUI.objectColor} b]{ResourceTypes.fullname(ty)}[/]', allow_expand = False)
				prevType = ty
			self.root.add(resource[0].rn, data = resource[0].ri, allow_expand = resource[1])
		self._update_content(self.cursor_node.data)


	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		try:
			if node.node.data:
				self._update_content(node.node.data)
			else:
				# No data means this is a type section
				self._update_type_section(str(node.node.label))
		except ResponseException as e:
			self.parentContainer.resourceView.update(f'ERROR: {e.dbg}')


	def on_tree_node_expanded(self, node:TextualTree.NodeSelected) -> None:
		node.node._children = []	# no available method?
		prevType = ''
		for resource in self._retrieve_resource_children(node.node.data):
			ty = resource[0].ty
			if ty != prevType and not ResourceTypes.isVirtualResource(ty):
				node.node.add(f'[{CSE.textUI.objectColor} b]{ResourceTypes.fullname(ty)}[/]', allow_expand = False)
				prevType = ty
			node.node.add(resource[0].rn, data = resource[0].ri, allow_expand = resource[1])
	

	def on_tree_node_hover(self, event:events.MouseMove) -> None:
		self.parentContainer.setResourceHeader('## Resources')


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
		self.parentContainer.setResourceHeader(f'## {ResourceTypes.fullname(resource.ty)} - {resource.rn}' if resource else '## &nbsp;')

		# Set the visibility of the tabs
		self.parentContainer.tabs.show_tab('tree-tab-requests')
		if ri == CSE.cseRi:	
			# Don't allow to delete the CSE
			self.parentContainer.tabs.hide_tab('tree-tab-delete')
		else:
			self.parentContainer.tabs.show_tab('tree-tab-delete')


	def _update_type_section(self, label:str) -> None:
		"""	Update the resource view with a type section.
		
			Args:
				label: The label of the type section.
		"""
		self.parentContainer.setResourceHeader(f'## {label} Resources')
		self.parentContainer.resourceView.update('')
		self.parentContainer.tabs.hide_tab('tree-tab-diagram')
		self.parentContainer.tabs.hide_tab('tree-tab-requests')
		self.parentContainer.tabs.hide_tab('tree-tab-services')	
		self.parentContainer.tabs.hide_tab('tree-tab-delete')


	def _retrieve_resource_children(self, ri:str) -> List[Tuple[Resource, bool]]:
		"""	Retrieve the children of a resource and return a sorted list of tuples.
		
			Each tuple contains a resource and a boolean indicating if the resource
			has children itself.

			Sort order is: virtual and instance resources first, then by type and name.
			
			Args:
				ri: The resource id of the parent resource.
				
			Returns:
				A sorted list of tuples (resource, hasChildren).
		"""
		result:List[Tuple[Resource, bool]] = []
		chs = [ x for x in CSE.dispatcher.retrieveDirectChildResources(ri) if not x.ty in [ ResourceTypes.GRP_FOPT, ResourceTypes.PCH_PCU ]]
		
		# Sort resources: virtual and instance resources first, then by type and name
		top = []
		rest = []
		for resource in chs:
			if ResourceTypes.isVirtualResource(resource.ty) or ResourceTypes.isInstanceResource(resource.ty):
				top.append(resource)
			else:
				rest.append(resource)
		rest.sort(key = lambda r: (r.ty, r.rn))
		chs = top + rest

		for resource in chs:
			result.append((resource, len([ x for x in CSE.dispatcher.retrieveDirectChildResources(resource.ri)  ]) > 0))
		return result


class ACMEContainerTree(Container):

	BINDINGS = 	[ Binding('r', 'refresh_resources', 'Refresh'),
				#   Binding('o', 'overlay', 'Overlay'),
		  
				
				# TODO copy resource
				# TODO delete

				# delete requests
				]

	DEFAULT_CSS = '''
	#resource-view {
		width: auto;
		height: auto;
		margin: 0 0 0 1;
	}

	#tree-tab-resource {
		overflow: hidden auto;  
		height: 100%;
		/* TODO try to get padding working with later released of textualize */
	}
	'''

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp, id:str) -> None:
		super().__init__(id = id)
		self.tuiApp = tuiApp
		self.currentResource:Resource = None


	def compose(self) -> ComposeResult:
		with Container():
			yield ACMEResourceTree(CSE.cseRn, data = CSE.cseRi, id = 'tree-view', parentContainer = self)
			with TabbedContent(id = 'tree-tabs'):
				with TabPane('Resource', id = 'tree-tab-resource'):
					yield Markdown(id = 'tree-tab-resource-header')
					yield Static(id = 'resource-view', expand = True)

				with TabPane('Requests', id = 'tree-tab-requests'):
					yield ACMEViewRequests(id = 'tree-tab-requests-view')

				with TabPane('Diagram', id = 'tree-tab-diagram'):
					yield ACMEContainerDiagram(refreshCallback = lambda: self.updateResource(), 
											   tuiApp = self.tuiApp,
											   id = 'tree-tab-diagram-view')

				with TabPane('Services', id = 'tree-tab-services'):
					yield ACMEContainerResourceServices(id = 'tree-tab-resource-services')


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
					yield ACMEContainerDelete(id = 'tree-tab-resource-delete')
				
				
	@property
	def resourceHeader(self) -> Label:
		return cast(Label, self.query_one('#tree-tab-resource-header'))


	def on_mount(self) -> None:
		self.update()


	def on_show(self) -> None:
		self.resourceTree.focus()


	def services_refresh_resources(self) -> None:
		self.update()

			
	def update(self) -> None:
		self.resourceTree._update_tree()


	def updateResource(self, resource:Optional[Resource] = None) -> None:
		# Store the resource for later
		if resource:
			self.currentResource = resource

		# Add attribute explanations
		if self.currentResource:
			jsns = commentJson(self.currentResource.asDict(sort = True), 
							explanations = self.app.attributeExplanations,	# type: ignore [attr-defined]
							getAttributeValueName = lambda a, v: CSE.validator.getAttributeValueName(a, v, self.currentResource.ty if self.currentResource else None))	# type: ignore [attr-defined]
			
			# Update the requests view
			self._update_requests(self.currentResource.ri)

			# Update DELETE view
			self.deleteView.updateResource(self.currentResource)
			self.deleteView.disabled = False

			# Update the services view
			self.servicesView.updateResource(self.currentResource)
			self.tabs.show_tab('tree-tab-services')

			# Update Diagram view
			try:
				if self.currentResource.ty in (ResourceTypes.CNT, ResourceTypes.TS):
					instances = CSE.dispatcher.retrieveDirectChildResources(self.currentResource.ri, [ResourceTypes.CIN, ResourceTypes.TSI])
					
					# The following lines may fail if the content cannot be converted to a float or a boolean.
					# This is expected! This just means that any content is not a number and we cannot raw a diagram.
					# The exception is caught below and the diagram view is hidden.
					try:
						values = [float(r.con) for r in instances]
					except ValueError:
						# Number (int or float) failed. Now try boolean
						values = []
						for r in instances:
							_con = r.con
							if isinstance(_con, str):
								if _con.lower() in ['true', 'on', 'yes', 'high']:
									values.append(1)
								elif _con.lower() in ['false', 'off', 'no', 'low']:
									values.append(0)
								else:
									self.app.bell()
									raise ValueError	# not a "boolean" value
							else:
								raise ValueError	# Not a string in the first place

					dates = [r.ct for r in instances]

					self.diagram.setData(values, dates)
					self.diagram.plotGraph()
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
			case 'tree-tab-diagram':
				pass
			case 'tree-tab-delete':
				pass
			case 'tree-tab-services':
				pass

		self.app.updateFooter()	# type:ignore[attr-defined]


	def _update_requests(self, ri:Optional[str] = None) -> None:
		if self.tabs.active == 'tree-tab-requests':
			self.requestView.currentRI = ri if ri else self.resourceTree.cursor_node.data
			self.requestView.updateRequests()
			self.requestView.requestList.focus()
	

	def setResourceHeader(self, header:str) -> None:
		"""	Set the header of the tree view.
		
			Args:
				header: The header to set.
		"""
		self.resourceHeader.update(header)
	

	@property
	def tabs(self) -> TabbedContent:
		return cast(TabbedContent, self.query_one('#tree-tabs'))


	@property
	def resourceTree(self) -> ACMEResourceTree:
		return cast(ACMEResourceTree, self.query_one('#tree-view'))


	@property
	def deleteView(self) -> ACMEContainerDelete:
		return cast(ACMEContainerDelete, self.query_one('#tree-tab-resource-delete'))


	@property
	def servicesView(self) -> ACMEContainerResourceServices:
		return cast(ACMEContainerResourceServices, self.query_one('#tree-tab-resource-services'))


	@property
	def requestView(self) -> ACMEViewRequests:
		return cast(ACMEViewRequests, self.query_one('#tree-tab-requests-view'))


	@property
	def resourceView(self) -> Static:
		return cast(Static, self.query_one('#resource-view'))


	@property
	def diagram(self) -> ACMEContainerDiagram:
		return cast(ACMEContainerDiagram, self.query_one('#tree-tab-diagram-view'))

	
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
