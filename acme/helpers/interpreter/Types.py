#
#	Types.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Various types used in the ACMEScript Interpreter
"""
from __future__ import annotations

from typing import TYPE_CHECKING, cast, Union, Tuple, Callable, Optional, Any, NamedTuple
import json
from dataclasses import dataclass, field
from decimal import Decimal

if TYPE_CHECKING:
	from .PContext import PContext

from enum import IntEnum, auto


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
		match self:
			case SType.tListQuote:
				return SType.tList
			case SType.tSymbolQuote:
				return SType.tSymbol
			case _:
				return self


class SSymbol(object):
	"""	The basic class to store and handle symbols, lists, and values in the Interpreter. 
	"""

	__slots__ = (
		'type',
		'value',
		'length',
		'parent',
	)
	""" Slots of class attributes. """

	def __init__(self, typ:Optional[SType]=None,
					   parent:Optional[SSymbol]=None) -> None:
		"""	Initialization of a `SSymbol` object.
			
			Only one of the arguments must be passed to the function.
			If no argument is given, then the symbol becomes a NIL object.
		
			Args:
				typ: Type of the symbol.
				parent: Parent `SSymbol` object.
		"""

		self.value:Union[str, Decimal, bool, SSymbolsList, Tuple[list[str], SSymbol], dict[str, Any]] = None
		"""	The actual stored value. This is either one of the the basic data typs, of a `SSymbol`, list of `SSymbol`, dictionary, etc."""
		
		self.type:SType = typ
		""" `SType` to indicate the type. """
		
		self.length:int = 0
		""" The length of the symbol. Could be the length of a string, number of items in a list etc. """
		
		self.parent:Optional[SSymbol] = parent
		""" Parent `SSymbol` object. """


	@classmethod
	def symbolFromValue(cls, value:Union[bool, str, int, float, list, dict]) -> SSymbol:
		"""	Create a new `SSymbol` object from a value.

			Args:
				value: A value that is then automatically assigned to one of the basic, quoted types.
			
			Return:
				A new `SSymbol` sub-class object.
		"""
		# Try to determine an unknown type
		match value:
			case bool():
				return SBooleanSymbol(value)
			case str():
				return SStringSymbol(value)
			case int() | float():
				return SNumberSymbol(Decimal(value))
			case dict():
				return SJsonSymbol(jsn=value)
			case list():
				return SListSymbol([ cls.symbolFromValue(v) for v in value ])
			case _:
				raise ValueError(f'Unsupported type: {type(value)} for value: {value}')


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
		return self.toString(quoteStrings=True)
	

	def __len__(self) -> int:
		"""	Return the length of the value.

			Return:
				Length of the value.
		"""
		return self.length


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
	

	def __eq__(self, other:Any) -> bool:
		"""	Check whether two `SSymbol` objects are equal.

			Args:
				other: The other object to compare.
			
			Return:
				True if the two objects are equal, False otherwise.
		"""
		if isinstance(other, SSymbol):
			return self.raw() == other.raw()
		return self.raw() == other
	

	def __gt__(self, other:Any) -> bool:
		"""	Check whether the value is greater than another value.

			Args:
				other: The other object to compare.
			
			Return:
				True if the value is greater, False otherwise.
		"""
		if isinstance(other, SSymbol):
			return self.raw() > other.raw()
		return self.raw() > other
	

	def __lt__(self, other:Any) -> bool:
		"""	Check whether the value is less than another value.

			Args:
				other: The other object to compare.
			
			Return:
				True if the value is less, False otherwise.
		"""
		if isinstance(other, SSymbol):
			return self.raw() < other.raw()
		return self.raw() < other
	

	def toString(self, quoteStrings:bool = False, pythonList:bool = False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.
			
			Return:
				A string representation of the value.
		"""
		return str(self.value)
			
	
	def printHierarchy(self, depth:int = 0, max_depth:int = None) -> str:
		""" Print the hierarchy in reverse order (parent first) 
			with reversed indentation.

			Args:
				depth: Current depth level.
				max_depth: Maximum depth level.
			
			Return:
				Parent hierarchy as a string.
		"""

		prefix = '->  ' if not max_depth else '    '
		if max_depth is None:
			# Calculate the maximum depth
			max_depth = 0
			node = self
			while node.parent is not None:
				node = node.parent
				max_depth += 1

		indentStr = '  ' * (max_depth - depth)
		parentHierarchy = self.parent.printHierarchy(depth + 1, max_depth) if self.parent is not None else ''
		return f'{parentHierarchy}{prefix}{indentStr}{self.toString(quoteStrings=True)}\n'
	

	def raw(self) -> Any:
		"""	The Python "raw" value.

			Return:
				The raw value. For types that could not be converted directly the stringified version is returned.
		"""
		match self.type:
			case SType.tList | SType.tListQuote:
				return [ v.raw() for v in cast(list, self.value) ]
			case SType.tBool | SType.tString | SType.tSymbol | SType.tSymbolQuote | SType.tJson:
				return self.value
			case SType.tNumber:
				if '.' in str(self.value):	# float or int?
					return float(cast(Decimal, self.value))
				return int(cast(Decimal, self.value))
			case _:
				return str(self.value)
	

