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
from time import sleep
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Center, Middle
from textual.widgets import Button, Tree as TextualTree, Markdown, RichLog, Label
from textual.widgets.tree import TreeNode
from ..services import CSE
from ..services.ScriptManager import PContext
from ..helpers.ResourceSemaphore import CriticalSection
from ..helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from ..helpers.Interpreter import SSymbol
from ..textui.ACMEFieldOriginator import ACMEInputField

# TODO Add editing of configuration values

idTools = 'tools'

class ACMEToolsTree(TextualTree):

	def __init__(self, *args, **kwargs) -> None:	# type: ignore[no-untyped-def]
		super().__init__(*args, **kwargs)
		self.allLogs = False
		self.logs:dict[str, List[str]] = {'Commands': []}	# Create a log for the tree root
		self.nodes:dict[str, TreeNode] = {}
		self.autoRunWorker:BackgroundWorker = None
		self.autoRunName:str = None

		
	def on_mount(self) -> None:
		self.parentContainer = cast(ACMEContainerTools, self.parent.parent)

		# Build the resource tree
		self.auto_expand = False
		root = self.root

		# def _sortTools(item) -> bool:
		# 	return item[1].meta.get('tuiSortOrder', 999)

		# Iterate over all scripts and add them to the tree. Sort them by the meta tag "tuiSortOrder" and then by name.
		for name, context in dict( sorted(CSE.script.scripts.items(), key = lambda x: (int(x[1].meta.get('tuiSortOrder', '500')), x[1].scriptName)) ).items():
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
				_nn = _n.add(f'[{CSE.textUI.objectColor}]{name}[/]', allow_expand = False)
				self.nodes[name] = _nn
				self.logs[name] = []	# Create a log for each script

		# Expand the root element, but the others
		self.root.expand()
	

	def on_show(self) -> None:
		# self.app.bell()
		node = self.cursor_node
		self._showTool(node)
	

	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		"""	Show the tool description when a node is highlighted.
		
			Args:
				node: The highlighted node.
		"""
		self._showTool(node.node)
	

	def _showTool(self, node:TreeNode) -> None:
		"""	Show the script's description when a node is highlighted.

			Also start the autorun worker if the meta tag "tuiAutoRun" is set.

			Args:
				node: The highlighted node.
		"""
		# Stop a currently running autorun worker when the node is different 
		# from the previous autorun node
		self.stopAutoRunScript(str(node.label))
		self.parentContainer.toolsInput.value = ''


		if node.children:	
			# This is a category node, so set the description, clear the button etc.
			self.parentContainer.toolsHeader.update(f'## {node.label}\n{CSE.script.categoryDescriptions.get(str(node.label), "")}')
			self.parentContainer.toolsExecButton.styles.visibility = 'hidden'
			self.parentContainer.toolsInput.styles.visibility = 'hidden'
			self.parentContainer.toolsLog.clear()


		elif (ctx := _getContext(str(node.label))):
			# Get the description from the meta data and format it for Markdown
			description = ctx.meta.get('description')
			description = description.replace('\n', '\n\n') if description is not None else ''

			# Update the header and the button
			if description.startswith('#'):
				self.parentContainer.toolsHeader.update(description)
			else:    
				self.parentContainer.toolsHeader.update(f"""\
## {node.label}

{description}
""")

			# Add input field if the meta tag "tuiInput" is set
			if (_l := ctx.getMeta('tuiInput')):
				self.parentContainer.toolsInput.styles.visibility = 'visible'
				self.parentContainer.toolsInput.setLabel(_l)
			else:
				self.parentContainer.toolsInput.styles.visibility = 'hidden'
			
			# configure the button according to the meta tag "tuiExecuteButton"
			self.parentContainer.toolsExecButton.styles.visibility = 'visible'
			self.parentContainer.toolsExecButton.label = 'Execute'
			if ctx.hasMeta('tuiExecuteButton'):
				if (_b := ctx.getMeta('tuiExecuteButton')):
					self.parentContainer.toolsExecButton.label = _b
				else:
					self.parentContainer.toolsExecButton.styles.visibility = 'hidden'
			self.parentContainer.toolsExecButton.styles.width = len(self.parentContainer.toolsExecButton.label) + 4

			self.parentContainer.toolsLog.clear()
			self.printLogs()

			# Autorun the script if the meta tag "tuiAutoRun" is set
			if ctx.hasMeta('tuiAutoRun'):
				# check if the autorun interval is set
				if (_i := ctx.getMeta('tuiAutoRun')):
					# Run the script periodically
					self.stopAutoRunScript()
					try:
						_interval = float(_i)
						if _interval <= 0.0:
							raise Exception('tuiAutoRun interval must be >= 0')
						self.autoRunWorker = BackgroundWorkerPool.newWorker(_interval, 
				     														lambda:_executeScript(ctx.scriptName, autoRun = True), 
													   						f'ts_{ctx.scriptName}').start()
						self.autoRunName = ctx.scriptName
					except Exception as e:
						self.parentContainer.scriptLogError(ctx.scriptName, f'Invalid interval for autorun: {e}')
						pass
				else:
					# Run the script once
					_executeScript(ctx.scriptName, autoRun = True)

		else:
			self.parentContainer.toolsHeader.update('')
			self.parentContainer.toolsExecButton.styles.visibility = 'hidden'
			self.parentContainer.toolsInput.styles.visibility = 'hidden'
		
	
	def printLogs(self) -> None:
		"""	Print the logs of the selected node to the log widget.
			The output depends on the value of self.allLogs.
		"""
		# Print the logs, but only those that are selected:
		# - If a line starts with a space, it is console output
		# - Otherwise (L, E) its a log entry
		self.parentContainer.toolsLog.write('\n'.join(
			[l[1:] 
    		 for l in self.logs.get(str(self.cursor_node.label), [])
			 if l[0] == ' ' or self.allLogs]))


	def stopAutoRunScript(self, name:Optional[str] = None) -> None:
		"""	Stop the autorun worker if it is running and the node is different 
			from the previous autorun node.
		
			Args:
				name: The name of the script to stop. If None, the current autorun
					  script is stopped, independent of its name.
		"""
		if name == None or name != self.autoRunName:
			if self.autoRunWorker:
				self.autoRunWorker.stop()
				self.autoRunWorker = None
				self.autoRunName = None



