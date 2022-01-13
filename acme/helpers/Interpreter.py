#
#	Interpreter.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of a simple batch command processor.
#

"""	The interpreter implements an extensible script runtime.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum, auto
import datetime, time, re, copy
from typing import 	Callable, Dict, Tuple, Union

_maxProcStackSize = 64	# max number of calls to procedures

# return with return value. result in pcontext?

class PState(IntEnum):
	"""	The states of a process/batch.
	"""
	created 				= auto()
	ready 					= auto()
	running 				= auto()
	canceled 				= auto()
	terminated 				= auto()
	terminatedWithResult	= auto()
	terminatedWithError 	= auto()


class PError(IntEnum): 
	"""	Error codes.
	"""
	noError 				= auto()
	unknown 				= auto()
	undefined				= auto()
	assertionFailed			= auto()
	unexpectedArgument		= auto()
	unexpectedCommand		= auto()
	maxProceduresExceeded 	= auto()
	notANumber				= auto()
	divisionByZero			= auto()
	procedureWithoutEnd		= auto()
	nestedProcedure			= auto()
	interrupted				= auto()
	invalid					= auto()
	canceled				= auto()


@dataclass
class PScope():
	"""	Scope-specific data points.
	"""
	name:str				= None
	argument:str			= None
	result:str				= None
	returnPc:int			= 0
	whileStack:list[int]	= field(default_factory = list)
	ifLevel:int				= 0


class PContext():
	"""	Process context for a single script. Can be re-used.s
	"""

	def __init__(self, 
				 script:Union[str,list[str]],
				 commands:PCmdDict 			= None,
				 macros:PMacroDict 			= None,
				 logFunc:PLogCallable 		= lambda pcontext, msg: print(f'** {msg}'),
				 logErrorFunc:PLogCallable	= lambda pcontext, msg: print(f'!! {msg}'),
				 printFunc:PLogCallable 	= lambda pcontext, msg: print(msg),
				 preFunc:PFuncCallable		= None,
				 postFunc:PFuncCallable		= None,
			 	 errorFunc:PFuncCallable	= None) -> None:
		"""	Initialize the process context.

			Args:
				script: a single \\n-seprated string, or a list of strings.
				commands: optional list of additional commands and their callbacks.
				macros: optional list of additional commands and their callbacks.
				logFunc: optional callback for log messages (and the LOG command).
				logErrorFunc: optional callback for error log messages (and the ERROR command).
				printFunc: optional callback for PRINT command messages.
				preFunc: optional callback that is called with the PContext object just before the script is executed. Returning *None* prevents the script execution.
				postFunc: optional callback that is called with the PContext object just after the script finished execution.
				errorFunc: optional callback that is called with the PContext object when encountering an error during script execution.
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

		# State, result and error attributes
		self.pc:int 						= 0
		self.state:PState 					= PState.created
		self.error:Tuple[PError,int,str]	= ( PError.noError, 0, '' )
		self.meta:Dict[str, str]			= {}
		self.runs:int						= 0

		# Internal attributes that should not be accessed
		self._length:int					= 0
		self.variables:Dict[str,str]		= {}
		self._scopeStack:list[PScope]		= []
		self._commands:PCmdDict				= None		# builtins + provided commands
		self._macros:PMacroDict				= None		# builtins + provided macros

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


	def run(self, doLogging:bool = False, argument:str = '') -> PContext:
		"""	Run the script.

			Args:
				doLogging: Boolean to indicate whether each executed line shall be logged.
				argument: String with the argument(s)

			Return:
				PContext object, or None in case of an error.
		"""
		global run
		self.reset()	# Reset the PContext
		self.runs += 1
		return run(self, doLogging = doLogging, argument = argument)


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
			if line.startswith('${'):
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
				prefix: If `prefix` is given then it is added to the begining of the result.
				upto:  If `upto` is given then only the lines up to the first line that starts with `upto` are returned.
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
		"""	Test whether a line should be ignored, e.g. a comment (ie. the line starts with # or //), 
			or meta data (ie, the line starts with @). White spaces before the characters are ignored.

			Args:
				line: The line to test
				
			Return:
				Boolean indicating whether a line shall be ignored.
		"""
		return line.startswith(('#', '//', '@'))
	

	def reset(self) -> None:
		"""	Reset the context / script. May also be implemented in a sub-class, but the must then call this
			method as well.
		"""
		self.pc = 0
		self.error = ( PError.noError, 0, '' )
		self.variables.clear()
		self._scopeStack.clear()
		self.saveScope(pc = -1, name = self.meta.get('name'))
		self.state = PState.ready


	def setError(self, error:PError, msg:str, pc:int = -1, state:PState = PState.terminatedWithError) -> None:
		"""	Set the internal state and error codes. These can be retrieved by the calling function in order
			to provide informations.

			Args:
				error: PError to indicate the type of error.
				msg: String that further explains the error.
				pc: Integer, the program counter pointing at the line causing the error. Default -1 means the current pc.
				state: PState to indicate the state of the script. Default is "terminatedWithError".

		"""
		self.state = state
		self.error = ( error, self.pc if pc == -1 else pc, msg )


	@property
	def result(self) -> str:
		"""	The last result of a procedure, while etc. .nly valid within a scope 
			and before the next call to a procedure, while, etc.

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
		"""	Return the nested if-commands of the current scope.

			Return:
				Integer, the IF-Level.
		"""
		return self.scope.ifLevel


	@ifLevel.setter
	def ifLevel(self, level:int) -> None:
		"""	Set the number of nested if-commands of the current scope.

			Args:
				level: Integer, the if-level of the current scope.
		"""
		self.scope.ifLevel = level


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


	@property
	def whilePc(self) -> int:
		"""	Return the latest saved program counter for a while loop.

			Return:
				Integer, the program counter that points to the top of the current while scope.
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


