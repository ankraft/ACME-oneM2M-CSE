#
#	TextTools.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various helpers for working with strings and texts
#

""" Utility functions for strings, JSON, and texts.
"""

from typing import Optional, Any, Dict, Union, Callable, List

import base64, binascii, re, json, unicodedata

_commentRegex = re.compile(r'(\".*?(?<!\\)\".*?(?<!\\))|(/\*.*?\*/|//[^\r\n]*$|#[^\r\n]*$|;;[^\r\n]*$)',
						   re.MULTILINE|re.DOTALL)
"""	Compiled regex expression of recognize comments. """

def removeCommentsFromJSON(data:str) -> str:
	r"""	Remove comments from JSON string input.

		This will remove:

		- \/\* multi-line comments \*\/
		- \// single-line comments
		- \# single-line comments
		- ;; single-line comments
		
		It will **NOT** remove:
		
		- String var1 = "this is \/\* not a comment. \*\/";
		- char \*var2 = "this is \/\/ not a comment, either.";
		- url = 'http://not.comment.com';

		Args:
			data: JSON string.
		Return:
			JSON string without comments.
	"""
	def _replacer(match):	# type: ignore
		# if the 2nd group (capturing comments) is not None,
		# it means we have captured a non-quoted (real) comment string.
		if match.group(2):
			return '' # so we will return empty to remove the comment
		else: # otherwise, we will return the 1st group
			return match.group(1) # captured quoted-string
	return _commentRegex.sub(_replacer, data)


def flattenJSON(data:Union[str, dict]) -> str:
	"""	Flatten a JSON string or dictionary.

		Args:
			data: The JSON string or as a dictionary.
		
		Return:
			The flattened JSON string.
	"""
	if isinstance(data, dict):
		return json.dumps(data) # default of dumps flattens the JSON
	return ' '.join([ l.strip() for l in data.split()])	# remove all whitespace


def parseJSONDecodingError(e:json.JSONDecodeError) -> str:
	"""	Parse a JSON decoding error and return a readable error message including the error location.

		Args:
			e: The JSON decoding error.

		Return:
			A readable error message.
	"""
	start, stop = max(0, e.pos - 20), e.pos + 20
	snippet = e.doc[start:stop].replace('\n', ' ')
	errorline = f'{"... " if start else ""}{snippet}{" ..." if stop < len(e.doc) else ""}'
	errorline += f'\n{("^".rjust(21 if not start else 25))}'
	return errorline


def commentJson(data:Union[str, dict], 
				explanations:Dict[str,str], 
				getAttributeValueName:Optional[Callable] = lambda k, v: '',
				width:Optional[int] = None) -> str:
	"""	Add explanations for JSON attributes as comments to the end of the line.

		Args:
			data: The JSON string or as a dictionary.
			explanations: A dictionary with the explanations. The keys must match the JSON keys.
			getAttributeValueName: A function that returns the named value of an attribute. 
			width: Optional width of the output. If greater then the comment is put above the line.
		
		Return:
			The JSON string with comments.
	"""

	if isinstance(data, dict):
		data = json.dumps(data, indent=2, sort_keys=True)

	# find longest line
	maxLineLength = 0
	for line in data.splitlines():
		if len(line) > maxLineLength:
			maxLineLength = len(line)
	
	# Add comments to each line
	lines = []
	_valueStripChars = ', []{}"'
	previousKey:Optional[str] = None
	key:str = ''
	maxLength:int = 0
	for line in data.splitlines():
		# Find the key
		if len(_sp := re.split(r':(?=\ )', line.strip())) == 1:
			if key:
				previousKey = key
				key = ''
			value = _sp[0].strip(_valueStripChars)
			value = getAttributeValueName(previousKey, value) if value else ''
		else:
			previousKey = None
			key = _sp[0].strip('"')
			value = _sp[1].strip(_valueStripChars)
			value = getAttributeValueName(key, value) if value else ''

		if key and key in explanations:
			lines.append(f'// {explanations[key]}{(": " + value) if value else ""}')
			lines.append(line)
			_m = len(lines[-2]) + maxLineLength
			maxLength = _m if _m > maxLength else maxLength

	
		elif previousKey and value: # when the value is on the next line, w/o a key
			lines.append(f'// {value}')
			lines.append(line)
			_m = len(lines[-2]) + maxLineLength
			maxLength = _m if _m > maxLength else maxLength
	
		else:
			lines.append('') # comment
			lines.append(line)
			maxLength = maxLineLength if maxLineLength > maxLength else maxLength

	# Build the result depending on the width of lines and comments
	maxLength += 2 	# Add 2 spaces for the comment
	result:List[str] = []
	for comment, line in zip(lines[0::2], lines[1::2]):
		if comment == '':	# skip empty comments
			result.append(line)
		else:
			if width is not None and maxLength > width:	# Put comment above line
				result.append(f'{" " * (len(line) - len(line.lstrip()))}{comment}')
				result.append(line)
			else:
				result.append(f'{line.ljust(maxLineLength)}  {comment}')

	return '\n'.join(result)
	
	

