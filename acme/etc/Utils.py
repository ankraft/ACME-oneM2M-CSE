#
#	Utils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

""" This module provides various non-oneM2M related utility functions. """

from __future__ import annotations

from typing import Any, Tuple, Generator, Optional
import os, platform, re, subprocess, traceback, threading, hashlib, hmac
from urllib.parse import urlsplit, urlunsplit


def strToBool(value:str) -> bool:
	"""	Convert a string value to a boolean.
	
		Args:
			value: Any string value that looks like a boolean *true* or *false*.
		Return:
			The boolean value.
		Raises:
			ValueError if the string does not look like a boolean.
	"""
	value = value.lower()
	if value in ('y', 'yes', 't', 'true', 'on', '1'):
		return True
	elif value in ('n', 'no', 'f', 'false', 'off', '0'):
		return False
	raise ValueError("invalid truth value %r" % (value,))


def runsInIPython() -> bool:
	"""	Check whether the current runtime environment is IPython or not.

		This is a hack!

		Return:
			True if run in IPython, otherwise False.
	"""
	for each in traceback.extract_stack():
		if each.filename.startswith('<ipython'):
			return True
	return False


def reverseEnumerate(data:list) -> Generator[Tuple[int, Any], None, None]:
	"""	Reverse enumerate a list.

		Args:
			data: List to enumerate.
		Return:
			Generator that yields a tuple with the index and the value of the list.
	"""
	for i in range(len(data)-1, -1, -1):
		yield (i, data[i])


#########################################################################

def openFileWithDefaultApplication(filename:str) -> None:
	"""	Open a file with the default application.

		Args:
			filename: Name of the file to open.
	"""
	if platform.system() == 'Windows':
		os.startfile(filename)	# type: ignore[attr-defined]
	elif platform.system() == 'Darwin':
		subprocess.call(['open', filename])
	else:
		subprocess.call(['xdg-open', filename])


##############################################################################
#
#	Threads
#

def renameThread(prefix:Optional[str] = None,
				 name:Optional[str] = None,
				 thread:Optional[threading.Thread] = None) -> bool:
	"""	Rename a thread.

		If *name* is provided then the thread is renamed to that name.
		If *name* is not provided, but *prefix* is, then the thread is renamed to the prefix + the last 5 digits of its thread ID.
		If neither *name* nor *prefix* is provided, then the thread is renamed to its own ID.
	
		Args:
			name: New name for a thread. 
			thread: The Thread to rename. If none is provided then the current thread is renamed.
			prefix: Used for "prefix + ID" procedure explained above.

		Returns:
			Always True.
		"""
	thread = threading.current_thread() if not thread else thread
	if name is not None:
		thread.name = name 
	elif prefix is not None:
		thread.name = f'{prefix}_{str(thread.native_id)[-5:]}'
	else:
		thread.name = str(thread.native_id)
	return True


def getThreadName(thread:Optional[threading.Thread] = None) -> str:
	"""	Get the name of a thread.

		Args:
			thread: The Thread to get the name from. If none is provided then the current thread is used.

		Returns:
			The name of the thread.
	"""
	return threading.current_thread().name if not thread else thread.name


##############################################################################
#
#	URL and Addressung related
#
_urlregex = re.compile(
		r'^(?:http|ftp|mqtt|ws|coap)s?://|^(?:acme)://' 	# http://, https://, ftp://, ftps://, coap://, coaps://, mqtt://, mqtts://
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
		r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9]))|' # localhost or single name w/o domain
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 		# ipv4
		r'(?::\d+)?' 								# optional port
		r'(?:/?|[/?]\S+)$', re.IGNORECASE			# optional path

		# Alternative version of the last line: match everything for the path and also remove the IGNORECASE
		# r'\S+' # re.IGNORECASE		 			# optional path

		)
"""	Regular expression to test for a valid URL. """

def isURL(url:str) -> bool:
	""" Check whether a given string is a URL. 

		Args:
			url: String to check for URL-ness.
		Return:
			Boolean indicating whether the argument is a valid URL.
	"""
	return isinstance(url, str) and re.match(_urlregex, url) is not None


def isCoAPUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL, and indicates a coap or coaps scheme.

		Args:
			url: String to check.
		Returns:
			True if the argument is a URL, and is an coap or coaps scheme.
	"""
	return isURL(url) and url.startswith(('coap:', 'coaps:'))


def isHttpUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL, and indicates an http or https scheme.

		Args:
			url: String to check.
		Returns:
			True if the argument is a URL, and is an http or https scheme.
	"""
	return isURL(url) and url.startswith(('http:', 'https:'))


def isMQTTUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL, and indicates an mqtt URL. 

		Args:
			url: String to check.
		Returns:
			True if the argument is a URL, and is an mqtt or mqtts scheme.
	"""
	return isURL(url) and url.startswith(('mqtt:', 'mqtts:'))


def isWSUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL, and indicates a WebSocket URL. 

		Args:
			url: String to check.
		Returns:
			True if the argument is a URL, and is a ws or wss scheme.
	"""
	return isURL(url) and url.startswith(('ws:', 'wss:'))


def isAcmeUrl(url:str) -> bool:
	"""	Test whether a URL is a valid URL and an internal ACME event URL. 

		Args:
			url: URL to check.
		Returns:
			True if the argument is a URL, and is an internal ACME scheme.
	"""
	return isURL(url) and url.startswith('acme:')


def normalizeURL(url:str) -> str:
	""" Remove trailing / from a url. 

		Args:
			url: URL to remove trailing /'s from.
		Returns:
			URL without trailing /'s.
	"""
	if url:
		while len(url) > 0 and url[-1] == '/':
			url = url[:-1]
	return url


def getBasicAuthFromUrl(url:str) -> Tuple[str, str, str]:
	""" Get the basic auth credentials from a URL.

		Args:
			url: URL to extract the basic auth credentials from.
		Returns:
			A tuple with the URL without the basic auth credentials, the username and the password.
	"""
	split = urlsplit(url)
	if split.username is not None and split.password is not None:
		return urlunsplit((split.scheme, 
					 	   f'{split.hostname}{":"+str(split.port) if split.port else ""}',
						   split.path,
						   split.query, 
						   split.fragment)), split.username, split.password
	return url, '', ''


def buildBasicAuthUrl(url:str, username:str, password:str) -> str:
	""" Build a URL with basic auth credentials.

		Args:
			url: URL to add the basic auth credentials to.
			username: Username for the basic auth.
			password: Password for the basic auth.

		Returns:
			URL with the basic auth credentials.
	"""
	split = urlsplit(url)
	return urlunsplit((split.scheme, 
					   f'{username}:{password}@{split.hostname}{":"+str(split.port) if split.port else ""}',
					   split.path,
					   split.query, 
					   split.fragment))


def hashString(s:str, salt:str='') -> str:
	""" Hash a string using SHA256.

		Args:
			s: String to hash.
			salt: Salt to add to the string before hashing. 

		Returns:
			The SHA256 hash of the string as hex.
	"""
	return hmac.new(salt.encode(), msg=s.encode(), digestmod=hashlib.sha256).digest().hex()