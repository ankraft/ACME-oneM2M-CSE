#
#	SExprParser.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.

from typing import Optional, cast
from decimal import Decimal, InvalidOperation
from .Types import SSymbol, SBooleanSymbol, SNumberSymbol, SStringSymbol, SSymbolQuoteSymbol, \
	SListCharSymbol, SJsonSymbol, SListQuoteSymbol, SListSymbol, \
	SType, SSymbolsList, SSymbolSymbol, SNilSymbol

class SExprParser(object):
	"""	Class that implements an S-Expression parser. """

	errorExpression:SSymbol = None
	"""	In case of an error this attribute contains the error expression. """

	def normalizeInput(self, input:str, allowBrackets:bool = False) -> SSymbolsList:
		"""	Parse an input string into a list of opening and closing parentheses, and
			atoms. Atoms include symbols, numbers and strings.

			The results excludes all whitespaces. Also, special escape characters 
			outside and inside of strings are handled. The escape character is backslash.

			Args:
				input: The input string.
				allowBrackets: Allow "[" and "]" for opening and closing lists as well.
			
			Return:
				A list of paranthesis and atoms.
		"""
		normalizedInput:SSymbolsList = []	# a list of normalized symbols
		currentSymbol = ''
		isEscaped = False
		inString = False
		jsonLevel = 0

		# prepare the list chars () or mappings for brackets if allowed
		if allowBrackets:
			listChars = '()[]'
			listCharsMapping = { 
				'(': '(',
				')': ')',
				'[': '(',
				']': ')',
			}
		else:
			listChars = '()'
			listCharsMapping = { 
				'(': '(',
				')': ')',
			}


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
				normalizedInput.append(SStringSymbol(currentSymbol[1:-1]))		# add to normalized list
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
					normalizedInput.append(SJsonSymbol(jsnString=currentSymbol))		# add to normalized list
					currentSymbol = ''
					jsonLevel = 0
				continue

			# spaces are separators
			if ch.isspace():
				if currentSymbolLen > 1:
					normalizedInput.append(SSymbolSymbol(currentSymbol[:-1]))
				currentSymbol = ''
				continue

			# detect parenthesis
			if ch in listChars:
				if currentSymbolLen > 1:
					normalizedInput.append(SSymbolSymbol(currentSymbol[:-1]))
				if allowBrackets and ch == '[':
					normalizedInput.append(SSymbolSymbol("'"))
				normalizedInput.append(SListCharSymbol(listCharsMapping[ch]))
				currentSymbol = ''
				continue

		return normalizedInput


	def ast(self, input:SSymbolsList|str, 
				  topLevel:bool = True, 
				  allowBrackets:bool = False,
				  parentSymbol:Optional[SSymbol] = None) -> SSymbolsList:
		""" Generate an abstract syntax tree (AST) from normalized input.

			The result is a list of elements. Each element is either an
			atom, a string, a number, or again a list of elements.

			Args:
				input: Either a string or a list of `SSymbol` elements. A string would internally be parsed to a list of `SSymbol` elements before further processing.
				topLevel: Indicating whether a parsed input is at the top level or a branch of a another AST.
				allowBrackets: Allow "[" and "]" for opening and closing lists as well.
				parentSymbol: The parent symbol of the current AST.
			
			Return:
				A list that represents the abstract syntax tree.
			
			Raises:
				ValueError: In case of a syntax error (usually missing opening or closing paranthesis).
		"""

		# Normalize if the input is a string
		if isinstance(input, str):
			input = self.normalizeInput(input, allowBrackets)

		_ast:SSymbolsList = []
		# Go through each element in the normalizedInput:
		# - if it is an open parenthesis, find matching parenthesis and make an recursive
		#   call for content in-between. Add the result as an element to the current list.
		# - if it is an atom, just add it to the current list.
		# At the end, return the current ast
		index = 0
		isQuote = False
		while index < len(input):
			symbol = input[index]
			symbol.parent = parentSymbol
			
			# A list may be prefixed with a single '. It is then traited as a plain list or symbol, and not executed
			if symbol.value == '\'':
				isQuote = True
				index += 1
				continue

			match symbol.type:
				case SType.tListBegin:
					startIndex = index + 1
					matchCtr = 1 # If 0, parenthesis has been matched.
					# Determine the matching closing paranthesis on the same level
					while matchCtr != 0:
						index += 1
						if index >= len(input):
							self.errorExpression = input	# type:ignore[assignment]
							raise ValueError(f'Invalid input: Unmatched opening parenthesis: {input[startIndex-1:]}')
						symbol = input[index]
						
						match symbol.type:
							case SType.tListBegin:
								matchCtr += 1
							case SType.tListEnd:
								matchCtr -= 1
							# ignore other types
				
					# Recursive call for the content in-between the paranthesis
					_s = SListQuoteSymbol(parent=parentSymbol) if isQuote else SListSymbol(parent=parentSymbol)
					_childAst = self.ast(input[startIndex:index], False, allowBrackets, parentSymbol=_s)
					match _s:
						case SListQuoteSymbol():
							_ast.append(_s.setLstQuote(_childAst))
						case SListSymbol():
							_ast.append(_s.setLst(_childAst))
				
				case SType.tListEnd:
					self.errorExpression = input	# type:ignore[assignment]
					raise ValueError(f'Invalid input: Unmatched closing parenthesis: {input[:index+1]}')
			
				case SType.tJson | SType.tString:
					_ast.append(symbol)

				case _:				
					try:
						_ast.append(SNumberSymbol(Decimal(symbol.value), parent = parentSymbol)) # type:ignore [arg-type]
					except InvalidOperation:
						match symbol.type:
							case SType.tSymbol if symbol.value in [ 'true', 'false' ]:
								_ast.append(SBooleanSymbol(symbol.value == 'true', parentSymbol))
							case SType.tSymbol if symbol.value == 'nil':
								_ast.append(SNilSymbol(parent=parentSymbol))
							case _:
								if (_str := cast(str, symbol.value)).startswith('\''):
									_ast.append(SSymbolQuoteSymbol(_str, parentSymbol))
								else:
									_ast.append(symbol)
			index += 1
			isQuote = False
		
		# If we are on the top level, *all* the symbols must be S-expressions, not stand-alone symbols
		if topLevel:
			for a in _ast:
				if a.type != SType.tList:
					raise ValueError(f'Invalid input: plain symbols are not allowed at top-level: {a}')

		return _ast
