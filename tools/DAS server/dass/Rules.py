#
#	Rules.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Access control rules for the DAS server
#
"""	Loads, watches, and evaluates the DAS's access control rule files.

	Rules live in a directory as YAML files: "_common.yaml" (applied to every
	CSE) plus one "<cseId>.yaml" file per CSE (the CSE-ID without its leading
	"/"). Each file has the shape:

		rules:
		  - match:
		      originator: "Csensor*"      # optional, glob pattern, default: match any
		      resourceID: "id-in/cnt-*"    # optional, glob pattern, default: match any
		      resourceType: [cnt, 4]       # optional, name or number, default: match any
		      operation: [R, U]            # optional, C/R/U/D/N/F, 1/2/4/8/16/32, or a combined
		                                   # bitmask (eg. 6 for R+U); default: match any
		    grant:
		      acor: ["Csensor*"]
		      acop: [R, U]                 # optional, defaults to match.operation

	Every rule whose "match" is satisfied contributes its "grant" block, as-is,
	to the result - matches are not merged together.
"""

import logging
from pathlib import Path
from fnmatch import fnmatch
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)


_COMMON_RULES_FILENAME = '_common.yaml'
""" The name of the rules file that applies to every CSE. """


_PERMISSIONS = {
	'C': 1,		# CREATE
	'R': 2,		# RETRIEVE
	'U': 4,		# UPDATE
	'D': 8,		# DELETE
	'N': 16,	# NOTIFY
	'F': 32,	# DISCOVERY ("Find")
}
""" oneM2M permission bits, addressed by a single, case-insensitive letter. """

_PERMISSION_VALUES = set(_PERMISSIONS.values())
""" The valid individual permission bit values, for validating a numeric operation/acop entry. """

_ALL_PERMISSIONS_MASK = sum(_PERMISSION_VALUES)
""" The combined mask of all defined permission bits (63), for validating a bitmask entry. """

_OPERATION_TO_PERMISSION = {
	1:  _PERMISSIONS['C'],	# CREATE
	2:  _PERMISSIONS['R'],	# RETRIEVE
	3:  _PERMISSIONS['U'],	# UPDATE
	4:  _PERMISSIONS['D'],	# DELETE
	5:  _PERMISSIONS['N'],	# NOTIFY
	-2: _PERMISSIONS['F'],	# DISCOVERY
}
""" Maps the incoming oneM2M request "Operation" code (TS-0004, as sent in dreq.op) to its
	corresponding permission bit from _PERMISSIONS. This is the WIRE-level request operation,
	not to be confused with the "operation"/"acop" rule-file syntax parsed by _parsePermission/
	_parseOperations above - that parses how a rule author writes permissions in YAML; this
	table translates what a request carries on the wire before it is compared against them. """


# A small, curated set of the most commonly relevant base resource type
# names. Numeric resourceType values always work regardless of this table.
_RESOURCE_TYPES = {
	'mixed': 0, 'acp': 1, 'ae': 2, 'cnt': 3, 'cin': 4, 'csebase': 5, 'cb': 5,
	'grp': 9, 'lcp': 10, 'mgmtobj': 13, 'nod': 14, 'pch': 15, 'csr': 16,
	'req': 17, 'sch': 18, 'sub': 23, 'smd': 24, 'fcnt': 28, 'ts': 29,
	'tsi': 30, 'dac': 34, 'crs': 48,
}
""" Resource type short names, addressed case-insensitively. """


def _parsePermission(value: Any) -> Optional[int]:
	""" Convert a single operation/permission entry to its permission bit - either a
		C/R/U/D/N/F letter (case-insensitive) or its numeric oneM2M permission value
		(1, 2, 4, 8, 16, or 32).

		Args:
			value: The letter or number to convert.
		Return:
			The permission bit, or *None* if *value* is not recognized.
	"""
	if isinstance(value, int):
		return value if value in _PERMISSION_VALUES else None
	if isinstance(value, str) and value.strip().isdigit():
		v = int(value.strip())
		return v if v in _PERMISSION_VALUES else None
	return _PERMISSIONS.get(str(value).upper())


def _decomposeBitmask(value: int) -> Optional[list[int]]:
	""" Decompose a combined oneM2M permission bitmask (eg. 6 for RETRIEVE + UPDATE -
		a common oneM2M convention) into its individual permission bits.

		Args:
			value: The bitmask to decompose.
		Return:
			A list of the individual permission bits set in *value*, or *None* if
			*value* is negative or contains a bit that isn't a defined permission.
	"""
	if value < 0 or (value & ~_ALL_PERMISSIONS_MASK):
		return None
	return [ p for p in _PERMISSION_VALUES if value & p ]


