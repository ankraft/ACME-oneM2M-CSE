#
#	PContext.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Process context for a single script. 
	This is the main runtime object for the interpreter.

	To run a script, create a `PContext` object, and call its `run()` method.
"""

from __future__ import annotations

from typing import Optional, Tuple
import re
from copy import deepcopy

from .Constants import maxRecursionDepth

from .Types import	PErrorState, PError, PErrorState, PError
from .Types import PState, SSymbol, SNilSymbol
from .Types import PSymbolDict, PLogCallable, PErrorLogCallable, PFuncCallable, PMatchCallable
from .Types import PSymbolCallable, SSymbolsList, PCall, FunctionDefinition
from .Exceptions import PInvalidArgumentError, PUnsupportedError, PRuntimeError

from .Interpreter import runScript

class PContext():
	"""	Process context for a single script. 
	
		This is the main runtime object for the interpreter. 
		To run a script, create a `PContext` object, and call its `run()` method.

		To add new symbols to the interpreter, inherit from `PContext` 
		and add them to the `symbols` dictionary during initialization.	
		
		A `PContext` object can be re-used.
	"""

	__slots__ = (
		'script',
		'symbols',
		'debugExecutedSymbols',
		'logFunc',
		'logErrorFunc',
		'printFunc',
		'preFunc',
		'postFunc',
		'errorFunc',
		'matchFunc',
		'maxRuntime',
		'fallbackFunc',
		'monitorFunc',
		'allowBrackets',
		'ast',
		'result',
		'state',
		'error',
		'meta',
		'functions',
		'environment',
		'argv',
		'evaluateInline',
		'verbose',
		'_maxRTimestamp',
		'_callStack',
		'startupSymbols',
		'_variables',
	)
	""" Slots of class attributes. """

	_macroMatch = re.compile(r'\$\{.*?\}|\\\\\$\{.*?\}')	# Trick: ".*?" The ? is for non-greedy, for the shortest match
	"""	Regex for matching macros in strings and JSON. """


	def __init__(self, 
				 script:str,
				 symbols:Optional[PSymbolDict]				= None,
				 logFunc:Optional[PLogCallable] 			= lambda pcontext, msg: print(f'** {msg}'),
				 logErrorFunc:Optional[PErrorLogCallable]	= lambda pcontext, msg, exception: print(f'!! {msg}'),
				 printFunc:Optional[PLogCallable] 			= lambda pcontext, msg: print(msg),
				 preFunc:Optional[PFuncCallable]			= None,
				 postFunc:Optional[PFuncCallable]			= None,
			 	 errorFunc:Optional[PFuncCallable]			= None,
				 matchFunc:Optional[PMatchCallable]			= lambda pcontext, l, r: l == r,
				 maxRuntime:Optional[float]					= None,
				 fallbackFunc:Optional[PSymbolCallable]		= None,
				 monitorFunc:Optional[PSymbolCallable]		= None,
				 allowBrackets:Optional[bool]				= False,
				 verbose:Optional[bool]						= False) -> None:
		"""	Initialization of a `PContext` object.

			Args:
				script: The script to run.
				symbols: An optional dictionary of new symbols / functions to add to the interpreter.
				logFunc: An optional function that receives non-error log messages.
				logErrorFunc: An optional function that receives error log messages.
				printFunc: An optional function for printing messages to the screen, console, etc.
				preFunc: An optional function that is called before running a script.
				postFunc: An optional function that is called after running a script.
				errorFunc: An optional function that is called when an error occured.
				matchFunc: An optional function that is used to run regex comparisons.
				maxRuntime: Number of seconds that is a script allowed to run.
				fallbackFunc: An optional function to retrieve unknown symbols from the caller.
				monitorFunc: An optional function to monitor function calls, e.g. to forbid them during particular executions.
				allowBrackets: Allow "[" and "]" for opening and closing lists as well.
				verbose: Print more debug messages.
		"""

		from .Interpreter import parseScript, builtinFunctions

		# Extra parameters that can be provided
		self.script = script
		""" The script to run. """
		self.symbols:PSymbolDict = deepcopy(builtinFunctions)
		""" A dictionary of new symbols / functions to add to the interpreter. """
		self.logFunc = logFunc
		""" An optional function that receives non-error log messages. """
		self.logErrorFunc = logErrorFunc
		""" An optional function that receives error log messages. """
		self.printFunc = printFunc
		""" An optional function for printing messages to the screen, console, etc. """
		self.preFunc = preFunc
		""" An optional function that is called before running a script. """
		self.postFunc = postFunc
		""" An optional function that is called after running a script. """
		self.errorFunc = errorFunc
		""" An optional function that is called when an error occured. """
		self.matchFunc = matchFunc
		""" An optional function that is used to run regex comparisons. """
		self.maxRuntime = maxRuntime
		""" Number of seconds that is a script allowed to run. """
		self.fallbackFunc = fallbackFunc
		""" An optional function to retrieve unknown symbols from the caller. """
		self.monitorFunc = monitorFunc
		""" An optional function to monitor function calls, e.g. to forbid them during particular executions. """
		self.allowBrackets = allowBrackets
		""" Allow "[" and "]" for opening and closing lists as well. """

		# State, result and error attributes	
		self.ast:SSymbolsList = None
		""" The script's abstract syntax tree."""
		self.result:SSymbol = None
		""" Intermediate and final results during the execution. """
		self.verbose:bool = verbose
		""" Print more debug messages. """
		self.state:PState = PState.created
		""" The internal state of a script."""
		self.error:PErrorState = PErrorState(PError.noError, '', None, None )
		""" Error state. """
		self.meta:dict[str, str] = {}
		""" Dictionary of the script's meta tags and their arguments. """
		self.functions:dict[str, FunctionDefinition] = {}
		""" Dictoonary of defined script functions. """
		self.environment:dict[str, SSymbol] = {}		# Similar to variables, but not cleared
		""" Dictionary of variables that are passed by the application to the script. Similar to `variables`, but the environment is not cleared. """
		self.argv:list[str] = []
		""" List of string that are arguments to the script. """
		self.evaluateInline = True		# check and execute inline expressions
		""" Check and execute inline expressions in strings. """

		# Internal attributes that should not be accessed from extern
		self._maxRTimestamp:float = None
		""" The max timestamp until the script may run (internal). """
		self._callStack:list[PCall] = []
		""" The internal call stack (internal). """
		# self._variables:Dict[str, SSymbol] = {}


		# Add one to the callstack to add variables
		self.pushCall()

		# Add new commands
		if symbols:
			self.symbols.update(deepcopy(symbols))
		
		# Save the built-in commands. Will be restored later during reset.
		self.startupSymbols = deepcopy(self.symbols)
		""" The built-in commands. This original list will be restored later during reset. """


		# Extract meta data
		# These are lines idn the format:
		#	@key [<argument> ... ]
		# where <argument> is optional 
		# Running script:fy lines starting with @, extract meta data, remove this line from the script
		for line in self.script.splitlines():
			line = line.strip()
			if line.startswith('@'):
				_n, _, _v = line.strip().partition(' ')
				self.meta[_n[1:]] = _v.replace('\\n', '\n')
				self.script = self.script.replace(line, '')
		
		if not parseScript(self):
			raise PInvalidArgumentError(self)
		self.state = PState.ready


	def reset(self) -> None:
		"""	Reset the context / script. 
		"""
		self.symbols = deepcopy(self.startupSymbols)
		self.error = PErrorState(PError.noError, '', None, None)
		self._callStack.clear()
		self.pushCall(name = self.meta.get('name'))
		self.functions.clear()
		self.state = PState.ready

	def setError(self, error:PError, 
					   msg:str, 
					   state:Optional[PState] = PState.terminatedWithError, 
					   expression:SSymbol = None,
					   exception:Optional[Exception] = None) -> PContext:
		"""	Set the internal state and error codes. 
		
			These can be retrieved by accessing the state and error	attributes.

			Args:
				error: `PError` to indicate the type of error.
				msg: String that further explains the error.
				state: `PState` to indicate the state of the script. Default is "terminatedWithError".
				expression: The original `SSymbol` that caused the error.
				exception: Optional exception to provide with the error message.
			
			Return:
				Self.
		"""
		self.result = SNilSymbol()
		self.state = state
		self.error = PErrorState(error, msg, expression, exception)
		return self


	def copyError(self, pcontext:PContext) -> None:
		"""	Copy the error attributes from another `PContext` object.

			Args:
				pcontext: PContext object from which to copy the error status.
		"""
		self.result = pcontext.result
		self.state = pcontext.state
		self.error = pcontext.error


	def setResult(self, symbol:SSymbol) -> PContext:
		"""	Set the result symbol. The difference to directly setting the `result` attribute is that his
			method return *self*.
			
			Args:
				symbol: The `SSymbol` object to set as a result.
			
			Return:
				Self.
		"""
		self.result = symbol
		return self


	def logSymbol(self, symbol:SSymbol) -> None:
		"""	Log a symbol in verbose mode to the script's log function.

			Args:
				symbol: The `SSymbol` object to log.
		"""
		if self.verbose and self.logFunc:
			self.logFunc(self, f'Executed symbol: {symbol}')


	def pushCall(self, name:Optional[str] = None, args:dict[str, SSymbol] = {}) -> PCall:
		"""	Save various stack information to the script's call stack. 
			This creates a new PCall object.

			Args:
				name: Name of the function. 
				args: Arguments for the function call.

			Return:
				The new `PCall` object.
		"""
		if len(self._callStack) == maxRecursionDepth:
			raise PRuntimeError(self.setError(PError.maxRecursionDepth, f'Max level of function calls exceeded'))
		call = PCall(name = name, arguments = args)
		if len(self._callStack):
			call.variables = deepcopy(self._callStack[-1].variables)	# copy variables from the previous scope
		self._callStack.append(call)
		return call
	

	def popCall(self) -> None:
		"""	Remove a call from the stack..
		"""
		if not len(self._callStack):
			raise PRuntimeError(self.setError(PError.invalid, f'No call call to restore'))
		self._callStack.pop()


	@property
	def currentCall(self) -> Optional[PCall]:
		"""	Get the current call as a `PCall` object.

			Return:
				`PCall` object, or None.
		"""
		if not self._callStack:
			return None
		return self._callStack[-1]


	@property
	def arguments(self) -> dict[str, SSymbol]:
		"""	Return the arguments of the current call.

			Returns:
				The arguments of the current call.
		"""
		return self.currentCall.arguments
	

	@arguments.setter
	def arguments(self, value:dict[str, SSymbol]) -> None:
		"""	Set the arguments for the current call scope.

			Args:
				value: The arguments for the current call scope.
		"""
		self.currentCall.arguments = value


	def getVariables(self, expression:str) -> list[Tuple[str, SSymbol]]:
		"""	Return all variables and values which names match a
			regular expression.

			Args:
				expression: A string with the regular expression.

			Return:
				List of tuples ( *variable name*, *variable value* ).
		"""
		_expr = re.compile(expression, flags = re.IGNORECASE)
		_keys = [ k 
				  for k in self.variables.keys()
				  if re.match(_expr, k) ]
		return [ ( k, self.variables[k] ) 
				 for k in _keys ]
	

	@property
	def variables(self) -> dict[str, SSymbol]:
		"""	The variables of the current scope.

			Returns:
				The variables of the current scope.
		"""
		return self._callStack[-1].variables


	def setVariable(self, key:str, value:SSymbol) -> None:
		"""	Set a variable for a name. If the variable exists in the global scope, it is updated or set in all scopes.
			Otherwise, it is only updated or set in the current scope.

			Args:
				key: Variable name
				value: Value to store
		"""
		if key in self._callStack[0].variables:
			for eachCall in self._callStack:
				eachCall.variables[key] = value
		else:
			self._callStack[-1].variables[key] = value


	def delVariable(self, key:str) -> Optional[SSymbol]:
		"""	Delete a variable for a name. If the variable exists in the global scope, it is deleted in all scopes.
			Otherwise, it is only deleted in the current scope.

			Args:
				key: Variable name

			Return:
				Variable content, or None if variable is not defined.		
		"""
		try:
			if key in self._callStack[0].variables:
				v = self._callStack[-1].variables[key]	# return latest value afterwards
				for eachCall in self._callStack:
					del eachCall.variables[key]	
			else:
				v = self._callStack[-1].variables.get(key)
				del self._callStack[-1].variables[key]
			return v
		except KeyError:
			return None


	def getEnvironmentVariable(self, key:str) -> SSymbol:
		"""	Return an evironment variable for a case insensitive name.

			Args:
				key: Environment variable name

			Return:
				Environment variable content, or None.		
		"""
		return self.environment.get(key)
	

	def setEnvironmentVariable(self, key:str, value:SSymbol) -> None:
		"""	Set an environment variable for a name.

			Args:
				key: Environment variable name
				value: Value to store	
		"""
		self.environment[key] = value
	

	def clearEnvironment(self) -> None:
		"""	Remove all environment variables.
		"""
		self.environment.clear()


	def setEnvironment(self, environment:Optional[dict[str, SSymbol]] = {}) -> None:
		"""	Clear old environment and assign a new environment.

			This includes the meta tags in the format *meta.<tag>*.
			
			Args:
				environment: Dictionary with the new environment
		"""
		self.clearEnvironment()
		# First, add meta tags
		for eachKey, eachMeta in self.meta.items():
			self.setEnvironmentVariable(f'meta.{eachKey}', SSymbol.symbolFromValue(eachMeta))

		# Add the environment variables
		for eachKey, eachValue in environment.items():
			self.setEnvironmentVariable(eachKey, eachValue)

	
	@property
	def scriptName(self) -> str:
		"""	The name of the script (from the meta data).

			Return:
				The name of the script, or *None*.
		"""
		return self.meta.get('name')


	@scriptName.setter
	def scriptName(self, name:str) -> None:
		"""	Set the name of the script in the meta data.

			Args:
				name: Name of the script.
		"""
		self.meta['name'] = name
	

	def setMaxRuntime(self, maxRuntime:float) -> None:
		"""	Set the maximum runtime of the script.

			Args:
				maxRuntime: Maximum runtime in seconds.
		"""
		if self.state == PState.running:
			raise PUnsupportedError(self.setError(PError.runtime, f'Cannot set runtime while script is running'))
		self.maxRuntime = maxRuntime


	def getMeta(self, key:str, default:Optional[str] = '') -> str:
		"""	Return the argument of meta data, or an empty string.

			Args:
				key: Key of the meta data to look for.
				default: Default value to return if the key is not found.

			Return:
				String, value or the default value.
		"""
		return self.meta.get(key, default)


	def hasMeta(self, key:str) -> bool:
		"""	Check if a meta data key exists.

			Args:
				key: Key of the meta data to look for.

			Return:
				True if the key exists, False otherwise.
		"""
		return key in self.meta


	def run(self,
			arguments:list[str] = [], 
			isSubCall:Optional[bool] = False) -> PContext:
		"""	Run the script in the `PContext` instance.

			Args:
				arguments: Optional list of string arguments to the script. They are available to the script via the *argv* function.
				isSubCall: Optional indicator whether the script is called from another script.
			
			Return:
				`PContext` object with the result and the termination reason.
		"""
		return runScript(self, arguments, isSubCall)

