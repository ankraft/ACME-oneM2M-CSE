#
#	Interpreter.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Implementation of a simple s-expression-based command processor.
#
"""	The interpreter module implements an extensible lisp-based scripting runtime.

	See:
		`PContext` for the main class to run a script.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, cast, Tuple, cast, Callable

import re, random, json, operator, time, string, base64, urllib.parse
from datetime import timezone, datetime
from decimal import Decimal, DivisionUndefined, InvalidOperation
from copy import deepcopy

from ..TextTools import removeCommentsFromJSON, findXPath, setXPath

from .Types import SSymbol, SBooleanSymbol, SNumberSymbol, SStringSymbol, SSymbolSymbol, \
	SListSymbol, SListQuoteSymbol, SLambdaSymbol, SJsonSymbol, SNilSymbol, STSymbol, \
	SSymbolsList, PState, SType, PError, FunctionDefinition, PSymbolDict
from .Exceptions import PAssertionFailed, PTimeoutError, PInvalidArgumentError, PUndefinedError, \
	PReturnFrom, PQuitRegular, PQuitWithError, PInvalidTypeError, PDivisionByZeroError, \
	PNotANumberError, PInterruptedError
from .Exceptions import PException, PInvalidArgumentError, PTimeoutError, PUndefinedError
from .SExprParser import SExprParser

if TYPE_CHECKING:
	from .PContext import PContext

# TODO More functions: set-nth, count-of, remove-nth, Insert-nth, floors, let in parallel, etc.

# TODO Allow progn without a first parameter . This should reduce the construction efforts for executing list

_onErrorFunction = 'on-error'
"""	Name of the on-error function that is executed in case of an error """


###############################################################################


def parseScript(pcontext:PContext) -> bool:
	"""	Parse and validate a script in a context.

		Args:	
			pcontext: The `PContext` object that contains the script to parse.

		Return:
			Boolean indicating the success.
	"""
	# Validate script first.
	parser = SExprParser()
	try:
		pcontext.ast = parser.ast(removeCommentsFromJSON(pcontext.script), allowBrackets = pcontext.allowBrackets)
	except ValueError as e:
		pcontext.setError(PError.invalid, str(e), expression = parser.errorExpression)
		return False
	return True


def runScript(pcontext:PContext,
			  arguments:list[str] = [], 
			  isSubCall:Optional[bool] = False) -> PContext:
	"""	Run the script in the `PContext` instance.

		Args:
			arguments: Optional list of string arguments to the script. They are available to the script via the *argv* function.
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
				_s = SListSymbol()
				pcontext = executeFunction(pcontext, 
							   			   _s.setLst([	SSymbolSymbol(_onErrorFunction, _s), 
														SStringSymbol(pcontext.error.error.name, _s),
														SStringSymbol(pcontext.error.message, _s)
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

	if not parseScript(pcontext):
		return pcontext
	if not isSubCall:
		pcontext.reset()

	# There is some more functionality offered in form of the "argv" function (direct access to elements),
	# so "argv" couldn't just be a variable.
	pcontext.argv = arguments	
	pcontext.environment['argc'] = SNumberSymbol(Decimal(len(pcontext.argv)))

	# Call Pre-Function
	if pcontext.preFunc:
		if pcontext.preFunc(pcontext) is None:
			pcontext.setError(PError.canceled, 'preFunc canceled', state=PState.canceled)
			_terminating(pcontext)
			return pcontext

	# Start running
	pcontext.state = PState.running
	if pcontext.maxRuntime:	# > 0 or not None: set max runtime
		pcontext._maxRTimestamp = _utcTimestamp() + pcontext.maxRuntime
	if (scriptName := pcontext.scriptName) and not isSubCall:
		if pcontext.verbose:
			pcontext.logFunc(pcontext, f'Running script: {scriptName}, arguments: {arguments}, environment: {pcontext.environment}')
		else:
			pcontext.logFunc(pcontext, f'Running script: {scriptName}, arguments: {arguments}')

	# execute all top level S-expressions
	for symbol in pcontext.ast:
		try:
			executeExpression(pcontext, symbol)
		except PException as e:
			if isSubCall:
				raise e
			pcontext.copyError(e.pcontext)	# Copy error from subcall
			_terminating(e.pcontext)
			return e.pcontext
		except Exception as e:
			if isSubCall:
				raise e
			pcontext.setError(PError.runtime, f'runtime exception: {str(e)}', exception = e)
			_terminating(pcontext)
			return pcontext

	_terminating(pcontext)
	return pcontext


def executeExpression(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Recursively execute a symbol as an expression.

		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the result.
		
		Raises:
			`PUndefinedError`: In case a symbol is undefined.
			`PInvalidArgumentError`: In case an unexpected symbol is encountered.
	"""

	# Check for timeout
	checkScriptTimeout(pcontext)

	# Log current symbol etc
	pcontext.logSymbol(symbol)
	
	# First resolve the S-Expression
	match symbol.type:	# Check for zero-length symbols
		case SType.tString:
			pass
		case SType.tNIL:
			return pcontext.setResult(SNilSymbol(symbol))
		case SType.tT:
			return pcontext.setResult(STSymbol(symbol))
		case _ if not symbol.length:
			return pcontext.setResult(SNilSymbol(symbol))
		
	firstSymbol = symbol[0] if symbol.length and symbol.type == SType.tList else symbol

	match firstSymbol.type:
		case SType.tString:
			return evaluateInlineExpressions(pcontext, firstSymbol)	# Evaluate inline expressions in strings
	
		case SType.tNumber | SType.tBool | SType.tNIL | SType.tT:
			return pcontext.setResult(firstSymbol)	# type:ignore [arg-type]
	
		case SType.tJson:
			return evaluateInlineExpressions(pcontext, symbol) # Evaluate inline expressions in JSON

		case SType.tList:
			if not firstSymbol.length:
				pcontext.result = SNilSymbol(symbol)
				return pcontext
			# implicit progn
			return __doProgn(pcontext, symbol)	#type:ignore[operator]
		
		case SType.tListQuote:
			return _doQuote(pcontext, SListSymbol([ SSymbolSymbol('quote'), SListSymbol(cast(list, firstSymbol.value))], symbol)) 

		case SType.tSymbol:
			_s = cast(str, firstSymbol.value)

			# Execute function, if defined, or try to find the value in variables, environment, etc.
			if (_fn := pcontext.functions.get(_s)) is not None:
				return executeFunction(pcontext, symbol, _s, _fn)
			elif _s in pcontext.currentCall.arguments:
				pcontext.result = deepcopy(pcontext.currentCall.arguments[_s])
				return pcontext
			elif _s in pcontext.variables:
				pcontext.result = deepcopy(pcontext.variables[_s])
				return pcontext
			elif (_cb := pcontext.symbols.get(_s)) is not None:	# type:ignore[arg-type]
				if pcontext.monitorFunc:
					pcontext.monitorFunc(pcontext, firstSymbol)

				# If the callback is actually a symbol and a lambda function, then execute it
				if type(_cb) == SLambdaSymbol:
					return executeSymbolWithArguments(pcontext, _cb, symbol[1:])	

				# Otherwise call the callback function			
				return cast(Callable, _cb)(pcontext, symbol)
			elif _s in pcontext.environment:
				pcontext.result = deepcopy(pcontext.environment[_s])
				return pcontext

			# Try to get the symbol's value from the caller as a last resort
			else:
				if pcontext.fallbackFunc:
					return pcontext.fallbackFunc(pcontext, symbol)
				raise PUndefinedError(pcontext.setError(PError.undefined, f'undefined symbol: {_s}\n{firstSymbol.printHierarchy()}'))

		case SType.tSymbolQuote:
			return _doQuote(pcontext, SListSymbol([ SSymbolSymbol('quote'), SSymbolSymbol(cast(str, firstSymbol.value), symbol)], symbol))	#type:ignore[operator]

		case SType.tLambda:
			return executeFunction(pcontext, symbol, cast(str, firstSymbol.value))
				
		case _:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Unexpected symbol: {firstSymbol.type}\n{firstSymbol.printHierarchy()}'))


def executeSubexpression(pcontext:PContext, expression:str) -> PContext:
	"""	Execute an expression that is contained in a string. This starts a sub-execution of a new script,
		but in the same context.

		Args:
			expression: String with list of symbols to execute.
		
		Return:
			`PContext` object.
		
		Raises:
			`PInvalidArgumentError`: In case of an error.
	"""
	# check if expression is an s-expression. If not, add parentheses to make it one.
	expression = expression.strip()
	if not (expression.startswith('(') and expression.endswith(')')):
		expression = f'({expression})'
		
	# Save current state
	_ast = pcontext.ast
	_script = pcontext.script

	# Assign new expression
	pcontext.script = expression

	# Parse and run the expression in the current context
	if not parseScript(pcontext):
		raise PInvalidArgumentError(pcontext)
	pcontext.result = None
	pcontext.run(arguments=pcontext.argv, isSubCall=True)	# might throw exception

	# Restore old state
	if pcontext.state in (PState.terminated, PState.terminatedWithResult):	# Correct state for subcall
		pcontext.state = PState.running
	pcontext.ast = _ast
	pcontext.script = _script

	return pcontext


def executeFunction(pcontext:PContext, symbol:SSymbol, functionName:str, functionDef:Optional[FunctionDefinition]=None) -> PContext:
	""" Execute a named function or lambda function.

		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The symbol to execute.
			functionName: The name of the function that is executed. In case of a lambda this name is random.
			functionDef: The executable part of a function or lambda function.

		Return:
			The updated `PContext` object with the function result.
	"""
	if not functionDef:
		functionDef = pcontext.functions[functionName]
	_argNames, _code = functionDef # type:ignore[misc]

	# check arguments
	if not (symbol.type == SType.tSymbol and len(_argNames) == 0) and not (symbol.type == SType.tList and len(_argNames) == symbol.length - 1):
	# if symbol.type != SType.tList or len(_argNames) != symbol.length - 1:	# type:ignore
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'number of arguments doesn\'t match for function : {functionName}. Expected: {len(_argNames)}, got: {symbol.length - 1}\n{symbol.printHierarchy()}'))

	# execute and assign arguments
	_args:dict[str, SSymbol] = {}
	if symbol.length > 1:
		for i in range(1, symbol.length):
			_args[_argNames[i-1]] = executeExpression(pcontext, symbol[i]).result	# type:ignore [index]

	# Assign arguments to new scope
	pcontext.pushCall(functionName, _args)

	# execute the code
	executeExpression(pcontext, _code)
	pcontext.popCall()
	return pcontext


def executeSymbolWithArguments(pcontext:PContext, symbol:SSymbol, arguments:SSymbolsList=[]) -> PContext:
	"""	Execute a symbol with a list of arguments. A symbol can be a function,
		a lambda function, or another (quoted) symbol.

		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The symbol/function/lambda to execute.
			arguments: List of arguments to pass to the symbol.

		Return:
			The updated `PContext` object with the function result.
	"""
	# lambda functions are handled differently
	if symbol.type == SType.tLambda:
		pcontext = __doProgn(pcontext, SListSymbol([symbol] + arguments, symbol), doEval=False)	#type:ignore[operator]
	else:
		if symbol.value in pcontext.symbols:
			_symbol = SSymbolSymbol(symbol.value) if symbol.type == SType.tSymbolQuote else symbol	# type:ignore[arg-type]
			pcontext = executeExpression(pcontext, SListSymbol([_symbol] + arguments, symbol))
		else:
			pcontext = executeFunction(pcontext, SListSymbol([symbol] + arguments, symbol), symbol.value)	# type:ignore[arg-type]
	return pcontext



def assertSymbol(pcontext:PContext, symbol:SSymbol, length:int=None, minLength:int=None, maxLength:int=None) -> None:
	"""	Assert that the symbol is a list of symbols, and that the list length is within the given
		arguments: either an exact length, or a minimum lenght and a maximum length. 
		
		All length parameter are optional. If none is given then no length check happens.

		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The `SSymbol` to check. It must be a list.
			length: Optional exact list length to assert.
			minLength: Optional minimum list length to assert.
			maxLength: Optional maximum list length to assert.
		
		Raises:
			`PInvalidArgumentError`: In case any assertion fails.
	"""

	if symbol.type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong expression format for symbol "{symbol[0]}":\n{symbol.printHierarchy()}'))
	if length is not None and symbol.length != length:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong number of arguments for symbol "{symbol[0]}": {symbol.length - 1}. Must be {length - 1} for expression:\n{symbol.printHierarchy()} '))
	if minLength is not None and symbol.length < minLength:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong length for expression - too few arguments for symbol "{symbol[0]}":\n{symbol.printHierarchy()}'))
	if maxLength is not None and symbol.length > maxLength:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong length for expression - too many arguments for symbol "{symbol[0]}" ({symbol.length} > {maxLength}):\n{symbol.printHierarchy()}'))


def getArgument(pcontext:PContext,
				symbol:SSymbol, 
				idx:Optional[int]=None, 
				expectedType:Optional[SType|Tuple[SType, ...]]=None, 
				doEval:Optional[bool]=True,
				optional:Optional[bool]=False) -> PContext:
	"""	Verify that an expression is a list and return an argument symbol,
		while optionally verify the allowed type(s) for that argument.

		If any of these validations fail, an exception is raised.

		This method also assigns a result and error state to *self*.

		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The symbol that contains an expression.
			idx: Optional index if the symbol contains a list of symbols.
			expectedType: one or multiple data types that are allowed for the retrieved argument symbol.
			doEval: Optionally recursively evaluate the symbol.
			optional: Allow the argument to be None.
		
		Return:
			Result `PContext` object with the result, possible changed variable and other states.
		
		Raises:
			`PInvalidArgumentError`: In case of an error.
	"""

	# evaluate symbol
	_symbol = symbol[idx] if idx is not None else symbol

	if doEval:
		pcontext = executeExpression(pcontext, _symbol)
	else:
		pcontext.result = _symbol
	
	# Check result type
	if expectedType is not None:
		if isinstance(expectedType, SType):
			expectedType = ( expectedType, )
		# add NIL if optional
		if optional:
			expectedType = expectedType + ( SType.tNIL, )
		if pcontext.result is not None and pcontext.result.type not in expectedType: 
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'expression:\n{symbol.printHierarchy()}\nInvalid type for argument: {_symbol}, expected type: {expectedType}, is: {pcontext.result.type}'))

	return pcontext


# TODO check whether resultFromArgumnent and valueFromArgument can be merged

def resultFromArgument(pcontext:PContext,
					   symbol:SSymbol, 
					   idx:Optional[int]=None, 
					   expectedType:Optional[SType|Tuple[SType, ...]]=None, 
					   doEval:Optional[bool]=True,
					   optional:Optional[bool]=False) -> Tuple[PContext, SSymbol]:
	"""	Return the `SSymbol` result from an argument symbol.
		
		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The symbol that contains an expression.
			idx: Optional index if the symbol contains a list of symbols.
			expectedType: one or multiple data types that are allowed for the retrieved argument symbol.
			doEval: Optionally recursively evaluate the symbol.
			optional: Allow the argument to be optional.
		
		Return:
			Result tuple of the updated `PContext` object with the result and the symbol.
	"""
	return (p := getArgument(pcontext, symbol, idx, expectedType, doEval, optional), p.result)
	


def valueFromArgument(pcontext:PContext,
					  symbol:SSymbol, 
					  idx:Optional[int]=None, 
					  expectedType:Optional[SType|Tuple[SType, ...]]=None, 
					  doEval:Optional[bool]=True,
					  optional:Optional[bool]=False,
					  default:Optional[Any]=None) -> Tuple[PContext, Any]:
	"""	Return the actual value from an argument symbol.
		
		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbol: The symbol that contains an expression.
			idx: Optional index if the symbol contains a list of symbols.
			expectedType: one or multiple data types that are allowed for the retrieved argument symbol.
			doEval: Optionally recursively evaluate the symbol.
			optional: Allow the argument to be optional.
			default: Optional default value to return if the argument is not found or is None.
		
		Return:
			Result tuple of the updated `PContext` object with the result and the value.
	"""
	if idx < symbol.length:
		p, r = resultFromArgument(pcontext, symbol, idx, expectedType, doEval, optional)
		return (p, r.value)
	elif optional:
		if default is not None:
			pcontext.result = default
			return (pcontext, default)
		return (pcontext, None)
	raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Invalid argument index: {idx} for expression:\n{symbol.printHierarchy()}'))
		

def joinExpression(pcontext:PContext,
				   symbols:SSymbolsList, 
				   parentSymbol:SSymbol, 
				   sep:str=' ') -> PContext:
	"""	Join all symbols in an expression. 

		Args:
			pcontext: The `PContext` object that represents the current script state.
			symbols: A list of symbols to join.
			parentSymbol: The parent symbol that will contain the result.
			sep: An optional separator for each of the stringified symbols.
		
		Return:
			The updated `PContext` object with the function result. The `PContext.result` attribute contains the joint string.

	"""
	strings:list[str] = []
	for i in range(len(symbols)):	
		p = getArgument(pcontext, symbols[i])
		if p.result is None:
			strings.append('nil')
		else:
			strings.append(str(p.result))
			
	pcontext.result = SStringSymbol(sep.join(strings), parentSymbol)
	return pcontext


def evaluateInlineExpressions(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Replace all inline expressions in a string. 
	
		Expressions are replaced recursively.

		Args:
			symbol: The symbol to execute.

		Return:
			`PContext` object that contains as a result the string with all expressions executed.
	"""

	# Return immediately if inline replacements are disabled
	if not pcontext.evaluateInline or symbol.type not in [ SType.tString, SType.tJson ]:
		return pcontext.setResult(symbol)
	
	line = str(symbol) 

	# match macros and escaped macros
	# find matches
	matches = re.findall(pcontext._macroMatch, line)
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
			_x = str(_m[2:-1]).replace('\\"', '"')	# remove '${' and '}' and unescape escaped quotes
			_e = executeSubexpression(pcontext, _x)	# may throw exception
			# replace only the first occurance
			line = line.replace(_m, str(_e.result), 1)
	
	# Replace placeholders for escaped macros
	for _p, _m in _escapedMatches.items():
		line = line.replace(_p, _m[2:], 1)
	if symbol.type == SType.tString:
		return pcontext.setResult(SStringSymbol(line, symbol))
	return pcontext.setResult(SJsonSymbol(jsnString=line, parent=symbol))


def checkScriptTimeout(pcontext:PContext) -> None:
	"""	Check for script timeout.

		Args:
			pcontext: The `PContext` object to check.

		Raises:
			`PTimeoutError`: In case the script timeout is reached.
	"""
	if pcontext._maxRTimestamp is not None and pcontext._maxRTimestamp < _utcTimestamp():
		raise PTimeoutError(pcontext.setError(PError.timeout, f'Script timeout ({pcontext.maxRuntime} s)'))


################################################################################
#
#	Utilities
#

def _utcNow() -> datetime:
	"""	Return the current time, but relative to UTC.

		Return:
			Datetime UTC-based timestamp
	"""
	return datetime.now(tz = timezone.utc)


def _utcTimestamp() -> float:
	"""	Return the current time's timestamp, but relative to UTC.

		Return:
			Float UTC-based timestamp
	"""
	return _utcNow().timestamp()


################################################################################
#
#	Built-in functions
#


def _doAll(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Return *True* if all of the arguments are *True*. The arguments can be a list of symbols.
		The type of all arguments must be *Bool*.

		Example:
			::

				(any true false) -> false
				(any true true) -> true
				(any '(false false)) -> false
				(any '(true true)) -> true

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is either *True* or *False*.
	"""

	assertSymbol(pcontext, symbol, minLength=2)

	# If we have only one argument, then this must be a list or a single boolean value
	_values:SSymbolsList = []
	if len(symbol) == 2:
		pcontext, _v = resultFromArgument(pcontext, symbol, 1, (SType.tList, SType.tListQuote, SType.tBool, SType.tNIL))
		match _v.type:
			case SType.tBool:	# single boolean value
				_values.append(_v)
			case SType.tNIL:
				return pcontext.setResult(SBooleanSymbol(False, symbol))
			case SType.tList | SType.tListQuote:
				_values = cast(list, _v.value)
			

	# Else build a list from the remaining arguments
	else:
		for i in range(1, symbol.length):
			pcontext, _v = resultFromArgument(pcontext, symbol, i, SType.tBool)
			_values.append(_v)

	for v in _values:
		match v.type:
			case SType.tBool:
				if not v.value:
					return pcontext.setResult(SBooleanSymbol(False, symbol))
			case SType.tNIL:
				return pcontext.setResult(SBooleanSymbol(False, symbol))
			case _:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid argument type for any: {v.type} (must be boolean) in symbol\n{symbol.printHierarchy()}'))
	return pcontext.setResult(SBooleanSymbol(True, symbol))


def _doAny(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Return *True* if any of the arguments is *True*. The arguments can be a list of symbols.
		The type of all arguments must be *Bool*.

		Example:
			::

				(any true false) -> true
				(any false false) -> false
				(any '(false false)) -> false
				(any '(false true)) -> true

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is either *True* or *False*.
	"""

	assertSymbol(pcontext, symbol, minLength = 2)

	# If we have only one argument, then this must be a list or a single boolean value
	_values:SSymbolsList = []
	if len(symbol) == 2:
		pcontext, _v = resultFromArgument(pcontext, symbol, 1, (SType.tList, SType.tListQuote, SType.tBool, SType.tNIL))
		match _v.type:
			case SType.tBool:	# single boolean value
				return pcontext.setResult(SBooleanSymbol(cast(bool, _v.value), symbol))
			case SType.tNIL:
				return pcontext.setResult(SBooleanSymbol(False, symbol))
			case SType.tList | SType.tListQuote:
				_values = cast(SSymbolsList, _v.value)

	# Else build a list from the remaining arguments
	else:
		for i in range(1, symbol.length):
			pcontext, _v = resultFromArgument(pcontext, symbol, i, SType.tBool)
			_values.append(_v)

	for v in _values:
		match v.type:
			case SType.tBool:
				if v.value:
					# If any value is True, then we return True
					return pcontext.setResult(SBooleanSymbol(True, symbol))
			case SType.tNIL:
				# NIL is treated as False, therefore we continue to the next value
				pass
			case _:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid argument type for any: {v.type} (must be boolean) in symbol\n{symbol.printHierarchy()}'))

	# If we reach this point, then all values are False
	return pcontext.setResult(SBooleanSymbol(False, symbol))


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
		return pcontext.setResult(SStringSymbol(' '.join(pcontext.argv), symbol))
	else:
		pcontext, _idx = valueFromArgument(pcontext, symbol, 1, SType.tNumber)
		idx = int(_idx)
		if idx < 0 or idx >= len(pcontext.argv):
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong index: {idx} for argv. Must be [0..{len(pcontext.argv)-1}]\n{symbol.printHierarchy()}'))
		return pcontext.setResult(SStringSymbol(pcontext.argv[idx], symbol))


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
	assertSymbol(pcontext, symbol, 2)
	pcontext, value = valueFromArgument(pcontext, symbol, 1, SType.tBool)
	if not value:
		raise PAssertionFailed(pcontext.setError(PError.assertionFailed, f'Assertion failed: {symbol[1]}\n{symbol.printHierarchy()}'))
	return pcontext


def _doB64Decode(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Base64-decode a string.

		Example:
			::

				(base64-decode "SGVsbG8gV29ybGQ=") -> "Hello, World"

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result includes the decoded string.
	"""
	assertSymbol(pcontext, symbol, 2)

	# get string
	pcontext, value = valueFromArgument(pcontext, symbol, 1, SType.tString)
	return pcontext.setResult(SStringSymbol(base64.b64decode(value.encode('utf-8')).decode('utf-8'), symbol))


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
	assertSymbol(pcontext, symbol, 2)

	# get string
	pcontext, value = valueFromArgument(pcontext, symbol, 1, SType.tString)
	return pcontext.setResult(SStringSymbol(base64.b64encode(value.encode('utf-8')).decode('utf-8'), symbol))


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
	assertSymbol(pcontext, symbol, 1)
	return pcontext.setResult(SBooleanSymbol(value, symbol))


def _doBlock(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Execute a block of expressions.

		Example:
			::

				;; Prints "Hello" and "World". The result is "World".
				(block aSymbol
					(print "Hello")
					(print "World"))
				
				
				;; Prints only "Hello". The result is 42.
				(block aSymbol
					(print "Hello")
					(return-from aSymbol 42)
					(print "World"))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is the result of the last executed expression in the block, or the result of a matching *return-from* expression.
	"""
	assertSymbol(pcontext, symbol, minLength=2)

	# get block name
	if symbol[1].type != SType.tSymbol:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'block requires symbol name, got type: {symbol[1].type}\n{symbol.printHierarchy()}'))
	_name = symbol[1].value

	# execute block expressions
	pcontext.result = SNilSymbol(symbol)	# Default result is NIL for empty blocks
	for e in symbol[2:]:
		try:
			pcontext = executeExpression(pcontext, e)
		except PReturnFrom as e:
			# If the exception is raised for the current block, then return the result
			if e.name == _name:	
				return pcontext.setResult(e.pcontext.result)
			# Otherwise raise the exception again until the block is found
			raise e

	return pcontext


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
	assertSymbol(pcontext, symbol, 2)

	pcontext, value = valueFromArgument(pcontext, symbol, 1, (SType.tListQuote, SType.tList, SType.tNIL))
	if pcontext.result.length == 0 or pcontext.result.type == SType.tNIL:
		return pcontext.setResult(SNilSymbol(symbol))	# nil
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
	assertSymbol(pcontext, symbol, minLength=3)

	# Get value
	pcontext, value = valueFromArgument(pcontext, symbol, 1)

	# Iterate through remaining list arguments
	e:SSymbol
	for e in symbol[2:]:
		assertSymbol(pcontext, e, 2)

		# if it is the "orherwise" symbol (!) then execute that one and return
		if e[0].type == SType.tSymbol and e[0].value == 'otherwise':
			return executeExpression(pcontext, e[1])

		# Get match symbol
		m = executeExpression(pcontext, e[0])

		# match is string, number, or boolean
		if m.result.type in [ SType.tString, SType.tNumber, SType.tBool] and m.result.value == value:
			return executeExpression(pcontext, e[1])
		
	return pcontext.setResult(SNilSymbol(symbol)) # NIL


def _doCdr(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	The CDR of a list is the rest of the list without the first symbol. 
		The original list is not changed.

		Example:
			::

				(cdr '(1 2 3)) -> (2 3)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is the rest of the list without the first symbol or NIL.
	"""
	assertSymbol(pcontext, symbol, 2)

	pcontext, result = resultFromArgument(pcontext, symbol, 1, (SType.tListQuote, SType.tList, SType.tNIL))
	if result.length == 0 or result.type == SType.tNIL:
		return pcontext.setResult(SNilSymbol(symbol))
	return pcontext.setResult(SListSymbol(cast(list, result.value)[1:], symbol))


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
	assertSymbol(pcontext, symbol, minLength=2)
	return pcontext.setResult(joinExpression(pcontext, symbol[1:], symbol, sep='').result)


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
	assertSymbol(pcontext, symbol, 3)

	# get first symbol
	pcontext, _first = valueFromArgument(pcontext, symbol, 1)

	# get second symbol
	pcontext, _second = valueFromArgument(pcontext, symbol, 2)

	match _second.type:
		case SType.tList | SType.tListQuote:
			pcontext.result = deepcopy(_second)
		case SType.tNIL:
			pcontext.result = SListSymbol(parent = symbol)
		case _:
			pcontext.result = SListSymbol([ deepcopy(_second) ], symbol)
	
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
	assertSymbol(pcontext, symbol, maxLength=2)
	_format = '%Y%m%dT%H%M%S.%f'

	# get format
	pcontext, format = valueFromArgument(pcontext, symbol, 1, SType.tString, optional = True)
	if format is None:
		format = _format
	return pcontext.setResult(SStringSymbol(_utcNow().strftime(format), symbol))


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
	assertSymbol(pcontext, symbol, 4)

	# function name
	if symbol[1].type != SType.tSymbol:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun requires symbol name, got type: {symbol[1].type}\n{symbol.printHierarchy()}'))
	_name = symbol[1].value
	
	# arguments
	if symbol[2].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun requires symbol argument list, got type: {symbol[2].type}\n{symbol.printHierarchy()}'))
	_args = cast(SSymbolsList, symbol[2].value)

	_argNames:list[str] = []
	for a in cast(SSymbolsList, _args):		# type:ignore[union-attr]
		if a.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun arguments must be symbol, got: {a}\n{symbol.printHierarchy()}'))
		_argNames.append(a.value) 	# type:ignore[arg-type]
	
	# code
	if symbol[3].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'defun requires code list, got: {symbol[3].type}\n{symbol.printHierarchy()}'))
	_code = symbol[3]
	pcontext.functions[str(_name)] = ( _argNames, _code )
	return pcontext


def _doDolist(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	This function executes a code block for each element in a list.

		The first argument is a list that contains the loop variable symbol and the
		list to loop over. An optional third argument is the result variable for the loop.
		The second argument is the code block to execute.

		Example:
			::

				(dolist (i (1 2 3)) (print i))
				(dolist (i (1 2 3) result) (setq (+ result i))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is the last executed code block or NIL.
	"""
	assertSymbol(pcontext, symbol, 3)

	# arguments
	pcontext, _arguments = valueFromArgument(pcontext, symbol, 1, SType.tList, doEval=False)	# don't evaluate the argument
	if 2 <= len(_arguments) <= 3:
		# get loop variable
		_loopvar = cast(SSymbol, _arguments[0])
		if _loopvar.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dolist "var" must be a symbol, got: {pcontext.result.type}\n{symbol.printHierarchy()}'))

		# get list to loop over
		pcontext = executeExpression(pcontext, _arguments[1])
		if pcontext.result.type not in (SType.tList, SType.tListQuote):
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dolist "list" must be a (quoted) list, got: {pcontext.result.type}\n{symbol.printHierarchy()}'))
		_looplist = pcontext.result
	else:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dolist first argument requires 2 or 3 arguments, got: {len(_arguments)}\n{symbol.printHierarchy()}'))

	# Get result variable name	
	if len(_arguments) == 3:
		_resultvar = cast(SSymbol, _arguments[2])
		if _resultvar.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dolist "result" must be a symbol, got: {pcontext.result.type}\n{symbol.printHierarchy()}'))
		
		# if the variable does not exist, create it as a nil symbol
		if not str(_resultvar) in pcontext.variables:
			pcontext.setVariable(str(_resultvar), SNilSymbol(symbol))
	else:
		_resultvar = None

	# code
	pcontext, _code = valueFromArgument(pcontext, symbol, 2, SType.tList, doEval=False)	# don't evaluate the argument (yet)
	_code = SListSymbol(_code, symbol)	# We got a python list, but need a SSymbol list

	# execute the code
	pcontext.setVariable(str(_loopvar), SNumberSymbol(Decimal(0), symbol))
	for i in _looplist.value: # type:ignore[union-attr]
		pcontext.setVariable(str(_loopvar), i) # type:ignore[arg-type]
		pcontext = executeExpression(pcontext, _code)

	# set the result
	if _resultvar:
		pcontext.result = pcontext.variables[str(_resultvar)]
	else:
		pcontext.result = SNilSymbol(symbol)

	# return
	return pcontext



def _doDotimes(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	This function executes a code block a number of times.

		The first argument is a list that contains the loop counter symbol and the
		loop limit. An optional third argument is the result variable for the loop.
		The second argument is the code block to execute.

		Example:
			::

				(dotimes (i 10) (print i))
				(dotimes (i 10 result) (setq result i))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result 

	"""
	assertSymbol(pcontext, symbol, 3)

	# arguments
	pcontext, _arguments = valueFromArgument(pcontext, symbol, 1, SType.tList, doEval=False)	# don't evaluate the argument
	if 2 <= len(_arguments) <= 3:
		# get loop variable
		_loopvar = cast(SSymbol, _arguments[0])
		if _loopvar.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dotimes "counter" must be a symbol, got: {pcontext.result.type}\n{symbol.printHierarchy()}'))

		# get loop count
		pcontext = executeExpression(pcontext, _arguments[1])
		if pcontext.result.type != SType.tNumber:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dotimes "count" must be a number, got: {pcontext.result.type}\n{symbol.printHierarchy()}'))
		_loopcount = pcontext.result
		if int(_loopcount.value) < 0:	# type:ignore[arg-type]
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dotimes "count" must be a non-negative number, got: {_loopcount.value}\n{symbol.printHierarchy()}'))
	else:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dotimes first argument requires 2 or 3 arguments, got: {len(_arguments)}\n{symbol.printHierarchy()}'))
	
	# Get result variable name	
	if len(_arguments) == 3:
		_resultvar = cast(SSymbol, _arguments[2])
		if _resultvar.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'dotimes "result" must be a symbol, got: {pcontext.result.type}\n{symbol.printHierarchy()}'))
		
		# if the variable does not exist, create it as a nil symbol
		if not str(_resultvar) in pcontext.variables:
			pcontext.setVariable(str(_resultvar), SNilSymbol(symbol))
	else:
		_resultvar = None

	# code
	pcontext, _code = valueFromArgument(pcontext, symbol, 2, SType.tList, doEval=False)	# don't evaluate the argument (yet)
	_code = SListSymbol(_code, symbol)	# We got a python list, but must have a SSymbol list

	# execute the code
	pcontext.setVariable(str(_loopvar), SNumberSymbol(Decimal(0), symbol))
	for i in range(0, int(cast(Decimal, _loopcount.value))):
		pcontext.setVariable(str(_loopvar), SNumberSymbol(Decimal(i), symbol))
		pcontext = executeExpression(pcontext, _code)

	# set the result
	if _resultvar:
		pcontext.result = pcontext.variables[str(_resultvar)]
	else:
		pcontext.result = SNilSymbol(symbol)

	# return
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
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong format for quitwitherror: {symbol.printHierarchy()}'))
	if symbol.length == 2:
		pcontext = executeExpression(pcontext, symbol[1])
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
	assertSymbol(pcontext, symbol, 2)

	# get and evaluate symbol or list
	pcontext, result = resultFromArgument(pcontext, symbol, 1, (SType.tListQuote, SType.tSymbolQuote, SType.tString, SType.tSymbol, SType.tNIL))
	_s = deepcopy(result)
	_s.type = _s.type.unquote()
	return executeExpression(pcontext, _s)


def _doEvaluateInline(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Enable or disable inline string evaluation.

		Example:
			::

				(evaluate-inline false) ;; Disable inline evaluation

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.
	"""
	assertSymbol(pcontext, symbol, 2)

	# value
	pcontext, value = valueFromArgument(pcontext, symbol, 1, SType.tBool)
	pcontext.evaluateInline = cast(bool, value)
	return pcontext


def _doFilter(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Filter a list based on a condition.

		Example:
			::

				(filter (lambda (x) (< x 3)) (1 2 3 4 5)) -> (1 2)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object. The result is a new list.
	"""
	assertSymbol(pcontext, symbol, 3)

	# Get  function
	pcontext, _function = resultFromArgument(pcontext, symbol, 1, (SType.tLambda, SType.tSymbol, SType.tSymbolQuote))

	# Get list
	pcontext, _list = valueFromArgument(pcontext, symbol, 2, (SType.tList, SType.tListQuote, SType.tNIL))
	if symbol[2].type == SType.tNIL or not _list:	# type:ignore[union-attr]
		# Return NIL if the input list is empty or nil
		return pcontext.setResult(SNilSymbol(symbol))

	# The first element of the list determines the type
	_type = _list[0].type	# type:ignore[union-attr]

	# apply the function to each element of the list
	_result = []
	for value in _list:	# type:ignore[union-attr]
		
		# Check the type of the value.
		if value.type != _type:
			raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'invalid type in list for value {value} (expected type {_type}, found {value.type}):\n{symbol.printHierarchy()}'))

		# Execute the function/lambda/symbol and store the result for the next iteration	
		pcontext = executeSymbolWithArguments(pcontext, _function, [ value ])
		match pcontext.result.type:
			case SType.tBool | SType.tNIL:
				if pcontext.result.value:
					_result.append(value)
			case _:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid return type for filter function: {pcontext.result.type} (must be boolean)\n{symbol.printHierarchy()}'))
	return pcontext.setResult(SListSymbol(_result, symbol))


def _doFset(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	This function defines an alias for a symbol.

		An alias is a new symbol that points to an existing symbol.
		Aliased symbols can be aliases themselves.

		The symbols must be quoted.

		If the second symbold is not provided, then the alias is removed.

		Example:
			::

				(fset 'aSymbol 'anotherSymbol)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object.

		Raises:
			`PInvalidArgumentError`: In case of an error.
	"""
	assertSymbol(pcontext, symbol, minLength=2, maxLength=3)

	# get alias name
	if symbol[1].type != SType.tSymbolQuote:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'fset requires quoted symbol name for symbol 1, got type: {symbol[1].type}\n{symbol.printHierarchy()}'))
	_name = symbol[1].value

	# Remove alias if only two arguments are given
	if symbol.length == 2:
		if _name in pcontext.symbols:
			del pcontext.symbols[_name]
		return pcontext
	
	# get symbol
	# if symbol[2].type not in (SType.tSymbolQuote, SType.tLambda):
	# 	raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'fset requires quoted symbol name or lambda for argument 2, got type: {symbol[2].type}\n{symbol.printHierarchy()}'))

	# pcontext, _symbol = pcontext.valueFromArgument(symbol, 2)
	pcontext, _symbol = resultFromArgument(pcontext, symbol, 2)

	match _symbol.type:
		case SType.tLambda:
			pcontext.symbols[_name] = _symbol
		case SType.tSymbolQuote :
			if _symbol.value in pcontext.functions:
				# If the symbol is a function, then we need to copy it
				pcontext.functions[_name] = deepcopy(pcontext.functions[cast(str, _symbol.value)])
			else:
				# pcontext.symbols[_name] = _symbol
				pcontext.symbols[_name] = deepcopy(pcontext.symbols[cast(str, _symbol.value)])
		case _:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'fset requires quoted symbol name or lambda for argument 2, got type: {_symbol.type}\n{symbol.printHierarchy()}'))

	return pcontext.setResult(_symbol)



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
		match value:
			case str():
				return SStringSymbol(value, symbol)
			case int(), float():
				return SNumberSymbol(Decimal(value), symbol)
			case dict():
				return SJsonSymbol(jsn=value, parent=symbol)
			case bool():
				return SBooleanSymbol(value, symbol)
			case list():
				return SListSymbol([ _toSymbol(l) for l in value], symbol)
			case _:
				return SNilSymbol() 

	assertSymbol(pcontext, symbol, 3)

	# json
	pcontext, _json = valueFromArgument(pcontext, symbol, 1, SType.tJson)

	# key path
	pcontext, _key = valueFromArgument(pcontext, symbol, 2, SType.tString)

	# value
	if (_value := findXPath(_json, _key)) is None:
		return pcontext.setResult(SNilSymbol(symbol))
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
	assertSymbol(pcontext, symbol, 3)

	# json
	pcontext, _json = valueFromArgument(pcontext, symbol, 1, SType.tJson)

	# key path
	pcontext, _key = valueFromArgument(pcontext, symbol, 2, SType.tString)
	_key = _key.strip()

	return pcontext.setResult(SBooleanSymbol(findXPath(_json, _key) is not None, symbol))


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
	assertSymbol(pcontext, symbol, minLength=3)

	pcontext, _e = valueFromArgument(pcontext, symbol, 1, (SType.tBool, SType.tNIL, SType.tT, SType.tList, SType.tListQuote, SType.tString))
	if isinstance(_e, (list, str)):
		_e = len(_e) > 0

	if _e:
		_p = executeExpression(pcontext, symbol[2])
	elif symbol.length == 4:
		_p = executeExpression(pcontext, symbol[3])
	else:
		_p = pcontext
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
	assertSymbol(pcontext, symbol, 3)

	# Get value
	pcontext, _v = resultFromArgument(pcontext, symbol, 1)
	
	# Get symbol (!) to check
	pcontext, _s = resultFromArgument(pcontext, symbol, 2, (SType.tString, SType.tList, SType.tListQuote))
	# check
	return pcontext.setResult(SBooleanSymbol(_v in _s, symbol))


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
	assertSymbol(pcontext, symbol, minLength=2, maxLength=3)

	# Get variable and value first (symbol!)
	variable = symbol[1]
	if variable.type == SType.tList:
		pcontext, variable = resultFromArgument(pcontext, symbol, 1)

	if variable.type not in [SType.tString, SType.tSymbol]:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'variable name must be a string: {variable}\n{symbol.printHierarchy()}'))
	if variable.value not in pcontext.variables:
		raise PInvalidArgumentError(pcontext.setError(PError.undefined, f'undefined variable: {variable}\n{symbol.printHierarchy()}'))
	if (value := pcontext.variables[variable.value]).type != SType.tNumber:
		raise PInvalidArgumentError(pcontext.setError(PError.notANumber, f'variable value must be a number for inc/dec: {value}\n{symbol.printHierarchy()}'))
	
	# Get increment/decrement value
	pcontext, _idValue = valueFromArgument(pcontext, symbol, 2, SType.tNumber) if symbol.length == 3 else (pcontext, Decimal(1.0))
	idValue = cast(Decimal, _idValue)
	
	# Increment / decrement and Re-assign variable
	value.value = (cast(Decimal, value.value) + idValue) if isInc else (cast(Decimal, value.value) - idValue)
	pcontext.setVariable(variable.value, value)
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
	assertSymbol(pcontext, symbol, 3)

	# value
	pcontext, value = resultFromArgument(pcontext, symbol, 1)

	# list or string
	pcontext, lst = resultFromArgument(pcontext, symbol, 2, (SType.tList, SType.tListQuote, SType.tString))

	if lst.type == SType.tString and value.type !=SType.tString:
		raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'index-of: first argument must be a string if second argument is a string\n{symbol.printHierarchy()}'))
	try:
		return pcontext.setResult(SNumberSymbol(Decimal(operator.indexOf(lst.raw(), value.value)), symbol))
	except ValueError as e:
		return pcontext.setResult(SNilSymbol(symbol))


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
	assertSymbol(pcontext, symbol, 2)
	
	# symbol name
	pcontext, name = valueFromArgument(pcontext, symbol, 1, (SType.tString, SType.tSymbolQuote))
	return pcontext.setResult(SBooleanSymbol(name in pcontext.variables or
											 name in pcontext.functions or
											 name in pcontext.symbols or
											 name in pcontext.meta or 
											 name in pcontext.environment, symbol))


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
	assertSymbol(pcontext, symbol, 2)
	pcontext, _s = valueFromArgument(pcontext, symbol, 1, SType.tString)
	return pcontext.setResult(SStringSymbol(_s.replace('\n', '\\n').replace('"', '\\"'), symbol))


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
	assertSymbol(pcontext, symbol, 2)
	pcontext, _j = valueFromArgument(pcontext, symbol, 1, SType.tJson)
	try:
		_s = json.dumps(cast(str, _j))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid JSON: {str(e)}\n{symbol.printHierarchy()}'))
	return pcontext.setResult(SStringSymbol(_s, symbol))


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
	assertSymbol(pcontext, symbol, 3)

	# arguments
	if symbol[1].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'lambda requires symbol argument list, got: {symbol[1].type}\n{symbol.printHierarchy()}'))
	_args = cast(SSymbolsList, symbol[1].value)

	_argNames:list[str] = []
	for a in cast(SSymbolsList, _args):		# type:ignore[union-attr]
		if a.type != SType.tSymbol:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'lambda arguments must be symbol, got: {a}\n{symbol.printHierarchy()}'))
		_argNames.append(a.value) 	# type:ignore[arg-type]
	
	# code
	if symbol[2].type != SType.tList:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'lambda requires code list, got: {symbol[2].type}\n{symbol.printHierarchy()}'))
	return pcontext.setResult(SLambdaSymbol(( _argNames, symbol[2]), symbol))


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
	assertSymbol(pcontext, symbol, 2)
	pcontext, result = resultFromArgument(pcontext, symbol, 1, (SType.tString, SType.tList, SType.tListQuote))
	return pcontext.setResult(SNumberSymbol(Decimal(result.length), symbol))


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
	assertSymbol(pcontext, symbol, minLength=2)

	if sequential:
		for symbol in symbol[1:]:
			if symbol.type != SType.tList or symbol.length != 2:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'wrong format for let variable assignment:\n{symbol.printHierarchy()}'))

			# get variable name
			if symbol.value[0].type != SType.tSymbol:	# type:ignore[index, union-attr]
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Variable name must be a symbol:\n{symbol.printHierarchy()}'))
			variablename = cast(str, symbol.value[0].value)	# type:ignore[index, union-attr]

			# get value and assign variable (symbol!)
			pcontext, result = resultFromArgument(pcontext, cast(SSymbol, symbol.value), 1)
			pcontext.setVariable(variablename, result)

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
	assertSymbol(pcontext, symbol, minLength=2)
	# Let's explain the following:
	# 1) Construct a list from all argument using list comprehension
	#    This is a list of tuples (pcontext, symbol)
	# 2) use zip() to sort this into two sets: a) pcontexts and b) symbols
	# 3) Convert the zip() result into a list.
	# 4) Get the second set (symbols) and convert it into a list as well
	# 5) Create a new list symbol
	return pcontext.setResult(SListSymbol(list(list(
												zip(*[ resultFromArgument(pcontext, symbol, i) 
													   for i in range(1, symbol.length) ])
											  )[1]), 
										  symbol))


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
	p = joinExpression(pcontext, symbol[1:], symbol)
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
	assertSymbol(pcontext, symbol, 2)

	# value
	pcontext, value = valueFromArgument(pcontext, symbol, 1, SType.tString)
	pcontext.result.value = value.lower() if toLower else value.upper()	# type:ignore[union-attr]
	return pcontext


