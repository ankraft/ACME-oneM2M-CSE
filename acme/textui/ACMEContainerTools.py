#
#	ACMEContainerConfigurations.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Commands* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast, Optional, List, Any
from time import sleep
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Center, Horizontal, Container
from textual.widgets import Button, Tree as TextualTree, Markdown, RichLog
from textual.widgets.tree import TreeNode
from ..runtime import CSE
from ..runtime.ScriptManager import PContext
from ..helpers.ResourceSemaphore import CriticalSection
from ..helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from ..helpers.Interpreter import SSymbol
from ..textui.ACMEFieldOriginator import ACMEInputField

# TODO Add editing of configuration values


class ACMEToolsTree(TextualTree):

	def __init__(self, *args:Any, **kwargs:Any) -> None:	# type: ignore[no-untyped-def]
		from ..textui.ACMETuiApp import ACMETuiApp

		self.parentContainer = kwargs.pop('parentContainer', None)
		super().__init__(*args, **kwargs)

		self.allLogs = False
		self.logs:dict[str, List[str]] = {'Commands': []}	# Create a log for the tree root
		self.nodes:dict[str, TreeNode] = {}
		self.autoRunWorker:BackgroundWorker = None
		self.autoRunName:str = None
		self._app = cast(ACMETuiApp, self.app)

		
	def on_mount(self) -> None:

		# Build the resource tree
		self.auto_expand = False
		root = self.root

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
						_n = root.add(f'[{self._app.objectColor}]{category}[/]', allow_expand = False, expand = True)
				# Add the script to a category or to the root
				_nn = _n.add(name, allow_expand = False)
				self.nodes[name] = _nn
				self.logs[name] = []	# Create a log for each script

		# Expand the root element, but the others
		self.root.expand()
	

	def on_show(self) -> None:
		node = self.cursor_node
		self._showTool(node)
	

	def on_tree_node_highlighted(self, node:TextualTree.NodeHighlighted) -> None:
		"""	Show the tool description when a node is highlighted.
		
			Args:
				node: The highlighted node.
		"""
		try:
			self._showTool(node.node)
		except:
			# This can happen when the tree is constructed and the first node is highlighted
			# before the tree is fully constructed.
			pass
	

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
			self.parentContainer.updateHeader(str(node.label), 
									 		  f'{CSE.script.categoryDescriptions.get(str(node.label), "")}')
			self.parentContainer.toolsExecButton.display = False
			self.parentContainer.toolsInput.display = False
			self.parentContainer.toolsLog.clear()


		elif (ctx := _getContext(str(node.label))):
			# Get the description from the meta data and format it for Markdown
			description = ctx.meta.get('description')
			description = description.replace('\n', '\n\n') if description is not None else ''

			# Update the header and the button
			# if description.startswith('#'):
			# 	self.parentContainer.updateHeader(description)
			# else:    
			# 	self.parentContainer.updateHeader(node.label, description)
			
			self.parentContainer.updateHeader(node.label, description)

			# Add input field if the meta tag "tuiInput" is set
			if (_l := ctx.getMeta('tuiInput')):
				self.parentContainer.toolsInput.display = True
				self.parentContainer.toolsInput.setLabel(_l)
			else:
				self.parentContainer.toolsInput.display = False
			
			# configure the button according to the meta tag "tuiExecuteButton"
			self.parentContainer.toolsExecButton.display = True
			self.parentContainer.toolsExecButton.label = 'Execute'
			if ctx.hasMeta('tuiExecuteButton'):
				if (_b := ctx.getMeta('tuiExecuteButton')):
					self.parentContainer.toolsExecButton.label = _b
				else:
					self.parentContainer.toolsExecButton.display = False
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
			self.parentContainer.updateHeader('')
			# self.parentContainer.toolsHeader.update('')
			self.parentContainer.toolsExecButton.display = False
			self.parentContainer.toolsInput.display = False
		
	
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


class ACMEContainerTools(Horizontal):

	from . import ACMETuiApp

	BINDINGS = 	[ Binding('C', 'clear_log', 'Clear Log', key_display = 'SHIFT+C'),
	      		  Binding('l', 'toggle_log', 'Toggle Log') ]

	def __init__(self, *args:Any, **kwargs:Any) -> None:
		from ..textui.ACMETuiApp import ACMETuiApp

		super().__init__(*args, **kwargs)
		self._app = cast(ACMETuiApp, self.app)

	def compose(self) -> ComposeResult:

		# Prepare some widgets in advance
		self._toolsTree = ACMEToolsTree(f'[{self._app.objectColor}]Tools & Commands[/]', 
								 		id = 'tools-tree-view',
										parentContainer = self)

		yield self._toolsTree
		with Vertical():
			with Center(id = 'tools-top-view'):
				yield Markdown('', id = 'tools-header')
				with Container(id = 'tools-arguments-view'):
					with Center():
						yield ACMEInputField(label = 'Argument', id = 'tools-argument')
					with Center():
						yield Button('Execute', id = 'tool-execute-button', variant = 'primary')
			yield RichLog(id = 'tools-log-view', markup=True)
	

	def on_mount(self) -> None:
		self.toolsInput.display = False
		self.toolsExecButton.display = False
		self.toolsLog.border_title = 'Output'


	def updateHeader(self, title:str, description:Optional[str] = '') -> None:
		"""	Set the header and description of the tools view.

			Args:
				title: The title text.
				description: The description text.
		"""
		t = cast(Center, self.query_one('#tools-top-view'))
		t.border_title = title
		d = cast(Markdown, self.query_one('#tools-header'))
		d.update(description)

	@property
	def toolsInput(self) -> ACMEInputField:
		return cast(ACMEInputField, self.query_one('#tools-argument'))


	@property
	def toolsExecButton(self) -> Button:
		return cast(Button, self.query_one('#tool-execute-button'))


	@property
	def toolsLog(self) -> RichLog:
		return cast(RichLog, self.query_one('#tools-log-view'))
	

	@property
	def toolsTree(self) -> ACMEToolsTree:
		# This is a bit of a hack to get the ACMEToolsTree object
		# because it is not available anymore after the DOM is removed.
		return self._toolsTree


	def on_show(self) -> None:
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
		msg = msg.replace('[', r'\[')
		self._logMessage(scriptName, f'[dim]{msg}[/dim]', 'L')


	def scriptLogError(self, scriptName:str, msg:str) -> None:
		""" Prints an error message for a script.
		
			Args:
				scriptName: The name of the script.
				msg: The message to print.	
		"""
		msg = msg.replace('[', r'\[')
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
			self.toolsTree.nodes[scriptName].set_label(f'[reverse {self._app.objectColor}]{oldLabel}')
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