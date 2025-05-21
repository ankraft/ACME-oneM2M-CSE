#
#	zk-tool.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Tool to manage Zookeeper configurations for the ACME CSE
#

from __future__ import annotations

import pathlib, os, sys
parent = pathlib.Path(os.path.abspath(os.path.dirname(__file__))).parent.parent
sys.path.append(f'{parent}')

import acme.helpers.Zookeeper as Zookeeper

import os, configparser, argparse
import atexit

from rich.console import Console
console = Console()
print = console.print

_configFile = '../../acme.ini'
""" Instance specific configuration file. """

_defaultConfigFile = '../../acme/init/acme.ini.default'
""" Default configuration file. """

_zookeeperRootNode = '/acme'
""" Zookeeper node for the ACME CSE. """


def readConfigFile(file:str) -> configparser.ConfigParser:
	""" Read the configuration file and return a ConfigParser object. 

		Args:
			file: The path to the configuration file.

		Returns:
			A ConfigParser object containing the configuration.
	"""
	config = configparser.ConfigParser()
	if not os.path.exists(file):
		raise FileNotFoundError(f'Configuration file {file} does not exist')
	config.read(file)
	return config

# App start

if __name__ == '__main__':
	
	# Parse command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('--zookeeper-host', '-host', dest='zkHost', metavar='hostname', default='localhost', help=f'hostname of the Zookeeper server (default: localhost)')
	parser.add_argument('--zookeeper-port', '-port', dest='zkPort', default=Zookeeper.zookeeperDefaultPort, metavar='port', type=int, help=f'port of the Zookeeper server (default: {Zookeeper.zookeeperDefaultPort})')
	parser.add_argument('--zookeeper-root', '-root', dest='zkRoot', default=_zookeeperRootNode, metavar='nodeName', help=f'name of the configuration node (default: {_zookeeperRootNode})')
	parser.add_argument('--verbose', '-v', dest='verbose', action='store_true', help='enable verbose output')
	parser.add_argument('--case-sensitive', '-cs', dest='caseSensitive', action='store_true', default=False, help='enable case sensitive node and key names (default: False)')

	configGroup = parser.add_argument_group('ACME CSE configuration operations')
	configGroup.add_argument('--config', '-c', dest='config', default=_configFile, metavar='filename', help=f'specify the ACME CSE\'s instance configuration file (default: {_configFile})')
	configGroup.add_argument('--config-default', '-cd', dest='configDefault', default=_defaultConfigFile, metavar='filename', help=f'specify the ACME CSE\' default configuration file (default: {_defaultConfigFile})')

	configFileGroup = configGroup.add_mutually_exclusive_group(required=False)
	configFileGroup.add_argument('--store-config', '-store', dest='storeConfig', action='store_true', help='store individual ACME CSE configuration in Zookeeper')
	configFileGroup.add_argument('--store-config-all', dest='storeConfigAll', action='store_true', help='store all (incl. defaults) ACME CSE configuration in Zookeeper')
	configFileGroup.add_argument('--retrieve-config', '-retrieve', dest='retrieveConfig', action='store_true', help='retrieve ACME CSE configuration from Zookeeper')

	operationGroup_ = parser.add_argument_group('Zookeeper basic operations')
	operationGroup = operationGroup_.add_mutually_exclusive_group(required=False)
	operationGroup.add_argument('--list', '-ls', dest='list', nargs='?', const='', default=None, metavar='path', help='list contents of a Zookeeper node (optional: specify path to list, defaults to root node)')
	operationGroup.add_argument('--add', '-a', dest='add', nargs=2, metavar=('keyPath', 'value'), help='add a key-value pair to a Zookeeper node')
	operationGroup.add_argument('--update', '-u', dest='update', nargs=2, metavar=('keyPath', 'value'), help='update a key-value pair')
	operationGroup.add_argument('--DELETE', dest='delete', nargs=1, metavar='keyPath', help='delete a key-value pair')

	args = parser.parse_args()

	# connect to Zookeeper
	zk =Zookeeper.Zookeeper(args.zkHost, 
						 	args.zkPort, 
							args.zkRoot, 
							lambda x: print(f'[dim]{x}'), verbose=args.verbose,
							caseSensitive=False)
	zk.connect()
	atexit.register(zk.disconnect)	# Register the disconnect function to be called on exit

	try:

		# Handle configuration operations

		if args.storeConfig:
			zk.storeIniConfig([readConfigFile(args.config)])
			quit()

		if args.storeConfigAll:
			zk.storeIniConfig([readConfigFile(args.configDefault), readConfigFile(args.config)])
			quit()

		if args.retrieveConfig:
			args.verbose and print(f'[dim]Retrieving configuration from Zookeeper node {args.zkRoot}')	# type: ignore[func-returns-value]
			print(zk.retrieveIniConfig(args.zkRoot), markup=False, highlight=False)
			quit()

		# Handle basic Zookeeper operations

		if args.add:
			zk.addKeyValue(args.add[0], args.add[1])
			quit()

		if args.update:
			zk.updateKeyValue(args.update[0], args.update[1])
			quit()

		if args.list is not None:
			result = zk.listNode(args.list)
			# Print the result nicely with rich
			if result is not None:
				for index, item in enumerate(result):
					item.print(index==0)
			else:
				print(f'[dim]Node {args.list} does not exist')	# type: ignore[func-returns-value]
			quit()
		
		if args.delete:
			zk.delete(args.delete[0])
			quit()

	except Exception as e:
		import traceback
		traceback.print_exc()
		print(f'[red]Error: {e}')