def _doMap(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Apply a function to each element of a list or multiple lists, accumulating the result.

		Example:
			::

				(map (lambda (x y) (+ x y)) '(1 2 3) '(4 6 7)) -> (5 8 10)

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	assertSymbol(pcontext, symbol, minLength=3)

	# function
	pcontext, _function = resultFromArgument(pcontext, symbol, 1, (SType.tLambda, SType.tSymbol, SType.tSymbolQuote))

	# get the list(s)
	_lists:SSymbolsList = []
	for i in range(2, symbol.length):
		pcontext, _list = resultFromArgument(pcontext, symbol, i, (SType.tList, SType.tListQuote, SType.tNIL))
		_lists.append(_list)

	_result:SSymbolsList = []
	# Get the length. The shortest list determines the length.
	# Lists can be empty or nil, in which case the length is 0.
	length = min([0 if not lst else len(cast(SSymbol, lst.value)) for lst in _lists])	# type:ignore[union-attr]

	# apply the function to each element of the list(s)
	for i in range(length):

		# Get the arguments, one element from each list
		_args = [cast(SSymbol, lst.value)[i] for lst in _lists]	# type:ignore[union-attr]

		# Execute the function/lambda/symbol and store the result for the next iteration	
		pcontext = executeSymbolWithArguments(pcontext, _function, _args)
		_result.append(pcontext.result)

	return pcontext.setResult(SListSymbol(_result, symbol))


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

	assertSymbol(pcontext, symbol, 3)

	# value
	pcontext, _in = valueFromArgument(pcontext, symbol, 1, SType.tString)
	
	# match expression
	pcontext, _match = valueFromArgument(pcontext, symbol, 2, SType.tString)

	# match
	return pcontext.setResult(SBooleanSymbol(pcontext.matchFunc(pcontext, _in, _match), symbol))


def _doMinMax(pcontext:PContext, symbol:SSymbol, doMax:Optional[bool] = True) -> PContext:
	"""	Get the minimum or maximum value of a list of numbers, strings or orher comparables.
	
		Example:
			::

				(min (1 2 3)) -> 1
				(min 1 2) -> 1
				(max (1 2 3)) -> 3
				(max 1 2) -> 2

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			doMax: Indicator whether to get the maximum (True) or minimum (False) value.

		Return:
			The updated `PContext` object with the function result.
	"""

	assertSymbol(pcontext, symbol, minLength=2)

	# Assign the function to use
	_func = max if doMax else min

	# If we have only one argument, then this must be a list
	_list:SSymbolsList = []
	if len(symbol) == 2:
		pcontext, _l = resultFromArgument(pcontext, symbol, 1, (SType.tList, SType.tListQuote, SType.tNIL))
		if symbol[1].type == SType.tNIL or not _l:	# type:ignore[union-attr]
			return pcontext.setResult(SNilSymbol(symbol))
		_list = cast(SSymbolsList, _l.value)
	
	# Else build a list from the remaining arguments
	else:
		for i in range(1, symbol.length):
			pcontext, _v = resultFromArgument(pcontext, symbol, i)
			_list.append(_v)
	
	if not _list:
		return pcontext.setResult(SNilSymbol(symbol))
	_type = _list[0].type

	_values:list[Any] = []
	for _v in _list:
		if _v.type != _type:
			raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'invalid type in list for min/max. Expected {_type}, got {_v.type} in symbol\n{symbol.printHierarchy()}'))
		_values.append(_v.value)
		
	# call the function
	try:
		return pcontext.setResult(_func(_values))
	except ValueError as _e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid list for min/max: {_values} in symbol\n{symbol.printHierarchy()}'))
	

