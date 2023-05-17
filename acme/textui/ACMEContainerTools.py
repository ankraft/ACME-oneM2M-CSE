#
#	ACMEContainerConfigurations.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Commands* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast, Optional, List
from datetime import datetime, timezone
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Center, Middle
from textual.widgets import Button, Tree as TextualTree, Markdown, TextLog, Static, ContentSwitcher
from textual.widgets.tree import TreeNode
from rich.text import Text
from ..services import CSE
from ..services.ScriptManager import PContext

# TODO Add editing of configuration values

idTools = 'tools'

class ACMEToolsTree(TextualTree):

	def on_mount(self) -> None:
		self.parentContainer = cast(ACMEContainerTools, self.parent.parent)
		self.logs:dict[str, List[str]] = {'Commands': []}	# Create a log for the tree root
		self.allLogs = False

		# Build the resource tree
		self.auto_expand = False
		root = self.root


		for name, context in dict(sorted(CSE.script.scripts.items())).items():
		# for name, context in CSE.script.scripts.items():
			if 'tuiTool' in context.meta:	# Only add scripts marked as tools
				_n = root	# Fallback: add to root
				if (category := context.meta.get('category')):
					for c in root.children:
						if str(c.label) == category:
							_n = c	# Found category
							break
					else:	# not found
						# Add new node to the tree for the category
						_n = root.add(category, allow_expand = False, expand = True)
				# Add the script to a category or to the root
				_n.add(f'[{CSE.textUI.objectColor}]{name}[/]', allow_expand = False)
				self.logs[name] = []	# Create a log for each script

		# Expand the root element, but the others
		self.root.expand()
	
	def on_show(self) -> None:
		node = self.cursor_node
		self._showTool(node)


	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		self._showTool(node.node)
	

	def _showTool(self, node:TreeNode) -> None:
		# Get the description from the meta data and format it for Markdown
		if node.children:	# This is a category
			self.parentContainer.toolsHeader.update(f'## {node.label}')
			self.parentContainer.toolsExecButton.styles.visibility = 'hidden'
			self.parentContainer.toolsLog.clear()


		elif (ctx := _getContext(str(node.label))):
			description = ctx.meta.get('description')
			description = description.replace('\n', '\n\n') if description is not None else ''

			# Update the header and the button
			self.parentContainer.toolsHeader.update(f"""\
## {node.label}

{description}
""")

			# configure the button according to the meta tag "tuiExecuteButton"
			self.parentContainer.toolsExecButton.styles.visibility = 'visible'
			self.parentContainer.toolsExecButton.label = 'Execute'
			if ctx.hasMeta('tuiExecuteButton'):
				if (_b := ctx.getMeta('tuiExecuteButton')):
					self.parentContainer.toolsExecButton.label = _b
				else:
					self.parentContainer.toolsExecButton.styles.visibility = 'hidden'

			self.parentContainer.toolsLog.clear()
			self.printLogs()

		else:
			self.parentContainer.toolsHeader.update('')
			self.parentContainer.toolsExecButton.styles.visibility = 'hidden'
		
	

	def printLogs(self) -> None:
		# Print the logs, but only those that are selected:
		# - If a line starts with a space, it is console output
		# - Otherwise (L, E) its a log entry
		self.parentContainer.toolsLog.write('\n'.join(
			[l[1:] 
    		 for l in self.logs[str(self.cursor_node.label)]
			 if l[0] == ' ' or self.allLogs]))



class ACMEContainerTools(Container):

	from . import ACMETuiApp

	BINDINGS = 	[ Binding('C', 'clear_log', 'Clear Log', key_display = 'SHIFT+C'),
	      		  Binding('l', 'toggle_log', 'Toggle Log') ]


	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idTools)
		self.tuiApp = tuiApp

		self.toolsHeader = Markdown('')

		self.toolsTree = ACMEToolsTree('Commands', id = 'tree-view')
		self.toolsTree.parentContainer = self
		
		self.toolsExecButton = Button('Execute', id = 'tool-execute', variant = 'primary')
		self.toolsExecButton.styles.visibility = 'hidden'

		self.toolsLog = TextLog(id = 'tools-log-view', markup=True)


	def compose(self) -> ComposeResult:
		with Container():
			yield self.toolsTree
			with Vertical():
				with Center(id = 'tools-top-view'):
					yield self.toolsHeader
				with Middle(id = 'tools-arguments-view'):
					with Center():
						yield self.toolsExecButton
				yield self.toolsLog


	def on_show(self) -> None:
		self.tuiApp.logDebug('show')
		self.toolsTree.focus()

	
	@on(Button.Pressed, '#tool-execute')
	def buttonExecute(self) -> None:
		if (ctx := _getContext(str(self.toolsTree.cursor_node.label))):
			CSE.script.runScript(ctx)
	

	def action_clear_log(self) -> None:
		# Clear the log view
		self.toolsLog.clear()

		# Clear the log for the current script
		if (_l := str(self.toolsTree.cursor_node.label)) in self.toolsTree.logs:
			self.toolsTree.logs[_l] = []


	def action_toggle_log(self) -> None:
		# Clear the log view
		self.toolsLog.clear()
		# toggle logs
		self.toolsTree.allLogs = not self.toolsTree.allLogs
		# Print the logs
		self.toolsTree.printLogs()
	

	#################################################################
	#
	# Logging
	#

	def _logMessage(self, scriptName:str, msg:str, prefix:str) -> None:

		# Prepare the message
		_s = msg if msg else ' '

		# _s = msg if prefix == ' ' else f'[dim]{datetime.now(tz = timezone.utc).strftime("%H:%M:%S")} -[/dim] {msg}'
		# Add to the log
		if (_l := self.toolsTree.logs.get(scriptName)) is not None:
			_l.append(f'{prefix}{_s}')
		# If this is the current script, add to the log view but only if the log mode matches
		if str(self.toolsTree.cursor_node.label) == scriptName and (self.toolsTree.allLogs or prefix == ' '):
			self.toolsLog.write(_s)


	def scriptPrint(self, scriptName:str, msg:str) -> None:
		"""	Prints a normal message for a script.

			Args:
				scriptName: The name of the script.
				msg: The message to print.
		"""
		self._logMessage(scriptName, msg, ' ')


	def scriptLog(self, scriptName:str, msg:str) -> None:
		""" Prints a log message for a script.

			Args:
				scriptName: The name of the script.
				msg: The message to print.
		"""
		self._logMessage(scriptName, f'[dim]{msg}[/dim]', 'L')


	def scriptLogError(self, scriptName:str, msg:str) -> None:
		""" Prints an error message for a script.
		
			Args:
				scriptName: The name of the script.
				msg: The message to print.	
		"""
		self._logMessage(scriptName, f'[red1]{msg}[/red1]', 'E')
	

	def scriptClearConsole(self, scriptName:str) -> None:
		""" Clears the console for a script.

			Args:
				scriptName: The name of the script.
		"""
		if (_l := self.toolsTree.logs.get(scriptName)) is not None:
			_l.clear()
		if str(self.toolsTree.cursor_node.label) == scriptName:
			self.toolsLog.clear()


def _getContext(name:str) -> Optional[PContext]:
	"""	Returns the context for the given script name or None if not found. 
	"""
	if (res := CSE.script.findScripts(name)):
		return res[0]
	return None


# TODO add input field for arguments
# TODO Binding for executing a script (R?)
# TODO Menu for editing a script (E?)
# TODO Menu for deleting a script (D?)
# TODO Menu for adding a script (A?)