def _parseOperations(values: Any) -> Optional[list[int]]:
	""" Convert C/R/U/D/N/F letters and/or their numeric permission values to a list
		of permission bits. *values* is usually a list, but a single, bare entry is
		also accepted - including a combined bitmask number (eg. 6 for RETRIEVE +
		UPDATE), a common oneM2M convention.

		Args:
			values: A list of letters and/or numbers, a single letter/number, or *None*.
		Return:
			A list of permission bits, or *None* if *values* is *None*. Unrecognized
			entries are logged and skipped.
	"""
	if values is None:
		return None

	if not isinstance(values, list):
		if isinstance(values, str) and values.strip().isdigit():
			values = int(values.strip())
		if isinstance(values, int):
			if (decomposed := _decomposeBitmask(values)) is not None:
				return decomposed
			log.warning(f'Unknown operation/permission bitmask: "{values}". Ignoring.')
			return []
		values = [ values ]	# a single letter, eg. "R"

	result = []
	for v in values:
		if (p := _parsePermission(v)) is None:
			log.warning(f'Unknown operation/permission: "{v}". Ignoring.')
			continue
		result.append(p)
	return result


def operationToPermission(operation: Optional[int]) -> Optional[int]:
	""" Translate an incoming request's oneM2M "Operation" code (dreq.op on the wire) to the
		permission bit used internally by rules (see _PERMISSIONS).

		Args:
			operation: The oneM2M Operation code from the request (eg. 1=CREATE ... 5=NOTIFY,
				-2=DISCOVERY), or *None*.
		Return:
			The corresponding permission bit, or *None* if *operation* is *None* or not a
			recognized operation code. Passing *None* through is intentional: *_matches*
			already treats *operation=None* as "match only rules with no operation condition".
	"""
	if operation is None:
		return None
	if (permission := _OPERATION_TO_PERMISSION.get(operation)) is None:
		log.warning(f'Unknown/unrecognized request operation code: "{operation}". Treating as no-operation for rule matching.')
		return None
	return permission


def _parseResourceTypes(values: Any) -> Optional[list[int]]:
	""" Convert a list of resource type names or numbers to a list of type numbers.

		Args:
			values: A list of names and/or numbers, or *None*.
		Return:
			A list of resource type numbers, or *None* if *values* is *None*.
			Unrecognized entries are logged and skipped.
	"""
	if values is None:
		return None
	result = []
	for v in values:
		if isinstance(v, int):
			result.append(v)
		elif isinstance(v, str) and v.strip().lstrip('-').isdigit():
			result.append(int(v))
		elif isinstance(v, str) and (t := _RESOURCE_TYPES.get(v.strip().lower())) is not None:
			result.append(t)
		else:
			log.warning(f'Unknown resourceType: "{v}". Ignoring.')
	return result


def _normalizeRule(rawRule: dict, source: str) -> Optional[dict]:
	""" Validate and normalize one rule from a YAML file: parse the letter/name
		forms in "match" and "grant" into their numeric forms, once, so that
		matching a request against a rule is cheap.

		Args:
			rawRule: The rule as loaded from YAML.
			source: The file the rule came from, for log messages.
		Return:
			The normalized rule, or *None* if the rule is malformed.
	"""
	match = rawRule.get('match') or {}
	grant = rawRule.get('grant')

	if not grant or not grant.get('acor'):
		log.error(f'{source}: rule is missing a "grant.acor" - skipping rule: {rawRule}')
		return None

	operations = _parseOperations(match.get('operation'))

	if (acop := grant.get('acop')) is not None:
		acop = _parseOperations(acop)
		acopValue = 0
		for p in acop:
			acopValue |= p
	elif operations is not None:
		acopValue = 0
		for p in operations:
			acopValue |= p
	else:
		log.error(f'{source}: rule has neither "grant.acop" nor "match.operation" to derive it from - skipping rule: {rawRule}')
		return None

	grant = { **grant, 'acop': acopValue }

	return {
		'match': {
			'originator': match.get('originator'),
			'resourceID': match.get('resourceID'),
			'resourceType': _parseResourceTypes(match.get('resourceType')),
			'operation': operations,
		},
		'grant': grant,
	}


