#
#	Interpreter.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of a simple s-expression-based command processor.
#
"""	The interpreter module implements an extensible lisp-based scripting runtime.
"""
from __future__ import annotations

from rich import inspect, print
from typing import Any, List, Union, Callable, Optional, Dict, cast, Tuple, cast
from dataclasses import dataclass, field

import re, random, time, string, base64, urllib.parse
import json
from decimal import Decimal, InvalidOperation, DivisionUndefined
from copy import deepcopy
from enum import IntEnum, auto
from collections import namedtuple
import datetime, operator

from .TextTools import removeCommentsFromJSON, findXPath, setXPath

# TODO More functions: set-nth, count-of, remove-nth, Insert-nth, floors



_maxRecursionDepth = 512
""" Max number of recursive calls. """

_onErrorFunction = 'on-error'
"""	Name of the on-error function that is executed in case of an error """

class PException(Exception):
	"""	Baseclass for interpreter exceptions. 
	
		Attributes:
			pcontext: `PContext` object with the error state.
	"""

	def __init__(self, pcontext:PContext) -> None:
		"""	Exception initialization.
		
			Args:
				pcontext: `PContext` object with the interpreter state and error messages.
		"""
		self.pcontext = pcontext
	
	def __str__(self) -> str:
		"""	Nicely printable version of the exception.

			Return:
				String.
		"""
		if self.pcontext:
			return str(self.pcontext.error)
		return super().__str__()


class PAssertionFailed(PException):
	"""	Exception to indicate a failed assertion. """
	...


class PDivisionByZeroError(PException):
	"""	Exception to indicate a division-by-zero error. """
	...


class PInterruptedError(PException):
	"""	Exception when the script execution was interrupted. """
	...


class PInvalidArgumentError(PException):
	"""	Exception when there was an invalid argument to a symbol etc. """
	...


class PInvalidTypeError(PException):
	"""	Exception when an invalid type was encountered. """
	...


class PNotANumberError(PException):
	"""	Exception when a number is expected. """
	...

class PPermissionError(PException):
	"""	Exception when execution of a function is not allowed. """
	...

class PQuitWithError(PException):
	"""	Exception to regularly quit the script execution with an error status. """
	...


class PQuitRegular(PException):
	"""	Exception to regularly quit the script execution without an error. """
	...


class PRuntimeError(PException):
	"""	Exception to indicate an interpreter runtime error. """
	...


class PTimeoutError(PException):
	"""	Exception to indicate a timeout of the running script. """
	...


class PUndefinedError(PException):
	"""	Exception to indicate an undefined symbol, variable, etc. """
	...


class PUnsupportedError(PException):
	"""	Exception to indicate an unsupported type or feature. """
	...


class SType(IntEnum):
	"""	Type definitions for supported interpreter types. """

	tNIL 			= auto()
	"""	NIL data type. """
	tString	 		= auto()
	"""	String data type. """
	tSymbol 		= auto()
	"""	Symbol data type. """
	tSymbolQuote	= auto()
	"""	Quoted data type. It is not executed. """
	tNumber			= auto()
	"""	Number data type (integer or float). """
	tBool			= auto()
	"""	Boolean data type. """
	tList			= auto()
	"""	List of `SSymbol`'s data type. """
	tListQuote		= auto()
	"""	List of `SSymbol`'s data type. It it not executed. """
	tLambda			= auto()
	"""	Lambda expression data type. """
	tJson			= auto()
	"""	JSON / dictionary data type. """
	tListBegin		= auto()
	"""	Beginning of a list. Internally used only. """
	tListEnd 		= auto()
	"""	Ending of a list. Internally used only. """

	def __str__(self) -> str:
		"""	Nice representation of a data type name.
		
			Return:
				String representation.
		"""
		return self.name[1:]
	

	def __repr__(self) -> str:
		"""	Nice representation of a data type name.
		
			Return:
				String representation.
		"""
		return self.__str__()
	

	def unquote(self) -> SType:
		"""	Return the unquoted equivalet type of a quoted type.

			Return:
				The unquotde version of a quoted type. If the type is not a quoted type then return the same type.
		"""
		if self == SType.tListQuote:
			return SType.tList
		elif self == SType.tSymbolQuote:
			return SType.tSymbol
		return self


class SSymbol(object):
	"""	The basic class to store and handle symbols, lists, and values in the Interpreter. 

		Attributes:
			value:	The actual stored value. This is either one of the the basic data typs, of a `SSymbol`, list of `SSymbol`, dictionary, etc.
			type: `SType` to indicate the type.
			length: The length of the symbol. Could be the length of a string, number of items in a list etc.
	
	"""

	__slots__ = (
		'type',
		'value',
		'length',
	)
	""" Slots of class attributes. """

	def __init__(self,	string:str = None,
						symbol:str = None,
						symbolQuote:str = None,
						number:Decimal = None,
						boolean:bool = None,
						lst:list[SSymbol] = None,
						lstQuote:list[SSymbol] = None,
						listChar:str = None,
						lmbda:Tuple[list[str], SSymbol] = None,
						jsnString:str = None,
						jsn:dict = None,
						value:Union[bool, str, int, float, list, dict] = None) -> None:
		"""	Initialization of a `SSymbol` object.
			
			Only one of the arguments must be passed to the function.
			If no argument is given, then the symbol becomes a NIL object.
		
			Args:
				string: `value` is a string (`SType.tString`).
				symbol: `value` is a string that represents a symbol (`SType.tSymbol`).
				symbolQuote: `value` is a string that represents quoted (ie. not executed) symbol (`SType.tSymbolQuote`).
				number: `value` is a Decimal number (`SType.tNumber`).
				boolean: `value` is a boolean value (`SType.tBool`).
				lst: `value` is a list of `SSymbol` elements (`SType.tList`).
				lstQuote: `value` is a list of quoted `SSymbol` elements (ie. not executed) (`SType.tListQuote`).
				listChar: `value` is a character that represents the start or end of a list (for parsing lists) (`SType.tListBegin` or `SType.tListEnd`)
				lmbda: `value` is a `SSymbol` object or a symbol that represents the executable part of a lambda expression (`SType.tLambda`).
				jsnString: `value` is a JSON string representation. It will be converted internally to a dictionary (`SType.tJson`).
				jsn: `value` is a JSON dictionary (`SType.tJson`).
				value: A value that is then automatically assigned to one of the basic, quoted types.
		"""

		self.value:Union[str, Decimal, bool, list[SSymbol], Tuple[list[str], SSymbol], Dict[str, Any]] = None
		self.type:SType = SType.tNIL

		# Try to determine an unknown type
		if value:
			if isinstance(value, bool):
				boolean = value
			elif isinstance(value, str):
				string = value
			elif isinstance(value, (int, float)):
				number = Decimal(value)
			elif isinstance(value, list):
				lstQuote = value
			elif isinstance(value, dict):
				jsn = value
			else:
				raise ValueError(f'Unsupported type: {type(value)} for value: {value}')

		if string:
			self.type = SType.tString
			self.value = string
			self.length = len(self.value)
		elif symbol:
			self.type = SType.tSymbol
			self.value = symbol
			self.length = 1
		elif symbolQuote:
			self.type = SType.tSymbolQuote
			self.value = symbolQuote[1:]
			self.length = 1
		elif listChar:
			self.type = SType.tListBegin if listChar == '(' else SType.tListEnd
			self.value = listChar
			self.length = 1
		elif number is not None:
			self.type = SType.tNumber
			self.value = number
			self.length = 1
		elif boolean is not None:
			self.type = SType.tBool
			self.value = boolean
			self.length = 1
		elif lst is not None:
			self.type = SType.tList
			self.value = lst
			self.length = len(self.value)
		elif lstQuote is not None:
			self.type = SType.tListQuote
			self.value = lstQuote
			self.length = len(self.value)
		elif lmbda is not None:
			self.type = SType.tLambda
			self.value = lmbda
			self.length = 1
		elif jsnString is not None:
			self.type = SType.tJson
			self.value = json.loads(jsnString)
			self.length = 1
		elif jsn is not None:
			self.type = SType.tJson
			self.value = jsn
			self.length = 1
		else:
			self.type = SType.tNIL
			self.value = False
			self.length = 0


	def __str__(self) -> str:
		"""	Nicely printable version of `value`.

			Return:
				String representation.
		"""
		return self.toString()
	

	def __repr__(self) -> str:
		"""	Nicely printable version of `value`.

			Return:
				String representation.
		"""
		return self.__str__()


	def __getitem__(self, key:int|slice) -> Any:
		"""	Return an element or a slice from a list, or a character from a string.

			Args:
				key: Either an number or a slice.
			
			Return:
				A single element or a sice of elements if `value` is a list, or a single or multiple characters if `value` is a string.
		"""
		if self.type in [ SType.tList, SType.tListQuote, SType.tString ]:
			return self.value[key]	# type:ignore [arg-type, index]
		return None
	

	def __contains__(self, obj:Any) -> bool:
		""" Check whether an object is contained within the value.

			This works for characters and strings, and elements and lists.
		
			Args:
				obj: Object to check.
			
			Return:
				True if the object is contained, False otherwise.
		"""
		if isinstance(obj, SSymbol):
			obj = obj.raw()
		if self.type == SType.tString:
			return obj in cast(str, self.value)
		if self.type in [ SType.tList, SType.tListQuote ]:
			for elem in cast(list, self.raw()):	# we need to iterate the list because of symbols, not values
				if obj == elem:
					return True
		return False
	

	def toString(self, quoteStrings:bool = False) -> str:
		if self.type in [ SType.tList, SType.tListQuote ]:
			return f'( {" ".join("(" if v == "[" else ")" if v == "]" else v.toString(quoteStrings = quoteStrings) for v in cast(list, self.value))} )'
			# return f'( {" ".join(str(v) for v in cast(list, self.value))} )'
		elif self.type == SType.tLambda:
			return f'( ( {", ".join(v.toString(quoteStrings = quoteStrings) for v in cast(tuple, self.value)[0])} ) {str(cast(tuple, self.value)[1])} )'
		elif self.type == SType.tBool:
			return str(self.value).lower()
		elif self.type == SType.tString:
			if quoteStrings:
				return f'"{str(self.value)}"'
			return str(self.value)
		elif self.type == SType.tJson:
			return json.dumps(self.value)
		elif self.type == SType.tNIL:
			return 'nil'
		return str(self.value)


	def append(self, arg:SSymbol) -> SSymbol:
		"""	Append an element if `value` is a list.

			Args:
				arg: Element to add to a list.
			
			Return:
				Self, or *None* in case of an error.
		"""
		if self.type == SType.tList:
			self.value.append(arg)	# type:ignore[union-attr]
			return self
		return None
	

	def raw(self) -> Any:
		"""	The Python "raw" value.

			Return:
				The raw value. For types that could not be converted directly the stringified version is returned.
		"""
		if self.type in [ SType.tList, SType.tListQuote ]:
			return [ v.raw() for v in cast(list, self.value) ]
		elif self.type in [ SType.tBool, SType.tString, SType.tSymbol, SType.tSymbolQuote, SType.tJson ]:
			return self.value
		if self.type == SType.tNumber:
			if '.' in str(self.value):	# float or int?
				return float(cast(Decimal, self.value))
			return int(cast(Decimal, self.value))
		return str(self.value)
	