def _doNot(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Boolean *not* operation.
	
		Example:
			::

				(not true) -> false

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	assertSymbol(pcontext, symbol, maxLength=2)
	pcontext, _v = valueFromArgument(pcontext, symbol, 1, (SType.tBool, SType.tNIL, SType.tT))
	match pcontext.result.type:
		case SType.tNIL:
			return pcontext.setResult(STSymbol(symbol))
		case SType.tT:
			return pcontext.setResult(SNilSymbol(symbol))
		case _:
			return pcontext.setResult(SBooleanSymbol(not _v, symbol))


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
	assertSymbol(pcontext, symbol, 3)

	# get index
	pcontext, _idx = valueFromArgument(pcontext, symbol, 1, SType.tNumber)

	# get list or string as SSymbol
	pcontext, _value = resultFromArgument(pcontext, symbol, 2, (SType.tString, SType.tList, SType.tListQuote))
	
	# Get nth element
	if _idx < 0 or _idx >= _value.length:
		pcontext.result = SNilSymbol(symbol)
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
	assertSymbol(pcontext, symbol, minLength=2)
	r1 = deepcopy(executeExpression(pcontext, symbol[1]).result)

	for i in range(2, symbol.length):
		try:
			# Get the second operant
			r2 = executeExpression(pcontext, symbol[i]).result
			
			match r1.type:
				
				# If the first operant is a list, then we have to perform a bit different
				case SType.tList | SType.tListQuote:

					# If both operants are list then do a raw comparison
					if r2.type in (SType.tList, SType.tListQuote):
						r1.value = op(r1.raw(), r2.raw())
					
					# If the second operant is NOT a list, then iterate of the first and do the
					# operation. If any succeeds, then the operation is true.
					# This is only possible for boolean operations
					else:
						if tp != SType.tBool:
							raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'if the first operant is a list then iterating over it is only allowed for boolean operators:\n{symbol.printHierarchy()}'))
						_v1 = None
						for s in cast(list, r1.value):
							if _v1 := op(s.value, r2.value):	# True if any
								break
						r1.value = _v1
				
				case SType.tNIL | SType.tT:
					if r2.type not in (SType.tNIL, SType.tT):
						raise InvalidOperation()
					r1.value = op(r1.value, r2.value)
			
				# Otherwise just apply the operator
				case _:
					r1.value = op(r1.value, r2.value)

		except ZeroDivisionError as e:
			raise PDivisionByZeroError(pcontext.setError(PError.divisionByZero, f'{str(e)}\n{symbol.printHierarchy()}'))
		except TypeError as e:
			raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'invalid types in expression: {str(e)}\n{symbol.printHierarchy()}'))
		except InvalidOperation as e:
			if DivisionUndefined in e.args:
				raise PDivisionByZeroError(pcontext.setError(PError.divisionByZero, str(e)))
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid arguments in expression: {str(e)}\n{symbol.printHierarchy()}'))

	if r1.type in (SType.tNIL, SType.tT):
		# If the result is nil or t, then we return a boolean symbol
		r1 = SBooleanSymbol(cast(bool, r1.value), symbol)
	else:
		r1.type = tp
	return pcontext.setResult(r1)