class Rules:
	""" Loads, watches, and evaluates the DAS's access control rule files. """

	def __init__(self, path: str) -> None:
		self.path = Path(path)
		""" Directory containing the rule files. """

		self._commonRules: list[dict] = []
		self._cseRules: dict[str, list[dict]] = {}
		self._mtimes: dict[str, float] = {}

		self.reload()


	def reload(self) -> None:
		""" (Re-)load every rule file in `path`. Each file is loaded independently:
			a broken file is logged and skipped, it does not affect the others.
		"""

		if not self.path.is_dir():
			log.warning(f'Rules directory not found: {self.path}. No access control rules are loaded.')
			self._commonRules = []
			self._cseRules = {}
			self._mtimes = {}
			return

		mtimes: dict[str, float] = {}
		commonRules: list[dict] = []
		cseRules: dict[str, list[dict]] = {}

		for filePath in sorted(self.path.glob('*.yaml')):
			mtimes[filePath.name] = filePath.stat().st_mtime
			rules = self._loadFile(filePath)
			if filePath.name == _COMMON_RULES_FILENAME:
				commonRules = rules
			else:
				cseRules[filePath.stem] = rules

		self._commonRules = commonRules
		self._cseRules = cseRules
		self._mtimes = mtimes

		log.info(f'Loaded {len(commonRules)} common rule(s) and rules for {len(cseRules)} CSE(s) from {self.path}')


	def reloadIfChanged(self) -> bool:
		""" Reload the rule files if any of them were added, removed, or modified
			since the last (re-)load.

			Return:
				*True* if a reload happened, *False* otherwise.
		"""

		if not self.path.is_dir():
			if self._mtimes:	# was present before, now it's gone
				self.reload()
				return True
			return False

		currentMtimes = { p.name: p.stat().st_mtime for p in self.path.glob('*.yaml') }
		if currentMtimes != self._mtimes:
			log.info('Rule files changed, reloading')
			self.reload()
			return True
		return False


	def _loadFile(self, filePath: Path) -> list[dict]:
		""" Load and normalize the rules from a single YAML file.

			Args:
				filePath: The file to load.
			Return:
				A list of normalized rules. Empty if the file is empty, missing
				a "rules" list, or fails to parse.
		"""
		try:
			with open(filePath, 'r') as f:
				content = yaml.safe_load(f)
		except (yaml.YAMLError, OSError) as e:
			log.error(f'Error reading rule file {filePath}: {e}. Skipping this file.')
			return []

		if not content:
			return []

		rawRules = content.get('rules') or []
		rules = []
		for rawRule in rawRules:
			if (rule := _normalizeRule(rawRule, str(filePath))) is not None:
				rules.append(rule)
		return rules


	def getAcrs(self, cseId: str, originator: Optional[str], resourceId: Optional[str],
					  resourceType: Optional[int], operation: Optional[int]) -> list[dict]:
		""" Return the "grant" block of every rule (common, plus the given CSE's own)
			whose "match" conditions are satisfied by the given request.

			Args:
				cseId: The CSE-ID the request is for (with or without a leading "/").
				originator: The originator to check.
				resourceId: The (structured) resource ID of the target resource.
				resourceType: The resource type of the target resource.
				operation: The requested operation, as the oneM2M request Operation code (eg.
					1=CREATE ... 5=NOTIFY, -2=DISCOVERY) - translated internally to a permission
					bit via operationToPermission() before matching.
			Return:
				A list of accessControlRule dictionaries (possibly empty).
		"""
		cseId = cseId.lstrip('/')
		permission = operationToPermission(operation)
		candidates = self._commonRules + self._cseRules.get(cseId, [])
		return [ rule['grant']
				 for rule in candidates
				 if self._matches(rule['match'], originator, resourceId, resourceType, permission) ]


	def _matches(self, match: dict, originator: Optional[str], resourceId: Optional[str],
					   resourceType: Optional[int], operation: Optional[int]) -> bool:
		""" Test whether a single rule's "match" conditions are satisfied.
			A condition that is *None* (not present in the rule) matches anything.
		"""
		if (pat := match['originator']) is not None and not fnmatch(originator or '', pat):
			return False
		if (pat := match['resourceID']) is not None and not fnmatch(resourceId or '', pat):
			return False
		if (types := match['resourceType']) is not None and resourceType not in types:
			return False
		if (ops := match['operation']) is not None and operation not in ops:
			return False
		return True