##############################################################################
#
#	Type definitions
#


PFuncCallable = Callable[[PContext], PContext]
"""	Function callback for pre, post and error functions.
"""

PLogCallable = Callable[[PContext, str], None]
"""	Function callback for log functions.
"""

PCmdDict = Dict[str, Callable[[PContext, str], PContext]]
"""	Function callback for commands. The callback is called with a `PContext` object
	and is supposed to return it again, or None in case of an error.
"""

PMacroDict = Dict[str, Callable[[PContext, str], str]]
"""	Function callback for macros. The callback is called with a `PContext` object
	and returns a string.
"""


##############################################################################
#
#	Run a script
#

def run(pcontext:PContext, doLogging:bool = False, argument:str = '') -> PContext:
	"""	Run a script. An own, extended `contextClass` can be provided, that supports the `extraCommands`.

		Args:
			pcontext: Current PContext for the script.
			doLogging: Log each executed line.
			argument: The argument to the script, available via the `argv` macro.

		Return:
			PContext object, or None in case of an error.
		"""

	def _terminating(pcontext:PContext) -> None:
		"""	Handle the error setup, fill in error and message, and call the error and post function callbacks.
			Don't overwrite already set error values.
				
			Args:
				pcontext: Current PContext for the script.
		"""
		if pcontext.error[0] != PError.noError:
			_doLog(pcontext, f'{pcontext.error[1]}: {pcontext.error[2]}', isError = True)
			if pcontext.errorFunc:
				pcontext.errorFunc(pcontext)
		if pcontext.state != PState.ready and pcontext.postFunc:	# only when really running, after preFunc succeeded
			pcontext.postFunc(pcontext)


	# Validate script first.
	if not pcontext.validate():
		return pcontext
	pcontext.reset()
	pcontext.argument = argument
	
	# Call Pre-Function
	if pcontext.preFunc:
		if pcontext.preFunc(pcontext) is None:
			pcontext.setError(PError.canceled, 'preFunc canceled', state=PState.canceled)
			_terminating(pcontext)
			return pcontext

	# Start running
	pcontext.state = PState.running
	if scriptName := pcontext.scriptName:
		pcontext.logFunc(pcontext, f'Running script: {scriptName}, arguments: {argument}')


	# main processing loops
	endScriptStates = [ PState.canceled, PState.terminated, PState.terminatedWithResult, PState.terminatedWithError ]
	while (line := pcontext.nextLine) is not None and pcontext.state not in endScriptStates:
		
		# Resolve macros and variables
		if (line := checkMacros(pcontext, line)) is None:
			pcontext.state = PState.terminatedWithError
			break

		# get command and arguments
		if doLogging:
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
				except Exception as e:
					#pcontext.logErrorFunc(e)
					pcontext.setError(PError.unknown, f'Error: {e}')
			else:
				# Ignore "empty" (None) commands
				pass
		
		elif (result := _executeProcedure(pcontext, cmd, arg.strip())):
			pcontext = result

		else:
			pcontext.setError(PError.undefined, f'Undefined command: {line}')
			break
	
	# Check for gosub without return when reaching the end of the script
	if pcontext.state != PState.terminatedWithResult:
		pcontext.result = None
	if pcontext.state not in endScriptStates:
		if len(pcontext._scopeStack) > 1:
			pcontext.setError(PError.procedureWithoutEnd, f'PROCEDURE without return', pcontext.scope.returnPc )

	# Return after running. Set the pcontext.state accordingly
	pcontext.state = PState.terminated if pcontext.state == PState.running else pcontext.state
	_terminating(pcontext)
	return pcontext

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
	if (result := _compareExpression(pcontext, arg)) is None:
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


