#
#	Interpreter.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of a simple batch command processor.
#

"""	The interpreter module implements an extensible scripting and batch runtime.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import namedtuple
from enum import IntEnum, auto
from decimal import Decimal, InvalidOperation
import datetime, time, re, copy, random, shlex, operator
from typing import 	Callable, Dict, Tuple, Union

_maxProcStackSize = 64	
""" Max number of recursive procedures calls. """

class PState(IntEnum):
	"""	The internal states of a script.
	"""
	created 				= auto()
	"""	Script has been created. """
	ready 					= auto()
	"""	Script is read to run. """
	running 				= auto()
	""" Script is running. """
	canceled 				= auto()
	""" Running of the script is canceled externally. """
	terminated 				= auto()
	"""	Script terminated normally. """
	terminatedWithResult	= auto()
	""" Script terminated normally with a result. """
	terminatedWithError 	= auto()
	""" Script terminated with an error. """


class PError(IntEnum): 
	"""	Error codes.
	"""
	assertionFailed			= auto()
	canceled				= auto()
	divisionByZero			= auto()
	interrupted				= auto()
	invalid					= auto()
	maxProceduresExceeded 	= auto()
	nestedProcedure			= auto()
	noError 				= auto()
	notANumber				= auto()
	quitWithError			= auto()
	timeout					= auto()
	undefined				= auto()
	unexpectedArgument		= auto()
	unexpectedCommand		= auto()


@dataclass
class PScope():
	"""	Scope-specific data points.
	"""
	name:str				= None
	argument:str			= ''
	result:str				= None
	returnPc:int			= 0
	whileStack:list[int]	= field(default_factory = list)
	whileLoop:dict[int, int]= field(default_factory = dict)	# Loop counter for while loops, automatic incremented
	ifLevel:int				= 0
	switchLevel:int			= 0


class PContext():
	"""	Process context for a single script. Can be re-used.s
	"""

	def __init__(self, 
				 script:Union[str,list[str]],
				 commands:PCmdDict 				= None,
				 macros:PMacroDict 				= None,
				 logFunc:PLogCallable 			= lambda pcontext, msg: print(f'** {msg}'),
				 logErrorFunc:PErrorLogCallable	= lambda pcontext, msg, exception: print(f'!! {msg}'),
				 printFunc:PLogCallable 		= lambda pcontext, msg: print(msg),
				 preFunc:PFuncCallable			= None,
				 postFunc:PFuncCallable			= None,
			 	 errorFunc:PFuncCallable		= None,
				 matchFunc:PMatchCallable		= lambda pcontext, l, r: l == r,
				 maxRuntime:float				= None) -> None:
		"""	Initialize the process context.

			Args:
				script: A single \\n-seprated string, or a list of strings.
				commands: An optional list of additional commands and their callbacks.
				macros: An optional list of additional commands and their callbacks.
				logFunc: An optional callback for log messages (and the LOG command). The default is the normal print() function.
				logErrorFunc: An optional callback for error log messages (and the ERROR command). The default is the normal print() function.
				printFunc: An optional callback for PRINT command messages. The default is the normal print() function.
				preFunc: An optional callback that is called with the PContext object just before the script is executed. Returning *None* prevents the script execution.
				postFunc: An optional callback that is called with the PContext object just after the script finished execution.
				errorFunc: An optional callback that is called with the PContext object when encountering an error during script execution.
				matchFunc: An optional callback that is called to perform matches. This could be, for example, a regex matcher. The default is just a normal compare for equality.
				maxRuntime: An optional limitation for script runtime in seconds.
		"""
		
		# Extra parameters that can be provided
		self.script							= script
		self.extraCommands					= commands
		self.extraMacros					= macros
		self.logFunc						= logFunc
		self.logErrorFunc					= logErrorFunc
		self.printFunc						= printFunc
		self.preFunc						= preFunc
		self.postFunc						= postFunc
		self.errorFunc						= errorFunc
		self.matchFunc						= matchFunc
		self.maxRuntime						= maxRuntime

		# State, result and error attributes
		self.pc:int 						= 0
		self.state:PState 					= PState.created
		self.error:PErrorState				= PErrorState(PError.noError, 0, '', None )
		self.meta:Dict[str, str]			= {}
		self.variables:Dict[str,str]		= {}
		self.environment:Dict[str,str]		= {}	# Similar to variables, but not cleared
		self.runs:int						= 0

		# Internal attributes that should not be accessed from extern
		self._length:int					= 0
		self._maxRTimestamp:float			= None
		self._scopeStack:list[PScope]		= []
		self._commands:PCmdDict				= None		# builtins + provided commands
		self._macros:PMacroDict				= None		# builtins + provided macros
		self._verbose:bool					= None		# Store the runtime verbosity of the run() function
		self._line:str						= ''		# Currently executed line

		#
		# Further initializations and copying of context information
		#

		# If the script is just a string then convert it to a list of strings 
		self.script = self.script if isinstance(self.script, list) else self.script.splitlines()

		# Strip and prepare lines
		self.script = [ line.strip().replace('\t', ' ') for line in self.script ] # strip all input lines
		self._length = len(self.script)

		# Extract meta data
		# These are lines in the format:
		#	@key [<argument> ... ]
		# where <argument> is optional.
		# The following line works like this: create an array of partitions of all @-lines. Then extract partitions, remove @, and build the dictionary
		self.meta = { p[0][1:].lower():p[2] for p in [ line.partition(' ') for line in self.script if line.startswith('@') ] if len(p[0]) > 1 }

		# Create a dictionary of commands from the builtins and, if available, 
		# from the provided commands dictionary.
		self._commands = copy.deepcopy(_builtinCommands)
		if self.extraCommands:
			self._commands.update( { k:v for k,v in self.extraCommands.items() if k not in self._commands } )

		# Create a dictionary of macros from the builtins and, if available, 
		# from the provided macros dictionary.
		self._macros = copy.deepcopy(_builtinMacros)
		if self.extraMacros:
			self._macros.update( { k:v for k,v in self.extraMacros.items() if k not in self._macros } )
		
		# Set state to ready
		self.state = PState.ready


	def run(self, verbose:bool = False, argument:str = '') -> PContext:
		"""	Run the script.

			Args:
				verbose: Boolean to indicate whether each executed line shall be logged.
				argument: String with the argument(s)
			Return:
				PContext object, or None in case of an error.
		"""
		global run
		self.runs += 1
		return run(self, verbose = verbose, argument = argument)


	def stop(self) -> None:
		"""	Try to terminate the script by setting its state to canceled.
		"""
		self.state = PState.canceled
		self.setError(PError.canceled, f'Script canceled')


	def validate(self) -> bool:
		"""	Validate script. Prevent macros as commands.

			Return:
				Boolean that indicates the validation status.
		"""
		while (line := self.nextLine):
			if line.startswith('['):
				self.setError(PError.invalid, f'Macros and variables are not allowed as command: {line}')
				return False
		return True


	@property
	def nextLine(self) -> str:
		"""	Return the next line in a batch. This depends on the internal program counter (pc).
			Empty lines and comments are skipped.
			The program counter is incremented accordingly.
			Macros and variables are NOT evaluated.

			Return:
				The next line in the script.
		"""
		while True:
			if self.pc >= self._length:
				return None
			line = self.script[self.pc]
			self.pc += 1 
			# Only return not-empty lines and no comments 			
			if line and not self.ignoreLine(line):
				break
		self._line = line
		return line
	

	def nextLinePartition(self, sep:str = ' ') -> Tuple[str, str, str, str]:
		"""	Return the next line in the script, and partition it. Return the partitions as
			well as the line itself in a tuple: cmd, separator, rest, line.

			Args:
				sep: Separator for partitioning the command from the rest of the arguments.
			Returns:
				Tuple: command, separator, rest of the line, full line
		"""
		if (line := self.nextLine) is None:
			return None, None, None, None
		cmd, found, arg = line.lower().partition(sep)
		return cmd, found, arg, line
	
	
	def remainingLinesAsString(self, prefix:str = None, upto:str = None, ignoreComments:bool = True) -> str:
		"""	Return the remaining lines in a script as a single string, including the current one. Lines are still
			separated with \\n.

			Args:
				prefix: If *prefix* is given then it is added to the begining of the result.
				upto:  If *upto* is given then only the lines up to the first line that starts with *upto* are returned.
				ignoreComments: If set to True then comment lines are not included in the result.
			Return:
				String with all the remaining lines in a single string.
		"""
		# replace comments etc with empty lines to keep the number of lines to skip the same
		lines:Union[str, list[str]] = None
		if ignoreComments:
			lines = [ l if not self.ignoreLine(l) else ''  for l in self.script[self.pc:] ]	
		else:
			lines = self.script[self.pc:]

		end = len(lines)
		if upto is not None:
			end = 0
			for l in lines:
				if l.lower().startswith(upto):
					break
				end += 1
		if prefix is not None:	# prefix could be an empty string, but this is not None
			return prefix + '\n' + '\n'.join(lines[:end])
		return '\n'.join(lines[:end])
	

	def ignoreLine(self, line:str) -> bool:
		"""	Test whether a line should be ignored.
		
			For example a comment (ie. the line starts with # or //), or meta data (ie, the line starts with @). 
			White spaces before the characters are ignored.

			Args:
				line: The line to test.
			Return:
				Boolean indicating whether a line shall be ignored.
		"""
		return line.startswith(('#', '//', '@'))
	

	def reset(self) -> None:
		"""	Reset the context / script. 
		
			
			This methoth ,ay also be implemented in a sub-class, but the must then call this method as well.
		"""
		self.pc = 0
		self.error = PErrorState(PError.noError, 0, '', None)
		self.variables.clear()
		self._scopeStack.clear()
		self.saveScope(pc = -1, name = self.meta.get('name'))
		self.state = PState.ready


	def setError(self, error:PError, msg:str, pc:int = -1, state:PState = PState.terminatedWithError, exception:Exception = None) -> None:
		"""	Set the internal state and error codes. 
		
			These can be retrieved by accessing the state and error	attributes.

			Args:
				error: PError to indicate the type of error.
				msg: String that further explains the error.
				pc: Integer, the program counter pointing at the line causing the error. Default -1 means the current pc.
				state: PState to indicate the state of the script. Default is "terminatedWithError".
				exception: Optional exception to provide with the error message.
		"""
		self.state = state
		self.error = PErrorState(error, self.pc if pc == -1 else pc, msg, exception)


	@property
	def result(self) -> str:
		"""	The last result of a procedure, while etc. 
		
			The result is only valid within the calling scope and before the next
			call to a procedure, while, etc.

			Return:
				String with the result
		"""
		return self.scope.result
	

	@result.setter
	def result(self, value:str) -> None:
		"""	Set the result to the current scope.

			Args:
				value: String to set the result to.
		"""
		self.scope.result = value


	@property
	def argument(self) -> str:
		"""	Return the argument of the current scope (procedure).

			Returns:
				The argument of the current scope.
		"""
		return self.scope.argument
	

	@argument.setter
	def argument(self, value:str) -> None:
		"""	Set the argument for the current scope.

			Args:
				value: The argument for the current scope.
		"""
		self.scope.argument = value


	@property
	def ifLevel(self) -> int:
		"""	Return the nested IF-commands of the current scope.

			Return:
				Integer, the IF-Level.
		"""
		return self.scope.ifLevel


	@ifLevel.setter
	def ifLevel(self, level:int) -> None:
		"""	Set the number of nested IF-commands of the current scope.

			Args:
				level: Integer, the IF-level of the current scope.
		"""
		self.scope.ifLevel = level


	@property
	def switchLevel(self) -> int:
		"""	Return the nested SWITCH-commands of the current scope.

			Return:
				Integer, the SWITCH-Level.
		"""
		return self.scope.switchLevel


	@switchLevel.setter
	def switchLevel(self, level:int) -> None:
		"""	Set the number of nested SWITCH-commands of the current scope.

			Args:
				level: Integer, the SWITCH-level of the current scope.
		"""
		self.scope.switchLevel = level


	def saveScope(self, pc:int = None, arg:str = None, name:str = None) -> bool:
		"""	Save the current program counter and other information to the scope stack. 
			This creates a new scope.

			Args:
				pc: Program counter.
				arg: Arguments for the scope.
				name: Name of the scope. Relevant for procedures.
			Return:
				Boolean, whether setting of the scope succeeded.
		"""
		if len(self._scopeStack) == _maxProcStackSize:
			self.setError(PError.maxProceduresExceeded, f'Max level of PROCEDURE calls exceeded')
			return False
		if pc == None:
			pc = self.pc
		self._scopeStack.append(PScope(returnPc = pc, argument = arg, name = name))
		return True
	

	def restoreScope(self) -> bool:
		"""	Restore the program counter and other information from the scope stack.
			This removes the current scope and replaces it with the previous scope.

			Return:
				Boolean, indicating whether the scope could be restored.
		"""
		if not len(self._scopeStack):
			self.setError(PError.invalid, f'No scope to restore')
			return False
		sc = self._scopeStack.pop()
		self.pc = sc.returnPc
		self.scope.result = sc.result	# assign the old scope the result from the previous scope
		return True

	
	@property
	def scope(self) -> PScope:
		"""	Get the current scope as a property.

			Return:
				PScope object, the current scope, or None.
		"""
		if not self._scopeStack:
			return None
		return self._scopeStack[-1]


	def saveWhileState(self) -> None:
		"""	Save the current program counter to the while stack.
			This is used to keep the beginning line of the while loop.
		"""
		self.scope.whileStack.append(self.pc-1)	# point to the line with the while. 
												# pc was post-incremented after reading the line with the while	


	def restoreWhileState(self) -> None:
		"""	Restore the program counter from the while stack.
		"""
		if len(self.scope.whileStack) > 0:
			self.scope.whileStack.pop()

	def addWhileLoop(self) -> None:
		"""	Save the current while program counter and initialize it with 0.
			This is used to keep the beginning line of the while loop.
			It is only done once because we need to keep the counter!
		"""
		if not self.whilePc in self.scope.whileLoop:
			self.scope.whileLoop[self.whilePc] = 0


	def removeWhileLoop(self) -> None:
		"""	Remove the current while loop's counter.
		"""
		if self.whilePc in self.scope.whileLoop:
			del self.scope.whileLoop[self.whilePc]


	def incrementWhileLoop(self) -> int:
		"""	Increment the current while loop's counter by 1.

			Return:
				The new value of the loop counter, or 0
		"""
		if (l := self.scope.whileLoop.get(self.whilePc)) is not None:
			self.scope.whileLoop[self.whilePc] = l + 1
			return l + 1
		return 0
	

	def whileLoopCounter(self) -> int:
		"""	Return the latest loop counter for a while loop.

			Return:
				Integer, the loop counter for the current while loop.
		"""
		# The following is important. When the line with the "while ..." loop is evaluated for the first time
		# then no loop counter for this line exists. Also, the whilePc variable that points to the to while start line
		# is not yet set. This is while we need to check the program counter instead, and return a 0 as a default
		# if nothing has been assigned yet. Otherwise this would return the loop counter for that while.
		# If the line isn't a "while ..." then we can savely return the normal loop counter for the while.
		line = self._line
		if line.lower().startswith('while'):
			return self.scope.whileLoop.get(self.pc - 1, 0)
		if (loop := self.scope.whileLoop.get(self.whilePc)) is None:
			self.setError(PError.undefined, f'Undefined variable: loop')
			return None
		return loop


	@property
	def whilePc(self) -> int:
		"""	Return the latest saved program counter for a while loop.

			Return:
				Integer, the program counter that points to the top of the current while scope, or *None* when the whileStack is empty.
		"""
		if not self.scope.whileStack:
			return None
		return self.scope.whileStack[-1]


	@property
	def name(self) -> str:
		"""	The name of the current scope. This could be the name
			of the current script (from the meta data) or the name of the 
			current procedure.

			Returns:
				The name of the current scope, or None.
		"""
		return self.scope.name if self.scope else None
	

	@property
	def scriptName(self) -> str:
		"""	The name of the scriptt script (from the meta data).

			Returns:
				The name of the script, or None.
		"""
		return self.meta.get('name')


	@scriptName.setter
	def scriptName(self, name:str) -> None:
		"""	Set the name of the script in the meta data.

			Args:
				name: Name of the script.
		"""
		self.meta['name'] = name
	

	def getMeta(self, key:str) -> str:
		"""	Return the argument of meta data, or an empty string.

			Args:
				key: Key of the meta data to look for.
			Return:
				String, value or empty string.
		"""
		if v := self.meta.get(key):
			return v
		return ''
	

	def getVariable(self, key:str) -> str:
		"""	Return a variable for a case insensitive name.

			Args:
				key: Variable name
			Return:
				Variable content, or None.		
		"""
		return self.variables.get(key.lower())
	

	def setVariable(self, key:str, value:str) -> None:
		"""	Set a variable for a case insensitive name.

			Args:
				key: Variable name
				value: Value to store	
		"""
		self.variables[key.lower()] = value
	

	def delVariable(self, key:str) -> str:
		"""	Delete a variable for a case insensitive name.

			Args:
				key: Variable name
			Return:
				Variable content, or None if variable is not defined.		
		"""
		key = key.lower()
		if key in self.variables:
			v = self.variables[key]
			del self.variables[key]
			return v
		return None


	def getEnvironmentVariable(self, key:str) -> str:
		"""	Return an evironment variable for a case insensitive name.

			Args:
				key: Environment variable name
			Return:
				Environment variable content, or None.		
		"""
		return self.environment.get(key.lower())
	

	def setEnvironmentVariale(self, key:str, value:str) -> None:
		"""	Set an environment variable for a case insensitive name.

			Args:
				key: Environment variable name
				value: Value to store	
		"""
		self.environment[key.lower()] = value
	

	def clearEnvironment(self) -> None:
		"""	Clear the environment variables.
		"""
		self.environment.clear()


	def setEnvironment(self, environment:dict[str, str] = {}) -> None:
		"""	Clear old and assign a new environment.
			
			Args:
				environment: Dictionary with the new environment
		"""
		self.clearEnvironment()
		for eachKey, eachValue in environment.items():
			self.setEnvironmentVariale(eachKey, eachValue)


	def getMacro(self, key:str) -> PMacroCallable:
		"""	Return a macro callable for a case insensitive name.

			Args:
				key: Macro name
			Return:
				Macro callable, or None.		
		"""
		return self._macros.get(key.lower())


##############################################################################
#
#	Type definitions
#

# TODO docs bellow

PFuncCallable = Callable[[PContext], PContext]
"""	Function callback for pre, post and error functions.
"""

PLogCallable = Callable[[PContext, str], None]
"""	Function callback for log functions.
"""

PErrorLogCallable = Callable[[PContext, str, Exception], None]
"""	Function callback for error og functions.
"""

PCmdCallable = Callable[[PContext, str], PContext]
"""	Signature of a command callable.
"""

PCmdDict = Dict[str, PCmdCallable]
"""	Function callback for commands. The callback is called with a `PContext` object
	and is supposed to return it again, or None in case of an error.
	# TODO
"""

PMacroCallable = Callable[[PContext, str, str], str]
"""	Signature of a macro callable.
# TODO
"""

PMatchCallable = Callable[[PContext, str, str], bool]
"""	Signature of a match function callable.

	It will get called with the current `PContext` instance,
	a regular expression, and the string to check. It must return
	a boolean value that indicates the result of the match.
"""


PMacroDict = Dict[str, PMacroCallable]
"""	Function callback for macros. 

	The callback is called with a `PContext` object and returns a string.
"""


PErrorState = namedtuple('PErrorState', [ 'error', 'line', 'message', 'exception' ])
"""	Named tuple that represents an error state. 

	It contains the error code, the line number, and the error message.
"""


##############################################################################
#
#	Run a script
#

def run(pcontext:PContext, verbose:bool = False, argument:str = '', procedure:str = None) -> PContext:
	"""	Run a script. 
		
		An own, extended `PContext` instance can be provided, that supports extra commands and macros.
		If the method is been called for running a whole script (not only a procedure), then the
		*pcontext* instance is reset (see `PContext.reset()`).

		Args:
			pcontext: Current PContext for the script.
			verbose: Log each executed line.
			argument: The argument to the script, available via the *argv* macro.
			procedure: Optional. If assigned then it must contain the name of a procedure.
				In this case, a procedure defined in the script is called. Afterwards, execution
				is stopped.
		Return:
			PContext object, or None in case of an error.
		"""

	def _terminating(pcontext:PContext) -> None:
		"""	Handle the error setup, fill in error and message, and call the error and post function callbacks.
			Don't overwrite already set error values.
				
			Args:
				pcontext: Current PContext for the script.
		"""
		if pcontext.error.error not in [ PError.noError, PError.quitWithError ]:
			_doLog(pcontext, f'{pcontext.error.line}: {pcontext.error.message}', isError = True, exception = pcontext.error.exception)
			if pcontext.errorFunc:
				pcontext.errorFunc(pcontext)
		if pcontext.state != PState.ready and pcontext.postFunc:	# only when really running, after preFunc succeeded
			pcontext.postFunc(pcontext)


	# Validate script first.
	if not pcontext.validate():
		return pcontext
	if not procedure:	# only reset when not executing a procedure
		pcontext.reset()
	pcontext.argument = argument
	pcontext._verbose = verbose
	
	# Call Pre-Function
	if pcontext.preFunc:
		if pcontext.preFunc(pcontext) is None:
			pcontext.setError(PError.canceled, 'preFunc canceled', state=PState.canceled)
			_terminating(pcontext)
			return pcontext

	# Start running
	pcontext.state = PState.running
	if pcontext.maxRuntime is not None:	# set max runtime
		pcontext._maxRTimestamp = datetime.datetime.utcnow().timestamp() + pcontext.maxRuntime
	if scriptName := pcontext.scriptName:
		pcontext.logFunc(pcontext, f'Running script: {scriptName}, arguments: {argument}, procedure: {procedure}')

	# If procedure is set then the program counter is set to run a procedure with that name.
	# Or return an error
	# Only that procedure is executed
	if procedure is not None:
		if (result := _executeProcedure(pcontext, procedure, pcontext.argument)):
			pcontext = result
		else:
			pcontext.setError(PError.undefined, f'Undefined procedure: {procedure}')
			pcontext.result = None
			return pcontext

	# main processing loops
	endScriptStates = [ PState.canceled, PState.terminated, PState.terminatedWithResult, PState.terminatedWithError ]
	while (line := pcontext.nextLine) is not None and pcontext.state not in endScriptStates:

		# If we only run a procedure that ignore every scope that is not the proc
		# if procedure is set and we are just in the lowest script scope then we ignore that line:
		if procedure and len(pcontext._scopeStack) == 1:
			continue

		# Check for timeout
		if pcontext._maxRTimestamp is not None and pcontext._maxRTimestamp < datetime.datetime.utcnow().timestamp():
			pcontext.setError(PError.timeout, f'Script timeout ({pcontext.maxRuntime} s)')
			pcontext.state = PState.terminatedWithError
			break

		# Resolve macros and variables
		if (line := checkMacros(pcontext, line)) is None:
			pcontext.state = PState.terminatedWithError
			break

		# get command and arguments
		if verbose:
			pcontext.logFunc(pcontext, f'{pcontext.pc}: {line}')
		cmd, _, arg = line.partition(' ')
		cmd = cmd.lower()
		if cmd in pcontext._commands:
			# Buildin command
			if (cb := pcontext._commands.get(cmd)):
				try:
					if (result := cb(pcontext, arg.strip())):
						pcontext = result
					else:
						pcontext.state = PState.terminatedWithError
				except SystemExit:
					raise
				except Exception as e:
					pcontext.setError(PError.invalid, f'Error: {e}', exception = e)
			else:
				# Ignore "empty" (None) commands
				pass
		
		elif (result := _executeProcedure(pcontext, cmd, arg.strip())):
			pcontext = result

		else:
			pcontext.setError(PError.undefined, f'Undefined command: {line}')
			break
	
	# Determine the error states and codes
	# DONT remove the result when we only execute a procedure
	if pcontext.state != PState.terminatedWithResult and not procedure:
		pcontext.result = None
	if pcontext.state not in endScriptStates:
		# Check whether we reached the end of the script, but haven't ended a procedure
		if len(pcontext._scopeStack) > 1:
			pcontext.setError(PError.unexpectedCommand, f'PROCEDURE without return', pcontext.scope.returnPc )
		elif pcontext.whilePc is not None:
			pcontext.setError(PError.unexpectedCommand, f'WHILE without ENDWHILE', pcontext.scope.returnPc )

	# Return after running. Set the pcontext.state accordingly
	pcontext.state = PState.terminated if pcontext.state == PState.running else pcontext.state
	_terminating(pcontext)
	return pcontext


##############################################################################
#
#	Extra utility functions
#

def tokenize(line:str) -> list[str]:
	"""	Tokenize an input string.

		This function tokenizes a string like a shell command line. It takes quoted
		arguments etc into account.

		Args:
			line: String with arguments, possibly quoted.
		Return:
			List of tokens / arguments.
	"""
	return shlex.split(line)


##############################################################################
#
#	Build-in commands
#

def _doAssert(pcontext:PContext, arg:str) -> PContext:
	"""	Assert the condition. If it fails return None and interrupt the script.

		Args:
			pcontext: Current PContext for the script.
			arg: Assertion expression
		Return:
			The PContext object, or None in case of an error.
	"""
	if (result := _boolResult(pcontext, arg)) is None:
		return None
	if not result:
		pcontext.setError(PError.assertionFailed, f'Assertion failed: {arg}')
		return None
	return pcontext


def _doBreak(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a break command operation.

		Args:
			pcontext: Current PContext for the script.
			arg: The argument of the break, used as the result of a while
		Return:
			The PContext object, or None in case of an error.
	"""
	if pcontext.whilePc is None:
		pcontext.setError(PError.unexpectedCommand, 'BREAK without WHILE')
		return None
	pcontext.result = arg
	return _skipWhile(pcontext)	# jump out of while


def _doCase(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a case command operation. This command must occur only in a SWITCH block.

		Args:
			pcontext: Current PContext for the script.
			arg: The argument of the break statement, used to match the SWITCH argument.
		Return:
			The PContext object, or None in case of an error.
	"""
	if pcontext.switchLevel == 0:
		pcontext.setError(PError.unexpectedCommand, 'CASE without SWITCH')
		return None
	return _skipSwitch(pcontext, None, skip = True)	# jump out of switch


def _doContinue(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a continue command operation.

		Args:
			pcontext: Current PContext for the script.
			arg: not used.
		Return:
			The PContext object, or None in case of an error.
	"""
	if (wpc := pcontext.whilePc) is None:
		pcontext.setError(PError.unexpectedCommand, 'CONTINUE without WHILE')
		return None
	pcontext.pc = wpc	# jump back to while
	return pcontext


def _doPrint(pcontext:PContext, arg:str) -> PContext:
	"""	Print the argument to the console. If an print-callback
		was given when starting the script then that callback
		is called instead.

		Args:
			pcontext: Current PContext for the script.
			arg: The output to log.
		Return:
			The PContext object, or None in case of an error.
	"""
	if pcontext.printFunc:
		pcontext.printFunc(pcontext, arg)
	return pcontext


def _doElse(pcontext:PContext, arg:str) -> PContext:
	"""	Regularly, ELSE is only encountered at the end of an IF part of an IF statement.
		The pcontext's pc already points to the next statement.

		Args:
			pcontext: Current PContext for the script.
			arg: Else shall have no argument.
		Return:
			PContext object, or None in case of an error.
	"""
	if arg:
		pcontext.setError(PError.unexpectedArgument, 'ELSE has no argument')
		return None
	if pcontext.ifLevel == 0:
		pcontext.setError(PError.unexpectedCommand, 'ELSE without IF')
		return None
	return _skipIfElse(pcontext, isIf = False)


def _doEndIf(pcontext:PContext, arg:str) -> PContext:
	"""	Check the conditions that we are at the end of a regular IF or ELSE.

		Args:
			pcontext: Current PContext for the script.
			arg: ENDIF shall have no argument.
		Return:
			PContext object, or None in case of an error.
	"""
	if arg:
		pcontext.setError(PError.unexpectedArgument, 'ENDIF has no argument')
		return None
	if pcontext.ifLevel == 0:
		pcontext.setError(PError.unexpectedCommand, 'ENDIF without IF')
		return None
	pcontext.ifLevel -= 1
	return pcontext


def _doEndProcedure(pcontext:PContext, arg:str) -> PContext:
	"""	Handle an ENDPROCEDURE command operation. Copy the result to the previous scope.

		Args:
			pcontext: Current PContext for the script.
			arg: The result of the procedure.
		Return:
			PContext object, or None in case of an error.
	"""
	if pcontext.scope is None:
		pcontext.setError(PError.unexpectedCommand, 'ENDPROCEDURE without PROCEDURE')
		return None
	name = pcontext.name	# copy the name of the procedure. Gone after restoreScope
	pcontext.restoreScope()
	pcontext.result = arg	# Copy the argument (ie the result) to the previous scope
	return pcontext


def _doEndSwitch(pcontext:PContext, arg:str) -> PContext:
	"""	Handle an ENDSWITCH command. This ends a SWITCH block, and must only occurs as the last
		command of a SWITCH block.

		Args:
			pcontext: Current PContext for the script.
			arg: The result of the procedure, must be empty.
		Return:
			PContext object, or None in case of an error.
	"""
	if pcontext.switchLevel == 0:
		pcontext.setError(PError.unexpectedCommand, f'ENDSWITCH without SWITCH')
		return None
	if arg:
		pcontext.setError(PError.unexpectedArgument, 'ENDSWITCH has no argument')
		return None
	pcontext.switchLevel -= 1
	return pcontext

	
def _doEndWhile(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a endwhile command operation. Copy the argument as the result
		to the scope's result. This is only used when the while loop exits
		normally, but not via the BREAK command, which may provide an own 
		argument.

		Args:
			pcontext: Current PContext for the script.
			arg: The result of the while.
		Return:
			PContext object, or None in case of an error.
	"""
	if (wpc := pcontext.whilePc) is None:
		pcontext.setError(PError.unexpectedCommand, f'ENDWHILE without WHILE')
		return None
	pcontext.restoreWhileState()
	pcontext.result = arg	# copy arg as result
	pcontext.pc = wpc
	return pcontext


def _doError(pcontext:PContext, arg:str) -> PContext:
	"""	End script execution with an error. The optional argument will be 
		assigned as the result of the script (pcontect.result).

		Args:
			pcontext: Current PContext for the script.
			arg: The result of the script.
		Return:
			PContext object, or None in case of an error.
	"""
	pcontext.state = PState.terminatedWithError
	pcontext.setError(PError.quitWithError, arg)
	return None


def _doIf(pcontext:PContext, arg:str) -> PContext:
	"""	Handle an if...else...endif command operation.

		Args:
			pcontext: Current PContext for the script.
			arg: The IF-expressions.
		Return:
			PContext object, or None in case of an error.
	"""
	pcontext.ifLevel += 1
	if (result := _boolResult(pcontext, arg)) is None:
		return None
	if not result:
		# Skip to else or endif if False(!).
		return _skipIfElse(pcontext, isIf = True)
	return pcontext


def _doIncDec(pcontext:PContext, arg:str, isInc:bool = True) -> PContext:
	"""	Increment or decrement a variable by an optional value.
		The default is 1.

		Args:
			pcontext: Current PContext for the script.
			arg: The value to increment/decrement the variable. The default is 1.
			isInc: Indicate whether to increment or decrement.
		Return:
			PContext object, or None in case of an error.
	"""
	var, _, value = arg.partition(' ')
	value = value.strip()
	if (variable := pcontext.getVariable(var)) is None:
		pcontext.setError(PError.undefined, f'undefined variable: {var}')
		return None
	try:
		n = Decimal(value) if len(value) > 0 else Decimal(1.0)	# either a number or 1.0 (default)
		pcontext.setVariable(var, str(Decimal(variable) + n) if isInc else str(Decimal(variable) - n))
	except InvalidOperation as e:
		pcontext.setError(PError.notANumber, f'Not a number: {e}')
		return None
	return pcontext


def _doLog(pcontext:PContext, arg:str, isError:bool = False, exception:Exception = None) -> PContext:
	"""	Print a message to the debug or to the error. Either the internal or a provided log function.

		Args:
			pcontext: Current PContext for the script.
			arg: The message to log.
			isError: Indicate whether this message will be logged as an error or a normal log message.
		Return:
			PContext object, or None in case of an error.
	"""
	if isError:
		if pcontext.logErrorFunc:
			pcontext.logErrorFunc(pcontext, arg, exception)
	else:
		if pcontext.logFunc:
			pcontext.logFunc(pcontext, arg)
	return pcontext


def _doProcedure(pcontext:PContext, arg:str) -> PContext:
	"""	Define a procedure. Actually, jump over all instructions until endprocedure, but report
		an error if a procedure is defined within a procedure.

		Args:
			pcontext: Current PContext for the script.
			arg: Not used.
		Return:
			PContext object, or None in case of an error.
	"""
	while pcontext.pc < pcontext._length:
		cmd, _, _, _ = pcontext.nextLinePartition()
		# test for nested procedures
		if cmd == 'procedure':
			# not allowed
			pcontext.setError(PError.nestedProcedure, 'Nested procedures are not allowed')
			return None
		# Either a normal endprocedure or one with an argument/result
		if cmd == 'endprocedure':
			return pcontext
	# Reached end of script
	pcontext.setError(PError.unexpectedCommand, 'PROCEDURE without ENDPROCEDURE')
	return None


def _doQuit(pcontext:PContext, arg:str) -> PContext:
	"""	End script execution. The optional argument will be 
		assigned as the result of the script (pcontect.result).

		Args:
			pcontext: Current PContext for the script.
			arg: The result of the script.
		Return:
			PContext object, or None in case of an error.
	"""
	if arg:
		pcontext.state = PState.terminatedWithResult
		pcontext.result = arg
	else:
		pcontext.state = PState.terminated
		pcontext.result = None
	return pcontext


def _doSet(pcontext:PContext, arg:str) -> PContext:
	"""	Set a variable. This command behaves differently depending on how it 
		is used.

		- SET <variable> <any value> : Assigns a value/string/other variable
		- SET <variable> = <expression> : Assigns the result of an expression
		- SET <variable> - Deletes the variable

		Args:
			pcontext: Current PContext for the script.
			arg: The arguments to the SET command.
		Return:
			PContext object, or None in case of an error.
	"""

	def testMacro(name:str) -> bool:
		"""	Test whether we would overwrite a built-in macro.
		
			Args:
				name: The macro name
			Return:
				Boolean
		"""
		if pcontext.getMacro(name) is not None:
			pcontext.setError(PError.invalid, f'Overwriting built-in macro is not allowed: {var}')
			return False
		return True


	# Check whether this is an expression asignment
	# var, found, value = arg.partition('=')
	# if found:	# = means assignment
	# 	var = var.strip()
	# 	value = value.strip()

	# 	# Test for overwrite macro
	# 	if not testMacro(var):
	# 		return None

	# 	try:
	# 		if (result := str(_calcExpression(pcontext, value))) is None:
	# 			return None
	# 	except ConversionSyntax as e:
	# 		pcontext.setError(PError.notANumber, f'Not a number: {e}')
	# 		return None
	# 	except ZeroDivisionError as e:
	# 		pcontext.setError(PError.divisionByZero, f'Division by zero: {arg}')
	# 		return None
	# 	pcontext.setVariable(var, str(result))
	# 	return pcontext

	# Else: normal assignment
	var, _, value = arg.partition(' ')
	var = var.strip()

	# Test for overwrite macro
	if not testMacro(var):
		return None

	# remove variable if no value
	if not value:	
		if pcontext.delVariable(var) is None:
			pcontext.setError(PError.undefined, f'Undefined variable: {var}')
			return None
		return pcontext

	# Just assign
	pcontext.setVariable(var, value.strip())
	return pcontext


def _doSleep(pcontext:PContext, arg:str) -> PContext:
	"""	Sleep for a number of seconds. 
	
		This command can be interrupted when the script's state is set to *canceled*.

		Args:
			pcontext: Current PContext for the script.
			arg: Number of seconds to sleep.
		Return:
			Current PContext object, or None in case of an error.
	"""
	try:
		toTs = time.time() + float(arg)
		while pcontext.state == PState.running and toTs > time.time():
			time.sleep(0.01)
	except ValueError as e:
		pcontext.setError(PError.notANumber, f'Not a number: {e}')
		return None
	except KeyboardInterrupt:
		pcontext.setError(PError.interrupted, 'Keyboard interrupt')
		return None
	return pcontext


def _doSwitch(pcontext:PContext, arg:str) -> PContext:
	"""	Start a SWITCH block. 
	
		SWITCH blocks might be nested.

		Args:
			pcontext: Current PContext for the script.
			arg: Argument of the SWITCH to compare the CASE statements against.
		Return:
			Current PContext object, or None in case of an error.
	"""
	if not arg:
		arg = 'true'
	pcontext.switchLevel += 1
	return _skipSwitch(pcontext, arg)	# Skip to the correct switch block


def _doWhile(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a while...endwhile command operation.

		Args:
			pcontext: Current PContext for the script.
			arg: The comparison for the while loop.
		Return:
			Current PContext object, or None in case of an error.
	"""
	wpc = pcontext.whilePc
	if wpc is None or wpc != pcontext.pc:	# Only put this while on the stack if we just run into it for the first time
		pcontext.saveWhileState()
		pcontext.addWhileLoop()
	if (result := _boolResult(pcontext, arg)) is None:
		return None
	if not result:
		# Skip to endwhile if False(!).
		return _skipWhile(pcontext)
	pcontext.incrementWhileLoop()	# Increment the loop counter for this while loop
	return pcontext


##############################################################################
#
#	Build-in Macros
#

def _doAnd(pcontext:PContext, arg:str, line:str) -> str:
	"""	With the *and* macro one can evaluate boolean expressions and combine them with a boolean "and".

		The *and* macro will evaluate to *true* (all boolean expressions are true) or *false* 
		(one or many boolean expressions are false). 

		Example:

			[and <expression>+]

		There must be at least one expression result as an argument.

		Args:
			pcontext: Current PContext for the script.
			arg: The results of one or many boolean expressions.
			line: The original code line.
		Return:
			String with either *false* or *false*, or None in case of an error.
	"""
	if len(args := tokenize(arg)) == 0:
		pcontext.setError(PError.invalid, f'Wrong number of arguments for and: {len(args)}. Must be >= 1.')
		return None
	for each in args:
		if (l := each.lower()) not in ['true', 'false']:
			pcontext.setError(PError.invalid, f'Invalid boolean value for and: {l}. Must be true or false.')
			return None
		if l != 'true':
			return 'false'
	return 'true'


def _doArgv(pcontext:PContext, arg:str, line:str) -> str:
	"""	With the *argv* macro one can access the individual arguments of a script.

		Example:

			[argv [<index>] ]

		- Without an index argument this macro returns the whole argument.
		- If the index is 0 then script name is returned.
		- Otherwise the nth argument is returned, starting with 1.

		Args:
			pcontext: Current PContext for the script.
			arg: The optional index.
		Return:
			String or None in case of an error.
	"""

	# just return the whole argument if no parameter is given
	if not arg:
		return pcontext.argument

	# Otherwise return the nth argument. 
	try:
		i = int(arg)
		if i == 0:	# Traditionally argv[0] is the program name
			return pcontext.name if pcontext.name else ''	
		if pcontext.argument:
			args = tokenize(pcontext.argument)
			if 0 < i <= len(args):
				return args[i-1]
			return None
	except Exception as e:
		#_doLogError(str(e))
		return None
	return ''
			

def _doArgc(pcontext:PContext, arg:str, line:str) -> str:
	"""	This macro returns the number of arguments to the script.

		Args:
			pcontext: Current PContext for the script.
			arg: Not used.
		Return:
			String, or None in case of an error.
	"""
	if pcontext.argument:
		return str(len(tokenize(pcontext.argument)))
	return '0'


def _doIn(pcontext:PContext, arg:str, line:str) -> str:
	"""	With the *in* macro one can test whether a string can be found in another string.

		Example:

			[in <text> <string>]

		Args:
			pcontext: Current PContext for the script.
			arg: Two arguments: The first is the text to look for in the second argument.
			line: The original code line.
		Return:
			String with either *false* or *false*, or None in case of an error.
	"""
	if len(args := tokenize(arg)) == 0:
		pcontext.setError(PError.invalid, f'Wrong number of arguments for in: {len(args)}. Must be == 2.')
		return None
	return str(args[0] in args[1]).lower()


def _doMatch(pcontext:PContext, arg:str, line:str) -> str:
	"""	This macro returns the result of a match comparison.

		Args:
			pcontext: Current PContext for the script.
			arg: Not used.
			line: Not used.
		Return:
			String with *true* or *false*, or None in case of an error.
	"""
	if len(args := tokenize(arg)) == 2:
		return str(pcontext.matchFunc(pcontext, args[0], args[1])).lower()
	pcontext.setError(PError.invalid, f'Wrong number of arguments for match: {len(args)}. Must be 2.')
	return None


def _doNot(pcontext:PContext, arg:str, line:str) -> str:
	"""	With the *not* macro one can invert the result of a boolean expressions.

		The *nor* macro will evaluate to *true* if the argument is *false*, and to *false* 
		if the argument is *true*.

		Example:

		[not <expression>]

		There must be exactly one expression result as an argument.

		Args:
			pcontext: Current PContext for the script.
			arg: The results of one or many boolean expressions.
			line: The original code line.
		Return:
			String with either *false* or *false*, or None in case of an error.
	"""
	if len(args := tokenize(arg)) != 1:
		pcontext.setError(PError.invalid, f'Wrong number of arguments for not: {len(args)}. Must be == 1.')
		return None
	if (l := args[0].lower()) not in ['true', 'false']:
		pcontext.setError(PError.invalid, f'Invalid boolean value for or: {len(args)}. Must be true or false.')
		return None
	return 'false' if l == 'true' else 'true'


def _doOr(pcontext:PContext, arg:str, line:str) -> str:
	"""	With the *or* macro one can evaluate boolean expressions and combine them with a boolean "or".

		The *or* macro will evaluate to *true* (at least one boolean expressions is true) or *false* 
		(none of the boolean expressions is true). 

		Example:

			[or <expression>+]

		There must be at least one expression result as an argument.

		Args:
			pcontext: Current PContext for the script.
			arg: The results of one or many boolean expressions.
			line: The original code line.
		Return:
			String with either *false* or *false*, or None in case of an error.
	"""
	if len(args := tokenize(arg)) == 0:
		pcontext.setError(PError.invalid, f'Wrong number of arguments for or: {len(args)}. Must be >= 1.')
		return None
	for each in args:
		if (l := each.lower()) not in ['true', 'false']:
			pcontext.setError(PError.invalid, f'Invalid boolean value for or: {l}. Must be true or false.')
			return None
		if l == 'true':
			return 'true'
	return 'false'


def _doRandom(pcontext:PContext, arg:str, line:str) -> str:
	"""	Generate a random float number in the given range. The default for the
		range is [0.0, 1.0]. If one argument is given then this indicates a range
		of [0,0, arg].

		Examples:
			- random 1 -> 0.3
			- random 2 3 -> 2.87

		Args:
			pcontext: Current PContext for the script.
			arg: One or two arguments for the range.
		Return:
			String, or None in case of an error.
	"""
	try:
		start = 0.0
		end = 1.0
		if arg:
			args = tokenize(arg)
			if len(args) == 1:
				end = float(args[0])
			elif len(args) == 2:
				start = float(args[0])
				end = float(args[1])
			else:
				pcontext.setError(PError.invalid, f'Wrong number of arguments for random: {len(args)}')
				return None
		return str(random.uniform(start, end))
	except ValueError as e:
		pcontext.setError(PError.notANumber, f'Not a number: {e}')
		return None


def _doRound(pcontext:PContext, arg:str, line:str) -> str:
	"""	Return a number rounded to optional *ndigits* precision after the decimal point. 
	
		If *ndigits*, the second parameter, is omitted, it returns the nearest integer.

		Examples:
			- round 1.6 -> 2
			- round 1.678 2 -> 1.67

		Args:
			pcontext: Current PContext for the script.
			arg: One or two arguments for the number and precision.		
		Return:
			String, or None in case of an error.
	"""
	try:
		number = Decimal(0.0)
		ndigits = None
		if arg:
			if len(args := tokenize(arg)) == 1:
				number = Decimal(args[0])
			elif len(args) == 2:
				number = Decimal(args[0])
				ndigits = int(args[1])
			else:
				pcontext.setError(PError.invalid, f'Wrong number of arguments for round: {len(args)}')
				return None
		return str(round(number, ndigits))
	except (InvalidOperation, ValueError) as e:
		pcontext.setError(PError.notANumber, f'Not a number: {e}')
		return None


##############################################################################


# Assign build-in commands to handlers
_builtinCommands:PCmdDict = {
	'assert':		_doAssert,
	'break':		_doBreak,
	'case':			_doCase,
	'continue':		_doContinue,
	'dec':			lambda p, a : _doIncDec(p, a, isInc = False),
	'else':			_doElse,
	'endif':		_doEndIf,
	'endprocedure':	_doEndProcedure,
	'endswitch':	_doEndSwitch,
	'endwhile':		_doEndWhile,
	'if':			_doIf,
	'inc':			lambda p, a : _doIncDec(p, a),
	'log':			lambda p, a : _doLog(p, a,),
	'logerror':		lambda p, a : _doLog(p, a, isError = True),
	'print':		_doPrint,
	'procedure':	_doProcedure,
	'quit':			_doQuit,
	'quitwitherror':_doError,
	'set':			_doSet,
	'sleep':		_doSleep,
	'switch':		_doSwitch,
	'while':		_doWhile,
}


_builtinMacros:PMacroDict = {
	# !!! macro names must be lower case

	'argc':		_doArgc,
	'argv':		_doArgv,
	'datetime':	lambda c, a, l: datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S.%f' if not a else a),
	'in':		_doIn,
	'loop':		lambda c, a, l: str(x) if ((x := c.whileLoopCounter()) and x is not None) else x,	# type:ignore [dict-item, return-value]
	'lower':	lambda c, a, l: a.lower(),
	'match':	_doMatch,
	'random':	_doRandom,
	'result':	lambda c, a, l: c.result,
	'round':	_doRound,
	'runcount':	lambda c, a, l: str(c.runs),
	'upper':	lambda c, a, l: a.upper(),

	# Math operators
	'+':		lambda c, a, l: _calculate(c, a, l, operator.add),
	'-':		lambda c, a, l: _calculate(c, a, l, operator.sub),
	'*':		lambda c, a, l: _calculate(c, a, l, operator.mul),
	'/':		lambda c, a, l: _calculate(c, a, l, operator.truediv),
	'//':		lambda c, a, l: _calculate(c, a, l, operator.floordiv),
	'**':		lambda c, a, l: _calculate(c, a, l, operator.pow),
	'%':		lambda c, a, l: _calculate(c, a, l, operator.mod),
	
	# Comparisons
	'==':		lambda c, a, l: _compare(c, a, l, operator.eq),
	'!=':		lambda c, a, l: _compare(c, a, l, operator.ne),
	'>':		lambda c, a, l: _compare(c, a, l, operator.gt),
	'>=':		lambda c, a, l: _compare(c, a, l, operator.ge),
	'<':		lambda c, a, l: _compare(c, a, l, operator.lt),
	'<=':		lambda c, a, l: _compare(c, a, l, operator.le),

	# Logical operators
	'!':		_doNot,
	'not':		_doNot,
	'&&':		_doAnd,
	'and':		_doAnd,
	'||':		_doOr,
	'or':		_doOr,
}


##############################################################################
#
#	Internal helpers
#

def checkMacros(pcontext:PContext, line:str) -> str:
	"""	Replace all macros and variables in a line. 
	
		Variables have precedence over macros with the same name. Macros and variables are replaced recursively.

		Args:
			pcontext: Current PContext for the script.
			line: The line to process.
		Return:
			String, the line with all variabes, macros etc replaces, or None in case of an error.
	"""

	def _replaceMacro(macro:str) -> str:
		"""	Replace a single macro or variable. 
		
			This is done recursively.

			Args:
				macro: The name and argument of a macro. Everything between [...].
			Return:
				The fully replaced macro.
		"""
		# remove prefix & trailer
		macro = macro[1:-1] 			

		# Resolve contained macros recursively
		if (macro := checkMacros(pcontext, macro)) is None:
			return None

		# First check variables
		if (v := pcontext.getVariable(macro)) is not None:
			return v

		# Then check macros
		name, _, arg = macro.partition(' ')
		arg = arg.strip()
		if (cb := pcontext.getMacro(name)) is not None:
			if (result := cb(pcontext, arg, line)) is not None:
				return str(result)
			if pcontext.error.error == PError.noError:	# provide an own error if not set by the macro function
				pcontext.setError(PError.invalid, f'Error from macro: {macro}')
			return None
		
		# Then check environment variables
		if (v := pcontext.getEnvironmentVariable(macro)) is not None:
			return v
		
		# Then try the default macro definition
		if (cb := pcontext.getMacro('__default__')) is not None:
			if (result := cb(pcontext, macro, line)) is not None:
				return str(result)
			## FALL-THROUGH

		# Lastly try a procedure with that name
		# To do this we run the same script, but only looking for a procedure with that name.
		pcontext_ = copy.deepcopy(pcontext)				# Copy the pcontext
		#pcontext_.argument = arg.strip()				# Set a possible argument
		presult = run(pcontext_, verbose = pcontext_._verbose, argument = arg, procedure = name)

		# If undefined then return a general error
		if presult.error.error == PError.undefined:
			pcontext.setError(PError.undefined, f'Undefined variable, macro, or procedure: {name}')
			return None

		# Otherwise if any other error then return that error
		if presult.error.error != PError.noError:
			pcontext.state = pcontext_.state
			pcontext.error = pcontext_.error
			return None
		
		# Otherwise no error, so return the result from the call
		pcontext.variables = pcontext_.variables	# copy back the variables because the might have changed
		return pcontext_.result


	# replace macros
	# _macroMatch = re.compile(r"\$\{[\s\w-.]+\}")
	# items = re.findall(_macroMatch, line)
	# for item in items:
	# 	if (r := _replaceMacro(item)) is None:
	# 		return None
	# 	line = line.replace(item, r)

	# The following might be easier with a regex, but we want to allow recursive macros, therefore
	# parsing the string is simpler for now. Suggestions welcome!


	i = 0
	l = len(line)
	result = ''
	while i < l:
		c = line[i]
		i += 1

		# Found escape
		if c == '\\' and i < l:
			result += line[i]
			i += 1

		# Found [ in the input line
		elif c == '[':
			macro = c
			oc = 0	# macro deep level
			# try to find the end of the macro.
			# Skip contained macros in between. They will be
			# resolved recursively later
			while i < l:
				c = line[i]
				i += 1
				if c == '\\' and i < l:
					macro += line[i]
					i += 1
				elif c == '[':
					oc += 1
					macro += '['
				elif c == ']':
					if oc > 0:	# Skip if not end of _this_ macro
						oc -= 1
						macro += ']'
					else:	# End of macro. Might contain other macros! Those will be resolved later
						macro += c
						if (r := _replaceMacro(macro)) is None:
							return None
						result += r
						break	# Break the inner while
				else:
					macro += c
		
		# Normal character found
		else:
			result += c

	# Replace escapes and return
	#return line.replace('\\{', '{').replace('\\}', '}')
	return result


def _skipIfElse(pcontext:PContext, isIf:bool) -> PContext:
	"""	Skip to else or endif if *isIf* is False(!).
	
		Skip over "IF", "ELSE", or "ENDIF" commands that are not part of the scope.

		Args:
			pcontext: Current PContext for the script.
			isIf: True when the part to be skipped over is the if - part.
		Return:
			Current PContext object, or None in case of an error.
	"""
	level = 0		# level of ifs
	while pcontext.pc < pcontext._length and level >= 0:
		cmd, _, arg, _ = pcontext.nextLinePartition()

		if cmd == 'endif':
			if arg:
				pcontext.setError(PError.unexpectedArgument, 'ENDIF has no argument')
				return None
			# This will eventually find the fittig "if" and then
			# the level will be negative and thereby end the while loop
			level -=1
			continue
		if cmd == 'if':
			level += 1
			continue
		if isIf and cmd == 'else':
			if arg:
				pcontext.setError(PError.unexpectedArgument, 'ELSE has no argument')
				return None
			if level == 0:
				break
		if cmd == 'endprocedure':
			pcontext.setError(PError.unexpectedCommand, 'IF without ENDIF')
			return None
	
	if pcontext.pc == pcontext._length and level > 0:
		pcontext.setError(PError.unexpectedCommand, 'IF without ENDIF')
		return None

	return pcontext


def _skipSwitch(pcontext:PContext, compareTo:str, skip:bool = False) -> PContext:
	"""	Skip to the first matching CASE statement of a a SWITCH block, or to the
		end of the whole switch block

		Args:
			pcontext: Current PContext for the script.
			compareTo: Value to compare the CASE argument with.
			skip: If true then skip to the end of the SWITCH block..
		Return:
			Current PContext object, or None in case of an error.
	"""
	level = 0		# level of switches
	compareTo = ' '.join(tokenize(compareTo)).lower() if compareTo else 'true'
	while pcontext.pc < pcontext._length and level >= 0:
		cmd, _, arg, _ = pcontext.nextLinePartition()

		if cmd == 'case' and not skip:	# skip all cases if we just look for the end of the switch
			if not arg:	# default case, always matches
				break

			# Check all macros/variables, then use the provided match function to do the comparison.
			# This also matches any comparison against the default "true" value of the switch
			if pcontext.matchFunc(pcontext, compareTo, checkMacros(pcontext, arg)):
				break
			continue			# not the right one, continue search
		if cmd == 'endswitch':
			if arg:
				pcontext.setError(PError.unexpectedArgument, 'ENDSWITCH has no argument')
				return None
			# This will eventually find the fittig "switch" and then
			# the level will be negative and thereby end the SWITCH block
			level -=1
			continue
		if cmd == 'switch':
			level += 1
			continue
		if cmd == 'endprocedure':
			pcontext.setError(PError.unexpectedCommand, 'SWITCH without ENDSWITCH')
			return None
	
	if pcontext.pc == pcontext._length and level > 0:
		pcontext.setError(PError.unexpectedCommand, 'SWITCH without ENDSWITCH')
		return None

	return pcontext


def _skipWhile(pcontext:PContext) -> PContext:
	"""	Skip a WHILE block to its ENDWHILE. Skip over other WHILE..ENDWHILE that are 
		not part of this scope.

		Args:
			pcontext: Current PContext for the script.
		Return:
			Current PContext object, or None in case of an error.
	"""
	level = 0		# level of ifs
	while level >= 0:
		cmd, _, _, _ = pcontext.nextLinePartition()
		if cmd is None:
			break
		if cmd == 'endwhile': # no result handling here
			level -=1
			continue
		if cmd == 'while':
			level += 1
			continue
		if cmd == 'endprocedure':
			pcontext.setError(PError.unexpectedCommand, 'WHILE without ENDWHILE')
			return None
	pcontext.removeWhileLoop()
	pcontext.restoreWhileState()
	return pcontext


# # TODO delete
# def _compareExpression(pcontext:PContext, expr:str) -> bool:
# 	"""	Resolve a compare expression. boolean *true* and *false*, and the
# 		comparison operators ==, !=, <, <=, >, >= are supported.

# 		Args:
# 			pcontext: Current PContext for the script.
# 			expr: The compare expression.
# 		Return:
# 			Boolean.
# 	"""
# 	def _strDecimal(val:str) -> Union[Decimal, str]:
# 		try:
# 			return Decimal(val)	# try to unify float values
# 		except InvalidOperation as e:
# 			# print(str(e))
# 			return val.strip()
	
# 	def _checkDecimal(l:str, r:str) -> Tuple[Decimal, Decimal]:
# 		_l = _strDecimal(l)
# 		_r = _strDecimal(r)
# 		if isinstance(_l, Decimal) and isinstance(_r, Decimal):
# 			return _l, _r
# 		pcontext.setError(PError.invalid, f'Unknown expression: {expr}')
# 		return None

# 	# Boolean checks
# 	if expr.lower() == 'true':
# 		return True
# 	if expr.lower() == 'false':
# 		return False

# 	# equality checks
# 	if (t := expr.partition('==')) and t[1]:
# 		return _strDecimal(t[0]) == _strDecimal(t[2])	# still convert to Decimal to convert an int to a Decimal, if necessary
# 	if (t := expr.partition('!=')) and t[1]:
# 		return _strDecimal(t[0]) != _strDecimal(t[2])	# still convert to Decimal to convert an int to a Decimal, if necessary

# 	# order checks
# 	if (t := expr.partition('<=')) and t[1]:
# 		if not (lr := _checkDecimal(t[0], t[2])):	# Error set in function
# 			return None
# 		return lr[0] <= lr[1]
# 	elif (t := expr.partition('>=')) and t[1]:
# 		if not (lr := _checkDecimal(t[0], t[2])):	# Error set in function
# 			return None
# 		return lr[0] >= lr[1]
# 	elif (t := expr.partition('<')) and t[1]:
# 		if not (lr := _checkDecimal(t[0], t[2])):	# Error set in function
# 			return None
# 		return lr[0] < lr[1]
# 	elif (t := expr.partition('>')) and t[1]:
# 		if not (lr := _checkDecimal(t[0], t[2])):	# Error set in function
# 			return None
# 		return lr[0] > lr[1]
# 	pcontext.setError(PError.invalid, f'Unknown expression: {expr}')
# 	return None


def _compare(pcontext:PContext, arg:str, line:str, op:Callable) -> str:
	"""	Compare two arguments with a comparison operator.

		If both arguments are numbers then a numeric comparison is done, other a string compare is performed.
		The difference is that, for example, "4" > "30" when compared as a string.

		Args:
			pcontext: Current PContext for the script.
			arg: The arguments for the compare. This string must contain two arguments.
			line: The whole script line. Not used.
			op: An "operator" method used for the comparison.
		Return:
			String with *true* or *false* depending on the result of the comparison.
	"""
	def _strDecimal(val:str) -> Union[Decimal, str]:
		"""	Helper function to cast a comparable value.

			Args:
				val: The value to cast
			Return:
				Either a Decimal object (when the value is a number) as a string, or just a normal string.
		"""
		try:
			return Decimal(val)	# try to unify float values
		except InvalidOperation as e:
			return val.strip()

	if len(args := tokenize(arg)) != 2:
		pcontext.setError(PError.invalid, f'Wrong number of arguments for operation: Must be == 2.')
		return None
	
	# Convert to strings if either argument is a string
	l = _strDecimal(args[0])
	r = _strDecimal(args[1])
	if isinstance(l, str) or isinstance(r, str):
		l = str(l)
		r = str(r)
	
	# Compare and return
	return str(op(l, r)).lower()


def _boolResult(pcontext:PContext, arg:str) -> bool:
	"""	Test whether an argument is either *true* or *false*.

		Args:
			pcontext: Current PContext for the script.
			arg: The argument for the compare. 
		Return:
			Boolean *True* or *False*, or *None* in case of an error.
	"""
	if arg.lower() == 'true':
		return True
	if arg.lower() == 'false':
		return False
	pcontext.setError(PError.invalid, f'Expression must be "true" or "false"')
	return None


def _calculate(pcontext:PContext, arg:str, line:str, op:Callable, single:bool = False) -> str:
	"""	Perform an arithmetic calculation.

		This function performs an arithmetic operation on multiple arguments. The same
		operation is subsequentially performed on an argument to the result of the
		last iteration.

		Example:
			[+ 1 2 3]
			# yields 6
		Args:
			pcontext: Current PContext for the script.
			arg: Line that contains all the arguments.
			line: The whole script line. Not used.
			op: An "operator" method used for the arithmetics operation.
			single: The operation allows only one argument.
		Return:
			String with a number result of the operatio, or *None* in case of an error.
	"""
	
	if len(args := tokenize(arg)) < 2:
		pcontext.setError(PError.invalid, f'Wrong number of arguments for operation: Must be >= 2')
		return None
	
	# Convert strings to numbers
	nums:list[Decimal] = []
	try:
		for each in args:
			nums.append(Decimal(each))
	except InvalidOperation as e:
		pcontext.setError(PError.invalid, f'Not a number: {each}')
		return None

	# Do the calculation
	while len(nums) > 1:
		l = nums.pop(0)
		r = nums.pop(0)
		nums.insert(0, op(l, r)) # calculate and insert the result to the beginning of the list

	return str(nums[0])	# final result is the only element in the list.


def _executeProcedure(pcontext:PContext, cmd:str, arg:str) -> PContext:
	"""	Execute a PROCEDURE in its own scope. 
	
		Variables are still global. If the procedure returns a result then it is
		available in the PContext's	*result* attribute.

		Args:
			pcontext: Current PContext for the script.
			cmd: The name of the procedure to execute.
			arg: The argument for the procedure.
		Return:
			Current PContext object, or None in case of an error.

	"""
	pcontext.saveScope(arg = arg, name = cmd)
	pcontext.pc = 0
	_procedureMatch = re.compile(r'^\s*procedure\s*' + cmd + '\s*$', flags = re.IGNORECASE)
	while line := pcontext.nextLine:
		if re.match(_procedureMatch, line):
			return pcontext
	# if not found restore the pc and return an error
	pcontext.restoreScope()
	pcontext.setError(PError.undefined, f'Undefined PROCEDURE {cmd}')
	return None

