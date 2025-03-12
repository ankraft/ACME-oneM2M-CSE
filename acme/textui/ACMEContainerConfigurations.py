#
#	ACMEContainerConfigurations.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Configurations* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast, Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Tree as TextualTree, Markdown
from textual.widgets.tree import TreeNode
from ..runtime import CSE
from ..runtime.Configuration import Configuration


# TODO Add editing of configuration values

class ACMEConfigurationTree(TextualTree):
	"""	Configurations view for the ACME text UI.
	"""

	parentContainer:ACMEContainerConfigurations = None
	"""	The parent container. """
	prefixLen:int = 0
	"""	The length of the prefix. """

	def __init__(self, *args:Any, **kwargs:Any) -> None:
		"""	Constructor.

			An extra parameter "parentContainer" is added to the constructor.

			Args:
				args:	Variable length argument list.
				kwargs:	Arbitrary keyword arguments.
		"""

		self.parentContainer = kwargs.pop('parentContainer', None)
		super().__init__(*args, **kwargs)
		

	def on_mount(self) -> None:
		""" Called when the widget is mounted to the app.
		"""
		# Expand the root element
		self.root.expand()

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		""" A reference to the text UI application. """


	
	def on_show(self) -> None:
		""" Called when the widget is shown.
		"""
		# Build the configuration settings tree
		root = self.root
		root.data = root.label
		self.prefixLen = len(self.root.data) + 1 

		def _addSetting(splits:list[str], level:int, node:TreeNode) -> None:
			""" Add a setting to the tree.

				Args:
					splits:	The list of splits.
					level:	The level.
					node:	The node.
			"""
			_s = splits[level]
			_n = None
			for c in node.children:
				if str(c.label) == _s:
					_n = c
					break
			else:	# not found
				_n = node.add(f'[{self._app.objectColor}]{_s}[/]', f'{node.data}.{_s}' )
				node.children
				# Add new node to the tree. "data" contains the path to this node
			if level == len(splits) - 1:
				_n.allow_expand = False
				_n.label = _s
			else:
				_addSetting(splits, level + 1, _n)
			node._children.sort(key=lambda x: (len(x._children) == 0, str(x.label)))

		# Add all keys as paths recursively to the tree
		for k in CSE.Configuration.all().keys():
			_addSetting(k.split('.'), 0, self.root)

		# Show root documentation
		self._showDocumentation('Configurations')


	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		""" Called when a node is highlighted. Show the documentation for the node.

			Args:
				node:	The node.
		"""
		self._showDocumentation(str(node.node.data))


	def _showDocumentation(self, topic:str) -> None:
		""" Show the documentation for a topic.

			Args:
				topic:	The topic.
		"""
		if topic != str(self.root.data):
			topic = topic[self.prefixLen:]
		
		doc = Configuration.getDoc(topic)
		doc = doc if doc else ''

		value = Configuration.get(topic)
		if isinstance(value, list):
			value = ', '.join(value)
		
		header = f'# {topic}\n'
		if value is not None:
			# header with link for later editing feature
			if len(_s := str(value)):
				_s = _s.replace('*', '\\*')	# escape some markdown chars
				# header += f'> **{_s}**&nbsp;\n\n'
				header += f'> **{_s}**\n\n'
			else:
				header += f'> &nbsp;\n\n'

		self.parentContainer.updateDocumentation(header, doc)


class ACMEContainerConfigurations(VerticalScroll):
	"""	Container for the *Configurations* view.
	"""

	def __init__(self, *args:Any, **kwargs:Any) -> None:
		"""	Constructor.

			Args:
				args:	Variable length argument list.
				kwargs:	Arbitrary keyword arguments.
		"""

		super().__init__(*args, **kwargs)

		# self._configsTreeView = ACMEConfigurationTree(f'[{self._app.objectColor}]Configurations[/]', 
		self._configsTreeView = ACMEConfigurationTree(f'Configurations', 
							 				 		id = 'configs-tree-view',
													parentContainer = self)
		"""	The documentation tree view. """
		self._configsDocumentation = Markdown('', id = 'configs-documentation')
		"""	The documentation view. """
		
	
	def compose(self) -> ComposeResult:
		"""	Build the *Configurations* view.
		"""
		yield self._configsTreeView
		yield self._configsDocumentation

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		""" A reference to the text UI application. """

		# Change the root label colour
		self._configsTreeView.root.label = f'[{self._app.objectColor}]Configurations[/]'



	@property
	def treeView(self) -> ACMEConfigurationTree:
		""" Get the tree view widget.

			Returns:
				The tree view.
		"""
		return self._configsTreeView


	@property
	def documentationView(self) -> Markdown:
		""" Get the documentation view widget.

			Returns:
				The documentation view.
		"""
		return self._configsDocumentation


	def on_show(self) -> None:
		""" Called when the widget is shown.
		"""
		self.treeView.focus()


	def updateDocumentation(self, header:str, doc:str) -> None:
		""" Update the documentation view.

			Args:
				header:	The header.
				doc:	The documentation.
		"""
		self.documentationView.update(header + doc)
