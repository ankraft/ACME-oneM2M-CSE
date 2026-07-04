#
#	CertificateManager.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" This module implements the `CertificateManager` class, which is responsible for managing 
	certificates and authentication data for the CSE. It reads and stores HTTP and WebSocket 
	authentication data from specified files, providing a centralized way to handle security credentials.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from textual import case

from ..etc.Types import BindingType
from ..helpers.Singleton import Singleton
from ..helpers.CredentialTools import readCredentialFile, addCredentialEntry, removeCredentialEntry
from ..helpers.CredentialTools import readTokenFile, addTokenEntry, removeTokenEntry
from ..helpers.CredentialTools import DuplicateEntryError, EntryNotFoundError
from ..helpers.TextTools import truncateMiddle
from .Configuration import Configuration
from .Logging import Logging as L
from .PluginSupport import requires

if TYPE_CHECKING:
	from acmecse.plugins.bindings.HttpServer import HttpServer
	from acmecse.plugins.bindings.WebSocketServer import WebSocketServer


@requires(httpServer='acmecse.plugins.bindings.HttpServer', 
		  websocketServer='acmecse.plugins.bindings.WebSocketServer',
		  required=False)
class CredentialsManager(metaclass=Singleton):
	""" A class to manage credentials for the CSE. 

		It is mainly managed and used by the `SecurityManager` to handle authentication 
		and authorization of requests. It reads authentication data from specified files
		and provides methods to access this data for security checks.

		It does not refresh the data automatically, so if the authentication files are updated, 
		the respective read methods should be called again to refresh the data in memory.
	"""

	__slots__ = (
		'httpBasicAuthData',
		'httpTokenAuthData',
		'wsBasicAuthData',
		'wsTokenAuthData',
	)
	""" Slots for CertificateManager class. """

	httpServer: HttpServer = None	# type: ignore
	"""	The injected HttpServer plugin instance."""

	websocketServer: WebSocketServer = None	# type: ignore
	"""	The injected WebSocketServer plugin instance."""


	def initialize(self) -> None:
		""" Initialize the CertificateManager. 
		"""

		self.httpBasicAuthData: dict[str, str] = {}
		""" Dictionary to store the HTTP Basic Authentication data, mapping originators to their hashed passwords. """

		self.httpTokenAuthData: list[str] = []
		""" List to store the HTTP Token Authentication data. """

		self.wsBasicAuthData: dict[str, str] = {}
		""" Dictionary to store the WebSocket Basic Authentication data, mapping originators to their hashed passwords. """

		self.wsTokenAuthData: list[str] = []
		""" List to store the WebSocket Token Authentication data. """


	#
	#	Read the various credential and token files
	#

	def readHttpBasicAuthFile(self) -> None:
		"""	Read the HTTP basic authentication file and store the data in a dictionary.
			The authentication information is stored as username:password.

			The data is stored in the `httpBasicAuthData` dictionary.

			Raises:
				ValueError: If there is an error reading the basic authentication file.
		"""
		_newAuthData: dict[str, str] = {}
		# We need to access the configuration directly, since the http server is not yet initialized
		if self.httpServer:
			if Configuration.http_security_basicAuthFile:
				try:
					_newAuthData = readCredentialFile(Configuration.http_security_basicAuthFile)
				except DuplicateEntryError as e:
					raise ValueError(L.logErr(f'Duplicate username in http basic authentication file: {e}')) from e
				except Exception as e:
					raise ValueError(L.logErr(f'Error reading basic authentication file: {e}')) from e
			if not _newAuthData:
				if Configuration.http_security_enableBasicAuth:
					raise ValueError(L.logErr(f'HTTP basic authentication file not found or empty: {Configuration.http_security_basicAuthFile}'))
				else:
					L.isDebug and L.logDebug(f'HTTP basic authentication file not found or empty, but basic authentication is disabled: {Configuration.http_security_basicAuthFile}')

		# only update the httpBasicAuthData if the file was read successfully
		self.httpBasicAuthData = _newAuthData


	def readHttpTokenFile(self) -> None:
		"""	Read the HTTP token authentication file and store the data in a dictionary.
			The authentication information is stored as a single token per line.

			The data is stored in the `httpTokenAuthData` list.

			Raises:
				ValueError: If there is an error reading the token authentication file.
		"""
		_newAuthData: list[str] = []
		if self.httpServer:
			if Configuration.http_security_tokenAuthFile:
				try:
					_newAuthData = readTokenFile(Configuration.http_security_tokenAuthFile)
				except DuplicateEntryError as e:
					raise ValueError(L.logErr(f'Duplicate token in http token authentication file: {e}')) from e
				except Exception as e:
					raise ValueError(L.logErr(f'Error reading token authentication file: {e}')) from e
			if not _newAuthData:
					if Configuration.http_security_enableTokenAuth:
						raise ValueError(L.logErr(f'HTTP token authentication file not found or empty: {Configuration.http_security_tokenAuthFile}'))
					else:
						L.isDebug and L.logDebug(f'HTTP token authentication file not found or empty, but token authentication is disabled: {Configuration.http_security_tokenAuthFile}')

		# only update the httpTokenAuthData if the file was read successfully
		self.httpTokenAuthData = _newAuthData


	def readWSBasicAuthFile(self) -> None:
		"""	Read the WebSocket basic authentication file and store the data in a dictionary.
			The authentication information is stored as username:password.

			The data is stored in the `wsBasicAuthData` dictionary.

			Raises:
				ValueError: If there is an error reading the basic authentication file.
		"""
		_newAuthData: dict[str, str] = {}
		# We need to access the configuration directly, since the http server is not yet initialized
		if Configuration.websocket_security_basicAuthFile:
			try:
				_newAuthData = readCredentialFile(Configuration.websocket_security_basicAuthFile)
			except DuplicateEntryError as e:
				raise ValueError(L.logErr(f'Duplicate username in ws basic authentication file: {e}')) from e
			except Exception as e:
				raise ValueError(L.logErr(f'Error reading ws basic authentication file: {e}')) from e

		if not _newAuthData:
			if Configuration.websocket_security_enableBasicAuth:
				raise ValueError(L.logErr(f'WebSocket basic authentication file not found or empty: {Configuration.websocket_security_basicAuthFile}'))
			else:
				L.isDebug and L.logDebug(f'WebSocket basic authentication file not found or empty, but basic authentication is disabled: {Configuration.websocket_security_basicAuthFile}')

		# only update the wsBasicAuthData if the file was read successfully
		self.wsBasicAuthData = _newAuthData


	def readWSTokenFile(self) -> None:
		"""	Read the WebSocket token authentication file and store the data in a dictionary.
			The authentication information is stored as a single token per line.

			The data is stored in the `wsTokenAuthData` list.

			Raises:
				ValueError: If there is an error reading the token authentication file.
		"""
		_newAuthData: list[str] = []
		# We need to access the configuration directly, since the http server is not yet initialized
		if Configuration.websocket_security_tokenAuthFile:
			try:
				_newAuthData = readTokenFile(Configuration.websocket_security_tokenAuthFile)
			except DuplicateEntryError as e:
				raise ValueError(L.logErr(f'Duplicate token in ws token authentication file: {e}')) from e
			except Exception as e:
				raise ValueError(L.logErr(f'Error reading ws token authentication file: {e}')) from e

		if not _newAuthData:
			if Configuration.websocket_security_enableTokenAuth:
				raise ValueError(L.logErr(f'WebSocket token authentication file not found or empty: {Configuration.websocket_security_tokenAuthFile}'))
			else:
				L.isDebug and L.logDebug(f'WebSocket token authentication file not found or empty, but token authentication is disabled: {Configuration.websocket_security_tokenAuthFile}')

		# only update the wsTokenAuthData if the file was read successfully
		self.wsTokenAuthData = _newAuthData


	#
	#	Add to the various credential and token files
	#


	def addBasicAuthEntry(self, username: str, password: str, ty: BindingType) -> None:
		"""	Add HTTP basic authentication credentials to the file and update the in-memory data.
			The credentials are stored as username:password.

			Args:
				username: The username to add.
				password: The password to add.
				ty: The type of credentials to add.

			Raises:
				ValueError: If there is an error adding the credentials.
		"""
		try:
			match ty:
				case BindingType.HTTP:
					if not Configuration.http_security_basicAuthFile:
						raise ValueError(L.logErr('HTTP basic authentication file is not configured.'))
					addCredentialEntry(Configuration.http_security_basicAuthFile, username, password)
					self.readHttpBasicAuthFile()
				case BindingType.WS:
					if not Configuration.websocket_security_basicAuthFile:
						raise ValueError(L.logErr('WebSocket basic authentication file is not configured.'))
					addCredentialEntry(Configuration.websocket_security_basicAuthFile, username, password)
					self.readWSBasicAuthFile()
				case _:
					raise ValueError(L.logErr(f'Unsupported binding type for adding basic auth entry: {ty}'))
		except DuplicateEntryError as e:
			raise ValueError(L.logErr(f'Duplicate username in basic authentication file: {e}')) from e
		except Exception as e:
			raise ValueError(L.logErr(f'Error adding credentials to basic authentication file: {e}')) from e


	def addTokenEntry(self, token: str, ty: BindingType) -> None:
		"""	Add HTTP or WebSocket token authentication credentials to the file and update the in-memory data.
			The credentials are stored as token.

			Args:
				token: The token to add.
				ty: The type of credentials to add.

			Raises:
				ValueError: If there is an error adding the credentials.
		"""
		try:
			match ty:
				case BindingType.HTTP:
					if not Configuration.http_security_tokenAuthFile:
						raise ValueError(L.logErr('HTTP token authentication file is not configured.'))
					addTokenEntry(Configuration.http_security_tokenAuthFile, token)
					self.readHttpTokenFile()
				case BindingType.WS:
					if not Configuration.websocket_security_tokenAuthFile:
						raise ValueError(L.logErr('WebSocket token authentication file is not configured.'))
					addTokenEntry(Configuration.websocket_security_tokenAuthFile, token)
					self.readWSTokenFile()
				case _:
					raise ValueError(L.logErr(f'Unsupported binding type for adding token auth entry: {ty}'))
		except DuplicateEntryError as e:
			raise ValueError(L.logErr(f'Duplicate token in token authentication file: {e}')) from e
		except Exception as e:
			raise ValueError(L.logErr(f'Error adding credentials to token authentication file: {e}')) from e


	#
	#	Update the various credential and token files
	#

	def updateBasicAuthEntry(self, username: str, password: str, ty: BindingType) -> None:
		"""	Update HTTP or WebSocket basic authentication credentials in the file and update the in-memory data.
			The credentials are stored as username:password.

			Args:
				username: The username to update.
				password: The new password to set.
				ty: The type of credentials to update.

			Raises:
				ValueError: If there is an error updating the credentials.
		"""
		try:
			match ty:
				case BindingType.HTTP:
					if not Configuration.http_security_basicAuthFile:
						raise ValueError(L.logErr('HTTP basic authentication file is not configured.'))
					removeCredentialEntry(Configuration.http_security_basicAuthFile, username)
					addCredentialEntry(Configuration.http_security_basicAuthFile, username, password)
					self.readHttpBasicAuthFile()
				case BindingType.WS:
					if not Configuration.websocket_security_basicAuthFile:
						raise ValueError(L.logErr('WebSocket basic authentication file is not configured.'))
					removeCredentialEntry(Configuration.websocket_security_basicAuthFile, username)
					addCredentialEntry(Configuration.websocket_security_basicAuthFile, username, password)
					self.readWSBasicAuthFile()
				case _:
					raise ValueError(L.logErr(f'Unsupported binding type for updating basic auth entry: {ty}'))
		except EntryNotFoundError as e:
			raise ValueError(L.logErr(f'Username not found in http basic authentication file: {e}')) from e
		except Exception as e:
			raise ValueError(L.logErr(f'Error updating credentials in basic authentication file: {e}')) from e


	def updateTokenEntry(self, token: str, nt: str, ty: BindingType) -> None:
		"""	Update HTTP or WebSocket token authentication credentials in the file and update the in-memory data.
			The credentials are stored as token.

			Args:
				token: The token to update.
				nt: The new token to set.
				ty: The type of credentials to update.
		"""
		try:
			match ty:
				case BindingType.HTTP:
					if not Configuration.http_security_tokenAuthFile:
						raise ValueError(L.logErr('HTTP token authentication file is not configured.'))
					removeTokenEntry(Configuration.http_security_tokenAuthFile, token)
					addTokenEntry(Configuration.http_security_tokenAuthFile, nt)
					self.readHttpTokenFile()
				case BindingType.WS:
					if not Configuration.websocket_security_tokenAuthFile:
						raise ValueError(L.logErr('WebSocket token authentication file is not configured.'))
					removeTokenEntry(Configuration.websocket_security_tokenAuthFile, token)
					addTokenEntry(Configuration.websocket_security_tokenAuthFile, nt)
					self.readWSTokenFile()
				case _:
					raise ValueError(L.logErr(f'Unsupported binding type for updating token auth entry: {ty}'))
		except EntryNotFoundError as e:
			raise ValueError(L.logErr(f'Token not found in token authentication file: {e}')) from e
		except Exception as e:
			raise ValueError(L.logErr(f'Error updating credentials in token authentication file: {e}')) from e


	#
	#	Delete from the various credential and token files
	#

	def deleteBasicAuthEntry(self, id: str, ty: BindingType) -> None:
		"""	Delete HTTP or WebSocket basic authentication credentials from the file and update the in-memory data.
			The credentials are stored as username:password.

			Args:
				id: The username or token to delete.

			Raises:
				ValueError: If there is an error deleting the credentials.
		"""
		try:
			match ty:
				case BindingType.HTTP:
					if not Configuration.http_security_basicAuthFile:
						raise ValueError(L.logErr('HTTP basic authentication file is not configured.'))
					removeCredentialEntry(Configuration.http_security_basicAuthFile, id)
					self.readHttpBasicAuthFile()
				case BindingType.WS:
					if not Configuration.websocket_security_basicAuthFile:
						raise ValueError(L.logErr('WebSocket basic authentication file is not configured.'))
					removeCredentialEntry(Configuration.websocket_security_basicAuthFile, id)
					self.readWSBasicAuthFile()
				case _:
					raise ValueError(L.logErr(f'Unsupported binding type for deleting basic auth entry: {ty}'))
		except EntryNotFoundError as e:
			raise ValueError(L.logErr(f'Username not found in basic authentication file: {e}')) from e
		except Exception as e:
			raise ValueError(L.logErr(f'Error deleting credentials from basic authentication file: {e}')) from e


	def deleteTokenEntry(self, token: str, ty: BindingType) -> None:
		"""	Delete HTTP or WebSocket token credentials from the file and update the in-memory data.
			The credentials are stored as token.

			Args:
				token: The token to delete.

			Raises:
				ValueError: If there is an error deleting the credentials.
		"""
		try:
			match ty:
				case BindingType.HTTP:
					if not Configuration.http_security_tokenAuthFile:
						raise ValueError(L.logErr('HTTP token authentication file is not configured.'))
					removeTokenEntry(Configuration.http_security_tokenAuthFile, token)
					self.readHttpTokenFile()
				case BindingType.WS:
					if not Configuration.websocket_security_tokenAuthFile:
						raise ValueError(L.logErr('WebSocket token authentication file is not configured.'))
					removeTokenEntry(Configuration.websocket_security_tokenAuthFile, token)
					self.readWSTokenFile()
				case _:
					raise ValueError(L.logErr(f'Unsupported binding type for deleting token entry: {ty}'))
		except EntryNotFoundError as e:
			raise ValueError(L.logErr(f'Token not found in token authentication file: {e}')) from e
		except Exception as e:
			raise ValueError(L.logErr(f'Error deleting token from token authentication file: {e}')) from e

		