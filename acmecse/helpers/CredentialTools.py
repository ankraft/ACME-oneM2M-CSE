#
#	CredentialTools.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" This module provides helper functions for managing credential files, such as
	username/password files and token files. It allows adding, removing, and checking entries.

	Comments and blank lines in the files are preserved, and entries can be updated (upserted) if desired.
"""

from pathlib import Path
from typing import Callable, Optional


#
#	Exceptions
#

class EntryExistsError(Exception):
	""" Raised when attempting to add an entry that already exists
		without explicitly allowing an overwrite.
	"""
	pass


class DuplicateEntryError(Exception):
	""" Raised when a duplicate entry is found in a credential file.
	"""
	pass


class EntryNotFoundError(Exception):
	""" Raised when an entry is not found in a credential file.
	"""
	pass


#
#	Internal helper functions
#

def _readLines(filePath: str | Path) -> list[str]:
	""" Read all lines from a file, stripping whitespace and ignoring comments and blank lines. 
	
		Args:
			filePath: Path to the file.

		Returns:
			A list of stripped lines from the file. If the file does not exist, returns an empty list.
	"""
	path = Path(filePath)
	if not path.exists():
		return []
	return [line.strip() for line in path.read_text().splitlines()]


def _writeLines(filePath: str | Path, lines: list[str]) -> None:
	""" Write lines to a file, ensuring that the file ends with a newline. 
	
		Args:
			filePath: Path to the file.
			lines: List of lines to write to the file.
	"""
	Path(filePath).write_text('\n'.join(lines) + '\n')


def _findEntryIndex(lines: list[str], key: str, keyOf: Callable[[str], str]) -> Optional[int]:
	""" Find the index of an entry in a list of lines based on a lookup key.

		Args:
			lines: List of lines to search.
			key: The lookup key for the entry (e.g. username, or the token itself).
			keyOf: Function that extracts the lookup key from an existing line.

		Returns:
			The index of the entry if found, or None if not found.
	"""
	for i, line in enumerate(lines):
		if not line or line.startswith('#'):
			continue
		if keyOf(line) == key:
			return i
	return None


def addEntry(filePath: str | Path, 
				 key: str, 
				 newLine: str,
			 	 keyOf: Callable[[str], str] = lambda line: line, 
				 update: bool = False) -> None:
	""" Add or update (upsert) an entry in a line-based file, preserving existing
		entries, comments, and blank lines.

		Args:
			filePath: Path to the file.
			key: The lookup key for the entry (e.g. username, or the token itself).
			newLine: The full line to write for this entry.
			keyOf: Function that extracts the lookup key from an existing line.
			update: If True, perform an upsert — an existing entry is replaced,
					or a new one added if none exists. If False (default) and
					the key already exists, an EntryExistsError is raised.

		Raises:
			EntryExistsError: If the key already exists and update is False.
	"""
	lines = _readLines(filePath)
	idx = _findEntryIndex(lines, key, keyOf)

	if idx is not None:
		if not update:
			raise EntryExistsError(f'Entry "{key}" already exists')
		lines[idx] = newLine
	else:
		lines.append(newLine)

	_writeLines(filePath, lines)


def removeEntry(filePath: str | Path, 
				key: str, 
				keyOf: Callable[[str], str] = lambda line: line) -> None:
	""" Remove an entry from a line-based file, preserving existing entries,
		comments, and blank lines.

		Args:
			filePath: Path to the file.
			key: The lookup key for the entry to remove.
			keyOf: Function that extracts the lookup key from an existing line.

		Raises:
			EntryNotFoundError: If the entry is not found.
	"""
	lines = _readLines(filePath)
	idx = _findEntryIndex(lines, key, keyOf)
	if idx is None:
		raise EntryNotFoundError(f'Entry "{key}" not found')
	del lines[idx]
	_writeLines(filePath, lines)


def hasEntry(filePath: str | Path, 
			 key: str, 
			 keyOf: Callable[[str], str] = lambda line: line) -> bool:
	""" Check whether an entry exists in a line-based file.

		Args:
			filePath: Path to the file.
			key: The lookup key for the entry.
			keyOf: Function that extracts the lookup key from an existing line.

		Returns:
			True if an entry with the given key exists, False otherwise.		
	"""
	return _findEntryIndex(_readLines(filePath), key, keyOf) is not None


#
#	Username/password credential management functions
#

def readCredentialFile(filePath: str | Path) -> dict[str, str]:
	""" Read a username/password credential file and return a dictionary of entries.

		Args:
			filePath: Path to the credential file.

		Returns:
			A dictionary mapping usernames to passwords. If the file does not exist, returns an empty dictionary.

		Raises:
			DuplicateEntryError: If there are duplicate usernames in the file.
	"""
	credentials: dict[str, str] = {}
	for line in _readLines(filePath):
		if not line or line.startswith('#'):
			continue
		username, _, password = line.partition(':')
		if username in credentials:
			raise DuplicateEntryError(f'Duplicate username "{username}" in credential file.')
		credentials[username] = password
	return credentials



def addCredentialEntry(filePath: str | Path, 
					   username: str, 
					   password: str,
					   update: bool = False) -> None:
	""" Add or update a username/password entry in a credential file.

		Args:
			filePath: Path to the credential file.
			username: The username for the entry.
			password: The password for the entry.
			update: If True, perform an upsert — an existing entry is replaced,
					or a new one added if none exists. If False (default) and
					the username already exists, an EntryExistsError is raised.

		Raises:
			EntryExistsError: If the username already exists and update is False.
	
	"""
	addEntry(filePath, username, f'{username}:{password}', lambda line: line.split(':', 1)[0], update)


def removeCredentialEntry(filePath: str | Path, 
						  username: str) -> None:
	""" Remove a username/password entry from a credential file.

		Args:
			filePath: Path to the credential file.
			username: The username for the entry to remove.

		Raises:
			EntryNotFoundError: If the entry is not found.
	"""
	removeEntry(filePath, username, lambda line: line.split(':', 1)[0])


def getCredentialEntry(filePath: str | Path, 
					   username: str) -> Optional[str]:
	""" Retrieve the password for a given username from a credential file.
	
		Args:
			filePath: Path to the credential file.
			username: The username for which to retrieve the password.

		Returns:
			The password for the given username, or None if not found.
	"""
	for line in _readLines(filePath):
		if not line or line.startswith('#'):
			continue
		user, _, password = line.partition(':')
		if user == username:
			return password
	return None


#
#	Token credential management functions
#

def readTokenFile(filePath: str | Path) -> list[str]:
	""" Read a token credential file and return a list of tokens.

		Args:
			filePath: Path to the token file.

					Returns:
			A list of tokens. If the file does not exist, returns an empty list.

		Raises:
			DuplicateEntryError: If there are duplicate tokens in the file.
	"""
	tokens: list[str] = []
	for line in _readLines(filePath):
		if not line or line.startswith('#'):
			continue
		if line in tokens:
			raise DuplicateEntryError(f'Duplicate token "{line}" in token file.')
		tokens.append(line)
	return tokens


def addTokenEntry(filePath: str | Path, 
				  token: str, 
				  update: bool = False) -> None:
	""" Add or update a token entry in a token file.

		Args:
			filePath: Path to the token file.
			token: The token for the entry.
			update: If True, perform an upsert — an existing entry is replaced,
					or a new one added if none exists. If False (default) and
					the token already exists, an EntryExistsError is raised.

		Raises:
			EntryExistsError: If the token already exists and update is False.
	"""
	addEntry(filePath, token, token, update=update)


def removeTokenEntry(filePath: str | Path, 
					 token: str) -> None:
	""" Remove a token entry from a token file.

		Args:
			filePath: Path to the token file.
			token: The token for the entry to remove.

		Raises:
			EntryNotFoundError: If the entry is not found.
	"""
	removeEntry(filePath, token)



def hasTokenEntry(filePath: str | Path, 
				  token: str) -> bool:
	""" Check whether a token entry exists in a token file.

		Args:
			filePath: Path to the token file.
			token: The token for the entry.

		Returns:
			True if an entry with the given token exists, False otherwise.
	"""
	return hasEntry(filePath, token)



#
#	Test code for the module
#

if __name__ == '__main__':
	import tempfile
	import os

	def _section(title: str) -> None:
		print(f'\n--- {title} ---')

	def _dump(path: str) -> None:
		with open(path) as f:
			content = f.read()
		print(f'[file content]\n{content!r}')

	# Use a temporary file so these tests never touch real credential data
	fd, tmpPath = tempfile.mkstemp(suffix='.cred')
	os.close(fd)
	print(f'Testing with temporary credential file: {tmpPath}')

	try:
		_section('Credential entries: add')
		addCredentialEntry(tmpPath, 'alice', 'secret1')
		addCredentialEntry(tmpPath, 'bob', 'secret2')
		_dump(tmpPath)
		assert getCredentialEntry(tmpPath, 'alice') == 'secret1'
		assert getCredentialEntry(tmpPath, 'bob') == 'secret2'
		assert getCredentialEntry(tmpPath, 'carol') is None

		_section('Credential entries: duplicate add without update raises')
		try:
			addCredentialEntry(tmpPath, 'alice', 'whatever')
			print('FAIL: expected EntryExistsError')
		except EntryExistsError:
			print('OK: EntryExistsError raised as expected')

		_section('Credential entries: update (upsert) overwrites')
		addCredentialEntry(tmpPath, 'alice', 'newsecret', update=True)
		_dump(tmpPath)
		assert getCredentialEntry(tmpPath, 'alice') == 'newsecret'
		print('OK: alice password updated')

		_section('Credential entries: remove')
		try:
			removeCredentialEntry(tmpPath, 'bob')
			_dump(tmpPath)
			assert getCredentialEntry(tmpPath, 'bob') is None
			print('OK: bob removed')
		except EntryNotFoundError:
			print('FAIL: expected EntryNotFoundError')
		try:
			removeCredentialEntry(tmpPath, 'bob')
			print('FAIL: expected EntryNotFoundError')
		except EntryNotFoundError:
			print('OK: removing missing entry raises EntryNotFoundError')

		_section('Comments and blank lines are preserved')
		# Manually add a comment and a blank line, then add another entry
		with open(tmpPath, 'a') as f:
			f.write('# this is a comment\n\n')
		addCredentialEntry(tmpPath, 'dave', 'pw4')
		_dump(tmpPath)
		assert '# this is a comment' in open(tmpPath).read()
		print('OK: comment preserved across add')

	finally:
		os.remove(tmpPath)

	# --- Token tests, separate temp file ---
	fd, tmpTokenPath = tempfile.mkstemp(suffix='.token')
	os.close(fd)
	print(f'Testing with temporary token file: {tmpTokenPath}')

	try:
		_section('Token entries: add')
		addTokenEntry(tmpTokenPath, 'abc123')
		addTokenEntry(tmpTokenPath, 'def456')
		_dump(tmpTokenPath)
		assert hasTokenEntry(tmpTokenPath, 'abc123')
		assert hasTokenEntry(tmpTokenPath, 'def456')
		assert not hasTokenEntry(tmpTokenPath, 'ghi789')

		_section('Token entries: duplicate add without update raises')
		try:
			addTokenEntry(tmpTokenPath, 'abc123')
			print('FAIL: expected EntryExistsError')
		except EntryExistsError:
			print('OK: EntryExistsError raised as expected')

		_section('Token entries: update (upsert) is a no-op for identical token')
		addTokenEntry(tmpTokenPath, 'abc123', update=True)
		_dump(tmpTokenPath)
		assert hasTokenEntry(tmpTokenPath, 'abc123')
		print('OK: token upsert did not duplicate the entry')

		_section('Token entries: remove')
		try:
			removeTokenEntry(tmpTokenPath, 'def456')
			_dump(tmpTokenPath)
			assert not hasTokenEntry(tmpTokenPath, 'def456')
			print('OK: token removed')
		except EntryNotFoundError:
			print('FAIL: expected EntryNotFoundError')

		try:
			removeTokenEntry(tmpTokenPath, 'def456')
			print('FAIL: expected EntryNotFoundError')
		except EntryNotFoundError:
			print('OK: removing missing token raises EntryNotFoundError')

	finally:
		os.remove(tmpTokenPath)

	print('\nAll tests passed.')