class SExprParser(object):
	"""	Class that implements an S-Expression parser. """

	errorExpression:SSymbol = None
	"""	In case of an error this attribute contains the error expression. """

	def normalizeInput(self, input:str) -> List[SSymbol]:
		"""	Parse an input string into a list of opening and closing parentheses, and
			atoms. Atoms include symbols, numbers and strings.

			The results excludes all whitespaces. Also, special escape characters 
			outside and inside of strings are handled. The escape character is backslash.

			Args:
				input: The input string.
			
			Return:
				A list of paranthesis and atoms.
		"""
		normalizedInput:list[SSymbol] = []	# a list of normalized symbols
		currentSymbol = ''
		isEscaped = False
		inString = False
		jsonLevel = 0

		for ch in input:
			# escape and skip
			currentSymbol += ch
			currentSymbolLen = len(currentSymbol)

			# Handle Escpes
			if isEscaped:
				isEscaped = False
				continue
			if ch == '\\':
				isEscaped = True
				continue

			# String handling
			if currentSymbol == '"': # at the beginning of a quoted string -> continue reading
				continue
			if ch == '"' and currentSymbol[0] == '"':	# at the end of a quoted string. 
				normalizedInput.append(SSymbol(string = currentSymbol[1:-1]))		# add to normalized list
				currentSymbol = ''
				continue
			if currentSymbol[0] == '"': # in the middle of a quoted string. Then we accept all characters
				continue

			if ch == '{' and not inString:
				jsonLevel += 1
				continue
			if jsonLevel > 0:
				if ch == '"':	# ignore some things when we are in a JSON string
					inString = not inString
				if ch == '}' and not inString:
					jsonLevel -= 1
				if jsonLevel == 0 and currentSymbol[0] == '{':	# at the end of a JSON input 
					normalizedInput.append(SSymbol(jsnString = currentSymbol))		# add to normalized list
					currentSymbol = ''
					jsonLevel = 0
				continue

			# spaces are separators
			if ch.isspace():
				if currentSymbolLen > 1:
					normalizedInput.append(SSymbol(symbol = currentSymbol[:-1]))
				currentSymbol = ''
				continue

			# detect paranthesis
			if ch in '()':
				if currentSymbolLen > 1:
					normalizedInput.append(SSymbol(symbol = currentSymbol[:-1]))
				normalizedInput.append(SSymbol(listChar = ch))
				currentSymbol = ''
				continue

		return normalizedInput


	def ast(self, input:List[SSymbol]|str, topLevel:bool = True) -> List[SSymbol]:
		""" Generate an abstract syntax tree (AST) from normalized input.

			The result is a list of elements. Each element is either an
			atom, a string, a number, or again a list of elements.

			Args:
				input: Either a string or a list of `SSymbol` elements. A string would internally be parsed to a list of `SSymbol` elements before further processing.
				topLevel: Indicating whether a parsed input is at the top level or a branch of a another AST.
			
			Return:
				A list that represents the abstract syntax tree.
			
			Raises:
				ValueError: In case of a syntax error (usually missing opening or closing paranthesis).
		"""

		# Normalize if the input is a string
		if isinstance(input, str):
			input = self.normalizeInput(input)

		ast:list[SSymbol] = []
		# Go through each element in the normalizedInput:
		# - if it is an open parenthesis, find matching parenthesis and make an recursive
		#   call for content in-between. Add the result as an element to the current list.
		# - if it is an atom, just add it to the current list.
		# At the end, return the current ast
		index = 0
		isQuote = False
		while index < len(input):
			symbol = input[index]
			
			# A list may be prefixed with a single '. It is then traited as a plain list or symbol, and not executed
			if symbol.value == '\'':
				isQuote = True
				index += 1
				continue

			if symbol.type == SType.tListBegin:	# Start of another list
				startIndex = index + 1
				matchCtr = 1 # If 0, parenthesis has been matched.
				# Determine the matching closing paranthesis on the same level
				while matchCtr != 0:
					index += 1
					if index >= len(input):
						self.errorExpression = input	# type:ignore[assignment]
						raise ValueError(f'Invalid input: Unmatched opening parenthesis: {input}')
					symbol = input[index]
					if symbol.type == SType.tListBegin:
						matchCtr += 1
					elif symbol.type == SType.tListEnd:
						matchCtr -= 1
			
				if isQuote:	# escaped with ' -> plain list
					ast.append(SSymbol(lstQuote = self.ast(input[startIndex:index], False)))
				else:		# normal list
					ast.append(SSymbol(lst = self.ast(input[startIndex:index], False)))
			elif symbol.type == SType.tListEnd:
					self.errorExpression = input	# type:ignore[assignment]
					raise ValueError('Invalid input: Unmatched closing parenthesis.')
			elif symbol.type == SType.tJson:
				ast.append(symbol)
			elif symbol.type == SType.tString:
				ast.append(symbol)
			else:
				try:
					ast.append(SSymbol(number = Decimal(symbol.value))) # type:ignore [arg-type]
				except InvalidOperation:
					if symbol.type == SType.tSymbol and symbol.value in [ 'true', 'false' ]:
						ast.append(SSymbol(boolean = (symbol.value == 'true')))
					elif symbol.type == SType.tSymbol and symbol.value == 'nil':
						ast.append(SSymbol())
					else:
						if (_s := cast(str, symbol.value)).startswith('\''):
							ast.append(SSymbol(symbolQuote = _s))
						else:
							ast.append(symbol)
			index += 1
			isQuote = False
		
		# If we are on the top level, *all* the symbols must be S-expressions, not stand-alone symbols
		if topLevel:
			for a in ast:
				if a.type != SType.tList:
					raise ValueError(f'Invalid input: plain symbols are not allowed at top-level: {a}')

		return ast

###############################################################################

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
	returning				= auto()
	"""	script is returning from a scope. """

	def isEndscriptState(self) -> bool:
		"""	Check whether the end of a script has been reached.
		
			Return:
				True if one of the termination states is set.
		"""
		return self.value in  [ self.canceled, self.terminated, self.terminatedWithResult, self.terminatedWithError, self.returning ]


class PError(IntEnum): 
	"""	Error codes.
	"""
	quitWithError			= -1
	"""	Script terminates with an error. """
	noError 				= 0
	"""	No-error status. """
	assertionFailed			= auto()
	"""	Failed assertion. """
	canceled				= auto()
	"""	Cancel script execution. """
	divisionByZero			= auto()
	"""	Division by zero error. """
	invalid					= auto()
	"""	Invalid argument, input or condition. """
	invalidType				= auto()
	"""	Invalid type."""
	maxRecursionDepth 		= auto()
	"""	Maximum number of recursive function calls reached. """
	notANumber				= auto()
	"""	SSymbol is not a number, but it was exepected."""
	notAString				= auto()
	"""	SSymbol is not a string, but it was exepected."""
	notASymbol				= auto()
	"""	SSymbol is not a symbol, but it was exepected."""
	permissionDenied		= auto()
	"""	Function is not allowed to be executed. """
	timeout					= auto()
	"""	Script max runtime exceeded. """
	runtime					= auto()
	"""	Intneral runtime error. """
	undefined				= auto()
	"""	Requested symbol is undefined. """


@dataclass
class PScope():
	"""	A dataclass that holds scope-specific attributes.

		Attributes:
			name: Scope name, e.g. the name of another script.
			arguments: Dictionary of arguments (name -> `SSymbol`) for a scope.
			result: The result or return value of a scope.
	"""
	name:str						= None
	arguments:dict[str, SSymbol]	= field(default_factory = dict)
	result:str						= None


