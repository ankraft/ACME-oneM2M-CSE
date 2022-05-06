#
#	TextTools.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various helpers for working with strings and texts
#

import re
commentPattern = r'(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*$|#[^\r\n]*$)'	# recognized escaped comments
commentRegex = re.compile(commentPattern, re.MULTILINE|re.DOTALL)

def removeCommentsFromJSON(data:str) -> str:
	"""	This WILL remove:
			/* multi-line comments */
			// single-line comments
			# single-line comments
		
		Will NOT remove:
			String var1 = "this is /* not a comment. */";
			char *var2 = "this is // not a comment, either.";
			url = 'http://not.comment.com';
	"""
	def _replacer(match):	# type: ignore
		# if the 2nd group (capturing comments) is not None,
		# it means we have captured a non-quoted (real) comment string.
		if match.group(2):
			return '' # so we will return empty to remove the comment
		else: # otherwise, we will return the 1st group
			return match.group(1) # captured quoted-string
	return commentRegex.sub(_replacer, data)


def toHex(bts:bytes, toBinary:bool=False, withLength:bool=False) -> str:
	"""	Print bts as hex output, similar to the 'od' command.
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



def simpleMatch(st:str, pattern:str, star:str='*') -> bool:
	"""	Simple string match function. 

		This class supports the following expression operators:
	
		- '?' : any single character
		- '*' : zero or more characters
		- '+' : one or more characters
		- '\\' : Escape an expression operator

		Examples: 
			"hello" - "h?llo" -> True
	 		"hello" - "h?lo" -> False
	 		"hello" - "h*lo" -> True
			"hello" - "h*" -> True
			"hello" - "*lo" -> True
			"hello" - "*l?" -> True

		Parameter:
			- st : string to test
			- pattern : the pattern string
			- star : optionally specify a different character as the star character
	"""

	def _simpleMatchStar(st:str, pattern:str) -> bool:
		""" Recursively eat up a string when the pattern is a star at the beginning
			or middle of a pattern.
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

			# Match exactly one character, if there is one left
			if p == '?':
				if stIndex >= stLen:
					return False
				continue
			
			# Match zero or more characters
			if p == star:
				patternIndex += 1
				if patternIndex == patternLen:	# * is the last char in the pattern: this is a match
					return True
				return _simpleMatchStar(st[stIndex:], pattern[patternIndex:])	# Match recursively the remainder of the string

			if p == '+':
				patternIndex += 1
				if patternIndex == patternLen and len(st[stIndex:]) > 0:	# + is the last char in the pattern and there is enough string remaining: this is a match
					return True
				return _simpleMatchPlus(st[stIndex:], pattern[patternIndex:])	# Match recursively the remainder of the string

			# Literal match with the following character
			if p == '\\':
				patternIndex += 1
				p = pattern[patternIndex]
				# Fall-through
			
			# Literall match 
			if stIndex < stLen:
				if p != st[stIndex]:
					return False
		
		# End of matches
		return stIndex == stLen-1
	
	return _simpleMatch(st, pattern)
