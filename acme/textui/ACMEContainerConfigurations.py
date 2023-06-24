#
#	ACMEContainerConfigurations.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Configurations* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Tree as TextualTree, Markdown
from textual.widgets.tree import TreeNode
from ..services import CSE
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L

# TODO Add editing of configuration values

idConfigs = 'configurations'

class ACMEConfigurationTree(TextualTree):

	parentContainer:ACMEContainerConfigurations = None

	def on_mount(self) -> None:
		self.parentContainer = cast(ACMEContainerConfigurations, self.parent.parent)

		# Build the resource tree
		self.auto_expand = False
		root = self.root
		root.data = root.label
		self.prefixLen = len(self.root.data) + 1 

		def _addSetting(splits:list[str], level:int, node:TreeNode) -> None:
			_s = splits[level]
			_n = None
			for c in node.children:
				if str(c.label) == _s:
					_n = c
					break
			else:	# not found
				# Add new node to the tree. "data" contains the path to this node
				_n = node.add(_s, f'{node.data}.{_s}' )
			if level == len(splits) - 1:
				_n.allow_expand = False
				_n.label = f'[{CSE.textUI.objectColor}]{_s}[/]'
			else:
				_addSetting(splits, level + 1, _n)

		# Add all keys as paths recursively to the tree
		for k in CSE.Configuration.all().keys():
			_addSetting(k.split('.'), 0, self.root)

		# Expand the root element, but the others
		self.root.expand()
	
	def on_show(self) -> None:
		node = self.cursor_node
		self._showDocumentation(str(node.data))


	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		self._showDocumentation(str(node.node.data))


	def _showDocumentation(self, topic:str) -> None:
		if topic != str(self.root.data):
			topic = topic[self.prefixLen:]
		
		doc = Configuration.getDoc(topic)
		doc = doc if doc else ''

		value = Configuration.get(topic)
		if isinstance(value, list):
			value = ','.join(value)
		
		header = f'## {topic}\n'
		if value is not None:
			# header with link for later editing feature
			if len(_s := str(value)):
				_s = _s.replace('*', '\\*')	# escape some markdown chars
				header += f'> **{_s}**&nbsp;\n\n'
			else:
				header += f'> &nbsp;\n\n'

		self.parentContainer.tuiApp.logDebug(str(topic))
		self.parentContainer.documentationView.update(header + doc)


class ACMEContainerConfigurations(Container):


	DEFAULT_CSS = '''
#configs-documentation-view {
	display: block;
	overflow: auto auto;  
}
'''

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idConfigs)
		self.tuiApp = tuiApp
		self.documentationView = Markdown('')

		self.configurationsTree = ACMEConfigurationTree('Configurations', id = 'tree-view')
		self.configurationsTree.parentContainer = self


	def compose(self) -> ComposeResult:
		with Vertical():
			yield self.configurationsTree
			with Vertical(id = 'configs-documentation-view'):
				yield self.documentationView


	def on_show(self) -> None:
		self.tuiApp.logDebug('show')
		self.configurationsTree.focus()


	# def _configurationsUpdate(self) -> None:
	# 	self.configurationsView.update(CSE.console.getConfigurationRich())

