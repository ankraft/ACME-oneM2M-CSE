#
#	JSONUtils.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#

""" This module provides various JSON/Dictionary utility functions. """

from __future__ import annotations
from typing import Tuple, Optional
import re
from ..etc.Types import JSON
from ..etc.Constants import Constants

# Optimize access (fewer look-up)
_attrType = Constants.attrRtype

##############################################################################
#
#	Resource and content related
#

_excludeFromRoot = [ 'pi' ]
"""	Attributes that are excluded from the root of a resource tree. """

_pureResourceRegex = re.compile(r'[\w]+:[\w]')
"""	Regular expression to test for a pure resource name. """

def pureResource(dct:JSON) -> Tuple[JSON, str, str]:
	"""	Return the "pure" structure without the "<domain>:xxx" resource type name, and the oneM2M type identifier. 

		Args:
			dct: JSON dictionary with the resource attributes.
		Return:
			Tupple with the inner JSON, the resource type name, and the found key.
			If the resource type name is not in the correct format, eg the domain is missing, it is *None*.
			The third element always contains the found outer attribute name.
	"""
	try:
		rootKeys = list(dct.keys())
		# Try to determine the root identifier 
		if (lrk := len(rootKeys)) == 1 and (rk := rootKeys[0]) not in _excludeFromRoot and re.match(_pureResourceRegex, rk):
			return dct[rootKeys[0]], rootKeys[0], rootKeys[0]
		# Otherwise try to get the root identifier from the resource itself (stored as a private attribute)
		return dct, dct.get(_attrType), rootKeys[0] if lrk > 0 else None
	except Exception:
		raise


def resourceDiff(old:JSON, new:JSON, modifiers:Optional[JSON] = None) -> JSON:
	"""	Compare an old and a new resource. A comparison happens for keywords and values.
		Attributes which names start and end with "__" (ie internal attributes) are ignored.

		Args:
			old: Old resource dictionary to compare.
			new: New resource dictionary to compare.
			modifiers: A dictionary. If this dictionary is given then it contains the changes that let from old to new. This is used to determine if attributes were just updated with the same values.
		Return:	
			Return a dictionary of identified changes.
	"""
	res = {}
	for k, v in new.items():
		if k.startswith('__'):	# ignore all internal attributes
			continue
		if not k in old:		# Key not in old
			res[k] = v
		elif v != old[k]:		# Value different
			res[k] = v
		elif modifiers and k in modifiers:	# this means the attribute is overwritten by the same value. But still modified
			res[k] = v

	# Process deleted attributes. This is necessary since attributes can be
	# explicitly set to None/Nulls.
	for k, v in old.items():
		if k not in new:
			res[k] = None

	return res

def resourceModifiedAttributes(old:JSON, new:JSON, requestPC:JSON, modifiers:Optional[JSON] = None) -> JSON:
	"""	Calculate the difference between an original resource and after it has been updated, and then remove the attributes
		that are part of the update request.

		Args:
			old: Old resource dictionary to compare.
			new: New resource dictionary to compare.
			requestPC: The original request's content. This is used to remove the attributes that are part of the update request.
			modifiers: A dictionary. If this dictionary is given then it contains the changes that let from old to new. This is used to determine if attributes were just updated with the same values.
		Return:	
			Return a dictionary of those attributes that have been changed in a CREATE or UPDATE request.	
	"""
	return { k:v for k,v in resourceDiff(old, new, modifiers).items() if k not in requestPC or v != requestPC[k] }

