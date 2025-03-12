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
	"""	The tree view for the tools and commands.
	"""

	def __init__(self, *args:Any, **kwargs:Any) -> None:	# type: ignore[no-untyped-def]
		"""	Initialize the tree view.
		
			Args:
				args: The arguments.
				kwargs: The keyword arguments.
		"""

		self.parentContainer = kwargs.pop('parentContainer', None)
		"""	The parent container. """
		
		super().__init__(*args, **kwargs)

		self.allLogs = False
		"""	Whether all logs should be shown. """

		self.logs:dict[str, List[str]] = {'Commands': []}	# Create a log for the tree root
		"""	The logs for the scripts. """

		self.nodes:dict[str, TreeNode] = {}
		"""	The nodes for the scripts. """

		self.autoRunWorker:BackgroundWorker = None
		"""	The autorun worker. """

		self.autoRunName:str = None
		"""	The name of the autorun script. """

		
	def on_mount(self) -> None:
		"""	Mount the tree view.
		"""

		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		# Build the resource tree
		self.auto_expand = False
		"""	Whether the tree should auto expand. Inherited from TextualTree. """

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
		"""	Show the tools tree.
		"""
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
	"""	The container for the tools and commands.
	"""

	BINDINGS = 	[ Binding('C', 'clear_log', 'Clear Log', key_display = 'SHIFT+C'),
	      		  Binding('l', 'toggle_log', 'Toggle Log') ]
	"""	The bindings for the container. """

	def __init__(self, *args:Any, **kwargs:Any) -> None:
		"""	Initialize the container.

			Args:
				args: The arguments.
				kwargs: The keyword arguments.
		"""
		super().__init__(*args, **kwargs)

		# Initialize the compontents in advance
		self._toolsTree:ACMEToolsTree
		"""	The tree view for the tools. """
		
		# some widgets in advance
		self._toolsArgument = ACMEInputField(label = 'Argument', id = 'tools-argument')
		"""	The input field for the tools. """

		self._toolsExecuteButton = Button('Execute', id = 'tool-execute-button', variant = 'primary')
		"""	The execute button for the tools. """

		self._toolsTopView = Center(id = 'tools-top-view')
		"""	The top view for the tools. """

		self._toolsHeader = Markdown('', id = 'tools-header')
		"""	The header for the tools. """

		self._toolsLogView = RichLog(id = 'tools-log-view', markup=True)
		"""	The log view for the tools. """


	def compose(self) -> ComposeResult:
		"""	Compose the container.

			Yields:
				The container content.
		"""

		# Prepare some widgets in advance

		# App must be assigned here. This is a workaround because the app is not available in the constructor
		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		self._toolsTree = ACMEToolsTree(f'[{self._app.objectColor}]Tools & Commands[/]', 
								 		id = 'tools-tree-view',
										parentContainer = self)
		"""	The tree view for the tools. """

		yield self._toolsTree
		with Vertical():
			with self._toolsTopView:
				yield self._toolsHeader
				with Container(id = 'tools-arguments-view'):
					with Center():
						yield self._toolsArgument
					with Center():
						yield self._toolsExecuteButton
			yield self._toolsLogView
	

	def on_mount(self) -> None:
		"""	Mount the container.
		"""
		self.toolsInput.display = False
		self.toolsExecButton.display = False
		self.toolsLog.border_title = 'Output'


	def updateHeader(self, title:str, description:Optional[str] = '') -> None:
		"""	Set the header and description of the tools view.

			Args:
				title: The title text.
				description: The description text.
		"""
		t = cast(Center, self._toolsTopView)
		t.border_title = title
		d = cast(Markdown, self._toolsHeader)
		d.update(description)

	@property
	def toolsInput(self) -> ACMEInputField:
		"""	Return the input field for the tools.
		
			Returns:
				The input field for the tools.
		"""
		return self._toolsArgument


	@property
	def toolsExecButton(self) -> Button:
		"""	Return the execute button for the tools.
		
			Returns:
				The execute button for the tools.
		"""
		return self._toolsExecuteButton


	@property
	def toolsLog(self) -> RichLog:
		"""	Return the log view for the tools.
		
			Returns:
				The log view for the tools.
		"""
		return cast(RichLog, self._toolsLogView)
	

	@property
	def toolsTree(self) -> ACMEToolsTree:
		"""	Return the tools tree.

			Returns:
				The tools tree.
		"""
		# This is a bit of a hack to get the ACMEToolsTree object
		# because it is not available anymore after the DOM is removed.
		return self._toolsTree


	def on_show(self) -> None:
		"""	Show the tools container.
		"""
		self.toolsTree.focus()

	
	def leaving_tab(self) -> None:
		"""	Leaving the tab.

			Stop the autorun script if any.
		"""
		self.toolsTree.stopAutoRunScript()

	
	@on(Button.Pressed, '#tool-execute-button')
	def buttonExecute(self) -> None:
		"""	Callback for the execute button.
		"""
		_executeScript(str(self.toolsTree.cursor_node.label), argument = str(self.toolsInput.value))
	

	@on(ACMEInputField.Submitted)
	def inputFieldSubmitted(self) -> None:
		"""	Callback for the input field.
		"""
		self.buttonExecute()


	def action_clear_log(self) -> None:
		"""	Clear the log view.
		"""
		# Clear the log view
		self.toolsLog.clear()

		# Clear the log for the current script
		if (_l := str(self.toolsTree.cursor_node.label)) in self.toolsTree.logs:
			self.toolsTree.logs[_l] = []


	def action_toggle_log(self) -> None:
		"""	Toggle the log view.
		"""
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
		"""	Logs a message for a script.

			Args:
				scriptName: The name of the script.
				msg: The message to log.
				prefix: The prefix for the message.
		"""	
		
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