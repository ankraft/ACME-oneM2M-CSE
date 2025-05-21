#
#	Zookeeper.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" This module contains the Zookeeper class and helpers.
"""
from __future__ import annotations

from typing import Optional, Callable
from dataclasses import dataclass
from configparser import ConfigParser
from kazoo.client import KazooClient	# type:ignore[import-untyped]

from rich.console import Console
console = Console()
print = console.print

zookeeperDefaultPort = 2181
""" Default Zookeeper port. """

@dataclass
class ZookeperNode():
	""" Class to represent a Zookeeper node. """
	
	key:str
	""" The key of the Zookeeper node. """

	value:str
	""" The value of the Zookeeper node. """

	path:str
	""" The path of the Zookeeper node. """

	isNode:bool = False
	""" Flag to indicate if the node is a Zookeeper node. """


	def print(self, root:bool) -> None:
		""" Print the Zookeeper node with rich. 
		"""
		_indent = '  ' * (not root)
		_key = self.path if root else self.path.split('/')[-1]
		_value = f' = {self.value}' if self.value else ' = <none>'
		_color = 'blue' if self.isNode else 'none'
		_ob = '\[' if self.isNode else ''
		_cb = ']' if self.isNode else ''
		print(f'{_indent}[{_color}]{_ob}{_key}{_cb}{_value}[/{_color}]', highlight=False)


class Zookeeper():
	""" Class to manage Zookeeper configurations.

		This class provides methods to connect to a Zookeeper server, list nodes, retrieve and store INI configurations,
		add, update, delete key-value pairs, and manage the Zookeeper client connection.
	"""

	def __init__(self,	host:str, 
			  			port:Optional[int]=zookeeperDefaultPort, 
						rootNode:Optional[str]='/',
						logger:Optional[Callable]=print,
						verbose:Optional[bool]=False) -> None:
		""" Initialize the Zookeeper client. 
		
			Args:
				host: The hostname of the Zookeeper server.
				port: The port of the Zookeeper server.
				rootNode: The root node of the Zookeeper server.
				logger: The logger function to use for logging.
				verbose: Flag to enable verbose output.
		"""
		self.zk = None
		self.host = host
		self.port = port
		self.rootNode = f'/{rootNode.strip("/ ")}/'	# Remove leading and trailing slashes
		self.logger = logger
		self.verbose = verbose
		

	def connect(self, createRoot:Optional[bool]=True) -> Zookeeper:
		""" Connect to the Zookeeper server.

			Args:
				createRoot: Flag to create the root node if it doesn't exist.
		
			Returns:
				The Zookeeper instance.
		"""
		self.disconnect()
		self.zk = KazooClient(hosts=f'{self.host}:{self.port}')
		if not self.zk:
			raise Exception('Failed to connect to Zookeeper server')
		self.zk.start()
		self.verbose and self.logger(f'Connected to Zookeeper server at {self.host}:{self.port}')	# type: ignore[func-returns-value]

		# Check if the root node exists, if not create it
		if not self.zk.exists(self.rootNode) and createRoot:
			self.addKeyValue(self.rootNode)
			self.verbose and self.logger(f'[dim]Created root key at {self.rootNode}')
		return self
	

	def disconnect(self) -> Zookeeper:
		""" Disconnect from the Zookeeper server.

			Returns:
				The Zookeeper instance.
		"""
		if self.zk is not None:
			self.zk.stop()
			self.zk = None
			self.verbose and self.logger('Disconnected from Zookeeper server')	# type: ignore[func-returns-value]
		return self


	def exists(self, node:Optional[str]=None) -> bool:
		""" Check if the specified Zookeeper node exists.

			Args:
				node: The node to check. This must be an absolute path.

			Returns:
				True if the node exists, False otherwise.

			Raises:
				Exception: If the Zookeeper client is not connected.
		"""
		if self.zk is None:
			raise Exception('Not connected to Zookeeper server')
		return (self.zk.exists(node) if node else self.zk.exists(self.rootNode)) is not None


	def listNode(self, node:str) -> list[ZookeperNode]:
		""" List the contents of the Zookeeper node. 
		
			Args:
				node: The node to list. This can be node relative to the root node, or an absolute path.

			Returns:
				A list of Zookeeper nodes.
		"""
		if self.zk is None:
			raise Exception('Not connected to Zookeeper server')

		if not node.startswith('/'):
			node = f'{self.rootNode}{node}'.rstrip('/ ')
		result:list[ZookeperNode] = []
		if self.zk.exists(node):
			data, stat = self.zk.get(node)
			result.append(ZookeperNode('.', data.decode('utf-8') if data != '' else None, node, stat.children_count > 0))
			if stat.children_count > 0:
				for child in self.zk.get_children(node):
					childData, stat = self.zk.get(f'{node}/{child}')
					result.append(ZookeperNode(child, childData.decode('utf-8'), f'{node}/{child}', stat.children_count > 0))
			
			# Sort the child nodes alphabetically (all nodes except the first one)
			if len(result) > 1:
				result[1:] = sorted(result[1:], key=lambda node: node.key)

			return result
		return None
	

	def retrieveIniConfig(self, node:Optional[str]=None) -> str:
		""" Retrieve the Zookeeper node as an INI configuration string. 
		
			Args:
				node: The node to convert. This can be node relative to the root node, or an absolute path. The default is the root node.
			
			Returns:
				A multi-line string representing the INI configuration for the Zookeeper node.
		"""

		def buildSections(rows:list[ZookeperNode], sectionTitle:str = '') -> list[str]:
			""" Build the sections and key-value pairs for the configuration file. 

				This is a recursive function that builds the sections for the configuration file.

				Args:
					rows: The list of Zookeeper nodes to build the sections from.
					sectionTitle: The title of the section to build.

				Returns:
					A list of strings representing the sections for the configuration file.
			"""
			lines:list[str] = []
			sep = '.' if len(sectionTitle) > 0 else ''
			
			if rows:
				# first add the node's local keys
				for row in rows:
					if not row.isNode:
						lines.append(f'{row.key}={row.value}')
				
				# then add the node's children to the list
				for row in rows:
					if row.isNode and row.key != '.':
						l = buildSections(self.listNode(row.path), f'{sectionTitle}{sep}{row.key}')
						if len(l) and len(l[0]):	# only add a new section if it has own keys. The first line is empty otherwise
							lines.append('')
							lines.append(f'[{sectionTitle}{sep}{row.key}]')
						lines.extend(l)
			return lines

		return '\n'.join(buildSections(self.listNode(node if node else self.rootNode)))


	def storeIniConfig(self, config:ConfigParser|list[ConfigParser], node:Optional[str]=None) -> Zookeeper:
		""" Store the INI configuration in the Zookeeper node.

			Dots (.) in the section names will be replaced with slashes (/) and be stored as a path in Zookeeper.
			For example, the section name 'section.subsection' will be stored as 'section/subsection'.

			Args:
				config: The INI configuration to store. This can be a single ConfigParser object or a list of ConfigParser objects. The order of the list is important, as entries in the first ConfigParser will be overwritten by entries in the second ConfigParser if they have the same section and key.
				node: The node to store the configuration in. This can be node relative to the root node, or an absolute path.
			
			Returns:
				The Zookeeper instance.
			
			Raises:
				Exception: If the Zookeeper client is not connected or if the configuration is empty.
		"""
		config = config if isinstance(config, list) else [config]
		node = node if node else self.rootNode

		for c in config:
			self.verbose and self.logger(f'[dim]Writing configuration to Zookeeper node {node}')	# type: ignore[func-returns-value]
			for section in c.sections():
				zkSection = section.replace('.', '/')
				for key, value in c.items(section):
					self.upsertKeyValue(f'{zkSection}/{key}', value)
		return self
			

	def addKeyValue(self, key:str, value:str='') -> Zookeeper:
		""" Add a key-value pair to the Zookeeper node. 

			Section that are stored in multiple levels in the Zookeeper tree will be flattened and stored as a single section,
			separated by dots (.) in the section name. 

			Args:
				key: The key to add. This can be node relative to the root node, or an absolute path.
				value: The value to add. This is optional and defaults the root node.

			Returns:
				The Zookeeper instance.

			Raises:
				Exception: If the Zookeeper client is not connected or if the key already exists.
		"""
		if self.zk is None:
			raise Exception('Not connected to Zookeeper server')
		if not key.startswith('/'):
			key = f'{self.rootNode}{key}'.rstrip('/ ')
		
		if self.zk.exists(key):
			raise Exception(f'Key {key} already exists')
		self.zk.create(key, value.encode('utf-8'), makepath=True)
		self.verbose and self.logger(f'Created key at {key} with value: {value}')
		return self
	

	def updateKeyValue(self, key:str, value:str) -> Zookeeper:
		""" Update the value of the specified key in the Zookeeper node.
		 
			Args:
				key: The key to update. This can be node relative to the root node, or an absolute path.
				value: The new value to set for the key.

			Returns:
				The Zookeeper instance.

			Raises:
				Exception: If the Zookeeper client is not connected or if the key does not exist.
		"""
		if self.zk is None:
			raise Exception('Not connected to Zookeeper server')
		
		if not key.startswith('/'):
			key = f'{self.rootNode}{key}'.rstrip('/ ')
		
		if self.zk.exists(key):
			self.zk.set(key, value.encode('utf-8'))
			self.verbose and self.logger(f'Updated key at {key} with value: {value}')	# type: ignore[func-returns-value]
		else:
			raise Exception(f'Key {key} does not exist')
		return self
	

	def upsertKeyValue(self, key:str, value:str) -> Zookeeper:
		""" Upsert a key-value pair to the Zookeeper node. 
		
			Args:
				key: The key to upsert. This can be node relative to the root node, or an absolute path.
				value: The value to upsert. This is optional and defaults to an empty string.

			Returns:
				The Zookeeper instance.

			Raises:
				Exception: If the Zookeeper client is not connected.
		"""
		if self.zk is None:
			raise Exception('Not connected to Zookeeper server')
		
		if not key.startswith('/'):
			key = f'{self.rootNode}{key}'.rstrip('/ ')
		
		if self.zk.exists(key):
			return self.updateKeyValue(key, value)
		return self.addKeyValue(key, value)


	def delete(self, key:str) -> Zookeeper:
		""" Delete the specified key from the Zookeeper node. 
		
			Args:
				key: The key to delete. This can be node relative to the root node, or an absolute path.

			Returns:
				The Zookeeper instance.

			Raises:
				Exception: If the Zookeeper client is not connected or if the key does not exist.
		"""
		if self.zk is None:
			raise Exception('Not connected to Zookeeper server')
		
		if not key.startswith('/'):
			key = f'{self.rootNode}{key}'.rstrip('/ ')
		
		if self.zk.exists(key):
			self.zk.delete(key, recursive=True)
			self.verbose and self.logger(f'Deleted key {key}')	# type: ignore[func-returns-value]
		else:
			raise Exception(f'Key {key} does not exist')
		return self


