#
#	IDUtils.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module contains various utilty functions to handle, test and manipulate IDs.
	
	There are no ACME CSE internal dependencies. This heelps to keep the module small and standalone.
"""

from __future__ import annotations
from typing import Optional, Tuple

import random, re, string
from .Constants import RuntimeConstants as RC

##############################################################################
#
#	Identifier and path related
#

def uniqueRI(prefix:Optional[str] = '') -> str:
	"""	Generate a unique resource ID. Beside a random number it
		can have a prefix.
		
		Args:
			prefix: Prefix for the ID
		Return:
			String with the new ID
	"""
	return f'{noNamespace(prefix)}{uniqueID()}'


def uniqueID() -> str:
	"""	Generate a unique ID. This is for the moment just a large random number.
		NO check for uniqueness is done.
		
		Return:
			String with the identifier
	"""
	return _randomID()
	# return str(random.randint(1,sys.maxsize))



def uniqueRN(prefix:str) -> str:
	"""	Generate a unique resource name. A resource name has a prefix and 
		a random alpha-numeric string.

		Args:
			prefix: String prefix. If it contains a domain then that is removed
		Return:
			String with the resource name

	"""
	return f'{noNamespace(prefix)}_{_randomID()}'


# create a unique aei, M2M-SP type
def uniqueAEI(prefix:Optional[str] = 'S') -> str:
	"""	Create a new AE ID. An AE ID must always start with either "S" or "C".
	
		Args:
			prefix: "S" or "C"
		Return:
			String with the AE ID
	"""
	return f'{prefix}{_randomID()}'


def noNamespace(id:str) -> str:
	"""	Remove the namespace part of an identifier and return the remainder.

		Example: 
			'm2m:cnt' -> 'cnt'
		
		Args:
			id: String with the identifier. May be prefixed with a domain.
		Return:
			String that only contains the ID
	"""
	_, found, tail = id.partition(':')
	return tail if found else id



_randomIDCharSet = string.ascii_uppercase + string.digits + string.ascii_lowercase
"""	Character set for random IDs. """

def _randomID() -> str:
	""" Generate an ID. Prevent certain patterns in the ID.

		Return:
			String with a random ID
	"""
	while True:
		result = ''.join(random.choices(_randomIDCharSet, k = RC.idLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID
			return result


def localResourceID(ri:str) -> Optional[str]: # type: ignore[return]
	""" Test whether an ID is a resource ID of the local CSE.
	
		Args:
			ri: A resource ID in CSE-relative, SP-relative, or absolute notation.
		Return:
			If the ID targets a local resource then the CSE-relative form of the resource ID
			is returned, or None otherwise.
	"""
	
	def _checkDash(ri:str) -> str:
		"""	Handle the special case of '-'.

			Args:
				ri: The resource ID to check
			
			Return:
				The resource ID with the special case handled.
		"""
		if ri.startswith('-/'):
			return f'{RC.cseRn}{ri[1:]}'
		if ri == '-':
			return RC.cseRn
		return ri


	if ri == RC.cseCsi:
		return RC.cseRn
	
	match ri:
		case x if isAbsolute(x):
			if ri.startswith(RC.cseAbsoluteSlash):
				return _checkDash(ri[len(RC.cseAbsoluteSlash):])
			return None
		case x if isSPRelative(x):
			if ri.startswith(RC.cseCsiSlash):
				return _checkDash(ri[len(RC.cseCsiSlash):])
			return None
		case _:
			return ri


def isStructured(uri:str) -> bool: # type: ignore[return]
	""" Test whether a URI is in structured format.
	
		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in structured format
	"""
	match uri:
		case x if isCSERelative(uri):
			return '/' in uri or uri == RC.cseRn
		case x if isSPRelative(uri):
			return uri.count('/') > 2
		case x if isAbsolute(uri):
			return uri.count('/') > 4
		case _:
			return False
		

def isSPRelative(uri:str) -> bool:
	""" Test whether a URI is SP-Relative. 

		Args:
			uri: The URI to check
		Return:
			Boolean
	"""
	return uri is not None and len(uri) >= 2 and uri[0] == '/' and uri [1] != '/'


def isAbsolute(uri:str) -> bool:
	""" Test whether a URI is in absolute format.
	
		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in absolute format
	"""
	return uri is not None and uri.startswith('//')


def isCSERelative(uri:str) -> bool:
	""" Test whether a URI is in CSE-relative format.

		Args:
			uri: The URI to check
		Return:
			Boolean if the URI is in CSE-relative format
	"""
	return uri is not None and not uri.startswith('/')


def toSPRelative(id:str) -> str:
	"""	Add the CSI to an originator (if not already present).

		Args:
			id: A string with the originator or resource ID to convert.
		Return:
			A string in the format */<csi>/<id>*.
	"""
	if not isSPRelative(id):
		return  f'{RC.cseCsi}/{id}'
	return id


def toCSERelative(id:str) -> str:
	"""	Convert an id to CSE-Relative format.

		Args:
			id: 	An ID in SP-relative or absolute format.
		Return:
			An ID in CSE-Relative format.
	"""
	_e = id.split('/')
	if isSPRelative(id) and len(_e) > 2:
		return '/'.join(_e[2:])
	elif isAbsolute(id) and len(_e) > 3:
		return '/'.join(_e[3:])
	return id




_csiRx = re.compile(r'^/[a-zA-Z0-9\-._]+') # Must start with a / and must not contain a further / or white space
# _csiRx = re.compile(r'^/[^/\s]+') # Must start with a / and must not contain a further / or white space
"""	Regular expression to test for valid CSE-ID format (unreserved characters in IDs according to RFC 3986). """

def isValidCSI(csi:str) -> bool:
	"""	Test for valid CSE-ID format.

		Args:
			csi: The CSE-ID to check
		Return:
			Boolean
	"""
	return re.fullmatch(_csiRx, csi) is not None



_aeRx = re.compile(r'^[^/\s]+') # Must not start with a / and must not contain a further / or white space
"""	Regular expression to test for valid AE-ID format. """

def isValidAEI(aei:str) -> bool:
	"""	Test for valid AE-ID format. 

		It takes SP-Relative AEI's into account.

		Args:
			aei: The AE-ID to check
		Return:
			Boolean
	"""
	if isSPRelative(aei):
		ids = aei.split('/')
		aei = ids[-1]

	return re.fullmatch(_aeRx, aei) is not None



def isValidID(id:str, allowEmpty:Optional[bool] = False) -> bool:
	""" Test for a valid ID. 

		Args:
			id: The ID to check
			allowEmpty: Indicate whether an ID can be empty.
		Returns:
			Boolean
	"""
	if allowEmpty:
		return id is not None and '/' not in id	# pi might be ""
	
	return id is not None and len(id) > 0 and hasOnlyUnreserved(id)


_unreserved = re.compile(r'^[\w\-.~]*$')
"""	Regular expression to test for unreserved characters. """

def isCSI(uri:str) -> bool:
	""" Test whether a URI is a CSE-ID.

		Args:
			uri: The URI to check

		Return:
			Boolean if the URI is a CSE-ID
	"""
	_r = csiFromRelativeAbsoluteUnstructured(uri)[1]
	return len(_r) == 2 and _r[0] == ''



def hasOnlyUnreserved(id:str) -> bool:
	"""	Test that an ID only contains characters from the unreserved character set of 
		RFC 3986.
		
		Args:
			id: the ID to check.
		Returns:
			Boolean
	"""
	return re.match(_unreserved, id) is not None



def csiFromSPRelative(ri:str) -> Optional[str]:
	"""	Return the csi from a SP-relative resource ID. It is assumed that
		the passed *ri* is in SP-relative format.
		
		Args:
			ri: A SP-relative resource ID
		Return:
			The csi of the resource ID, or None
	"""
	ids = ri.split('/')
	# return f'/{ids[0]}' if len(ids) > 0 else None
	return f'/{ids[1]}' if len(ids) > 1 else None


def csiFromRelativeAbsoluteUnstructured(id:str) -> Tuple[str, list[str]]:
	"""	Get the csi from an unstructured CSE-relative, SP-relative, or
		absolute ID.
		
		Args:
			id: unstructured ID.
		Return:
			Tuple (CSE ID (no leading slashes) without any SP-ID or CSE-ID, list of path elements). If the ID is None or empty, the return value is ('', []).
	"""
	if not id:
		return '', []
	ids = id.split('/')
	match id:
		case x if isSPRelative(x):
			return ids[1], ids
		case x if isAbsolute(x):
			return ids[3], ids
	return id, ids


def getIdFromOriginator(originator: str, idOnly:Optional[bool] = False) -> str:
	""" Get AE-ID-Stem or CSE-ID from the originator (in case SP-relative or Absolute was used).

		Args:
			originator: An originator.
			idOnly: Indicator that only the CSE-local resource ID is provided.
		Returns:
			Resource ID.
	"""
	if idOnly:
		return originator.split("/")[-1] if originator else originator
	else:
		return originator.split("/")[-1] if originator and originator.startswith('/') else originator