class SStringSymbol(SSymbol):

	def __init__(self, string:str, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tString, parent=parent)
		self.value = string
		self.length = len(string)


	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		if quoteStrings:
			return f'"{str(self.value)}"'
		return str(self.value)


class SBooleanSymbol(SSymbol):

	def __init__(self, boolean:bool, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tBool, parent=parent)
		self.value = boolean
		self.length = 1


	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		return str(self.value).lower()


class SNumberSymbol(SSymbol):

	def __init__(self, number:Decimal, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tNumber, parent=parent)
		self.value = number
		self.length = 1


class SSymbolSymbol(SSymbol):

	def __init__(self, symbol:str, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tSymbol, parent=parent)
		self.value = symbol
		self.length = 1


class SSymbolQuoteSymbol(SSymbol):
	
	def __init__(self, symbol:str, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tSymbolQuote, parent=parent)
		self.value = symbol[1:]
		self.length = 1


	def toString(self, quoteStrings:bool = False, pythonList:bool = False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		return f"'{str(self.value)}"


class SListSymbol(SSymbol):

	def __init__(self, lst:Optional[SSymbolsList]=[], parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tList, parent=parent)
		self.setLst(lst)

	
	def setLst(self, lst:SSymbolsList) -> SSymbol:
		"""	Set the value of a list of elements.

			Args:
				lst: List of elements.

			Return:
				Self.
		"""
		self.value = lst
		self.length = len(self.value)
		return self
	

	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		# Set the list chars
		lchar1 = '[' if pythonList else '('
		lchar2 = ']' if pythonList else ')'
		return f'{lchar1} {" ".join(lchar1 if v == "[" else lchar2 if v == "]" else v.toString(quoteStrings=quoteStrings, pythonList=pythonList) for v in cast(list, self.value))} {lchar2}'


class SListQuoteSymbol(SSymbol):

	def __init__(self, lstQuote:Optional[SSymbolsList]=[], parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tListQuote, parent=parent)
		self.setLstQuote(lstQuote)


	def setLstQuote(self, lstQuote:SSymbolsList) -> SSymbol:
		"""	Set the value of a list of quoted elements.

			Args:
				lstQuote: List of quoted elements.

			Return:
				Self.
		"""
		self.value = lstQuote
		self.length = len(self.value)
		return self


	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		# Set the list chars
		lchar1 = '[' if pythonList else '('
		lchar2 = ']' if pythonList else ')'
		return f'\'{lchar1} {" ".join(lchar1 if v == "[" else lchar2 if v == "]" else v.toString(quoteStrings=quoteStrings, pythonList=pythonList) for v in cast(list, self.value))} {lchar2}'


class SListCharSymbol(SSymbol):

	def __init__(self, listChar:str, parent:Optional[SSymbol]=None) -> None:
		super().__init__(parent=parent)
		self.type = SType.tListBegin if listChar == '(' else SType.tListEnd
		self.value = listChar
		self.length = 1


class SLambdaSymbol(SSymbol):

	def __init__(self, lmbda:Tuple[list[str], SSymbol], parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tLambda, parent=parent)
		self.value = lmbda
		self.length = 1


	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		_p = (v.toString(quoteStrings=quoteStrings, pythonList=pythonList) if isinstance(v, SSymbol) else v
			  for v in cast(tuple, self.value)[0])
		return f'( lambda ( {", ".join(_p)} ) {str(cast(tuple, self.value)[1])} )'


class SJsonSymbol(SSymbol):
	
	def __init__(self, jsnString:Optional[str]=None,  jsn:Optional[dict]=None, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tJson, parent=parent)
		self.value = json.loads(jsnString) if jsnString else jsn
		self.length = 1


	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		return json.dumps(self.value)


class SNilSymbol(SSymbol):
	
	def __init__(self, parent:Optional[SSymbol]=None) -> None:
		super().__init__(SType.tNIL, parent=parent)
		self.value = None
		self.length = 0


	def toString(self, quoteStrings:bool=False, pythonList:bool=False) -> str:
		"""	Return a string representation of the value.

			Args:
				quoteStrings: Quote strings.
				pythonList: Return a Python list representation.

			Return:
				A string representation of the value.
		"""
		return 'nil'


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
	"""	script is returning from a call. """

	def isEndscriptState(self) -> bool:
		"""	Check whether the end of a script has been reached.
		
			Return:
				True if one of the termination states is set.
		"""
		return self.value in  [ self.canceled, self.terminated, self.terminatedWithResult, self.terminatedWithError, self.returning ]


	def isRunningState(self) -> bool:
		"""	Check whether the script is running.
		
			Return:
				True if the script is running.
		"""
		return self.value in [ self.running, self.returning ]


@dataclass
class PCall():
	"""	A dataclass that holds call-specific attributes.
	"""
	name:str						= None
	"""	Function name. """
	arguments:dict[str, SSymbol]	= field(default_factory = dict)
	"""	Dictionary of arguments (name -> `SSymbol`) for a call. """
	variables:dict[str,SSymbol]		= field(default_factory = dict)
	"""	Dictionary of variables (name -> `SSymbol`) for a call. """


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


# Define type for list of SSymbols
SSymbolsList = list[SSymbol]
"""	Type definition for a list of `SSymbol` objects. """


PFuncCallable = Callable[['PContext'], 'PContext']
"""	Function callback for pre, post and error functions.
"""


PSymbolCallable = Callable[['PContext', SSymbol], 'PContext']
"""	Signature of a symbol callable. The callbacks are 
	called with a `PContext` object	and is supposed to return
	it again, updated with a return value, or *None* in case of an error.
"""


PSymbolDict = dict[str, Union[PSymbolCallable, SSymbol]]
"""	Dictionary of function callbacks for commands. 
"""


# PErrorState = namedtuple('PErrorState', [ 'error', 'message', 'expression', 'exception' ])
PErrorState = NamedTuple('PErrorState', [ ('error', PError), 
										  ('message', str), 
										  ('expression', Optional[SSymbol]), 
										  ('exception', Optional[Exception]) ])
"""	Named tuple that represents an error state. 

	It contains the error code, the error message, the `SSymbol` expression that caused the error,
	and an (optional) exception.
"""


PLogCallable = Callable[['PContext', str], None]
"""	Function callback for normal log functions.
"""


PErrorLogCallable = Callable[['PContext', str, Exception], None]
"""	Function callback for error log functions.
"""


PMatchCallable = Callable[['PContext', str, str], bool]
"""	Signature of a match function callable.

	It will get called with the current `PContext` instance,
	a regular expression, and the string to check. It must return
	a boolean value that indicates the result of the match.
"""


FunctionDefinition = Tuple[list[str], SSymbol]
"""	A data type that defines a *defun* function definition. The first tupple
	element is a list of argument names, and the second element is an `SSymbol`
	that is executed as the function body.
"""

