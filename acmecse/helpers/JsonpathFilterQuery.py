#
#	jsonpathFilterQuery.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing JSON-path filter queries for oneM2M contentFilterQuery
#

"""	Managing JSON-path filter queries for oneM2M contentFilterQuery filterCriteria. 

	Implements the 'JSON-path' contentFilterSyntax for oneM2M contentFilterQuery
	filterCriteria, as specified in Annex J.2 of TS-0001 ("Syntaxes for content
	based discovery of <contentInstance>").

	The following syntax rules are supported:

	- '$' refers to the entire target data.
	- '[n]' refers to the n-th member of a JSON array.
	- '.name' (dot operator followed by a name) refers to a member of a JSON object.
	- A name MUST be quoted with "'" (single quote) when it contains any of: '$', '.', ' ' (space), '[', ']', '{', '}'.
	- A single space character must separate a reserved keyword from the surrounding query string components.
	- Reserved keywords: EQ, NE, GT, LT, GE, LE, MATCH, AND, OR.

	The following assumptions are made in the implementation, since the spec does not provide a 
	complete grammar or examples:

	- AND and OR are evaluated strictly left-to-right, with no precedence between them.
	- MATCH is implemented as a case-SENSITIVE substring test.
	- The query is evaluated once per <contentInstance> (CIN) resource.
	- The implicit root '$' of the path expression is always the CIN's parsed 'con' attribute value (not some larger document).
	- The overall result of evaluating a filterCriteria query against one CIN is a boolean: match (include the CIN in the result set) or no match.
	- If a path expression does not resolve (missing object member, array index out of range, 
		indexing into a scalar, etc.), the clause evaluates to "no match" (False) rather than raising an error, for
		every keyword. This makes filterCriteria evaluation robust against heterogeneous CON payloads.
	- GT/LT/GE/LE require BOTH the resolved value and the literal to be numbers (int or float); 
		a type mismatch evaluates to False rather than raising, consistent with A5's "be permissive, 
		don't except" stance. EQ/NE compare equal types only (a number is never == to its string 
		representation); MATCH requires the resolved value to be a string.
	- Literal values (the right-hand side of a clause) are delimited asfollows:
		- A STRING literal is surrounded by DOUBLE quotes ("..."), and is escaped exactly like a JSON string. Decoding is delegated to *json.loads* so the escaping behaviour is JSON's by construction.
		- A NUMBER literal is a bare, unquoted token parsed as int then float (e.g. 21, 21.5).

	Examples of valid filterCriteria queries:
		- ``$.temperature EQ 21``
		- ``$.temperature GT 21 AND $.humidity LT 50``
		- ``$.sensor.values[2] MATCH "abc"``
		- ``$.sensor.'a.b'[0] NE 42 OR $.sensor.'a b' EQ "hello world"``
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

COMBINATOR_PRECEDENCE_AND_BINDS_TIGHTER = False
""" If True, AND binds more tightly than OR in filterCriteria evaluation."""

class Keyword(str, Enum):
	"""	The reserved keywords of the J.2 query syntax.
	"""
	# Subclasses str so that members compare equal to their textual value (Keyword.EQ == 'EQ'), 
	# which keeps tokenizer text comparisons and match/case patterns straightforward. 
	# (str, Enum) is used rather than enum.StrEnum to remain compatible with Python 3.10; StrEnum is 3.11+.

	EQ = 'EQ'
	"""	Equal comparison keyword. """
	NE = 'NE'
	"""	Not equal comparison keyword. """
	GT = 'GT'
	"""	Greater than comparison keyword. """
	LT = 'LT'
	"""	Less than comparison keyword. """
	GE = 'GE'
	"""	Greater than or equal comparison keyword. """
	LE = 'LE'
	"""	Less than or equal comparison keyword. """
	MATCH = 'MATCH'
	"""	String match comparison keyword. """
	AND = 'AND'
	"""	Logical AND keyword. """
	OR = 'OR'
	"""	Logical OR keyword. """


COMPARISON_KEYWORDS = (
	Keyword.EQ, Keyword.NE, Keyword.GT, Keyword.LT,
	Keyword.GE, Keyword.LE, Keyword.MATCH,
)
""" The set of keywords that are used for comparison in a single clause of a filterCriteria query."""

COMBINATOR_KEYWORDS = (Keyword.AND, Keyword.OR)
""" The set of keywords that are used to combine clauses in a filterCriteria query."""

_SPECIAL_CHARS = set('$. []{}')
""" The set of characters that force quoting of a name or literal per the spec rule."""


class FilterQuerySyntaxError(ValueError):
	"""	Raised when a filterCriteria query string cannot be parsed. """


class TokenKind(Enum):
	"""	Lexical category of a token produced by the tokenizer. """
	PATH = 'PATH'
	""" A path expression token, e.g. "$.foo[2].bar" or "$.'a.b'[0]". """
	KEYWORD = 'KEYWORD'
	""" A reserved keyword token, e.g. EQ, NE, GT, LT, GE, LE, MATCH, AND, OR. """
	LITERAL = 'LITERAL'
	""" A literal value token, e.g. a number or a double-quoted string. """


class StepKind(Enum):
	"""	Kind of a single step in a path expression. """
	MEMBER = 'member'
	""" A member-name access step, e.g. ".foo" or ".'a.b'". """
	INDEX = 'index'
	""" An array index access step, e.g. "[0]"."""


#
#	Tokenizer
#

@dataclass
class Token:
	"""	A single token produced by the tokenizer. """
	kind: TokenKind
	""" The kind of token: PATH, KEYWORD, or LITERAL. """
	text: str
	"""	raw text as it appeared in the query."""
	value: Any = None 
	""" for LITERAL tokens, the parsed Python value. """


def _splitOnSpaces(query: str) -> List[str]:
	"""	Splits the raw query string into whitespace-delimited components, while keeping quoted spans
	 	intact. 
		
		Two independent quote contexts are recognised:

		- single-quoted spans ('...') protect spaces inside path member NAMES;
		- double-quoted spans ("...") protect spaces inside string VALUE literals, 
		  using JSON escaping, so a backslash escapes the following character and 
		  an escaped '"' does not close the span.

		A space outside of any quoted span is a component separator. An
		unterminated span of either kind raises `FilterQuerySyntaxError`.

		Args:
			query: The raw filterCriteria query string.

		Returns:
			A list of raw components (tokens) of the query string, with quotes preserved.

		Raises:
			FilterQuerySyntaxError: If a quoted span is unterminated.
	"""
	tokens: List[str] = []
	current = []
	quoteChar: Optional[str] = None   # None, "'" or '"' - the open span kind
	i = 0
	n = len(query)
	while i < n:
		ch = query[i]
		if quoteChar == '"':
			# Inside a JSON-style double-quoted value: honour backslash
			# escapes so that an escaped quote does not end the span.
			current.append(ch)
			if ch == '\\' and i + 1 < n:
				current.append(query[i + 1])
				i += 2
				continue
			if ch == '"':
				quoteChar = None
			i += 1
			continue
		if quoteChar == "'":
			# Inside a single-quoted name: no escape mechanism (the spec
			# defines none); the next single quote closes the span.
			current.append(ch)
			if ch == "'":
				quoteChar = None
			i += 1
			continue
		# Not currently inside any quoted span.
		match ch:
			case "'" | '"':
				quoteChar = ch
				current.append(ch)
			case ' ':
				if current:
					tokens.append(''.join(current))
					current = []
			case _:
				current.append(ch)
		i += 1
	if quoteChar is not None:
		raise FilterQuerySyntaxError(f'Unterminated {quoteChar}-quoted span in query: {query!r}')
	if current:
		tokens.append(''.join(current))
	return tokens


def _unquote(rawToken: str) -> str:
	"""	Strips a single layer of surrounding single quotes, if present.

		Used for path member NAMES (single-quoted per the spec). String VALUE
		literals use double quotes and are handled by `_parseLiteralValue` via
		json.loads, not here.

		Args:
			rawToken: The raw token text, possibly surrounded by single quotes.

		Returns:
			The token text with surrounding single quotes removed, if they were present.
	"""
	if len(rawToken) >= 2 and rawToken[0] == "'" and rawToken[-1] == "'":
		return rawToken[1:-1]
	return rawToken


def _parseLiteralValue(rawToken: str) -> Any:
	"""	Parses a literal's raw text into a Python value.

		Args:
			rawToken: The raw token text, possibly surrounded by double quotes.
		
		Returns:
			The parsed Python value: str, int, float, or the raw token text if it cannot be parsed.
		
		Raises:
			FilterQuerySyntaxError: If the token is a malformed double-quoted string literal.
	"""
	if len(rawToken) >= 2 and rawToken[0] == '"' and rawToken[-1] == '"':
		try:
			return json.loads(rawToken)
		except json.JSONDecodeError as exc:
			raise FilterQuerySyntaxError(f'Malformed double-quoted string literal: {rawToken!r}') from exc
	try:
		return int(rawToken)
	except ValueError:
		pass
	try:
		return float(rawToken)
	except ValueError:
		pass
	return rawToken


def tokenizeFilterQuery(query: str) -> List[Token]:
	"""	Tokenizes a full filterCriteria query string of the form:
		``pathExpr KEYWORD literal (AND|OR pathExpr KEYWORD literal)*```

		into a flat list of Token objects.

		Args:
			query: The raw filterCriteria query string.
		
		Returns:
			A list of Token objects representing the components of the query string.
	"""
	rawParts = _splitOnSpaces(query.strip())
	tokens: List[Token] = []
	keywordValues = frozenset(kw.value for kw in Keyword)
	for raw in rawParts:
		isQuoted = raw.startswith("'") or raw.startswith('"')
		if raw.upper() in keywordValues and not isQuoted:
			tokens.append(Token(kind=TokenKind.KEYWORD, text=raw.upper()))
		elif raw.startswith('$') or raw.startswith('.'):
			tokens.append(Token(kind=TokenKind.PATH, text=raw))
		else:
			tokens.append(Token(kind=TokenKind.LITERAL, text=raw, value=_parseLiteralValue(raw)))
	return tokens

#
#	Path expression parsing ($.foo[2].bar style addressing)
#

@dataclass(frozen=True)
class PathStep:
	"""	A single step in a path expression: either a member-name access	or an array index access. """
	kind: StepKind
	""" The kind of step: MEMBER or INDEX. """
	name: Optional[str] = None
	""" For MEMBER steps, the member name to access. None for INDEX steps. """
	index: Optional[int] = None
	""" For INDEX steps, the array index to access. None for MEMBER steps. """


def parsePathExpression(pathExpr: str) -> List[PathStep]:
	"""	Parses a oneM2M-style path expression (e.g. "$.sensor.values[2]" or	"$.'a.b'[0]") into a 
		list of PathStep objects.

		Grammar (per the spec's stated rules):
	
			| pathExpr := '$' step*  
			| step     := '.' name | '[' index ']'
			| name     := plainName | "'" quotedName "'"

			- plainName is read up to the next '.' or '[' (whichever comes first);
			- quotedName runs until the matching closing quote and may contain any character, including '.', '[', ']', '{', '}', and spaces.

		Args:
			pathExpr: The raw path expression string.

		Returns:
			A list of PathStep objects representing the steps in the path expression.

		Raises:
			FilterQuerySyntaxError: If the path expression is malformed.
	"""
	if not pathExpr.startswith('$'):
		raise FilterQuerySyntaxError(f"Path expression must start with '$': {pathExpr!r}")

	steps: List[PathStep] = []
	i = 1
	n = len(pathExpr)

	while i < n:
		ch = pathExpr[i]
		match ch:
			case '.':
				i += 1
				if i < n and pathExpr[i] == "'":
					# Quoted member name - run until the matching close quote.
					end = pathExpr.find("'", i + 1)
					if end == -1:
						raise FilterQuerySyntaxError(f'Unterminated quoted name in path: {pathExpr!r}')
					name = pathExpr[i + 1:end]
					steps.append(PathStep(kind=StepKind.MEMBER, name=name))
					i = end + 1
				else:
					# Plain member name - runs until next '.' or '['.
					start = i
					while i < n and pathExpr[i] not in '.[':
						i += 1
					name = pathExpr[start:i]
					if not name:
						raise FilterQuerySyntaxError(f'Empty member name in path: {pathExpr!r}')
					steps.append(PathStep(kind=StepKind.MEMBER, name=name))
			case '[':
				end = pathExpr.find(']', i + 1)
				if end == -1:
					raise FilterQuerySyntaxError(f"Unterminated '[' in path: {pathExpr!r}")
				indexText = pathExpr[i + 1:end]
				try:
					index = int(indexText)
				except ValueError as exc:
					raise FilterQuerySyntaxError(f'Non-integer array index {indexText!r} in path: {pathExpr!r}') from exc
				steps.append(PathStep(kind=StepKind.INDEX, index=index))
				i = end + 1
			case _:
				raise FilterQuerySyntaxError(f'Unexpected character {ch!r} at position {i} in path: {pathExpr!r}')

	return steps


_ABSENT = object()  
""" Internal sentinel. A path did not resolve to any value. """


def resolvePathValue(rootValue: Any, steps: List[PathStep]) -> Any:
	"""	Resolves a parsed path expression against rootValue (the CIN's already-JSON-parsed 'con' attribute). 
		Returns the resolved value, or the `_ABSENT` sentinel if any step cannot be applied.

		Args:
			rootValue: The root value to resolve the path against (the parsed 'con' attribute of a <contentInstance>).
			steps: The list of PathStep objects representing the parsed path expression.

		Returns:
			The resolved value if the path resolves successfully, or the `_ABSENT` sentinel if any step 
				cannot be applied (e.g., missing member, out-of-bounds index, type mismatch).
	"""

	current = rootValue
	for step in steps:
		match step.kind:
			case StepKind.MEMBER:
				if isinstance(current, dict) and step.name in current:
					current = current[step.name]
				else:
					return _ABSENT
			case StepKind.INDEX:
				if isinstance(current, list) and -len(current) <= step.index < len(current):
					current = current[step.index]
				else:
					return _ABSENT
			case _:  # pragma: no cover - defensive, kinds are fixed above
				return _ABSENT
	return current


#
#	Filter expression parsing
#

@dataclass(frozen=True)
class Clause:
	"""	A single clause in a filterCriteria query: a path expression, a comparison keyword, and a literal value. """
	pathSteps: List[PathStep]
	""" The parsed path expression steps. """
	keyword: Keyword          # one of the COMPARISON_KEYWORDS
	""" The comparison keyword for this clause (EQ, NE, GT, LT, GE, LE, MATCH). """
	literal: Any
	""" The literal value for this clause. """


@dataclass(frozen=True)
class FilterExpression:
	"""	A parsed filterCriteria query: a flat sequence of clauses joined by	AND / OR combinators 
		(one fewer combinator than there are clauses).
	"""
	clauses: List[Clause]
	""" The list of clauses in the filter expression. """
	combinators: List[Keyword]  # len == len(clauses) - 1, each AND or OR
	""" The list of combinators (AND/OR) in the filter expression. """


def parseFilterQuery(query: str) -> FilterExpression:
	"""	Parses a full filterCriteria query string into a FilterExpression object. 

		Args:
			query: The raw filterCriteria query string.

		Returns:
			A FilterExpression object representing the parsed query.

		Raises:
			FilterQuerySyntaxError: If the query string is malformed.
	"""
	tokens = tokenizeFilterQuery(query)

	clauses: List[Clause] = []
	combinators: List[Keyword] = []

	i = 0
	n = len(tokens)
	expectingClause = True

	while i < n:
		if expectingClause:
			if i + 2 >= n:
				raise FilterQuerySyntaxError(f'Incomplete clause near token {i} in query: {query!r}')
			pathTok, kwTok, litTok = tokens[i], tokens[i + 1], tokens[i + 2]
			if pathTok.kind is not TokenKind.PATH:
				raise FilterQuerySyntaxError(f'Expected a path expression, got {pathTok.text!r} in query: {query!r}')
			if kwTok.kind is not TokenKind.KEYWORD or Keyword(kwTok.text) not in COMPARISON_KEYWORDS:
				raise FilterQuerySyntaxError(f'Expected a comparison keyword (EQ/NE/GT/LT/GE/LE/MATCH), got {kwTok.text!r} in query: {query!r}')
			if litTok.kind is not TokenKind.LITERAL:
				raise FilterQuerySyntaxError(f'Expected a literal value, got {litTok.text!r} in query: {query!r}')
			clauses.append(Clause(pathSteps=parsePathExpression(pathTok.text),
						   keyword=Keyword(kwTok.text),
						   literal=litTok.value)
			)
			i += 3
			expectingClause = False
		else:
			combTok = tokens[i]
			if combTok.kind is not TokenKind.KEYWORD or Keyword(combTok.text) not in COMBINATOR_KEYWORDS:
				raise FilterQuerySyntaxError(f'Expected AND/OR, got {combTok.text!r} in query: {query!r}')
			combinators.append(Keyword(combTok.text))
			i += 1
			expectingClause = True

	if expectingClause:
		raise FilterQuerySyntaxError(f'Query ends with a dangling AND/OR: {query!r}')

	return FilterExpression(clauses=clauses, combinators=combinators)

# 
#	Predicate evaluation
#

def _isNumber(value: Any) -> bool:
	"""	Returns True if the value is an int or float (but not bool), False otherwise. 

		Args:
			value: The value to check.

		Returns:
			True if the value is an int or float (but not bool), False otherwise.
	"""
	return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluateClause(clause: Clause, rootValue: Any) -> bool:
	"""	Evaluates a single clause against rootValue (the parsed CON value).	

		Args:
			clause: The Clause object to evaluate.
			rootValue: The root value to resolve the path against (the parsed 'con' attribute of a <contentInstance>).

		Returns:
			True if the clause matches, False otherwise.

		Raises:
			FilterQuerySyntaxError: If the clause's keyword is unknown.
	"""
	resolved = resolvePathValue(rootValue, clause.pathSteps)

	if resolved is _ABSENT:
		return False

	kw = clause.keyword
	literal = clause.literal

	match kw:
		case Keyword.EQ:
			# Numbers and strings never compare equal across types (a number
			# is never EQ to its string representation), but int/float compare
			# numerically as usual (1 EQ 1.0 -> True).
			if _isNumber(resolved) != _isNumber(literal):
				return False
			return resolved == literal
		case Keyword.NE:
			if _isNumber(resolved) != _isNumber(literal):
				return True
			return resolved != literal
		case Keyword.GT | Keyword.LT | Keyword.GE | Keyword.LE:
			if not (_isNumber(resolved) and _isNumber(literal)):
				return False
			match kw:
				case Keyword.GT:
					return resolved > literal
				case Keyword.LT:
					return resolved < literal
				case Keyword.GE:
					return resolved >= literal
				case Keyword.LE:
					return resolved <= literal
		case Keyword.MATCH:
			if not isinstance(resolved, str) or not isinstance(literal, str):
				return False
			return literal in resolved
		case _:
			raise FilterQuerySyntaxError(f'Unknown comparison keyword: {kw!r}')  # pragma: no cover


def evaluateFilterExpression(expr: FilterExpression, conValue: Any) -> bool:
	"""	Evaluates a fully parsed FilterExpression against conValue (the	parsed JSON value of a
	 	CIN's 'con' attribute), returning True if the CIN should be included in the result set.

		Args:
			expr: The FilterExpression object to evaluate.
			conValue: The parsed JSON value of the CIN's 'con' attribute.

		Returns:
			True if the CIN matches the filter expression, False otherwise.
	"""
	if not expr.clauses:
		return True  # an empty filter matches everything (no clauses to fail)

	if not COMBINATOR_PRECEDENCE_AND_BINDS_TIGHTER:
		result = evaluateClause(expr.clauses[0], conValue)
		for comb, clause in zip(expr.combinators, expr.clauses[1:]):
			rhs = evaluateClause(clause, conValue)
			result = (result and rhs) if comb is Keyword.AND else (result or rhs)
		return result

	# Conventional precedence: AND binds tighter than OR. Clauses are
	# grouped into AND-chains, then those chains are OR'd together.
	orGroups: List[bool] = []
	currentAndResult = evaluateClause(expr.clauses[0], conValue)
	for comb, clause in zip(expr.combinators, expr.clauses[1:]):
		rhs = evaluateClause(clause, conValue)
		if comb is Keyword.AND:
			currentAndResult = currentAndResult and rhs
		else:  # OR - close out the current AND-chain, start a new one
			orGroups.append(currentAndResult)
			currentAndResult = rhs
	orGroups.append(currentAndResult)
	return any(orGroups)


#
#	Public convenience API
#

def matchesFilterQuery(query: str, conValue: Any) -> bool:
	"""	One-shot convenience function: parses *query* (a filterCriteria string)
	 	and evaluates it against *conValue* (the already-JSON-parsed value of a CIN's
		'con' attribute), returning True if the CIN matches and should be included in the result set.

		For repeated evaluation of the same query against many CIN resources, call 
		`parseFilterQuery` () once and reuse the FilterExpression with `evaluateFilterExpression` ()
		to avoid re-parsing on every resource.

		Args:
			query: The raw filterCriteria query string.
			conValue: The parsed JSON value of the CIN's 'con' attribute.

		Returns:
			True if the CIN matches the filter query, False otherwise.

		Raises:

	"""
	expr = parseFilterQuery(query)
	return evaluateFilterExpression(expr, conValue)