_decimalMatch = re.compile(r'{(\d+)}')
"""	Compiled regex expression of recognize decimal numbers in a string. """

def findXPath(dct:Dict[str, Any], key:str, default:Optional[Any] = None) -> Optional[Any]:
	""" Find a structured *key* in the dictionary *dct*. If *key* does not exists then
		*default* is returned.

		- It is possible to address a specific element in a list. This is done be
			specifying the element as "{n}".

		Example: 
			findXPath(resource, 'm2m:cin/{1}/lbl/{0}')

		- If an element is specified as "{}" then all elements in that list are returned in
			a list.

		Example: 
			findXPath(resource, 'm2m:cin/{1}/lbl/{}') or findXPath(input, 'm2m:cnt/m2m:cin/{}/rn')

		- If an element is specified as "{*}" and is targeting a dictionary then a single unknown key is
			skipped in the path. This can be used to skip, for example, unknown first elements in a structure. 
			This is similar but not the same as "{0}" that works on lists.

		Example: 
			findXPath(resource, '{*}/rn') 
		
		Args:
			dct: Dictionary to search.
			key: Key with path to an attribute.
			default: Optional return value if *key* is not found in *dct*
		
		Return:
			Any found value for the key path, or *None* resp. the provided *default* value.
	"""

	if not key or not dct:
		return default
	if key in dct:
		return dct[key]

	paths = key.split("/")
	data:Any = dct
	for i in range(0,len(paths)):
		if not data or not (pathElement := paths[i]) : # if empty of key not in dict
			return default
		elif (m := _decimalMatch.search(pathElement)) is not None:	# Match array index {i}
			idx = int(m.group(1))
			if not isinstance(data, (list,dict)) or idx >= len(data):	# Check idx within range of list
				return default
			if isinstance(data, dict):
				data = data[list(data)[i]]
			else:
				data = data[idx]

		elif pathElement == '{}':	# Match an array in general
			if not isinstance(data, (list,dict)):	# not a list, return the default
				return default
			if i == len(paths)-1:	# if this is the last element and it is a list then return the data
				return data
			return [ findXPath(d, '/'.join(paths[i+1:]), default) for d in data  ]	# recursively build an array with remnainder of the selector

		elif pathElement == '{*}':
			if isinstance(data, dict):
				if keys := list(data.keys()):
					data = data[keys[0]]
				else:
					return default
			else:
				return default

		# Only now test whether this is an unknown path element
		elif pathElement not in data:	# if key not in dict
			return default
		else:
			data = data[pathElement]	# found data for the next level down
	return data



def setXPath(dct:Dict[str, Any], 
			 key:str, 
			 value:Optional[Any] = None, 
			 overwrite:Optional[bool] = True, 
			 delete:Optional[bool] = False) -> bool:
	"""	Set a structured *key* and *value* in the dictionary *dict*.

		Create the attribute if necessary, and observe the *overwrite* option (True overwrites an
		existing key/value).

		When the *delete* argument is set to *True* then the *key* attribute is deleted from the dictionary.

		Examples:
			setXPath(aDict, 'a/b/c', 'aValue)

			setXPath(aDict, 'a/{2}/c', 'aValue)

		Args:
			dct: A dictionary in which to set or add the *key* and *value*.
			key: The attribute's name to set in *dct*. This could by a path in *dct*, where the separator is a slash character (/). To address an element in a list, one can use the *{n}* operator in the path.
			value: The value to set for the attribute. Could be left out when deleting an attribute or value.
			overwrite: If True that overwrite an already existing value, otherwise skip.
			delete: If True then remove the atribute or list attribute *key* from the dictionary.
		
		Retun:
			Boolean indicating the success of the operation.
	"""

	paths = key.split("/")
	ln1 = len(paths)-1
	data = dct
	if ln1 > 0:	# Small optimization. don't check if there is no extended path
		for i in range(0, ln1):
			_p = paths[i]
			if isinstance(data, list):
				if (m := _decimalMatch.search(_p)) is not None:
					data = data[int(m.group(1))]
			else:
				if _p not in data:
					data[_p] = {}
				data = data[_p]
	if isinstance(data, list):
		if (m := _decimalMatch.search(paths[ln1])) is not None:
			idx = int(m.group(1))
			if not overwrite and idx < len(data): # test overwrite first, it's faster
				return True # don't overwrite
			if delete :
				if idx < len(data):
					del data[idx]
				return True
			else:
				data[idx] = value
			return True
		return False
	else:
		if not overwrite and paths[ln1] in data: # test overwrite first, it's faster
			return True # don't overwrite
		if delete:
			del data[paths[ln1]]
			return True
		data[paths[ln1]] = value
	return True


