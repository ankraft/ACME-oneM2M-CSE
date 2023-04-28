#
#	ACMEContainerConfigurations.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Configurations* view for the ACME text UI.
"""

from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Tree as TextualTree
from textual.widgets.tree import TreeNode
from ..services import CSE
from ..services.Logging import Logging as L

idConfigs = 'configurations'

class ACMEConfigurationTree(TextualTree):

	parentContainer:ACMEContainerConfigurations = None

	async def _on_compose(self) -> None:
		#self._update_tree()
		return await super()._on_compose()

	def on_mount(self) -> None:

		# Build the resource tree
		root = self.root

		def _addSetting(splits:list[str], level:int, node:TreeNode, setting:str) -> None:
			_s = splits[level]
			_n = None
			for c in node.children:
				if str(c.label) == _s:
					_n = c
					break
			else:	# not found
				_n = node.add(_s)
			
			if level == len(splits) - 1:
				_n.allow_expand = False
				_n.data = setting
			else:
				_addSetting(splits, level + 1, _n, setting)


		for k, v in CSE.Configuration.all().items():
			s = k.split('.')
			for idx, element in enumerate(s):
				_addSetting(s, 0, self.root, k)

		self.root.expand()


	# def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
	# 	self.app.logDebug(str(node.node.data))



class ACMEContainerConfigurations(Container):

	from ..textui import ACMETuiApp

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idConfigs)
		self.tuiApp = tuiApp
		self.configurationsView = Static(expand = True)
		self._configurationsUpdate()

		self.configurationsTree = ACMEConfigurationTree('Configurations', id = 'tree-view')
		self.configurationsTree.parentContainer = self



	def compose(self) -> ComposeResult:
		with Container():
			yield self.configurationsTree
			with Vertical(id = 'configs-view'):
				yield self.configurationsView


	def on_show(self) -> None:
		self.tuiApp.logDebug('show')
		self._configurationsUpdate()
		self.configurationsTree.focus()


	def _configurationsUpdate(self) -> None:
		self.configurationsView.update(CSE.console.getConfigurationRich())