class PContext():
	"""	Process context for a single script. Can be re-used.

		Attributes:
			argv: List of string that are arguments to the script.
			ast: The script' abstract syntax tree.
			environment: Dictionary of variables that are passed by the application to the script. Similar to `variables`, but the environment is not cleared.
			error: Error state.
			errorFunc: An optional function that is called when an error occured.
			evaluateInline: Check and execute inline expressions in strings.
			functions: Dictoonary of defined script functions.
			logErrorFunc: An optional function that receives error log messages.
			logFunc: An optional function that receives non-error log messages.
			matchFunc: An optional function that is used to run regex comparisons.
			maxRuntime: Number of seconds that is a script allowed to run.
			meta: Dictionary of the script's meta tags and their arguments.
			postFunc: An optional function that is called after running a script.
			preFunc: An optional function that is called before running a script.
			printFunc: An optional function for printing messages to the screen, console, etc.
			result: Intermediate and final results during the execution.
			script: The script to run.
			state: The internal state of a script.
			symbols: A dictionary of new symbols / functions to add to the interpreter.
			variables: Dictionary of variables.
			verbose: Whether verbosity is turned on for a script run.
			_maxRTimestamp: The max timestamp until the script may run (internal).
			_scopeStack: The internal scopy stack (interna9).
			_symbolds: Dictionary with all build-in and provided functions (internal).
	"""

	__slots__ = (
		'script',
		'symbols',
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
		'ast',
		'result',
		'state',
		'error',
		'meta',
		'variables',
		'functions',
		'environment',
		'argv',
		'verbose',
		'evaluateInline',
		'_maxRTimestamp',
		'_scopeStack',
		'_symbolds',
	)
	""" Slots of class attributes. """

	_macroMatch = re.compile(r'\$\{.*?\}\$|\\\\\$\{.*?\}\$')	# Trick: ".*?" The ? is for non-greedy, for the shortest match
	"""	Regex for matching macros in strings and JSON. """

	def __init__(self, 
				 script:str,
				 symbols:PSymbolDict				= None,
				 logFunc:PLogCallable 				= lambda pcontext, msg: print(f'** {msg}'),
				 logErrorFunc:PErrorLogCallable		= lambda pcontext, msg, exception: print(f'!! {msg}'),
				 printFunc:PLogCallable 			= lambda pcontext, msg: print(msg),
				 preFunc:PFuncCallable				= None,
				 postFunc:PFuncCallable				= None,
			 	 errorFunc:PFuncCallable			= None,
				 matchFunc:PMatchCallable			= lambda pcontext, l, r: l == r,
				 maxRuntime:float					= None,
				 fallbackFunc:PSymbolCallable		= None,
				 monitorFunc:PSymbolCallable		= None) -> None:
		"""	Initialization of a `PContext` object.

			Args:
				script: The script to run.
				symbols: A dictionary of new symbols / functions to add to the interpreter.
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
		"""

		# Extra parameters that can be provided
		self.script = script
		self.symbols = _builtinCommands
		self.logFunc = logFunc
		self.logErrorFunc = logErrorFunc
		self.printFunc = printFunc
		self.preFunc = preFunc
		self.postFunc = postFunc
		self.errorFunc = errorFunc
		self.matchFunc = matchFunc
		self.maxRuntime = maxRuntime
		self.fallbackFunc = fallbackFunc
		self.monitorFunc = monitorFunc

		# State, result and error attributes	
		self.ast:list[SSymbol] = None
		self.result:SSymbol = None
		self.state:PState = PState.created
		self.error:PErrorState = PErrorState(PError.noError, 0, '', None )
		self.meta:Dict[str, str] = {}
		self.variables:Dict[str,SSymbol] = {}
		self.functions:dict[str, FunctionDefinition] = {}
		self.environment:Dict[str,SSymbol] = {}		# Similar to variables, but not cleared
		self.argv:list[str] = []
		self.verbose:bool = None		# Store the runtime verbosity of the run() function
		self.evaluateInline = True		# check and execute inline expressions

		# Internal attributes that should not be accessed from extern
		self._maxRTimestamp:float = None
		self._scopeStack:list[PScope] = [PScope()]
		self._symbolds:PSymbolDict = None		# builtins + provided commands

		# Add new commands
		if symbols:
			self.symbols.update(symbols)

		# Extract meta data
		# These are lines idn the format:
		#	@key [<argument> ... ]
		# where <argument> is optional 
		# Running script:fy lines starting with @, extract meta data, remove this line from the script
		for line in self.script.splitlines():
			line = line.strip()
			if line.startswith('@'):
				_n, _, _v = line.strip().partition(' ')
				self.meta[_n[1:]] = _v
				self.script = self.script.replace(line, '')
		
		if not self.validate():
			raise PInvalidArgumentError(self)
		self.state = PState.ready


	def validate(self) -> bool:
		"""	Parse and validate the script.

			Return:
				Boolean indicating the success.
		"""
		# Validate script first.
		parser = SExprParser()
		try:
			self.ast = parser.ast(removeCommentsFromJSON(self.script))
		except ValueError as e:
			self.setError(PError.invalid, str(e), expression = parser.errorExpression)
			return False
		return True


	def reset(self) -> None:
		"""	Reset the context / script. 
			
			This method may also be implemented in a subclass, but that subclass must then call this method as well.
		"""
		self.error = PErrorState(PError.noError, 0, '', None)
		self.variables.clear()
		self._scopeStack.clear()
		self.saveScope(name = self.meta.get('name'))
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
		self.result = SSymbol()
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


	def saveScope(self, name:Optional[str] = None) -> None:
		"""	Save the current program counter and other information to the scope stack. 
			This creates a new scope.

			Args:
				name: Name of the scope. Relevant for functions.
		"""
		if len(self._scopeStack) == _maxRecursionDepth:
			raise PRuntimeError(self.setError(PError.maxRecursionDepth, f'Max level of function calls exceeded'))
		pscope = PScope()
		pscope.name = name
		self._scopeStack.append(pscope)
	

	def restoreScope(self) -> None:
		"""	Restore the program counter and other information from the scope stack.
			This removes the current scope and replaces it with the previous scope.
		"""
		if not len(self._scopeStack):
			raise PRuntimeError(self.setError(PError.invalid, f'No scope to restore'))
		self.scope.result = self._scopeStack.pop().result	# assign the old scope the result from the previous scope


	@property
	def scope(self) -> Optional[PScope]:
		"""	Get the current scope as a `PScope` object.

			Return:
				`PScope` object, the current scope, or None.
		"""
		if not self._scopeStack:
			return None
		return self._scopeStack[-1]


	@property
	def name(self) -> str:
		"""	The name of the current scope. This could be the name
			of the current script (from the meta data) or the name of the 
			current function.

			Returns:
				The name of the current scope, or None.
		"""
		return self.scope.name if self.scope and self.scope.name else self.scriptName


	@property
	def arguments(self) -> dict[str, SSymbol]:
		"""	Return the arguments of the current scope.

			Returns:
				The arguments of the current scope.
		"""
		return self.scope.arguments
	

	@arguments.setter
	def arguments(self, value:dict[str, SSymbol]) -> None:
		"""	Set the arguments for the current scope.

			Args:
				value: The arguments for the current scope.
		"""
		self.scope.arguments = value


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


	def delVariable(self, key:str) -> Optional[SSymbol]:
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


	def getEnvironmentVariable(self, key:str) -> SSymbol:
		"""	Return an evironment variable for a case insensitive name.

			Args:
				key: Environment variable name

			Return:
				Environment variable content, or None.		
		"""
		return self.environment.get(key.lower())
	

	def setEnvironmentVariale(self, key:str, value:SSymbol) -> None:
		"""	Set an environment variable for a case insensitive name.

			Args:
				key: Environment variable name
				value: Value to store	
		"""
		self.environment[key.lower()] = value
	

	def clearEnvironment(self) -> None:
		"""	Remove all environment variables.
		"""
		self.environment.clear()


	def setEnvironment(self, environment:Optional[dict[str, SSymbol]] = {}) -> None:
		"""	Clear old environment and assign a new environment.
			
			Args:
				environment: Dictionary with the new environment
		"""
		self.clearEnvironment()
		for eachKey, eachValue in environment.items():
			self.setEnvironmentVariale(eachKey, eachValue)

	
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


	def getArgument(self, symbol:SSymbol, 
						  idx:int = None, 
						  expectedType:SType|Tuple[SType, ...] = None, 
						  doEval:bool = True) -> PContext:
		"""	Verify that an expression is a list and return an argument symbol,
			while optionally verify the allowed type(s) for that argument.

			If any of these validations fail, an exception is raised.

			This method also assigns a result and error state to *self*.

			Args:
				symbol: The symbol that contains an expression.
				idx: Optional index if the symbol contains a list of symbols.
				expectedType: one or multiple data types that are allowed for the retrieved argument symbol.
				doEval: Optionally recursively evaluate the symbol.
			
			Return:
				Result `PContext` object with the result, possible changed variable and other states.
			
			Raises:
				`PInvalidArgumentError`: In case of an error.
		"""

		# evaluate symbol
		_symbol = symbol[idx] if idx is not None else symbol

		if doEval:
			pcontext = self._executeExpression(_symbol, symbol)
		else:
			pcontext = self
			pcontext.result = _symbol
		
		# Check result type
		if expectedType is not None:
			if isinstance(expectedType, SType):
				expectedType = ( expectedType, )
			if pcontext.result is not None and pcontext.result.type not in expectedType: 
				raise PInvalidArgumentError(self.setError(PError.invalid, f'expression: {symbol} - invalid type for argument: {_symbol}, expected type: {expectedType}, is: {pcontext.result.type}'))

		self.result = pcontext.result
		self.state = pcontext.state
		return pcontext


	def valueFromArgument(self, symbol:SSymbol, 
								idx:int = None, 
						  		expectedType:SType|Tuple[SType, ...] = None, 
						  		doEval:bool = True) -> Tuple[PContext, Any]:
		"""	Return the actual value from an argument symbol.
			
			Args:
				symbol: The symbol that contains an expression.
				idx: Optional index if the symbol contains a list of symbols.
				expectedType: one or multiple data types that are allowed for the retrieved argument symbol.
				doEval: Optionally recursively evaluate the symbol.
			
			Return:
				Result tuple of the updated `PContext` object with the result and the value.
		"""
		p,r = self.resultFromArgument(symbol, idx, expectedType, doEval)
		return (p, r.value)
		

	def resultFromArgument(self, symbol:SSymbol, 
								 idx:int = None, 
						  		 expectedType:SType|Tuple[SType, ...] = None, 
						  		 doEval:bool = True) -> Tuple[PContext, SSymbol]:
		"""	Return the `SSymbol` result from an argument symbol.
			
			Args:
				symbol: The symbol that contains an expression.
				idx: Optional index if the symbol contains a list of symbols.
				expectedType: one or multiple data types that are allowed for the retrieved argument symbol.
				doEval: Optionally recursively evaluate the symbol.
			
			Return:
				Result tuple of the updated `PContext` object with the result and the symbol.
		"""
		return (p := self.getArgument(symbol, idx, expectedType, doEval), p.result)


	def executeSubexpression(self, expression:str) -> PContext:
		"""	Execute an expression that is contained in a string. This starts a sub-execution of a new script,
			but in the same context.

			Args:
				expression: String with list of symbols to execute.
			
			Return:
				`PContext` object.
			
			Raises:
				`PInvalidArgumentError`: In case of an error.
		"""
		_ast = self.ast
		_script = self.script
		self.script = expression
		if not self.validate():
			raise PInvalidArgumentError(self)
		self.result = None
		self.run(arguments = self.argv, verbose = self.verbose, isSubCall = True)	# might throw exception
		self.ast = _ast
		self.script = _script
		return self
	

	def assertSymbol(self, symbol:SSymbol, length:int = None, minLength:int = None, maxLength:int = None) -> None:
		"""	Assert that the symbol is a list of symbols, and that the list length is within the given
			arguments: either an exact length, or a minimum lenght and a maximum length. 
			
			All length parameter are optional. If none is given then no length check happens.

			Args:
				symbol: The `SSymbol` to check. It must be a list.
				length: Optional exact list length to assert.
				minLength: Optional minimum list length to assert.
				maxLength: Optional maximum list length to assert.
			
			Raises:
				PInvalidArgumentError: In case any assertion fails.
		"""

		if symbol.type != SType.tList:
			raise PInvalidArgumentError(self.setError(PError.invalid, f'wrong expression format: {symbol}'))
		if length is not None and symbol.length != length:
			raise PInvalidArgumentError(self.setError(PError.invalid, f'wrong number of arguments: {symbol.length} for expression: {symbol} must be {length}'))
		if minLength is not None and symbol.length < minLength:
			raise PInvalidArgumentError(self.setError(PError.invalid, f'wrong length for expression: {symbol}'))
		if maxLength is not None and symbol.length > maxLength:
			raise PInvalidArgumentError(self.setError(PError.invalid, f'wrong length for expression: {symbol}'))


	def run(self,
			arguments:List[str] = [], 
			verbose:Optional[bool] = False, 
			isSubCall:bool = False) -> PContext:
		"""	Run the script in the `PContext` instance.

			Args:
				arguments: Optional list of string arguments to the script. They are available to the script via the *argv* function.
				verbose: Optional indicator whether the interpreter runs the script in verbose mode.
				isSubCall: Optional indicator whether the script is called from another script.
			
			Return:
				`PContext` object with the result and the termination reason.
		"""

		def _terminating(pcontext:PContext) -> None:
			"""	Handle the error setup, fill in error and message, and call the error and post function callbacks.
				Don't overwrite already set error values.
					
				Args:
					pcontext: Current PContext for the script.
			"""
			if pcontext.error.error not in [ PError.noError, PError.quitWithError ]:
				if pcontext.logErrorFunc:
					# import traceback
					# traceback.print_exc()
					pcontext.logErrorFunc(pcontext, pcontext.error.message, pcontext.error.exception)
				if pcontext.errorFunc:
					pcontext.errorFunc(pcontext)
			
			# Run "on-error" function, if defined
			if pcontext.error.error != PError.noError and  _onErrorFunction in pcontext.functions:
				_p = deepcopy(pcontext)	# Save old pcontext state
				try:
					pcontext = pcontext._executeFunction(SSymbol(lst = [ SSymbol(symbol = _onErrorFunction), 
																		 SSymbol(number = pcontext.error.error.name),
																		 SSymbol(number = pcontext.error.message)
																	   ]),
														_onErrorFunction,
														pcontext.functions[_onErrorFunction])
				except Exception as e:
					if pcontext.logErrorFunc:
						pcontext.logErrorFunc(pcontext, pcontext.error.message, pcontext.error.exception)
				else:
					pcontext = _p	# restore old pcontext state

			if pcontext.state != PState.ready and pcontext.postFunc:	# only when really running, after preFunc succeeded
				pcontext.postFunc(pcontext)
			
			if pcontext.error.error == PError.noError:
				if pcontext.state not in [PState.terminated, PState.terminatedWithResult]:
					pcontext.state = PState.terminated
			else:
				pcontext.state = PState.terminatedWithError


		if not self.validate():
			return self
		if not isSubCall:
			self.reset()

		# There is some more functionality offered in form of the "argv" function (direct access to elements),
		# so "argv" couldn't just be a variable.
		self.argv = arguments	
		self.environment['argc'] = SSymbol(number = Decimal(len(self.argv)))
		self.verbose = verbose

		# Call Pre-Function
		if self.preFunc:
			if self.preFunc(self) is None:
				self.setError(PError.canceled, 'preFunc canceled', state=PState.canceled)
				_terminating(self)
				return self

		# Start running
		self.state = PState.running
		if self.maxRuntime is not None:	# set max runtime
			self._maxRTimestamp = datetime.datetime.utcnow().timestamp() + self.maxRuntime
		if scriptName := self.scriptName and not isSubCall:
			self.logFunc(self, f'Running script: {scriptName}, arguments: {arguments}')

		# execute all top level S-expressions
		for symbol in self.ast:
			try:
				self._executeExpression(symbol, None)
			except PException as e:
				if isSubCall:
					raise e
				self.copyError(e.pcontext)
				_terminating(e.pcontext)
				return e.pcontext
			except Exception as e:
				if isSubCall:
					raise e
				self.setError(PError.runtime, f'runtime exception: {str(e)}', exception = e)
				_terminating(self)
				return self

		_terminating(self)
		return self
	

	def _checkTimeout(self) -> None:
		"""	Check for script timeout.

			Raises:
				`PTimeoutError`: In case the script timeout is reached.
		"""
		if self._maxRTimestamp is not None and self._maxRTimestamp < datetime.datetime.utcnow().timestamp():
			raise PTimeoutError(self.setError(PError.timeout, f'Script timeout ({self.maxRuntime} s)'))


	def _executeExpression(self, symbol:SSymbol, parentSymbol:SSymbol) -> PContext:
		"""	Recursively execute a symbol as an expression.

			Args:
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the result.
			
			Raises:
				`PUndefinedError`: In case a symbol is undefined.
				`PInvalidArgumentError`: In case an unexpected symbol is encountered.
		"""

		# Check for timeout
		self._checkTimeout()

		# First resolve the S-Expression
		if not symbol.length:
			return self.setResult(SSymbol())
		firstSymbol = symbol[0] if symbol.length and symbol.type == SType.tList else symbol

		if firstSymbol.type == SType.tList:
			if firstSymbol.length > 0:
				# implicit progn
				return _doProgn(self, SSymbol(lst = [ SSymbol(symbol = 'progn') ] + symbol.value ))	#type:ignore[operator]
			else:
				self.result = SSymbol()
				return self

		elif firstSymbol.type == SType.tListQuote:
			return _doQuote(self, SSymbol(lst = [ SSymbol(symbol = 'quote'), SSymbol(lst = firstSymbol.value)]))	

		elif firstSymbol.type == SType.tSymbol:
			_s = cast(str, firstSymbol.value)

			# Just return already boolean values in the result here
			if (_fn := self.functions.get(_s)) is not None:
				return self._executeFunction(symbol, _s, _fn)
			elif (_cb := self.symbols.get(_s)) is not None:	# type:ignore[arg-type]
				if self.monitorFunc:
					self.monitorFunc(self, firstSymbol)
				return _cb(self, symbol)
			elif _s in self.scope.arguments:
				self.result = deepcopy(self.scope.arguments[_s])
				return self
			elif _s in self.variables:
				self.result = deepcopy(self.variables[_s])
				return self
			elif _s in self.environment:
				self.result = deepcopy(self.environment[_s])
				return self

			# Try to get the symbol's value from the caller, if possible
			else:
				if self.fallbackFunc:
					return self.fallbackFunc(self, symbol)
				raise PUndefinedError(self.setError(PError.undefined, f'undefined symbol: {_s} | in symbol: {parentSymbol}'))

		elif firstSymbol.type == SType.tSymbolQuote:
			return _doQuote(self, SSymbol(lst = [ SSymbol(symbol = 'quote'), SSymbol(symbol = firstSymbol.value)]))	

		elif firstSymbol.type == SType.tLambda:
			return self._executeFunction(symbol, _s)

		elif firstSymbol.type == SType.tString:
			return self.checkInStringExpressions(firstSymbol)
			
		elif firstSymbol.type == SType.tNumber:
			return self.setResult(firstSymbol)	# type:ignore [arg-type]

		elif firstSymbol.type == SType.tBool:
			return self.setResult(firstSymbol)

		elif firstSymbol.type == SType.tJson:
			return self.checkInStringExpressions(symbol)

		raise PInvalidArgumentError(self.setError(PError.invalid, f'Unexpected symbol: {firstSymbol.type} - {firstSymbol}'))


	def checkInStringExpressions(self, symbol:SSymbol) -> PContext:
		"""	Replace all inline expressions in a string. 
		
			Expressions are replaced recursively.

			Args:
				symbol: The symbol to execute.

			Return:
				`PContext` object that contains as a result the string with all expressions executed.
		"""

		# Return immediately if inline replacements are disabled
		if not self.evaluateInline or symbol.type not in [ SType.tString, SType.tJson ]:
			return self.setResult(symbol)
		
		line = str(symbol) 

		# match macros and escaped macros
		# find matches
		matches = re.findall(self._macroMatch, line)
		_escapedMatches:dict[str, str] = {}
		for idx, _m in enumerate(matches):

			# collect all escaped macros to be replaced later again
			# We need to do this first because they could match with
			# an unescaped macro during replacement
			if _m[0] == '\\':
				line = line.replace(_m, _p := f'__--{str(idx)}--__')
				_escapedMatches[_p] = _m
			
			# Replace macro text with result of its evaluation
			else:
				_x = str(_m[2:-2]).replace('\\"', '"')
				_e = self.executeSubexpression(_x)	# may throw exception
				# replace only the first occurance
				line = line.replace(_m, str(_e.result), 1)
		
		# Replace placeholders for escaped macros
		for _p, _m in _escapedMatches.items():
			line = line.replace(_p, _m[2:], 1)

		# The following might be easier with a regex, but we want to allow recursive macros, therefore
		# parsing the string is simpler for now. Suggestions welcome!

		# i = 0
		# l = len(line)
		# result = ''
		# while i < l:
		# 	c = line[i]
		# 	i += 1

		# 	# Found escape
		# 	if c == '\\' and i < l:
		# 		result += line[i]
		# 		i += 1

		# 	# Found [ in the input line
		# 	elif c == '[':
		# 		expression = c
		# 		oc = 0	# expression deep level
		# 		# try to find the end of the expression.
		# 		# Skip contained macros in between. They will be
		# 		# resolved recursively later
		# 		while i < l:
		# 			c = line[i]
		# 			i += 1
		# 			if c == '\\' and i < l:
		# 				expression += line[i]
		# 				i += 1
		# 			elif c == '[':
		# 				oc += 1
		# 				expression += '['
		# 			elif c == ']':
		# 				if oc > 0:	# Skip if not end of _this_ expression
		# 					oc -= 1
		# 					expression += ']'
		# 				else:	# End of macro. Might contain other expressions! Those will be resolved later
		# 					expression += c
		# 					r = self.executeSubexpression(expression[1:-1])	# may throw exception
		# 					result += str(r.result.value) if r.result else ''
		# 					break	# Break the inner while
		# 			else:
		# 				expression += c
			
		# 	# Normal character found
		# 	else:
		# 		result += c
		if symbol.type == SType.tString:
			return self.setResult(SSymbol(string = line))
		return self.setResult(SSymbol(jsnString = line))


	def _executeFunction(self, symbol:SSymbol, functionName:str, functionDef:Optional[FunctionDefinition] = None) -> PContext:
		""" Execute a named function or lambda function.

			Args:
				symbol: The symbol to execute.
				functionName: The name of the function that is executed. In case of a lambda this name is random.
				functionDef: The executable part of a function or lambda function.

			Return:
				The updated `PContext` object with the function result.
		"""
		if not functionDef:
			functionDef = self.functions[functionName]
		_argNames, _code = functionDef # type:ignore[misc]

		# check arguments
		if not (symbol.type == SType.tSymbol and len(_argNames) == 0) and not (symbol.type == SType.tList and len(_argNames) == symbol.length - 1):
		# if symbol.type != SType.tList or len(_argNames) != symbol.length - 1:	# type:ignore
			raise PInvalidArgumentError(self.setError(PError.invalid, f'number of arguments doesn\'t match for function : {functionName}. Expected: {len(_argNames)}, got: {symbol.length - 1}'))

		# execute and assign arguments
		_args:dict[str, SSymbol] = {}
		if symbol.length > 1:
			for i in range(1, symbol.length):
				_args[_argNames[i-1]] = self._executeExpression(symbol[i], symbol).result	# type:ignore [index]

		# Assign arguments to new scope
		self.saveScope(functionName)
		self.scope.arguments = _args

		# execute the code
		self._executeExpression(_code, symbol)
		self.restoreScope()
		return self


	def _joinExpression(self, symbols:list[SSymbol], sep:str = ' ') -> PContext:
		"""	Join all symbols in an expression. 

			Args:
				symbols: A list of symbols to join.
				sep: An optional separator for each of the stringified symbols.
			
			Return:
				The updated `PContext` object with the function result. The `PContext.result` attribute contains the joint string.

		"""
		strings:list[str] = []
		for i in range(len(symbols)):	
			p = self.getArgument(symbols[i])
			if p.result is None:
				strings.append('nil')
			else:
				strings.append(str(p.result))
				
		self.result = SSymbol(string = sep.join(strings))
		return self
 