def isNumber(string:Any) -> bool:
	"""	Check whether a string contains a convertible number. This could be an integer or a float.
	
		Args:
			string: The string or object to check.
			
		Return:
			Boolean indicating the result of the test.
	"""
	if isinstance(string, bool):
		return False
	try:
		float(string)
	except:
		return False
	return True



_soundexReplacements = (
		('BFPV', '1'),
		('CGJKQSXZ', '2'),
		('DT', '3'),
		('L', '4'),
		('MN', '5'),
		('R', '6'),
	)
"""	Replacement characters for the soundex algorithm. """

def soundex(s:str, maxCount:Optional[int] = 4) -> str:
	"""	Convert a string to a Soundex value.

		Args:
			s: The string to convert.

		Return:
			The Soundex value as a string.
	"""

	if not s:
		return ''

	s = unicodedata.normalize('NFKD', s).upper()

	result = [s[0]]
	count = 1

	# find would-be replacement for first character
	for lset, sub in _soundexReplacements:
		if s[0] in lset:
			last = sub
			break
	else:
		last = None

	for ch in s[1:]:
		for lset, sub in _soundexReplacements:
			if ch in lset:
				if sub != last:
					result.append(sub)
					count += 1
				last = sub
				break
		else:
			if ch != 'H' and ch != 'W':
				# leave last alone if middle letter is H or W
				last = None
		if count == maxCount:
			break

	result += '0' * (4 - count)
	return ''.join(result)


def soundsLike(s1:str, s2:str, maxCount:Optional[int] = 4) -> bool:
	"""	Compare two strings using the soundex algorithm.

		Args:
			s1: First string to compare.
			s2: Second string to compare.
			maxCount: Maximum number of soundex result characters to compare.
		
		Return:
			Boolean indicating the result of the comparison.
	"""
	# Remove 0 characters from the soundex result because they indicate a too short string
	_s1 = soundex(s1, maxCount).replace('0', '')
	_s2 = soundex(s2, maxCount).replace('0', '')

	# Only take the smaller number of characters of the soundex result into account
	_l = min(len(_s1), len(_s2))
	return _s1[:_l] == _s2[:_l]	

	return soundex(s1) == soundex(s2)


def toHex(bts:bytes, toBinary:Optional[bool] = False, withLength:Optional[bool] = False) -> str:
	"""	Print a byte string as hex output, similar to the "od" command.

		Args:
			bts: Byte string to print.
			toBinary: Print bytes as bit patterns.
			withLength: Additionally print length.
		
		Return:
			Formatted string with the output.
	"""
	if not bts or (len(bts) == 0 and not withLength): return ''
	result = ''
	n = 0
	b = bts[n:n+16]

	while b and len(b) > 0:

		if toBinary:
			s1 = ' '.join([f'{i:08b}' for i in b])
			s1 = f'{s1[0:71]} {s1[71:]}'
			width = 144
		else:
			s1 = ' '.join([f'{i:02x}' for i in b])
			s1 = f'{s1[0:23]} {s1[23:]}'
			width = 48

		s2 = ''.join([chr(i) if 32 <= i <= 127 else '.' for i in b])
		s2 = f'{s2[0:8]} {s2[8:]}'
		result += f'0x{n:08x}  {s1:<{width}}  | {s2}\n'

		n += 16
		b = bts[n:n+16]
	result += f'0x{len(bts):08x}'

	return result


def isBase64(value:str) -> bool:
	"""	Validate that a value is in base64 encoded format.
	
		Args:
			value: The value to test.

		Return:
			Boolean indicating the test result.
	"""
	try:
		base64.b64decode(value, validate = True)
	except binascii.Error as e:
		return False
	return True