def _doContinue(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a break command operation.

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
	pcontext.restoreScope()
	pcontext.result = arg	# Copy the argument (ie the result) to the previous scope
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


def _doIf(pcontext:PContext, arg:str) -> PContext:
	"""	Handle an if...else...endif command operation.

		Args:
			pcontext: Current PContext for the script.
			arg: The IF-expressions.

		Return:
			PContext object, or None in case of an error.
	"""
	pcontext.ifLevel += 1
	if (result := _compareExpression(pcontext, arg)) is None:
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
			isInc: Indicate whether to increment or decrement

		Return:
			PContext object, or None in case of an error.
	"""
	var, _, value = arg.partition(' ')
	value = value.strip()
	if (variable := pcontext.variables.get(var)) is None:
		pcontext.setError(PError.undefined, f'undefined variable: {var}')
		return None
	try:
		n = float(value) if len(value) > 0 else 1.0	# either a number or 1.0 (default)
		pcontext.variables[var] = str(float(variable) + n) if isInc else str(float(variable) - n)
	except ValueError as e:
		pcontext.setError(PError.notANumber, f'Not a number: {e}')
		return None
	return pcontext


def _doLog(pcontext:PContext, arg:str, isError:bool = False) -> PContext:
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
			pcontext.logErrorFunc(pcontext, arg)
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
	pcontext.setError(PError.procedureWithoutEnd, 'PROCEDURE without ENDPROCEDURE')
	return None
	

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
	# Check whether this is an expression asignment
	var, found, value = arg.partition('=')
	if found:	# = means assignment
		var = var.strip()
		value = value.strip()
		try:
			if (result := str(_calcExpression(pcontext, value))) is None:
				return None
		except ValueError as e:
			pcontext.setError(PError.notANumber, f'Not a number: {e}')
			return None
		except ZeroDivisionError as e:
			pcontext.setError(PError.divisionByZero, f'Division by zero: {arg}')
			return None
		pcontext.variables[var] = str(result)
		return pcontext

	# Else: normal assignment
	var, _, value = arg.partition(' ')
	var = var.strip()

	# remove variable if no value
	if not value:	
		if var in pcontext.variables:
			del pcontext.variables[var]
		else:
			pcontext.setError(PError.undefined, f'Undefined variable: {var}')
			return None
		return pcontext

	# Just assign
	pcontext.variables[var] = value.strip()
	return pcontext


def _doSleep(pcontext:PContext, arg:str) -> PContext:
	"""	Sleep for `arg` seconds. This command can be interrupted when the
		script's state is set to `canceled`.

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


def _doWhile(pcontext:PContext, arg:str) -> PContext:
	"""	Handle a while...endwhile command operation.

		Args:
			pcontext: Current PContext for the script.
			arg: The comparison for the while loop.
		
		Return:
			Current PContext object, or None in case of an error.
	"""
	wpc = pcontext.whilePc
	if wpc is None or wpc != pcontext.pc:	# Only put this while on the stack if we just run into it
		pcontext.saveWhileState()
	if (result := _compareExpression(pcontext, arg)) is None:
		return None
	if not result:
		# Skip to endwhile if False(!).
		return _skipWhile(pcontext)
	return pcontext


##############################################################################
#
#	Build-in Macros
#


def _doArgv(pcontext:PContext, arg:str) -> str:
	"""	With the `argv` macro one can access the individual arguments of a script.


		Example:

			${argv [<index>]}

		- Without an index argument this macro returns the whole argument.
		- If the index is 0 then script name is returned.
		- Otherwise the nth argument is returned, starting with 1.

		Args:
			pcontext: Current PContext for the script.
			arg: The optional index.
		
		Return:
			Current PContext object, or None in case of an error.
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
			args = pcontext.argument.split()
			if 0 < i <= len(args):
				return args[i-1]
			return None
	except Exception as e:
		#_doLogError(str(e))
		return None
	return ''
			

def _doArgc(pcontext:PContext, arg:str) -> str:
	"""	This macro returns the number of arguments to the script.

		Args:
			pcontext: Current PContext for the script.
			arg: Not used.
		
		Return:
			Current PContext object, or None in case of an error.
	"""
	if pcontext.argument:
		return str(len(pcontext.argument.split()))
	return '0'


##############################################################################


# Assign build-in commands to handlers
_builtinCommands:PCmdDict = {
	'assert':		_doAssert,
	'break':		_doBreak,
	'continue':		_doContinue,
	'dec':			lambda p, a : _doIncDec(p, a, isInc = False),
	'else':			_doElse,
	'endif':		_doEndIf,
	'endprocedure':	_doEndProcedure,
	'endwhile':		_doEndWhile,
	'error':		lambda p, a : _doLog(p, a, isError = True),
	'if':			_doIf,
	'inc':			lambda p, a : _doIncDec(p, a),
	'log':			lambda p, a : _doLog(p, a,),
	'print':		_doPrint,
	'procedure':	_doProcedure,
	'quit':			_doQuit,
	'set':			_doSet,
	'sleep':		_doSleep,
	'while':		_doWhile,
}


_builtinMacros:PMacroDict = {
	'datetime':	lambda c, a: datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S.%f' if not a else a),
	'result':	lambda c, a: c.result,
	'argc':		lambda c, a: _doArgc(c, a),
	'argv':		lambda c, a: _doArgv(c, a),
}


##############################################################################
#
#	Internal helpers
#

def checkMacros(pcontext:PContext, line:str) -> str:
	"""	Replace all macros and variables in a line. Variables have precedence
		over macros with the same name. Macros and variables are replaced recursively.

		Args:
			pcontext: Current PContext for the script.
			line: The line to process.
		
		Return:
			String, the line with all variabes, macros etc replaces, or None in case of an error.
	"""

	def _replaceMacro(macro:str) -> str:
		"""	Replace a single macro or variable. Do this recursively.

			Args:
				macro: The name and argument of a macro. Everything between ${...}.
			
			Return:
				The fully replaced macro.
		"""
		
		# remove prefix & trailer
		macro = macro[2:-1] 					
		
		# Resolve contained macros recursively
		if (macro := checkMacros(pcontext, macro)) is None:
			return None

		# First check variables
		if macro in pcontext.variables:
			return pcontext.variables[macro]

		# Then check macros
		name, _, arg = macro.partition(' ')
		arg = arg.strip()
		if (cb := pcontext._macros.get(name)) is not None:
			if (result := cb(pcontext, arg)) is not None:
				return str(result)
			if pcontext.error[0] == PError.noError:	# provide an own error if not set by the macro function
				pcontext.setError(PError.invalid, f'Error from macro: {macro}')
			return None
		
		# Lastly, try the default macro definition
		if (cb := pcontext._macros.get('__default__')) is not None:
			if (result := cb(pcontext, macro)) is not None:
				return str(result)
			## FALL-THROUGH

		pcontext.setError(PError.undefined, f'Undefined macro or variable: {macro}')
		return None

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

		# Found ${ in the input line
		elif c == '$' and i < l and line[i] == '{':
			macro = '${'
			i += 1
			oc = 0
			# try to find the end of the macro.
			# Skip contained macros in between. They will be
			# resolved recursively later
			while i < l:
				c = line[i]
				i += 1
				if c == '\\' and i < l:
					macro += line[i]
					i += 1
				elif c == '$' and i < l and line[i] == '{':
					oc += 1
					i += 1
					macro += '${'
				elif c == '}':
					if oc > 0:	# Skip if not end of _this_ macro
						oc -= 1
						macro += '}'
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
	"""	Skip to else or endif if `isIf` is False(!). Skip oer
		"if", "else", or "endif" that are not part of the scope.

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
	pcontext.restoreWhileState()
	return pcontext


def _compareExpression(pcontext:PContext, expr:str) -> bool:
	"""	Resolve a compare expression. boolean "true" and "false", and the
		comparison operators ==, !=, <, <=, >, >= are supported.

		Args:
			pcontext: Current PContext for the script.
			expr: The compare expression.
		
		Return:
			Boolean.
	"""
	def strFloat(val:str) -> Union[float, str]:
		try:
			return float(val)	# try to unify float values
		except ValueError as e:
			# print(str(e))
			return val.strip()

	if expr.lower() == 'true':
		return True
	if expr.lower() == 'false':
		return False
	if (t := expr.partition('==')) and t[1]:
		return strFloat(t[0]) == strFloat(t[2])
	if (t := expr.partition('!=')) and t[1]:
		return strFloat(t[0]) != strFloat(t[2])
	if (t := expr.partition('<=')) and t[1]:
		return strFloat(t[0]) <= strFloat(t[2])
	if (t := expr.partition('>=')) and t[1]:
		return strFloat(t[0]) >= strFloat(t[2])
	if (t := expr.partition('<')) and t[1]:
		return strFloat(t[0]) < strFloat(t[2])
	if (t := expr.partition('>')) and t[1]:
		return strFloat(t[0]) > strFloat(t[2])
	pcontext.setError(PError.unknown, f'Unknown expression: {expr}')
	return None


def _calcExpression(pcontext:PContext, expr:str) -> float:
	"""	Resolve a simple math expression. The operators +, -, *, /, % (mod), ^ are suppored.
		The result is always a float.

		Args:
			pcontext: Current PContext for the script.
			expr: The expression to calculate
		
		Return:
			Float, the result of the calculation.
	"""
	expr = expr.strip()
	
	# The following is a hack to allow negative numbers to be used with the
	# simple expression parser below. It just takes advantage that
	# -n = 0 - n
	# This way negative numbers are just a result of a calculation. 
	# Not prestty but lazy.
	if expr.startswith('-'):
		expr = f'0{expr}'
	
	if (t := expr.partition('+')) and t[1]:
		return _calcExpression(pcontext, t[0]) + _calcExpression(pcontext, t[2])
	if (t := expr.partition('-')) and t[1]:
		return _calcExpression(pcontext, t[0]) - _calcExpression(pcontext, t[2])
	if (t := expr.partition('*')) and t[1]:
		return _calcExpression(pcontext, t[0]) * _calcExpression(pcontext, t[2])
	if (t := expr.partition('/')) and t[1]:
		return _calcExpression(pcontext, t[0]) / _calcExpression(pcontext, t[2])
	if (t := expr.partition('%')) and t[1]:
		return _calcExpression(pcontext, t[0]) % _calcExpression(pcontext, t[2])
	if (t := expr.partition('^')) and t[1]:
		return _calcExpression(pcontext, t[0]) ** _calcExpression(pcontext, t[2])
	return float(expr)


def _executeProcedure(pcontext:PContext, cmd:str, arg:str) -> PContext:
	"""	Execute a PROCEDURE in its own scope. Variables are still global. If the
		procedure returns a result then it is available in the PContext's
		`result` attribute.

		Args:
			pcontext: Current PContext for the script.
			cmd: The name of the procedure to execute.
			arg: The argument for the procedure
		
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