def _doParseString(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Parse a string as executable code and return it for evaluation.

		Example:
			::

				(eval (parse-string "(print \"hello, world\")")) -> prints "hello, world"

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The `PContext` object with the new symbol as result.
	"""
	assertSymbol(pcontext, symbol, 2)

	# get string
	pcontext, _string = valueFromArgument(pcontext, symbol, 1, SType.tString)
	# replace escaped quotes
	_string = _string.replace('\\"', '"')
	parser = SExprParser()
	try:
		# parse string
		_lst = parser.ast(removeCommentsFromJSON(_string), allowBrackets=pcontext.allowBrackets)
		# return result as quoted list
		return pcontext.setResult(SListQuoteSymbol(_lst, symbol))
	except ValueError as e:
		pcontext.setError(PError.invalid, str(e), expression=parser.errorExpression)
		return pcontext


def _doPrint(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Print the arguments to the console.

		The function return the resulting string as a symbol.
	
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
		return pcontext.setResult(SStringSymbol('', symbol))
	pcontext.printFunc(pcontext, arg := str(joinExpression(pcontext, symbol[1:], symbol).result.value))
	return pcontext.setResult(SStringSymbol(arg, symbol))


def _doProgn(pcontext:PContext, symbol:SSymbol, doEval:bool = True) -> PContext:
	""" Evaluate one or multiple symbols in a list. This is the explicite function that many
		Example:
			::

				(progn (print "Hello, World"))

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			doEval: Indicator whether to evaluate the arguments.

		Return:
			The updated `PContext` object with the function result.
		
		Raises:
			`PInvalidArgumentError`: In case of an invalid argument or parameter.
	"""
	return __doProgn(pcontext, symbol, doEval=doEval, start=1)


def __doProgn(pcontext:PContext, symbol:SSymbol, doEval:bool=True, start:int=0) -> PContext:
	"""	Execute a symbol list.

		This function is used internally by the interpreter.

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.
			doEval: Indicator whether to evaluate the arguments.
			start: The offset to start the evaluation. This is 1 for the `_doProgn` function and 0 for the interpreter.
		
		Return:
			The updated `PContext` object with the function result.
	"""
	for i in range(start, symbol.length):	# type:ignore [arg-type]
		pcontext, result = resultFromArgument(pcontext, symbol, i, doEval=doEval)
		if pcontext.state == PState.returning:
			return pcontext
	

		# if the first element is a lambda then execute it
		if i == 0 and result is not None and result.type == SType.tLambda:
			# Construct lambda call
			_name = f'lambda_{"".join(random.choices(string.ascii_letters + string.digits, k = 10))}'
			_call = cast(Tuple[list[str], SSymbol], result.value)
			_arguments = _call[0]
			_code = _call[1]
			# print(f'progn> lambda: {_name} {_arguments} {_code}')
			
			# Check arguments
			if len(_arguments) != symbol.length - 1:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Number of arguments mismatch. Expected: {len(_arguments)}, got: {symbol.length - 1}\nHint: Lambdas assigned to a symbol must not be enclosed by parentheses\n{symbol.printHierarchy()}'))

			# Temporarily add to functions
			pcontext.functions[_name] = (_arguments, _code)

			# Execute as function
			pcontext = executeFunction(pcontext, 
							  		   SListSymbol(cast(SSymbolsList, symbol.value), symbol), 	# type:ignore[index]
									   _name)		

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
	assertSymbol(pcontext, symbol, maxLength=2)

	if symbol.length == 2:
		pcontext = getArgument(pcontext, symbol, 1)
		pcontext.state = PState.terminatedWithResult
	else:
		pcontext.state = PState.terminated
		pcontext.result = SNilSymbol(symbol)
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
	assertSymbol(pcontext, symbol, 2)
	pcontext, result = resultFromArgument(pcontext, symbol, 1, (SType.tList, SType.tSymbol), doEval=False)
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
	assertSymbol(pcontext, symbol, maxLength=3)
	start = Decimal(0.0)
	end = Decimal(1.0)
	if symbol.length == 2:
		pcontext, end = valueFromArgument(pcontext, symbol, 1, SType.tNumber)	# type:ignore [assignment]
	elif symbol.length == 3:
		pcontext, start = valueFromArgument(pcontext, symbol, 1, SType.tNumber)	# type:ignore [assignment]
		pcontext, end = valueFromArgument(pcontext, symbol, 2, SType.tNumber)			# type:ignore [assignment]
	return pcontext.setResult(SNumberSymbol(Decimal(random.uniform(float(start), float(end))), symbol))



def _doReduce(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Apply a function to each element of a list or multiple lists, accumulating the result.

		Example:
			::

				(reduce (lambda (x y) (+ x y)) '(1 2 3 4 5)) -> 15
				(reduce '+ '(1 2 3 4 5) 10) -> 25

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""

	assertSymbol(pcontext, symbol, minLength=3, maxLength=4)

	# function
	pcontext, _function = resultFromArgument(pcontext, symbol, 1, (SType.tLambda, SType.tSymbol, SType.tSymbolQuote))

	# get the list
	pcontext, _list = resultFromArgument(pcontext, symbol, 2, (SType.tList, SType.tListQuote, SType.tNIL))
	if _list.type == SType.tNIL:
		_list = SListSymbol(parent=symbol)	# type:ignore[union-attr]

	# Get the initial value. If there is one, then add it to the front of list
	if symbol.length == 4:
		pcontext, _initial = resultFromArgument(pcontext, symbol, 3)
		_list = SListSymbol([_initial] + cast(list, _list.value), symbol)	# type:ignore[union-attr]

	# Return the initial value if the list is empty, or NIL if there is no initial value
	if len(_list) == 0:	# type:ignore[union-attr]
		return pcontext.setResult(SNilSymbol(symbol))
	
	# The first element of the list determines the type
	_type = _list[0].type	# type:ignore[union-attr]

	# The initial value is the first element of the list
	_result = _list[0]

	# apply the function to each element of the list
	for value in _list[1:]:	# type:ignore[union-attr]
		
		# Check the type of the value.
		if value.type != _type:
			raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'invalid type in list for value {value} (expected type {_type}, found {value.type}):\n{symbol.printHierarchy()}'))

		# Execute the function/lambda/symbol and store the result for the next iteration	
		pcontext = executeSymbolWithArguments(pcontext, _function, [ _result, value])
		_result = pcontext.result
	return pcontext.setResult(_result)



def _doRemoveJSONAttribute(pcontext:PContext, symbol:SSymbol) -> PContext:
	""" Remove an attribute from a JSON structure via its key path.

		One may remove multiple attributes at once by providing multiple key paths.

		Example:
			::
			
				(remove-json-attribute { "a" : { "b" : "c" }} "a/b") -> { "a" : {} }

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result, ie a new JSON symbol.
	"""
	assertSymbol(pcontext, symbol, minLength=2)

	# json
	_json:dict
	pcontext, _json = valueFromArgument(pcontext, symbol, 1, SType.tJson)
	_json = deepcopy(_json)

	for i in range(2, symbol.length):
		# key path
		pcontext, _key = valueFromArgument(pcontext, symbol, i, SType.tString)
		# remove
		setXPath(_json, _key.strip(), delete = True)

	return pcontext.setResult(SJsonSymbol(jsn=_json, parent=symbol))


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
	assertSymbol(pcontext, symbol, maxLength=2)
	if symbol.length == 2:
		# Evaluate the first symbol
		pcontext = getArgument(pcontext, symbol, 1)
	else:
		# result is nil
		pcontext.result = SNilSymbol(symbol)
	pcontext.state = PState.returning
	return pcontext


def _doReturnFrom(pcontext:PContext, symbol:SSymbol) -> None:
	"""	Return from a named block.

		Example:
			::

				(block "aBlock" 1 (return-from "aBlock" 2) 3) -> 2

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
		
		Raises:
			`PReturnFrom`: Always raises this exception.
	"""
	assertSymbol(pcontext, symbol, minLength=2, maxLength=3)

	# get block name
	if symbol[1].type != SType.tSymbol:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'return-from requires symbol name, got type: {symbol[1].type}\n{symbol.printHierarchy()}'))
	_name = symbol[1].value

	if symbol.length == 3:
		# Evaluate the first symbol
		pcontext = getArgument(pcontext, symbol, 2)
	else:
		# result is nil
		pcontext.result = SNilSymbol(symbol)
	
	# do NOT return but raise an exception
	raise PReturnFrom(pcontext, _name)



def _doReverse(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Reverse a list or string.
	
		Example:
			::

				(reverse '(1 2 3)) -> (3 2 1)

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""
	assertSymbol(pcontext, symbol, 2)
	pcontext, _value = resultFromArgument(pcontext, symbol, 1, (SType.tList, SType.tListQuote, SType.tString, SType.tNIL))
	match _value.type:
		case SType.tList | SType.tListQuote:
			return pcontext.setResult(SListSymbol(list(reversed(cast(list, _value.value))), symbol))
		case SType.tString:
			return pcontext.setResult(SStringSymbol(cast(str, _value[::-1]), symbol))
		case SType.tNIL:
			return pcontext.setResult(SNilSymbol(symbol))
		case _:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid argument type for reverse: {_value.type}\n{symbol.printHierarchy()}'))



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
	assertSymbol(pcontext, symbol, minLength=2, maxLength=3)
	
	# Get number
	_number:Decimal
	pcontext, _number = valueFromArgument(pcontext, symbol, 1, SType.tNumber)
	
	# Get precision
	_precision:int = 0
	if symbol.length == 3:
		pcontext, _precision = valueFromArgument(pcontext, symbol, 2, SType.tNumber)
	
	# Round
	try:
		return pcontext.setResult(SNumberSymbol(round(_number, int(_precision)), symbol))
	except (InvalidOperation, ValueError) as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Invalid argument: {str(e)}\n{symbol.printHierarchy()}'))


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
	assertSymbol(pcontext, symbol, 3)

	# var
	pcontext, _var = valueFromArgument(pcontext, symbol, 1, SType.tSymbol, doEval=False)

	# value
	pcontext, _value = resultFromArgument(pcontext, symbol, 2)
	pcontext.setVariable(_var, _value)

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
	assertSymbol(pcontext, symbol, minLength=3, maxLength=4)

	# json
	_json:dict
	pcontext, _json = valueFromArgument(pcontext, symbol, 1, SType.tJson)
	_json = deepcopy(_json)

	if symbol.length == 3:
		pcontext, lst = resultFromArgument(pcontext, symbol, 2, (SType.tList, SType.tListQuote))
		for i in range(lst.length):
			_n:list
			pcontext, _result = resultFromArgument(pcontext, lst, i, (SType.tList, SType.tListQuote))
			_n = _result.raw()
			if (_l := len(_n)) != 2:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid number of arguments: {_l} (must be 2)\n{lst.printHierarchy()}'))
			_key = _n[0]
			_value = _n[1]
			if not setXPath(_json, _key, _value):
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid key for set-json-attribute: {_key}\n{lst.printHierarchy()}'))

	else:	# length = 4
		# key
		pcontext, _key = valueFromArgument(pcontext, symbol, 2, SType.tString)

		# value
		pcontext, _result = resultFromArgument(pcontext, symbol, 3, (SType.tString, SType.tNumber, SType.tBool, SType.tListQuote, SType.tList, SType.tJson))
		_value = _result.raw()	
		if not setXPath(_json, _key, _value):
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid key for set-json-attribute: {_key}\n{symbol.printHierarchy()}'))

	return pcontext.setResult(SJsonSymbol(jsn=_json, parent=symbol))


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
	assertSymbol(pcontext, symbol, 2)
	try:
		pcontext, _value = valueFromArgument(pcontext, symbol, 1, SType.tNumber)
		toTs = time.time() + float(_value)	# type:ignore [arg-type]
		while pcontext.state == PState.running and toTs > time.time():
			checkScriptTimeout(pcontext)
			time.sleep(0.01)
	except ValueError as e:
		raise PNotANumberError(pcontext.setError(PError.notANumber, f'Not a number: {e}\n{symbol.printHierarchy()}'))
	except KeyboardInterrupt:
		raise PInterruptedError(pcontext.setError(PError.canceled, f'Keyboard interrupt\n{symbol.printHierarchy()}'))
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
	assertSymbol(pcontext, symbol, 4)

	# start
	pcontext, start = valueFromArgument(pcontext, symbol, 1, SType.tNumber)

	# end
	pcontext, end = valueFromArgument(pcontext, symbol, 2, SType.tNumber)

	# list or string
	pcontext, lst = resultFromArgument(pcontext, symbol, 3, (SType.tList, SType.tListQuote, SType.tString))
	
	if lst.type == SType.tString:
		return pcontext.setResult(SStringSymbol(lst[int(start):int(end)], symbol))
	else:	# list
		return pcontext.setResult(SListSymbol(lst[int(start):int(end)], symbol))


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
	assertSymbol(pcontext, symbol, 2)
	_s = (pcontext := getArgument(pcontext, symbol, 1, SType.tString)).result
	try:
		return pcontext.setResult(SJsonSymbol(jsnString=cast(str, _s.value), parent=symbol))	# implicite conversion
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid JSON: {str(e)}\n{symbol.printHierarchy()}'))


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
	assertSymbol(pcontext, symbol, 2)

	# string
	pcontext, _string = valueFromArgument(pcontext, symbol, 1, SType.tString)
	try:
		pcontext = pcontext.setResult(SNumberSymbol(Decimal(_string), symbol))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'input for conversion must be a convertable number, is: {_string}\n{symbol.printHierarchy()}'))
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

	assertSymbol(pcontext, symbol, 2)

	# anything
	pcontext, _string = valueFromArgument(pcontext, symbol, 1)
	try:
		pcontext = pcontext.setResult(SStringSymbol(str(_string), symbol))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'input for conversion must be a convertable string, is: {_string}\n{symbol.printHierarchy()}'))
	return pcontext


def _doToSymbol(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Convert a string to a symbol. 
	
		Example:
			::

					(to-symbol "aSymbol") -> aSymbol

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
		
		Raises:
			`PInvalidArgumentError`: In case the input cannot be converted.
	"""
	assertSymbol(pcontext, symbol, 2)

	# string
	pcontext, _string = valueFromArgument(pcontext, symbol, 1, SType.tString)
	try:
		pcontext = pcontext.setResult(SSymbolSymbol(_string, symbol))
	except Exception as e:
		raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'input for conversion must be a convertable string, is: {_string}\n{symbol.printHierarchy()}'))
	return pcontext