def limitLines(text:str, maxLines:int, cont:str = '...') -> str:
	"""	Limit the number of lines and the length of lines in a text.

		Args:
			text: The text to limit.
			maxLines: The maximum number of lines.
			cont: The continuation string.
		
		Return:
			The limited text.
	"""
	lines = text.splitlines()
	if (orgLen := len(lines)) > maxLines:
		lines = lines[:maxLines]
		if orgLen > maxLines and cont:
			lines.append(cont)
		return '\n'.join(lines)
	return text

def simpleMatch(st:str, pattern:str, star:Optional[str] = '*', ignoreCase:bool = False) -> bool:
	r"""	Simple string match function. 

		This class supports the following expression operators:
	
		- '?' : any single character
		- '*' : zero or more characters
		- '+' : one or more characters
		- '\\' : Escape an expression operator

		A *pattern* must always match the full string *st*. This means that the
		pattern is implicit "^<pattern>$".

		Examples:
			"hello" - "h?llo" -> True
			
			"hello" - "h?lo" -> False

			"hello" - "h\*lo" -> True

			"hello" - "h\*" -> True  

			"hello" - "\*lo" -> True  

			"hello" - "\*l?" -> True  

		Args:
			st: string to test
			pattern: the pattern string
			star: optionally specify a different character as the star character
			ignoreCase: ignore case in the comparison
		
		Return:
			Boolean indicating a match.
	"""

	def _simpleMatchStar(st:str, pattern:str) -> bool:
		""" Recursively eat up a string when the pattern is a star at the beginning
			or middle of a pattern.

			Args:
				st: Input string.
				pattern: Match pattern.
			
			Return:
				*True* if there is a match.
		"""
		stLen	= len(st)
		stIndex	= 0
		while not _simpleMatch(st[stIndex:], pattern):
			stIndex += 1
			if stIndex >= stLen:
				return False
		return True
	

	def _simpleMatchPlus(st:str, pattern:str) -> bool:
		""" Recursively eat up a string when the pattern is a plus at the beginning
			or middle of a pattern.

			Args:
				st: Input string.
				pattern: Match pattern.
			
			Return:
				*True* if there is a match.
		"""
		stLen	= len(st)
		stIndex	= 1
		if len(st) == 0:
			return False
		while not _simpleMatch(st[stIndex:], pattern):
			stIndex += 1
			if stIndex >= stLen:
				return False
		return True


	def _simpleMatch(st:str, pattern:str) -> bool:
		""" Recursively eat up a string for a match pattern.

			Args:
				st: Input string.
				pattern: Match pattern.
			
			Return:
				*True* if there is a match.
		"""
		last:int		= 0
		matched:bool	= False
		reverse:bool	= False

		if st is None or pattern is None:
			return False
			
		stLen			= len(st)
		patternLen 		= len(pattern)

		# We later increment these indexes first in the loop below, therefore they need to be initialized with -1
		stIndex			= -1
		patternIndex 	= -1

		while patternIndex < patternLen-1:

			stIndex 		+= 1
			patternIndex 	+= 1
			p 				= pattern[patternIndex]

			if stIndex > stLen:
				return False

			match p:
				# Match exactly one character, if there is one left
				case '?':
					if stIndex >= stLen:
						return False
					continue

				# Match zero or more characters
				case p if p == star:
					patternIndex += 1
					if patternIndex == patternLen:	# * is the last char in the pattern: this is a match
						return True
					return _simpleMatchStar(st[stIndex:], pattern[patternIndex:])	# Match recursively the remainder of the string
				
				# Match one or more characters
				case '+':
					patternIndex += 1
					if patternIndex == patternLen and len(st[stIndex:]) > 0:	# + is the last char in the pattern and there is enough string remaining: this is a match
						return True
					return _simpleMatchPlus(st[stIndex:], pattern[patternIndex:])	# Match recursively the remainder of the string

				# Literal match with the following character
				case '\\':
					patternIndex += 1
					p = pattern[patternIndex]
					# Fall-through !

			# Literall match. Return False if a single character does not match
			if stIndex < stLen:
				match ignoreCase:
					case True:
						if p.casefold() != st[stIndex].casefold():
							return False
					case False:
						if p != st[stIndex]:
							return False

		# End of matches
		return stIndex == stLen-1
	
	return _simpleMatch(st, pattern)
