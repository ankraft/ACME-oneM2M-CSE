#
#	NetworkTools.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various helpers for working with strings and texts
#

""" Utility functions for network aspects.
"""

from typing import Optional
import ipaddress, re, socket, contextlib

def isValidateIpAddress(ip:str) -> bool:
	"""	Validate an IP address.
	
		Args:
			ip: The IP address to validate.
		
		Return:
			True or False.
	"""
	try:
		ipaddress.ip_address(ip)
	except Exception:
		return False
	return True

_allowedPart = re.compile(r'(?!-)[A-Z\d-]{1,63}(?<!-)$', re.IGNORECASE)
"""	Regular expression for validating host names. """

def isValidateHostname(hostname:str) -> bool:
	"""	Validate a host name.

		Args:
			hostname: The host name to validate.

		Return:
			True if the *hostname* is valid, or False otherwise.
	"""
	if not (1 < len(hostname) <= 255):
		return False
	if hostname[-1] == '.':
		hostname = hostname[:-1] # strip exactly one dot from the right, if present
	return all(_allowedPart.match(x) for x in hostname.split("."))


def isValidPort(port:str|int) -> bool:
	"""	Validate a port number.
	
		Args:
			port: The port number to validate.
		
		Return:
			True if *port* is valid, or False otherwise.
	"""
	if isinstance(port, int):
		_port = port
	else:
		try:
			_port = int(port)
		except ValueError:
			return False
	return 0 < _port <= 65535


def isTCPPortAvailable(port:int) -> bool:
	"""	Check whether a TCP port is available.
	
		Args:
			port: The port to check.

		Return:
			True if *port* is available, or False otherwise."""
	try:
		with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind(('', port))
	except OSError:
		return False
	return True


def getIPAddress(hostname:Optional[str] = None) -> str:
	"""	Lookup and return the IP address for a host name.
	
		Args:
			hostname: The host name to look-up. If none is given, the own host name is tried.
		Return:
			IP address, or 127.0.0.1 as a last resort. *None* is returned in case of an error.
	"""
	if not hostname:
		hostname = socket.gethostname()
	
	try:
		ip = socket.gethostbyname(hostname)
		# ip = socket.gethostbyname_ex(hostname)[2][0]

		#	Try to resolve a local address. For example, sometimes raspbian
		#	need to add a 'local' ir 'lan' postfix, depending on the local 
		#	device configuration
		if ip.startswith('127.'):	# All local host addresses
			for ext in ['.local', '.lan']:
				try:
					ip = socket.gethostbyname(hostname + ext)
				except:
					pass
		return ip
	except Exception:
		return ''


def pingTCPServer(server:str, port:int, timeout:float = 3.0) -> bool:
	"""	Ping a TCP server on a specific port.
	
		Args:
			server: The server to ping.
			port: The port to ping.
			timeout: The timeout in seconds.

		Return:
			True or False
	"""
	
	try:
		socket.setdefaulttimeout(timeout)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((server, port))
	except OSError as error:
		return False
	else:
		s.close()
		return True