class ACMEContainerTools(Container):

	from . import ACMETuiApp

	BINDINGS = 	[ Binding('C', 'clear_log', 'Clear Log', key_display = 'SHIFT+C'),
	      		  Binding('l', 'toggle_log', 'Toggle Log') ]

	DEFAULT_CSS = '''

#tools-top-view {
	display: block;
	overflow: auto auto;
	min-width: 100%;
	margin: 0 0 0 0;
	height: 3fr;
}

#tools-arguments-view {
	display: block;
	overflow: auto auto;
	min-width: 100%;
	height: 1fr;
	margin: 0 0 0 0;
}


#tools-arguments-view {
	display: block;
	overflow: auto auto;
	min-width: 100%;
	height: 1.5fr;
	margin: 0 0 0 0;
}

#tools-log-view {
	display: block;
	overflow: auto auto;
	height: 3fr;
	padding: 0 0 0 1;
	border-top: $panel;
}

#tools-run-button {
	background: red;
}

#tools-argument-view {
	display: block;
	overflow: auto auto;  
	margin: 0 4 1 4;
	layout: vertical;
	height: 1fr;
}

#tool-log {
	display: block;
	min-width: 100%;
	overflow: auto auto;  
	margin: 0 0 0 0;
	padding: 1 0 1 1;
	border-top: $panel;
}
 
'''

	def __init__(self, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__(id = idTools)
		self.tuiApp = tuiApp

		self.toolsHeader = Markdown('')

		self.toolsTree = ACMEToolsTree('Tools & Commands', id = 'tree-view')
		self.toolsTree.parentContainer = self

		self.toolsInput = ACMEInputField(id = 'tools-argument')
		self.toolsInput.styles.visibility = 'hidden'

		self.toolsExecButton = Button('Execute', id = 'tool-execute-button', variant = 'primary')
		self.toolsExecButton.styles.visibility = 'hidden'

		self.toolsLog = RichLog(id = 'tools-log-view', markup=True)


	def compose(self) -> ComposeResult:
		with Container():
			yield self.toolsTree
			with Vertical():
				with Center(id = 'tools-top-view'):
					yield self.toolsHeader
				with Middle(id = 'tools-arguments-view'):
					with Center():
						yield self.toolsInput
					with Center():
						yield self.toolsExecButton

				yield self.toolsLog


	def on_show(self) -> None:
		self.tuiApp.logDebug('show')
		self.toolsTree.focus()

	
	def leaving_tab(self) -> None:
		self.toolsTree.stopAutoRunScript()

	
	@on(Button.Pressed, '#tool-execute-button')
	def buttonExecute(self) -> None:
		_executeScript(str(self.toolsTree.cursor_node.label), argument = str(self.toolsInput.value))
	

	@on(ACMEInputField.Submitted)
	def inputFieldSubmitted(self) -> None:
		self.buttonExecute()


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
	

	def cleanUp(self) -> None:
		"""	Clean up the tools tree and stop the autorun script if any
		"""
		self.toolsTree.stopAutoRunScript()

	#################################################################
	#
	# Logging and other scripting stuff
	#

	def _logMessage(self, scriptName:str, msg:str, prefix:str) -> None:
		
		# Prepare the message
		_s = msg if msg else ' '

		# Add to the log
		if (_l := self.toolsTree.logs.get(scriptName)) is not None:
			_l.append(f'{prefix}{_s}')

		# If this is the current script, add to the log view but only if the log mode matches
		if self.toolsTree.cursor_node and str(self.toolsTree.cursor_node.label) == scriptName and (self.toolsTree.allLogs or prefix == ' '):
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
		# Escape "["" in log messages.
		msg = msg.replace('[', '\[')
		self._logMessage(scriptName, f'[dim]{msg}[/dim]', 'L')


	def scriptLogError(self, scriptName:str, msg:str) -> None:
		""" Prints an error message for a script.
		
			Args:
				scriptName: The name of the script.
				msg: The message to print.	
		"""
		msg = msg.replace('[', '\[')
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


	def scriptVisualBell(self, scriptName:str) -> None:
		""" Visual bell for a script. The script name in the tree
		 	will have a reverse appearance for a short time.

			Args:
				scriptName: The name of the script.
		"""
		with CriticalSection(scriptName):
			oldLabel = self.toolsTree.nodes[scriptName]._label
			self.toolsTree.nodes[scriptName].set_label(f'[reverse {CSE.textUI.objectColor}]{oldLabel}')
			self.toolsTree.refresh()
			sleep(0.3)
			self.toolsTree.nodes[scriptName].set_label(oldLabel)
			self.toolsTree.refresh()



def _getContext(name:str) -> Optional[PContext]:
	"""	Returns the context for the given script name or None if not found. 

		Args:
			name: The name of the script.
	
		Return:
			The context for the given script name or None if not found.
	"""
	if (res := CSE.script.findScripts(name)):
		return res[0]
	return None


def _executeScript(name:str, autoRun:Optional[bool] = False, argument:Optional[str] = '') -> bool:
	""" Executes the given script context.

		Args:
			name: The name of the script.
	"""
	if (ctx := _getContext(str(name))) and not ctx.state.isRunningState():
		return CSE.script.runScript(ctx,
			      					arguments = argument,
			      					background = True,
									environment = { 'tui.autorun': SSymbol(boolean = autoRun),
												  }
									)
	return False



# TODO add input field for arguments
# TODO Binding for executing a script (R?)
# TODO Menu for editing a script (E?)
# TODO Menu for deleting a script (D?)
# TODO Menu for adding a script (A?)