def _doUnwindProtect(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Execute a cleanup form after the main form has been executed or in case of an error.

		Currently only programmatic flow interrupts are supported to trigger the cleanup form:
		*assert*, *quit*, *quit-with-error*, *return*, *return-from*.
	
		Example:
			::

				(unwind-protect
					(print "main form")
					(print "cleanup form"))

		Args:
			pcontext: Current `PContext` for the script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the function result.
	"""

	def _cleanup(pcontext:PContext, symbol:SSymbol) -> PContext:
		for i in range(2, symbol.length):
			pcontext, _ = resultFromArgument(pcontext, symbol, i)
		return pcontext

	assertSymbol(pcontext, symbol, minLength=3)

	# protected form
	try:
		pcontext, _ = resultFromArgument(pcontext, symbol, 1)
		if pcontext.state == PState.returning:
			pcontext = _cleanup(pcontext, symbol)
		return pcontext
	
	# currently only programmatic flow interrups are supported:
	# return-from, assert, quit, quit-with-error, return
	# Those functions throw exception that are caught here,
	# and then the cleanup form is executed and the exception is re-raised
	except (PAssertionFailed, PQuitRegular, PQuitWithError, PReturnFrom) as e:
		pcontext = _cleanup(pcontext, symbol)
		e.pcontext = pcontext
		raise e


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
	assertSymbol(pcontext, symbol, 2)

	# arg
	pcontext, _url = valueFromArgument(pcontext, symbol, 1, SType.tString)
	return pcontext.setResult(SStringSymbol(urllib.parse.quote_plus(_url), symbol))


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
	assertSymbol(pcontext, symbol, 3)
	_lastResult = SNilSymbol(symbol)
	while True:
		
		# evaluate while expression
		pcontext, _e = valueFromArgument(pcontext, symbol, 1, (SType.tBool, SType.tNIL, SType.tT, SType.tList, SType.tListQuote, SType.tString))
		if isinstance(_e, (list, str)):
			_e = len(_e) > 0
		if not _e:
			break

		# Otherwise execute the loop
		pcontext, _lastResult = resultFromArgument(pcontext, symbol, 2)	# type:ignore[assignment]
		
		# Handle return gracefully
		if pcontext.state == PState.returning:
			pcontext.state = PState.running
			return pcontext

	return pcontext.setResult(_lastResult)


def _doZip(pcontext:PContext, symbol:SSymbol) -> PContext:
	"""	Zip lists together. 
	
		Example:
			::

				(zip '(1 2 3) '(4 5 6)) -> ((1 4) (2 5) (3 6))

		Args:
			pcontext: `PContext` object of the running script.
			symbol: The symbol to execute.

		Return:
			The updated `PContext` object with the operation result.
	"""
	assertSymbol(pcontext, symbol, minLength=2)

	# get the list(s)
	_lists = []
	for i in range(1, len(symbol)):
		pcontext, _list = resultFromArgument(pcontext, symbol, i, (SType.tList, SType.tListQuote, SType.tNIL))
		_lists.append(_list)

	_result = []
	# Get the length. The shortest list determines the length.
	length = min([len(lst) for lst in _lists])	# type:ignore[union-attr]

	# apply the function to each element of the list(s)
	for i in range(length):
		# Get the value of each list
		_result.append(SListSymbol([lst[i] for lst in _lists], symbol))	# type:ignore[union-attr]

	return pcontext.setResult(SListSymbol(_result, symbol))	# type:ignore[arg-type]


builtinFunctions:PSymbolDict = {
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

	'all':					_doAll,
	'any':					_doAny,
	'argv':					_doArgv,
	'assert':				_doAssert,
	'base64-decode':		_doB64Decode,
	'base64-encode':		_doB64Encode,
	'block':				_doBlock,
	'car':					_doCar,
	'case':					_doCase,
	'cdr': 					_doCdr,
	'cons':					_doCons,
	'datetime':				_doDatetime,
	'dec':					lambda p, a: _doIncDec(p, a, False),
	'defun':				_doDefun,
	'dolist':				_doDolist,
	'dotimes':				_doDotimes,
	'eval':					_doEval,
	'evaluate-inline':		_doEvaluateInline,
	'false':				lambda p, a: _doBoolean(p, a, False),
	'filter':				_doFilter,
	'fset':					_doFset,
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
	'map':					_doMap,
	'match':				_doMatch,
	'max':					lambda p, a: _doMinMax(p, a, True),
	'min':					lambda p, a: _doMinMax(p, a, False),
	'nth':					_doNth,
	'parse-string':			_doParseString,
	'print': 				_doPrint,
	'progn':				_doProgn,
	'quit':					_doQuit,
	'quit-with-error':		_doError,
	'quote':				_doQuote,
	'random':				_doRandom,
	'reduce':				_doReduce,
	'remove-json-attribute':_doRemoveJSONAttribute,
	'return':				_doReturn,
	'return-from':			_doReturnFrom,
	'reverse':				_doReverse,
	'round':				_doRound,
	'set-json-attribute':	_doSetJSONAttribute,
	'setq':					_doSetq,
	'sleep':				_doSleep,
	'slice':				_doSlice,
	'string-to-json':		_doStringToJson,
	'to-number':			_doToNumber,
	'to-string':			_doToString,
	'to-symbol':			_doToSymbol,
	'true':					lambda p, a: _doBoolean(p, a, True),
	'unwind-protect':		_doUnwindProtect,
	'upper':				lambda p, a: _doLowerUpper(p, a, False),
	'url-encode':			_doURLEncode,
	'while':				_doWhile,
	'zip':					_doZip,

	# characters
	'nl':				lambda p, a: p.setResult(SStringSymbol('\n')),
	'sp':				lambda p, a: p.setResult(SStringSymbol(' ')),

	# Variables
	
	# argc
}
""" Dictionary to map the functions to Python functions. """