###############################################################################


PFuncCallable = Callable[[PContext], PContext]
"""	Function callback for pre, post and error functions.
"""

PSymbolCallable = Callable[[PContext, SSymbol], PContext]
"""	Signature of a symbol callable. The callbacks are 
	called with a `PContext` object	and is supposed to return
	it again, or None in case of an error.
"""

PLogCallable = Callable[[PContext, str], None]
"""	Function callback for normal log functions.
"""

PErrorLogCallable = Callable[[PContext, str, Exception], None]
"""	Function callback for error log functions.
"""

PMatchCallable = Callable[[PContext, str, str], bool]
"""	Signature of a match function callable.

	It will get called with the current `PContext` instance,
	a regular expression, and the string to check. It must return
	a boolean value that indicates the result of the match.
"""

PSymbolDict = Dict[str, PSymbolCallable]
"""	Dictionary of function callbacks for commands. 
"""

PSymbolList = List[SSymbol]
"""	List of SSymbol instances.
"""

PErrorState = namedtuple('PErrorState', [ 'error', 'message', 'expression', 'exception' ])
"""	Named tuple that represents an error state. 

	It contains the error code, the error message, the `SSymbol` expression that caused the error,
	and an (optional) exception.
"""

FunctionDefinition = Tuple[List[str], SSymbol]
"""	A data type that defines a *defun* function definition. The first tupple
	element is a list of argument names, and the second element is an `SSymbol`
	that is executed as the function body.
"""


###############################################################################
#
#	build-in symbol functions
#

def _doArgv(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	With the *argv* function one can access the individual arguments of a script.

		- Without an index argument this function returns the whole argument list, including the script name.
		- If the index is 0 then only the script name is returned.
		- Otherwise the nth argument is returned, starting with 1.

		Example:
			::

				(argv) -> The script name and all arguments
				(argv 3) -> The third script arguments

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.
		
		Raises:
			`PInvalidArgumentError`: In case of an error.

	"""
	if symbol.type == SType.tSymbol or (symbol.type == SType.tList and symbol.length == 1):
		return pcontext.setResult(SSymbol(string = ' '.join(pcontext.argv)))
	else:
		pcontext, _idx = pcontext.valueFromArgument(symbol, 1, SType.tNumber)
		idx = int(_idx)
		if idx < 0 or idx >= len(pcontext.argv):
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong index: {idx} for argv. Must be [0..{len(pcontext.argv)-1}]'))
		return pcontext.setResult(SSymbol(string = pcontext.argv[idx]))


def _doAssert(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	 Assert a condition. If it fails an exception is raised and script execution interrupted.

		Example:
			::

				(assert (< x 4))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.

		Raises:
			`PAssertionFailed`: In case the assertion fails.
	"""
	pcontext.assertSymbol(symbol, 2)
	pcontext, value = pcontext.valueFromArgument(symbol, 1, SType.tBool)
	if not value:
		raise PAssertionFailed(pcontext.setError(PError.assertionFailed, f'Assertion failed: {symbol[1]}'))
	return pcontext


def _doB64Encode(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Base64-encode a string.

		Example:
			::

				(base64-encode "Hello, World") -> SGVsbG8gV29ybGQ=

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result includes the encoded string.
	"""
	pcontext.assertSymbol(symbol, 2)

	# get string
	pcontext, value = pcontext.valueFromArgument(symbol, 1, SType.tString)
	return pcontext.setResult(SSymbol(string = base64.b64encode(value.encode('utf-8')).decode('utf-8')))


def _doBoolean(pcontext:PContext, symbol:SSymbol, value:bool) -> PContext:
	"""	Just set and return a boolean value.

		Example:
			::

				(true)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.
			value: The actual boolean value.

		Return:
			The updated `PContext` object. The result includes either *True* or *False*.
	"""
	pcontext.assertSymbol(symbol, 1)
	return pcontext.setResult(SSymbol(boolean = value))


def _doCar(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Get the first symbol of a list without changing the list.

		Example:
			::

				(car (1 2 3)) -> 1

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is a list's first symbol or NIL.
	"""
	pcontext.assertSymbol(symbol, 2)

	pcontext, value = pcontext.valueFromArgument(symbol, 1, (SType.tListQuote, SType.tList, SType.tNIL))
	if pcontext.result.length == 0 or pcontext.result.type == SType.tNIL:
		return pcontext.setResult(SSymbol())	# nil
	return 	pcontext.setResult(cast(list, value)[0])


def _doCase(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	The case function implements multiple test-action clauses.
		It evaluates a symbol and compares the result against multiple action 
		lists based on the evaluation of that symbol.

		The special symbol *otherwise* is the default case if no other action
		list matches the symbol.

		Example:
			::

				(case aSymbol
					( 1 (print "Result: 1"))
					( 2 (print "Result: 2"))
					(otherwise (print "Result: something else")))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result result of the last executed action list, or NIL if nothing was matched and the *otherwise* symbol is not present.
	"""
	pcontext.assertSymbol(symbol, minLength = 3)

	# Get value
	pcontext, value = pcontext.valueFromArgument(symbol, 1)

	# Iterate through remaining list arguments
	e:SSymbol
	for e in symbol[2:]:
		pcontext.assertSymbol(e, 2)

		# if it is the "orherwise" symbol (!) then execute that one and return
		if e[0].type == SType.tSymbol and e[0].value == 'otherwise':
			return pcontext._executeExpression(e[1], symbol)

		# Get match symbol
		m = pcontext._executeExpression(e[0], symbol)

		# match is string, number, or boolean
		if m.result.type in [ SType.tString, SType.tNumber, SType.tBool] and m.result.value == value:
			return pcontext._executeExpression(e[1], symbol)
		
	return pcontext.setResult(SSymbol()) # NIL


def _doCdr(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	The CDR of a list is the rest of the list without the first symbol. 
		The original list is not changed.

		Example:
			::

				(cdr (1 2 3)) -> (2 3)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is the rest of the list without the first symbol or NIL.
	"""
	pcontext.assertSymbol(symbol, 2)

	pcontext, result = pcontext.resultFromArgument(symbol, 1, (SType.tListQuote, SType.tList, SType.tNIL))
	if result.length == 0 or result.type == SType.tNIL:
		return pcontext.setResult(SSymbol())
	return pcontext.setResult(SSymbol(lst = cast(list, result.value)[1:]))


def _doConcatenate(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Concat symbols together.

		Though this function is mainly for concatenation strings, all types are supported.
		No space is added between the symbols, but the special symbol *sp* can be used to add a space character.

		Example:
			::

				(. "Hello" sp "world")

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is a new string.
	"""
	pcontext.assertSymbol(symbol, minLength = 2)
	return pcontext.setResult(pcontext._joinExpression(symbol[1:], sep = '').result)


def _doCons(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	The *cons* function creates a new list out of a first element (the *car*) and a
		second element (the *cdr*).

		It can be seens as the reverse of a *car* and a *cdr* function calls.

		Example:
			::

				(cons "a" "b") -> ("a" "b")
				(cons "a" ("b" "c")) -> ("a" "b" "c")
				(cons ("a" "b") "c") -> (("a" "b") "c")

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is a new list.
	"""
	pcontext.assertSymbol(symbol, 3)

	# get first symbol
	pcontext, _first = pcontext.valueFromArgument(symbol, 1)

	# get second symbol
	pcontext, _second = pcontext.valueFromArgument(symbol, 2)

	if _second.type in [SType.tList, SType.tListQuote]:
		pcontext.result = deepcopy(_second)
	elif _second.type == SType.tNIL:
		pcontext.result = SSymbol(lst = [])
	else:
		pcontext.result = SSymbol(lst = [ deepcopy(_second) ])
	cast(list, pcontext.result.value).insert(0, deepcopy(_first))
	return pcontext


def _doDatetime(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	This function returns the the current time (UTC-based) in the specified format.

		This function has an optional format paramater that is the same as the 
		Python's strftime* function. 
		The default is *%Y%m%dT%H%M%S.%f*, which evaluates to an ISO8901 timestamp.

		Example:
			::

				(datetime) -> 20220107T221625.771604
				(datetime "%H:%M") -> 13:31

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is a date time string.
	"""
	pcontext.assertSymbol(symbol, maxLength = 2)
	_format = '%Y%m%dT%H%M%S.%f'
	if symbol.length == 2:
		pcontext, _format = pcontext.valueFromArgument(symbol, 1, SType.tString)
	return pcontext.setResult(SSymbol(string = datetime.datetime.utcnow().strftime(_format)))


def _doDefun(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	This function defines a new function.

		A new function may have zero, one or multiple arguments. The result of the
		last executed expression in the function determines the 
		function's result.

	Example:
		::

			(defun hello (name) (print (. "hello" sp name))) ;; define the function
			(hello "Arthur") ;; call the function

	Args:
		pcontext: Current `PContext` for the script.
		symbol: The symbol to execute. The function definition.

	Return:
		The updated `PContext` object.

	Raises:
		`PInvalidArgumentError`: In case of a wrong definition.
	"""
	pcontext.assertSymbol(symbol, 4)

	# function name
	if symbol[1].type != SType.tSymbol:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun requires symbol name, got type: {symbol[1].type}'))
	_name = symbol[1].value
	
	# arguments
	if symbol[2].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun requires symbol argument list, got type: {symbol[2].type}'))
	_args = cast(PSymbolList, symbol[2].value)

	_argNames:list[str] = []
	for a in cast(List[SSymbol], _args):		# type:ignore[union-attr]
		if a.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun arguments must be symbol, got: {a}'))
		_argNames.append(a.value) 	# type:ignore[arg-type]
	
	# code
	if symbol[3].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun requires code list, got: {symbol[3].type}'))
	_code = symbol[3]
	pcontext.functions[str(_name)] = ( _argNames, _code )
	return pcontext


def _doError(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	End script execution with an error. The optional argument will be 
		assigned as the result of the script (pcontext.result).

		Example:
			::

				(quit-with-error "Some error")

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.

		Raises:
			`PInvalidArgumentError`: In case of an invalid argument.
			`PQuitWithError`: In case the function quits successfully with an error. This is expected.
	"""
	if symbol.type != SType.tList or symbol.length > 2:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong format for quitwitherror: {symbol}'))
	if symbol.length == 2:
		pcontext = pcontext._executeExpression(symbol[1], symbol)
		raise PQuitWithError(pcontext.setError(PError.quitWithError, str(pcontext.result.value)))
	raise PQuitWithError(pcontext.setError(PError.quitWithError, ''))


def _doEval(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Evaluate a list as a function call.

		Example:
			::

				(eval '(print "Hello, world"))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.
	"""
	pcontext.assertSymbol(symbol, 2)

	# get and evaluate symbol or list
	pcontext, result = pcontext.resultFromArgument(symbol, 1, (SType.tListQuote, SType.tSymbolQuote))
	_s = deepcopy(result)
	_s.type = _s.type.unquote()
	return pcontext._executeExpression(_s, symbol)


def _doEvaluateInline(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Enable or disable inline string evaluation.

		Example:
			::

				(evaluate-line false) ;; Disable inline evaluation

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.
	"""
	pcontext.assertSymbol(symbol, 2)

	# value
	pcontext, value = pcontext.valueFromArgument(symbol, 1, SType.tBool)
	pcontext.evaluateInline = cast(bool, value)
	return pcontext


def _doGetJSONAttribute(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Retrieve an attribute from a JSON structure via a key path. 
	
		Example:
			::

				(get-json-attribute { "a" : { "b" : "c" }} "a/b" ) -> "c"

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
	"""

	def _toSymbol(value:Any) -> SSymbol:
		if isinstance(value, str):
			return SSymbol(string = value)
		elif isinstance(value, (int, float)):
			return SSymbol(number = Decimal(value))
		elif isinstance(value, dict):
			return SSymbol(jsn = value)
		elif isinstance(value, bool):
			return SSymbol(boolean = value)
		elif isinstance(value, list):
			return SSymbol(lst = [ _toSymbol(l) for l in value])
		return SSymbol() # nil

	pcontext.assertSymbol(symbol, 3)

	# json
	pcontext, _json = pcontext.valueFromArgument(symbol, 1, SType.tJson)

	# key path
	pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)

	# value
	if (_value := findXPath(_json, _key)) is None:
		return pcontext.setResult(SSymbol())
	return pcontext.setResult(_toSymbol(_value))


def _doHasJSONAttribute(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Check whether an attribute exists in a JSON structure for a key path.
	
		Example:
			::

				(has-json-attribute { "a" : { "b" : "c" }} "a/b" ) -> true

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
	"""
	pcontext.assertSymbol(symbol, 3)

	# json
	pcontext, _json = pcontext.valueFromArgument(symbol, 1, SType.tJson)

	# key path
	pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)
	_key = _key.strip()

	return pcontext.setResult(SSymbol(boolean = findXPath(_json, _key) is not None))


def _doIf(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Check whether an expression evaluates to *true* and then execute
		a symbol or list. Otherwise a second, optional symbol or list is executed. 
	
		Example:
			::

				(if (< 1 2)
					(print "true")
					(print "false")	)

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result of the last operation in the executed list or symbol.
	"""
	pcontext.assertSymbol(symbol, minLength = 3)

	pcontext, _e = pcontext.valueFromArgument(symbol, 1, SType.tBool)
	if _e:
		_p = pcontext._executeExpression(symbol[2], symbol)
	elif symbol.length == 4:
		_p = pcontext._executeExpression(symbol[3], symbol)
	else:
		_p = _e
	return _p


def _doIn(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Check whether a symbol is contained in a list, or a string is 
		contained in another string. 
	
		Example:
			::

				(in "Hello" "Hello, World") -> true
				(in a (b c)) -> false

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
	"""
	pcontext.assertSymbol(symbol, 3)

	# Get value
	pcontext, _v = pcontext.resultFromArgument(symbol, 1)
	
	# Get symbol (!) to check
	pcontext, _s = pcontext.resultFromArgument(symbol, 2, (SType.tString, SType.tList, SType.tListQuote))

	# check
	return pcontext.setResult(SSymbol(boolean = _v in _s))


def _doIncDec(pcontext:PContext, symbol:SSymbol, isInc:Optional[bool] = True) -> PContext:
	"""	Increment or decrement a variable by an optional value.
		
		The default is 1.

		Example:
			::

				(setq a 1)
				(inc a 2) -> 3
				(dec a) -> 2

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			isInc: Indicate whether to increment or decrement.

		Return:
			The updated `PContext` object with the function result.
		
		Raises:
			`PInvalidArgumentError`: In case the variable is not defined, or the second argument doesn't evaluate to a number.
	"""
	pcontext.assertSymbol(symbol, minLength = 2, maxLength = 3)

	# Get variable and value first (symbol!)
	variable = symbol[1]
	if variable.type == SType.tList:
		pcontext, variable = pcontext.resultFromArgument(symbol, 1)

	if variable.type not in [SType.tString, SType.tSymbol]:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'variable name must be a string: {variable}'))
	if variable.value not in pcontext.variables:
		raise PInvalidArgumentError(pcontext.setError(PError.undefined, f'undefined variable: {variable}'))
	if (value := pcontext.variables[variable.value]).type != SType.tNumber:
		raise PInvalidArgumentError(pcontext.setError(PError.notANumber, f'variable value must be a number for inc/dec: {value}'))
	
	# Get increment/decrement value
	pcontext, _idValue = pcontext.valueFromArgument(symbol, 2, SType.tNumber) if symbol.length == 3 else (pcontext, Decimal(1.0))
	idValue = cast(Decimal, _idValue)
	
	# Increment / decrement and Re-assign variable
	value.value = (cast(Decimal, value.value) + idValue) if isInc else (cast(Decimal, value.value) - idValue)
	pcontext.variables[variable.value] = value
	return pcontext.setResult(deepcopy(value))


def _doIndexOf(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Determine the index of a symbol or string in a list or string.
		
		If the second argument is a string, then the first argument must also be a string.

		Example:
			::

				(index-of 1 '(1 2 3)) -> 0
				(index-of "a" '("b", "c", "d")) -> nil
				(index-of "b" "abc") -> 1

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
		
		Raises:
			`PInvalidTypeError`: In case the first argument is not a string if the second argument is a string.
	"""
	pcontext.assertSymbol(symbol, 3)

	# value
	pcontext, value = pcontext.resultFromArgument(symbol, 1)

	# list or string
	pcontext, lst = pcontext.resultFromArgument(symbol, 2, (SType.tList, SType.tListQuote, SType.tString))

	if lst.type == SType.tString and value.type !=SType.tString:
		raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'index-of: first argument must be a string if second argument is a string'))
	try:
		return pcontext.setResult(SSymbol(number = Decimal(operator.indexOf(lst.raw(), value.value))))
	except ValueError as e:
		return pcontext.setResult(SSymbol())


def _doIsDefined(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Check whether a symbol, function, or variable is defined.
	
		Example:
			::

				(setq a 1)
				(is-defined a) -> true
				(is-defined b) -> false

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
	"""
	pcontext.assertSymbol(symbol, 2)
	
	# symbol name
	pcontext, name = pcontext.valueFromArgument(symbol, 1, SType.tString)
	return pcontext.setResult(SSymbol(boolean = name in pcontext.variables or
												name in pcontext.functions or
												name in pcontext.symbols or
												name in pcontext.meta or 
												name in pcontext.environment))


def _doJsonify(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Escape a string for use in a JSON structure. Newlines and quotes are escaped.

		Example:
			::

				(jsonify "Hello,
				World") -> "Hello\\nWorld"

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Returns:
			The updated `PContext` object with the escaped JSON string.
	"""
	pcontext.assertSymbol(symbol, 2)
	pcontext, _s = pcontext.valueFromArgument(symbol, 1, SType.tString)
	return pcontext.setResult(SSymbol(string = _s.replace('\n', '\\n').replace('"', '\\"')))


def _doJsonToString(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Convert a JSON structure to a string.
	
		Example:
			::

				(json-to-string { "a": 1 }) -> "{ \"a\": 1 }"

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, 2)
	pcontext, _j = pcontext.valueFromArgument(symbol, 1, SType.tJson)
	try:
		_s = json.dumps(cast(str, _j))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid JSON: {str(e)}'))
	return pcontext.setResult(SSymbol(string = _s))


def _doLambda(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Define a nameless lambda function.
	
		Example:
			::

				((lambda (x) (* x x)) 5) -> 25
				(setq y (lambda (x) (* x x)))
				((y) 5) -> 25

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the lambda result.
		
		Raises:
			`PInvalidArgumentError`: in case one of the arguments has the wrong type.
	"""
	pcontext.assertSymbol(symbol, 3)

	# arguments
	if symbol[1].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'lambda requires symbol argument list, got: {symbol[1].type}'))
	_args = cast(PSymbolList, symbol[1].value)

	_argNames:list[str] = []
	for a in cast(List[SSymbol], _args):		# type:ignore[union-attr]
		if a.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'lambda arguments must be symbol, got: {a}'))
		_argNames.append(a.value) 	# type:ignore[arg-type]
	
	# code
	if symbol[2].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'lambda requires code list, got: {symbol[2].type}'))
	return pcontext.setResult(SSymbol(lmbda = ( _argNames, symbol[2])))


def _doLength(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Get the length of a symbol or list.
	
		Example:
			::

				(length "Hello, World") -> 11
				(length (a b)) -> 2

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, 2)
	pcontext, result = pcontext.resultFromArgument(symbol, 1, (SType.tString, SType.tList, SType.tListQuote))
	return pcontext.setResult(SSymbol(number = Decimal(result.length)))


def _doLet(pcontext:PContext, symbol:SSymbol, sequential:bool = True) -> PContext:
	""" Perform multipe assignments in sequence (let* function).

		Note:
			Currently, assignment in parallel (let function) is not supported.
	
		Example:
			::

				(let* (a 1) 
					  (a (+ a 1))) -> a = 2

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			sequential: Indicator whether sequential (True) or parallel assignments shall be performed.

		Return:
			The updated `PContext` object with the function result and set variables.
		
		Raises:
			`PInvalidArgumentError`: In case the format of the variable assignment is wrong.
	"""
	pcontext.assertSymbol(symbol, minLength = 2)

	if sequential:
		for symbol in symbol[1:]:
			if symbol.type != SType.tList or symbol.length != 2:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong format for let variable assignment: {symbol}'))

			# get variable name
			if symbol.value[0].type != SType.tSymbol:	# type:ignore[index, union-attr]
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Variable name must be a symbol: {symbol}'))
			variablename = cast(str, symbol.value[0].value)	# type:ignore[index, union-attr]

			# get value and assign variable (symbol!)
			pcontext, result = pcontext.resultFromArgument(cast(SSymbol, symbol.value), 1)
			pcontext.variables[variablename] = result


	# TODO LET in parallel
	return pcontext


def _doList(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Create a list out of the arguments
	
		Example:
			::

				(list 1 2 3) -> (1 2 3)

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, minLength = 2)
	# Let's explain the following:
	# 1) Construct a list from all argument using list comprehension
	#    This is a list of tuples (pcontext, symbol)
	# 2) use zip() to sort this into two sets: a) pcontexts and b) symbols
	# 3) Convert the zip() result into a list.
	# 4) Get the second set (symbols) and convert it into a list as well
	# 5) Create a new list symbol
	return pcontext.setResult(SSymbol(lst = list(list(
												zip(*[ pcontext.resultFromArgument(symbol, i) 
													   for i in range(1, symbol.length) ])
											)[1])
							))


def _doLog(pcontext:PContext, symbol:SSymbol, isError:Optional[bool] = False, exception:Optional[Exception] = None) -> PContext:
	"""	Print a message to the debug or to the error log. 
		Either the internal or a provided log function is used.

		Example:
			::

				(log "Hello, World")

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			isError: Indicate whether this message will be logged as an error or a normal log message.
			exception: An optional exception

		Return:
			The updated `PContext` object with the function result.
	"""
	p = pcontext._joinExpression(symbol[1:])
	if isError:
		if pcontext.logErrorFunc:
			pcontext.logErrorFunc(pcontext, p.result.value, exception)	# type:ignore[arg-type]
	else:
		if pcontext.logFunc:
			pcontext.logFunc(pcontext, p.result.value)					# type:ignore[arg-type]
	return pcontext


def _doLowerUpper(pcontext:PContext, symbol:SSymbol, toLower:bool = True) -> PContext:
	""" Convert a string to upper or lower case.
	
		Example:
			::

				(upper "Hello, World") -> "HELLO, WORLD"
				(lower "Hello, World") -> "hello, world

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			toLower: Indicator whether the conversion shall be to lower or upper case.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, 2)

	# value
	pcontext, value = pcontext.valueFromArgument(symbol, 1, SType.tString)
	pcontext.result.value = value.lower() if toLower else value.upper()	# type:ignore[union-attr]
	return pcontext


def _doMatch(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Apply a regular expression to a string and return whether it matches.
	
		Note:
			The match function must be supplied to the interpreter.

		Example:
			::

				(match "aa" "a?") -> true
				(match "aa" "b*") -> false

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""

	pcontext.assertSymbol(symbol, 3)

	# value
	pcontext, _in = pcontext.valueFromArgument(symbol, 1, SType.tString)
	
	# match expression
	pcontext, _match = pcontext.valueFromArgument(symbol, 2, SType.tString)

	# match
	return pcontext.setResult(SSymbol(boolean = pcontext.matchFunc(pcontext, _in, _match)))


def _doNot(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Boolean *not* operation.
	
		Example:
			::

				(not tru) -> false

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, maxLength = 2)
	pcontext, _v = pcontext.valueFromArgument(symbol, 1, (SType.tBool, SType.tNIL))
	return pcontext.setResult(SSymbol(boolean = not _v))


def _doNth(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Get the nth element from a list, or the nth character from a string.
		The index is 0-based.
	
		Example:
			::

				(nth 2 '(1 2 3)) -> 3
				(nth 2 "Hello, World") -> "l"

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, 3)

	# get index
	pcontext, _idx = pcontext.valueFromArgument(symbol, 1, SType.tNumber)

	# get list or string as SSymbol
	pcontext, _value = pcontext.resultFromArgument(symbol, 2, (SType.tString, SType.tList, SType.tListQuote))
	
	# Get nth element
	if _idx < 0 or _idx >= _value.length:
		pcontext.result = SSymbol()
	else:
		pcontext.result = _value[int(_idx)]
	return pcontext


def _doOperation(pcontext:PContext, symbol:SSymbol, op:Callable, tp:SType) -> PContext:
	"""	Process various boolean and mathematical operations.

		The supported operations are:

		- "<": smaller
		- "<=": smaller or equal
		- ">": greater
		- ">=": greater or equal
		- "==": equal
		- "!=": unequal
		- "or": boolean or
		- "|": boolean or
		- "and": boolean and
		- "&": boolean and
		- "!": boolean not
		- "+": Addition
		- "-": Substraction
		- "*": Multiplication 
		- "/": Division
		- "//": Division, rounding down and returning an integer number
		- "**": Power 
		- "%": Modulo

		The mathematical operations may have more then two arguments.

		Example:
			::

				(+ 1 2) -> 3
				(+ 1 2 3) -> 6
				(< 1 2) -> true

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.
			op: The operation to use.
			tp: The expected result's data type.

		Return:
			The updated `PContext` object with the operation result.
		
		Raises:
			`PDivisionByZeroError`: In case a division by 0 happens.
			`PInvalidTypeError`: In case one or more invalid types are provided for the operation.

	"""
	pcontext.assertSymbol(symbol, minLength = 2)
	r1 = pcontext._executeExpression(symbol[1], symbol).result

	for i in range(2, symbol.length):
		try:
			r1.value = op(r1.value, pcontext._executeExpression(symbol[i], symbol).result.value)
		except ZeroDivisionError as e:
			raise PDivisionByZeroError(pcontext.setError(PError.divisionByZero, str(e)))
		except TypeError as e:
			raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'invalid types in expression: {str(e)}'))
		except InvalidOperation as e:
			if DivisionUndefined in e.args:
				raise PDivisionByZeroError(pcontext.setError(PError.divisionByZero, str(e)))
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid arguments in expression: {str(e)}'))

	r1.type = tp
	return pcontext.setResult(r1)


def _doPrint(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Print the arguments to the console
	
		Example:
			::

				(print "Hello, World")

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""

	if symbol.type != SType.tList or symbol.length == 1:
		pcontext.printFunc(pcontext, '')
		return pcontext.setResult(SSymbol())
	pcontext.printFunc(pcontext, str(pcontext._joinExpression(symbol[1:]).result.value))
	return pcontext.setResult(SSymbol())


def _doProgn(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Evaluate one or multiple symbols in a list. This is the explicite function that many
		evaluations automatically do
	
		Example:
			::

				(progn (print "Hello, World"))

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
		
		Raises:
			*PInvalidArgumentError`: In case of an invalid argument or parameter.
	"""

	# print(f'progn> {symbol} {symbol.len()}')
	for i in range(1, symbol.length):	# type:ignore [arg-type]
		pcontext, result = pcontext.resultFromArgument(symbol, i)
		if pcontext.state == PState.returning:
			return pcontext

		# if the first element is a lambda then execute it
		if i == 1 and result is not None and result.type == SType.tLambda:
			# Construct lambda call
			_name = f'lambda_{"".join(random.choices(string.ascii_letters + string.digits, k = 10))}'
			_call = cast(Tuple[List[str], SSymbol], result.value)
			_arguments = _call[0]
			_code = _call[1]
			
			# Check arguments
			if len(_arguments) != symbol.length - 2:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Number of arguments mismatch. Expected: {len(_arguments)}, got: {symbol.length - 2}'))
			
			# Temporarily add to functions
			pcontext.functions[_name] = (_arguments, _code)

			# Execute as function
			pcontext = pcontext._executeFunction(SSymbol(lst = cast(List[SSymbol], symbol.value[1:])), _name)		# type:ignore[index]

			# Remove temp function
			del pcontext.functions[_name]

			# Return whatever is the result. Don't execute progn any further
			return pcontext

	return pcontext


def _doQuit(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	End script execution. The optional argument will be assigned as the result of
		the script in the `PContext.result` attribute.

		Example:
			::

				(quit "some result") -> "some result"

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			This function doesn't return anything, it always raises an exception.
		
		Raises:
			`PQuitRegular`: Always raises this exception.
	"""
	pcontext.assertSymbol(symbol, maxLength = 2)

	if symbol.length == 2:
		pcontext = pcontext.getArgument(symbol, 1)
		pcontext.state = PState.terminatedWithResult
	else:
		pcontext.state = PState.terminated
		pcontext.result = SSymbol()
	raise PQuitRegular(pcontext)


def _doQuote(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Convert a symbol into a quotable version.

		Example:
			::

				(quote (a b c)) -> '(a b c)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, 2)
	pcontext, result = pcontext.resultFromArgument(symbol, 1, (SType.tList, SType.tSymbol), doEval = False)
	result = deepcopy(result)
	# Change type to quoted version
	pcontext.result.type = {	SType.tList: SType.tListQuote,
								SType.tSymbol: SType.tSymbolQuote }[result.type]
	return pcontext


def _doRandom(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Generate a random float number in the given range. The default for the
		range is [0.0, 1.0]. If one argument is given then this indicates a range
		of [0.0, arg].

		Example:
			::

				(random 1) -> 0.3
				(random 2 3) -> 2.87

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, maxLength = 3)
	start = Decimal(0.0)
	end = Decimal(1.0)
	if symbol.length == 2:
		pcontext, end = pcontext.valueFromArgument(symbol, 1, SType.tNumber)	# type:ignore [assignment]
	elif symbol.length == 3:
		pcontext, start = pcontext.valueFromArgument(symbol, 1, SType.tNumber)	# type:ignore [assignment]
		pcontext, end = pcontext.valueFromArgument(symbol, 2, SType.tNumber)			# type:ignore [assignment]
	return pcontext.setResult(SSymbol(number = Decimal(random.uniform(float(start), float(end)))))


def _doReturn(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Return from a function call or break from *while* loop.

		While returning it is possible to pass a return value.

		Example:
			::

				(return "some result") -> "some result"

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, maxLength = 2)
	if symbol.length == 2:
		# Evaluate the first symbol
		pcontext = pcontext.getArgument(symbol, 1)
	else:
		# result is nil
		pcontext.result = SSymbol()
	pcontext.state = PState.returning
	return pcontext


def _doRound(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Return a number rounded to optional *ndigits* precision after the decimal point. 
	
		If *ndigits*, the second parameter, is omitted, it returns the nearest integer.

		Example:
			::

				(round 1.6) -> 2
				(round 1.678 2) -> 1.67

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.
				
		Return:
			The updated `PContext` object with the function result.

		Raises:
			`PInvalidArgumentError`: In case of an invalid argument.
	"""
	pcontext.assertSymbol(symbol, minLength = 2, maxLength = 3)
	
	# Get number
	_number:Decimal
	pcontext, _number = pcontext.valueFromArgument(symbol, 1, SType.tNumber)
	
	# Get precision
	_precision:int = 0
	if symbol.length == 3:
		pcontext, _precision = pcontext.valueFromArgument(symbol, 2, SType.tNumber)
	
	# Round
	try:
		return pcontext.setResult(SSymbol(number = round(_number, int(_precision))))
	except (InvalidOperation, ValueError) as e:
		pcontext.setError(PError.invalid, f'Invalid argument: {str(e)}')
		raise PInvalidArgumentError(pcontext)


def _doSetq(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Set a variable. The second symbol is automatically quoted, so it is taken as the
		variable name.
	
		Example:
			::

				(setq a "Hello, World") -> "Hello, World"

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.
				
		Return:
			The updated `PContext` object with the function result, ie the expression result.
	"""
	pcontext.assertSymbol(symbol, 3)

	# var
	pcontext, _var = pcontext.valueFromArgument(symbol, 1, SType.tSymbol, doEval = False)

	# value
	pcontext, _value = pcontext.resultFromArgument(symbol, 2)
	pcontext.variables[_var] = _value

	return pcontext


def _doSetJSONAttribute(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Set an attribute of a JSON structure via its key path. 

		One may set multiple values at one by providing a list of (key/values).
	
		Example:
			::

				(set-json-attribute { "a" : { "b" : "c" }} "a/b" "d") -> { "a" : { "b" : "d" }
				(set-json-attribute { "a" : { "b" : "c" }} '('("a/b" "d") '("a/c" "e"))) -> { "a" : { "b" : "d", "c" : "e"}

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result, ie a new JSON symbol.
	"""
	pcontext.assertSymbol(symbol, minLength = 3, maxLength = 4)

	# json
	_json:dict
	pcontext, _json = pcontext.valueFromArgument(symbol, 1, SType.tJson)
	_json = deepcopy(_json)

	if symbol.length == 3:
		pcontext, lst = pcontext.resultFromArgument(symbol, 2, (SType.tList, SType.tListQuote))
		for i in range(lst.length):
			_n:list
			pcontext, _result = pcontext.resultFromArgument(lst, i, (SType.tList, SType.tListQuote))
			_n = _result.raw()
			if (_l := len(_n)) != 2:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid number of arguments: {_l} (must be 2)'))
			_key = _n[0]
			_value = _n[1]
			if not setXPath(_json, _key, _value):
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid key for set-json-attribute: {_key}'))

	else:	# length = 4
		# key
		pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)

		# value
		pcontext, _result = pcontext.resultFromArgument(symbol, 3, (SType.tString, SType.tNumber, SType.tBool, SType.tListQuote, SType.tList, SType.tJson))
		_value = _result.raw()	
		if not setXPath(_json, _key, _value):
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, 'invalid key for set-json-attribute: {key}'))

	return pcontext.setResult(SSymbol(jsn = _json))


def _doSleep(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Sleep for a number of seconds. 
	
		This function can be interrupted when the script's state is set to any other state than *running*.

		Example:
			::

					(sleep 2.5)

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
		
		Raises:
			`PNotANumberError`: In case there is a problem with the number conversion.
			`PInterruptedError`: In case the sleep was interrupted.
	"""
	pcontext.assertSymbol(symbol, 2)
	try:
		pcontext, _value = pcontext.valueFromArgument(symbol, 1, SType.tNumber)
		toTs = time.time() + float(_value)	# type:ignore [arg-type]
		while pcontext.state == PState.running and toTs > time.time():
			pcontext._checkTimeout()
			time.sleep(0.01)
	except ValueError as e:
		raise PNotANumberError(pcontext.setError(PError.notANumber, f'Not a number: {e}'))
	except KeyboardInterrupt:
		raise PInterruptedError(pcontext.setError(PError.canceled, 'Keyboard interrupt'))
	return pcontext


def _doSlice(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Return a slice of a string or list.
		
		The behaviour is the same as slicing in Python, except that both start and end
		must be provided.

		The first argument is the beginning of the slice, the second is the end (exlcuding) of the slice.
		The fourth argument is the list or string to slice.

		Example:
			::

				(slice 1 2 '(1 2 3)) -> (2)
				(slice 0 -1 "abcde") -> "abcd"
				(slice 99 100 '(1 2 3)) -> ()

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	pcontext.assertSymbol(symbol, 4)

	# start
	pcontext, start = pcontext.valueFromArgument(symbol, 1, SType.tNumber)

	# end
	pcontext, end = pcontext.valueFromArgument(symbol, 2, SType.tNumber)

	# list or string
	pcontext, lst = pcontext.resultFromArgument(symbol, 3, (SType.tList, SType.tListQuote, SType.tString))
	
	if lst.type == SType.tString:
		return pcontext.setResult(SSymbol(string = lst[int(start):int(end)]))
	else:	# list
		return pcontext.setResult(SSymbol(lst = lst[int(start):int(end)]))


def _doStringToJson(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Convert a string that contains a JSON structure to a JSON dictionary. 
	
		Example:
			::

					(string-to-json "{ \"a\": \"b\"")

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
		
		Raises:
			`PInvalidArgumentError`: In case the JSON input contains an error.
	"""
	pcontext.assertSymbol(symbol, 2)
	_s = (pcontext := pcontext.getArgument(symbol, 1, SType.tString)).result
	try:
		return pcontext.setResult(SSymbol(jsnString = cast(str, _s.value)))	# implicite conversion
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid JSON: {str(e)}'))


def _doToNumber(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Convert a string to a number. 
	
		Example:
			::

					(string-to-number "1") -> 1

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
		
		Raises:
			`PInvalidArgumentError`: In case the input cannot be converted.
	"""
	pcontext.assertSymbol(symbol, 2)

	# string
	pcontext, _string = pcontext.valueFromArgument(symbol, 1, SType.tString)
	try:
		pcontext = pcontext.setResult(SSymbol(number = Decimal(_string)))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'input for conversion must be a convertable number, is: {_string}'))
	return pcontext


def _doToString(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Convert any symbol to its string representation. 
	
		Example:
			::

					(to-string aSymbol) -> "[1, 2, 3]"

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
		
		Raises:
			`PInvalidArgumentError`: In case the input cannot be converted.
	"""

	pcontext.assertSymbol(symbol, 2)

	# anything
	pcontext, _string = pcontext.valueFromArgument(symbol, 1)
	try:
		pcontext = pcontext.setResult(SSymbol(string = str(_string)))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'input for conversion must be a convertable string, is: {_string}'))
	return pcontext


def _doURLEncode(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	URL-Encode a string.

		Example:
			::

				(url-encode "Hello, World") -> "Hello+World"

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Returns:
			The updated `PContext` object with the operation result.
	"""
	pcontext.assertSymbol(symbol, 2)

	# arg
	pcontext, _url = pcontext.valueFromArgument(symbol, 1, SType.tString)
	return pcontext.setResult(SSymbol(string = urllib.parse.quote_plus(_url)))


def _doWhile(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Provide a *while* loop functionality. 
	
		Example:
			::

				(setq i 0)
				(while (< i 10)
					((print i)
						(inc i)))

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result, ie the result of the evaluated expression or a return statement in the loop.
	"""
	pcontext.assertSymbol(symbol, 3)
	_lastResult = SSymbol()
	while True:
		
		# evaluate while expression
		pcontext, _e = pcontext.valueFromArgument(symbol, 1, SType.tBool)
		if not _e:
			break

		# Otherwise execute the loop
		pcontext, _lastResult = pcontext.resultFromArgument(symbol, 2)
		
		# Handle return gracefully
		if pcontext.state == PState.returning:
			pcontext.state = PState.running
			return pcontext

	return pcontext.setResult(_lastResult)


_builtinCommands:PSymbolDict = {
	'<':				lambda p, a : _doOperation(p, a, operator.lt, SType.tBool),
	'<=':				lambda p, a : _doOperation(p, a, operator.le, SType.tBool),
	'>':				lambda p, a : _doOperation(p, a, operator.gt, SType.tBool),
	'>=':				lambda p, a : _doOperation(p, a, operator.ge, SType.tBool),
	'==':				lambda p, a : _doOperation(p, a, operator.eq, SType.tBool),
	'!=':				lambda p, a : _doOperation(p, a, operator.ne, SType.tBool),
	'<>':				lambda p, a : _doOperation(p, a, operator.ne, SType.tBool),
	'or':				lambda p, a : _doOperation(p, a, operator.or_,  SType.tBool),
	'|':				lambda p, a : _doOperation(p, a, operator.or_,  SType.tBool),
	'and':				lambda p, a : _doOperation(p, a, operator.and_, SType.tBool),
	'&':				lambda p, a : _doOperation(p, a, operator.and_, SType.tBool),
	'!':				_doNot,
	'not':				_doNot,
	'in':				_doIn,
	'.':				_doConcatenate,
	'+':				lambda p, a : _doOperation(p, a, operator.add, SType.tNumber),
	'-':				lambda p, a : _doOperation(p, a, operator.sub, SType.tNumber),
	'*':				lambda p, a : _doOperation(p, a, operator.mul, SType.tNumber),
	'/':				lambda p, a : _doOperation(p, a, operator.truediv, SType.tNumber),
	'**':				lambda p, a : _doOperation(p, a, operator.pow, SType.tNumber),
	'%':				lambda p, a : _doOperation(p, a, operator.mod, SType.tNumber),

	'argv':					_doArgv,
	'assert':				_doAssert,
	'base64-encode':		_doB64Encode,
	'car':					_doCar,
	'case':					_doCase,
	'cdr': 					_doCdr,
	'cons':					_doCons,
	'datetime':				_doDatetime,
	'dec':					lambda p, a: _doIncDec(p, a, False),
	'defun':				_doDefun,
	'eval':					_doEval,
	'evaluate-inline':		_doEvaluateInline,
	'false':				lambda p, a: _doBoolean(p, a, False),
	'get-json-attribute':	_doGetJSONAttribute,
	'has-json-attribute':	_doHasJSONAttribute,
	'if':					_doIf,
	'inc':					lambda p, a: _doIncDec(p, a, True),
	'index-of':				_doIndexOf,
	'is-defined':			_doIsDefined,
	'json-to-string':		_doJsonToString,
	'jsonify':				_doJsonify,
	'lambda':				_doLambda,
	'length':				_doLength,
	'let*':					lambda p, a: _doLet(p, a),
	'list':					_doList,
	'log':					_doLog,
	'lower':				lambda p, a: _doLowerUpper(p, a, True),
	'log-error':			lambda p, a : _doLog(p, a, isError = True),
	'match':				_doMatch,
	'nth':					_doNth,
	'print': 				_doPrint,
	'progn':				_doProgn,
	'quit':					_doQuit,
	'quit-with-error':		_doError,
	'quote':				_doQuote,
	'random':				_doRandom,
	'return':				_doReturn,
	'round':				_doRound,
	'set-json-attribute':	_doSetJSONAttribute,
	'setq':					_doSetq,
	'sleep':				_doSleep,
	'slice':				_doSlice,
	'string-to-json':		_doStringToJson,
	'to-number':			_doToNumber,
	'to-string':			_doToString,
	'true':					lambda p, a: _doBoolean(p, a, True),
	'upper':				lambda p, a: _doLowerUpper(p, a, False),
	'url-encode':			_doURLEncode,
	'while':				_doWhile,

	# characters
	'nl':				lambda p, a: p.setResult(SSymbol(string = '\n')),
	'sp':				lambda p, a: p.setResult(SSymbol(string = ' ')),

	# Variables
	
	# argc
}
""" Dictionary to map the functions to Python functions. """
