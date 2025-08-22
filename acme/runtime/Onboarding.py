#
#	Onboarding.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Interactively create a new basic configuration file
#
"""	Interactively create a new basic configuration file.
"""

from __future__ import annotations 
from typing import List, cast, Tuple, Optional
import os, re
from datetime import datetime

from InquirerPy import inquirer
from InquirerPy.utils import InquirerPySessionResult
from InquirerPy.base import Choice

from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.spinner import Spinner

from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.IDUtils import isValidID, isValidPath
from ..helpers import Zookeeper

from ..helpers import NetworkTools

from ..runtime import Configuration



_iniValues = {
	'IN' : { 
		'cseID': 'id-in',
		'cseName': 'cse-in',
		'adminID': 'CAdmin',
		'networkInterface': '0.0.0.0',
		'cseHost': '${hostIPAddress}',
		'httpPort': 8080,

		'logLevel': 'debug',
		'databaseInMemory': 'False',
	},
	'MN' : { 
		'cseID': 'id-mn',
		'cseName': 'cse-mn',
		'adminID': 'CAdmin',
		'networkInterface': '0.0.0.0',
		'cseHost': '${hostIPAddress}',
		'httpPort': 8081,

		'logLevel': 'debug',
		'databaseInMemory': 'False',

		'registrarCseHost': '${hostIPAddress}',
		'registrarCsePort': 8080,
		'registrarCseID': 'id-in',
		'registrarCseName': 'cse-in',
		'INCSEcseID': 'id-in',
	},
	'ASN' : { 
		'cseID': 'id-asn',
		'cseName': 'cse-asn',
		'adminID': 'CAdmin',
		'networkInterface': '0.0.0.0',
		'cseHost': '${hostIPAddress}',
		'httpPort': 8082,

		'logLevel': 'debug',
		'databaseInMemory': 'False',

		'registrarCseHost': '${hostIPAddress}',
		'registrarCsePort': 8081,
		'registrarCseID': 'id-mn',
		'registrarCseName': 'cse-mn',
		'INCSEcseID': 'id-in',
	}		
}
""" Default values for the configuration file.
"""


def _print(msg:str|Rule = '\n') -> None:
	""" Print a message to the console.
	
		Args:
			msg: The message to print.
	"""
	if not RC.isHeadless:
		if isinstance(msg, Rule):
			Console().print('\n')
		Console().print(msg, highlight = False)	# Print error message to console
		if isinstance(msg, Rule):
			Console().print('\n')

_interpolationVariable = re.compile(r'\$\{([a-zA-Z0-9_]+)\}')
""" Regular expression to match interpolation variables. """
def _containsVariable(value:str) -> bool:
	""" Check if the value contains an interpolation variable.
	
		Args:
			value: The value to check.
		
		Return:
			True if the value contains an interpolation variable, False otherwise.
	"""
	return _interpolationVariable.search(value) is not None


def buildUserConfigFile(configFile:Optional[str],
						zkConfiguration:Optional[Tuple[str, int, Optional[str]]] = None,
						overwrite:bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
	""" Build a new user configuration file interactively. If the zookeeper host, port, and root path are provided, 
		the configuration will be stored in the ZooKeeper service instead of a local file.

		Args:
			configFile: The configuration file to create.
			zkConfiguration: A tuple containing the ZooKeeper host, port, and root path.
			overwrite: If True, overwrite the configuration or configuration file if it already exists.

		Return:
			A tuple with three elements:
			
				- True if the configuration was created, False otherwise.
				- The configuration file name if created, None otherwise.
				- The error message if the configuration file could not be created, None otherwise.
	"""
	cseType = 'IN'
	cseID:str = None
	cseSecret:str = None
	spID:str = None
	cseEnvironment = 'Development'
	runtimeDirectory = os.path.dirname(configFile) if configFile else None
	_configFile = os.path.basename(configFile) if configFile else None
	_zookeeperInstance:Optional[Zookeeper.Zookeeper] = None

	def directoriesAndConfigFile() -> None:
		nonlocal runtimeDirectory, _configFile, _zookeeperInstance, zkConfiguration

		if configFile:
			_print(Rule('[b]Directories and Configuration File[/b]', style = 'dim'))
			_print('The following questions determine the runtime data directory and the configuration file.\n')
			runtimeDirectory = inquirer.text(
								message = 'Runtime data directory:',
								default = str(Configuration.Configuration.baseDirectory) if Configuration.Configuration.baseDirectory else os.getcwd(),
								long_instruction = 'The directory under which the configuration file, and the "data", "init" and "log" directories are located.',
								amark = '✓', 
							).execute()
			_configFile = inquirer.text(
								message = 'Configuration file:',
								default = _configFile,
								long_instruction = 'The name of the configuration file in the runtime data directory.',
								amark = '✓', 
							).execute()
		else:
			_print(Rule('[b]Zookeeper[/b]', style = 'dim'))
			_print('You are using Zookeeper for configuration management.\n')
			_print('This means that the configuration will be stored in Zookeeper instead of a local file.\n')
			_print('The following questions determine the Zookeeper configuration.\n')
			_zkHost = inquirer.text(
					message = 'Zookeeper host:',
					default = zkConfiguration[0],
					validate= lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result),
					invalid_message = 'Invalid host name or IP address.',
					long_instruction = 'The host name or IP address of the Zookeeper server.',
					amark = '✓', 
				).execute()
			_zkPort = inquirer.number(
					message = 'Zookeeper port:',
					default = zkConfiguration[1],
					validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
					min_allowed = 1,
					max_allowed = 65535,
					invalid_message = 'Invalid port number.',
					long_instruction = 'The port number of the Zookeeper server.',
					amark = '✓', 
				).execute()
			_zkRoot = inquirer.text(
					message = 'Zookeeper root:',
					default = zkConfiguration[2] if zkConfiguration and zkConfiguration[2] else '',
					long_instruction = 'The root path in the Zookeeper server.\nLeave empty to use the CSE-ID as root path.',
					validate= lambda result: len(result.strip()) == 0 or isValidPath(result.strip()),
					invalid_message = 'Invalid root. Must be a valid path.',
					filter= lambda result: '' if not result else result.strip() if result.startswith('/') else f'/{result.strip()}',
					amark = '✓', 
				).execute()

			try:
				_print()
				with Console().status('Testing Zookeeper connection...'):
					_zookeeperInstance = Zookeeper.Zookeeper(_zkHost, _zkPort, _zkRoot)
					_zookeeperInstance.connect(createRoot=False)
					_zookeeperInstance.disconnect()
			except Exception as e:
				_print(f'\n[red]Error connecting to Zookeeper: {e}')
				raise ConnectionError(f'Could not connect to Zookeeper at {_zkHost}:{_zkPort}') from e
				return
			
			# set the Zookeeper configuration to the new values
			zkConfiguration = (_zkHost, _zkPort, _zkRoot)

	def basicConfig() -> None:
		nonlocal cseType, cseEnvironment, cseSecret
		_print(Rule('[b]Basic Configuration[/b]', style = 'dim'))

		cseEnvironment = inquirer.select(
							message = 'Select the target environment:',
							choices = [	Choice(name = 'Development  - Enable development, testing, and debugging support', 
								   			  value = 'Development'),
										Choice(name = 'Introduction - Install extra demo resources, documentation, and scripts',
											   value = 'Introduction'),
										Choice(name = 'Regular      - Disable development features',
											   value = 'Regular'),
										Choice(name = 'Headless     - Like "regular", plus disable most screen output, and the console and text UIs',
											   value = 'Headless'),
										Choice(name = 'WSGI         - Like "regular", but enable a WSGI server instead of the built-in HTTP server',
											   value = 'WSGI'),
									],
							default = 'Development',
							transformer = lambda result: result.split()[0],
							instruction="(select with cursor keys, confirm with <enter>)", 
							long_instruction = 'Run the CSE for development, for learning, regular operation, or in headless mode.',
							amark = '✓', 
						).execute()
		cseType = inquirer.select(
							message = 'What type of CSE do you want to run:',
							choices = [	Choice(name = 'IN  - Infrastructure Node      - Backend or stand-alone installation', 
								   			  value = 'IN'),
										Choice(name = 'MN  - Middle Node              - Edge device or gateway installation',
											   value = 'MN'),
										Choice(name = 'ASN - Application Service Node - On-device installation',
											   value = 'ASN'),
									  ],
							default = 'IN',
							transformer = lambda result: result.split()[0],
							instruction="(select with cursor keys, confirm with <enter>)", 
							long_instruction = 'Type of CSE to run: Infrastructure, Middle, or Application Service Node.',
							amark = '✓', 
						).execute()
		cseSecret = inquirer.secret(
							message = 'CSE Secret:',
							long_instruction='The secret key to secure credentials used by the CSE. Leave empty to use the default.',
							amark = '✓',
						).execute()


	def cseConfig() -> InquirerPySessionResult:
		_print(Rule('[b]CSE Configuration[/b]', style = 'dim'))
		_print('The following questions determine the basic CSE settings.\n')

		return {
			'cseID': inquirer.text(
						message = 'CSE-ID:',
						default = _iniValues[cseType]['cseID'],
						long_instruction = 'The CSE-ID of the CSE and the resource ID of the CSEBase.',
						validate = lambda result: isValidID(result) or (result.startswith('/') and isValidID(result[1:])) or _containsVariable(result),
						invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits, and the characters [-, _, .].',
						filter= lambda result: result if not result.startswith('/') else result[1:],	# Remove leading slash if present
						amark = '✓', 
					 ).execute(),
			'cseName': inquirer.text(
							message = 'Name of the CSE:',
							default = _iniValues[cseType]['cseName'],
							long_instruction = 'This is the resource name of the CSEBase.',
							validate = lambda result: isValidID(result) or _containsVariable(result),
							amark = '✓', 
							invalid_message = 'Invalid CSE name. Must not be empty and must only contain letters, digits, and the characters [-, _, .].',
						).execute(),
			'serviceProviderID' : inquirer.text(
							message = 'Service Provider ID:',
							default = '//acme.example.com',
							long_instruction = 'This is the ID of the own service provider.',
							validate = lambda result: isValidID(result) or (result.startswith('//') and isValidID(result[2:])) or _containsVariable(result),
							invalid_message = 'Invalid Service Provider ID. Must not be empty and must only contain letters, digits, and the characters [-, _, .] .',
							filter = lambda result: result if result.startswith('//') else f'//{result}',
							amark = '✓',
						).execute(),
			'adminID': inquirer.text(
							message = 'Admin Originator:',
							default = _iniValues[cseType]['adminID'],
							long_instruction = 'The originator who has admin access rights to the CSE and the CSE\'s resources.',
							validate = lambda result: (isValidID(result) and result.startswith('C')) or _containsVariable(result),
							amark = '✓', 
							invalid_message = 'Invalid Originator ID. Must start with "C", must not be empty and must only contain letters, digits, and the characters [-, _, .].',
						).execute(),
			'networkInterface': inquirer.text(
								message = 'Network interface to bind to (IP address):',
								default = _iniValues[cseType]['networkInterface'],
								long_instruction = 'The network interface to listen for requests. Use "0.0.0.0" for all interfaces.',
								validate = lambda result: NetworkTools.isValidateIpAddress(result) or _containsVariable(result),
								amark = '✓', 
								invalid_message = 'Invalid IPv4 or IPv6 address.',
							).execute(),
			'cseHost': inquirer.text(
							message = 'CSE host address (IP address or host name):',
							default = _iniValues[cseType]['cseHost'],
							long_instruction = f'The IP address, or "${{hostIPAddress}}" for the current value ({NetworkTools.getIPAddress()}).',
							validate =  lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result) or _containsVariable(result),
							amark = '✓', 
							invalid_message = 'Invalid IPv4 or IPv6 address or hostname.',
						).execute(),
			'httpPort': inquirer.number(
							message = 'CSE host http port:',
							default = _iniValues[cseType]['httpPort'],
							long_instruction = 'TCP port at which the CSE is reachable for requests.',
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
        					max_allowed = 65535,
							amark = '✓',
							invalid_message = 'Invalid port number. Must be a number between 1 and 65535.',
						).execute(),
			}


	def registrarConfig() -> InquirerPySessionResult:
		_print(Rule('[b]Registrar Configuration[/b]', style = 'dim'))
		_print('The following settings concern the registrar CSE to which this CSE will be registering.\n')

		return {
			'registrarCseID':	inquirer.text(
									message = 'The Registrar CSE-ID:',
									default = _iniValues[cseType]['registrarCseID'],
									long_instruction = 'This is the CSE-ID of the remote (Registrar) CSE.',
									validate = lambda result: isValidID(result) or _containsVariable(result),
									amark = '✓', 
									invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits, and the characters [-, _, .] .',
								).execute(),
			'registrarCseName':	inquirer.text(
									message = 'The Name of the Registrar CSE:',
									default = _iniValues[cseType]['registrarCseName'],
									long_instruction = 'The resource name of the remote (Registrar) CSE.',
									validate = lambda result: isValidID(result) or _containsVariable(result),
									amark = '✓', 
									invalid_message = 'Invalid CSE Name. Must not be empty and must only contain letters, digits, and the characters [-, _, .].',
								).execute(),
			'registrarCseHost':	inquirer.text(
									message = 'The Registrar CSE\' IP address / host name:',
									default = _iniValues[cseType]['registrarCseHost'],
									long_instruction = f'The IP address / host name of the remote (Registrar) CSE, or "${{hostIPAddress}}" for the current value ({NetworkTools.getIPAddress()})',

									validate = lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result) or _containsVariable(result),
									amark = '✓', 
									invalid_message = 'Invalid IPv4 or IPv6 address or hostname.',
								).execute(),
			'registrarCsePort': inquirer.number(
									message = 'The Registrar CSE\' host http port:',
									default = _iniValues[cseType]['registrarCsePort'],
									long_instruction = 'The TCP port of the remote (Registrar) CSE.',
									validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
									min_allowed = 1,
									max_allowed = 65535,
									amark = '✓',
									invalid_message = 'Invalid port number. Must be a number between 1 and 65535.',
								).execute(),
			'INCSEcseID':	inquirer.text(
									message = 'The Infrastructure CSE\'s CSE-ID:',
									default = _iniValues[cseType]['INCSEcseID'],
									long_instruction = 'This is the CSE-ID of the top Infrastructure CSE, NOT the registrar\'s one.',
									validate = lambda result: isValidID(result) or _containsVariable(result),
									amark = '✓', 
									invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits, and the characters [-, _, .] .',
								).execute(),
		}
	

	def spRegistrations() -> dict:
		nonlocal spID

		_print(Rule('[b]Service Provider Registration[/b]', style = 'dim'))
		_print('The following settings concern the service provider registration.')
		_print('This is only relevant for Infrastructure Nodes (IN) in a multi-provider environment.\n')

		spRegistration = False
		result = {}
		if cseType in ['IN']:
			spRegistration = inquirer.confirm(
								message = 'Do you want to register this CSE with one or more service providers\' IN-CSE?',
								default = False,
								long_instruction = 'Register this CSE with one or more service providers\' IN-CSE.'
							).execute()

		if not spRegistration:
			return {}
		
		idx = 0
		_print()
		_print('Please provide the connection parameters for the service provider\'s IN-CSE.\n')
		_continue = True
		while _continue:
			idx += 1
			_print(f'\n[b][u]Service Provider {idx}[/]\n')
			_result = {}

			_result['SPName'] = inquirer.text(
				message = 'Service Provider Name:',
				default = f'sp{idx}',
				long_instruction = 'The name of the service provider.',
				validate= lambda result: (isValidID(result) or _containsVariable(result)) and not result.endswith('.security'),
				invalid_message = 'Invalid Service Provider Name. Must not be empty and must only contain letters, digits, and the characters [-, _, .] and must not end with ".security".',
				amark = '✓',
			).execute()
			_result['SPID'] = inquirer.text(
				message = 'Service Provider ID:',
				default = f'sp-{idx}.example.com',
				validate = lambda result: isValidID(result) or (result.startswith('//') and isValidID(result[2:])) or _containsVariable(result),
				invalid_message = 'Invalid Service Provider ID. Must not be empty and must only contain letters, digits, and the characters [-, _, .] .',
				filter = lambda result: result if not result.startswith('//') else result[2:],
				long_instruction = 'The ID of the service provider.',
				amark = '✓',
			).execute()
			_result['SPCSEID'] = inquirer.text(
				message = 'Service Provider\'s IN-CSE CSE-ID:',
				default = f'sp-{idx}-id-in',
				amark = '✓',
				long_instruction = 'The CSE-ID of the service provider\'s IN-CSE.',
				validate = lambda result: isValidID(result) or (result.startswith('/') and isValidID(result[1:])) or _containsVariable(result),
				invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits, and the characters [-, _, .] .',
				filter = lambda result: result if not result.startswith('/') else result[1:],	# Remove leading slash if present

			).execute()
			_result['SPCSERN'] = inquirer.text(
				message = 'Service Provider\'s IN-CSE Resource Name:',
				default = f'sp-{idx}-cse-in',
				long_instruction = 'The resource name of the service provider\'s IN-CSE.',
				amark = '✓',
				validate = lambda result: isValidID(result) or _containsVariable(result),
				invalid_message = 'Invalid CSE Name. Must not be empty and must only contain letters, digits, and the characters [-, _, .].',
			).execute()
			_result['url'] = inquirer.text(
				message = 'Service Provider URL Address:',
				default = f'http://${{basic.config:registrarCseHost}}:{8080 + (idx*100)}',
				# default = f'http://sp-{idx}.example.com:8080',
				long_instruction = 'The address (URL) of the service provider.',
				validate= lambda result: NetworkTools.isValidURL(result) or _containsVariable(result),
				invalid_message = 'Invalid URL.',
				amark = '✓',
			).execute()

			result[_result['SPName']] = _result

			_print('\n')
			_continue = inquirer.confirm(
				message = 'Do you want to add another service provider?',
				default = False,
				long_instruction = 'Add another service provider\'s IN-CSE to register with.'
			).execute()

		return result
		

	def csePolicies() -> InquirerPySessionResult:
		""" Prompts for CSE policies. 

			Return:
				A dictionary with the selected policies.
		"""
		_print(Rule('[b]CSE Policies[/b]', style = 'dim'))
		_print('The following configuration settings determine miscellaneous CSE policies.\n')

		return {
			'logLevel': inquirer.select(
							message = 'Log level:',
							choices = [ 'debug', 'info', 'warning', 'error', 'off' ],
							default = 'debug' if cseEnvironment in ('Development') else 'warning',
							instruction="(select with cursor keys, confirm with <enter>)", 
							long_instruction = 'Set the logging verbosity',
							amark = '✓',
						).execute(),
			'consoleTheme': inquirer.select(
								message = 'Console and Text UI Theme:',
								choices = [ Choice(name = 'Dark', 
												value = 'dark'),
											Choice(name = 'Light', 
												value = 'light'),
										],
								default = 'dark',
								instruction="(select with cursor keys, confirm with <enter>)", 
								long_instruction = 'Set the console and Text UI theme',
								amark = '✓',
							).execute(),
			}


	def cseDatabase() -> InquirerPySessionResult:
		""" Prompts for CSE Database settings. 

			Return:
				A dictionary with the selected policies.
		"""
		_print(Rule('[b]Database Configuration[/b]', style = 'dim'))
		_print('The following configuration settings determine the database configuration.\n')

		dbType = inquirer.select(
							message = 'Database type:',
							choices = [ Choice(name = 'memory     - Faster, but data is lost when the CSE terminates', 
			  								   value = 'memory'),
		  								Choice(name = 'TinyDB     - Simple but fast file-based database', 
		   									   value = 'tinydb'),
		  								Choice(name = 'PostgreSQL - Data is stored in a separate PostgreSQL database', 
		   									   value = 'postgresql'),
									  ],
							default = 'memory' if cseEnvironment in ('Development', 'Introduction') else 'tinydb',
							transformer = lambda result: result.split()[0],
							instruction="(select with cursor keys, confirm with <enter>)", 
							long_instruction = 'Store data in memory, or persist in a database.',
							amark = '✓',
						).execute()
		if dbType == 'postgresql':
			_print('\n[b][u]PostgreSQL configuration[/]\n')
			_print('Please provide the connection parameters for the PostgreSQL database.\n')
			return {
				'databaseType': dbType,
				'dbName': inquirer.text(
							message = 'Database name:',
							default = cseID,
							long_instruction = 'The name of the PostgreSQL database.',
							amark = '✓', 
						).execute(),
				'dbSchema': inquirer.text(
							message = 'Database schema:',
							default = 'acmecse',
							long_instruction = 'The schema name of the PostgreSQL database.',
							amark = '✓',
						).execute(),
				'dbUser': inquirer.text(
							message = 'Database role:',
							default = cseID,
							long_instruction = 'The role/user name to connect to the PostgreSQL database.',
							amark = '✓', 
						).execute(),
				'dbPassword': inquirer.secret(
							message = 'Database password:',
							long_instruction = 'The password to connect to the PostgreSQL database.',
							amark = '✓', 
						).execute(),
				'dbHost': inquirer.text(
							message = 'Database host:',
							default = 'localhost',
							long_instruction = 'The host name or IP address of the PostgreSQL database server.',
							amark = '✓', 
						).execute(),
				'dbPort': inquirer.number(
							message = 'Database port:',
							default = 5432,
							long_instruction = 'The port number of the PostgreSQL database server.',
							amark = '✓', 
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
							max_allowed = 65535,
						).execute(),
			}
		else:
			return {
				'databaseType': dbType
			}


	def cseBindings() -> dict:
		""" Prompts for CSE Protocol Bindings settings. 

			Return:
				A dictionary with the selected policies.
		"""
		_print(Rule('[b]Protocol Bindings Configuration[/b]', style = 'dim'))
		_print('The following allows to enable additional protocol bindings.\n')

		bindings = inquirer.checkbox(
			message='Select additional bindings to enable:',
        	choices=['MQTT', 'CoAP', 'WebSocket'],
	        instruction="(select with cursor keys and <space>, confirm with <enter>)", 
			long_instruction='Enable additional protocol bindings in addition to HTTP.',
			amark='✓',
			transformer=lambda result: ', '.join(result),

    	).execute()

		result = {}
		if 'MQTT' in bindings:
			_print('\n[b][u]MQTT configuration[/]\n')
			_print('Please provide the connection parameters for the MQTT broker.\n')
			result['mqtt'] = {
				'address': inquirer.text(
							message = 'MQTT broker host address:',
							default = 'localhost',
							long_instruction = 'The host name or IP address of the MQTT broker.',
							amark = '✓', 
							validate = lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result) or _containsVariable(result),
						).execute(),
				'port': inquirer.number(
							message = 'MQTT broker port:',
							default = 1883,
							long_instruction = 'The port number of the MQTT broker.',
							amark = '✓', 
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
							max_allowed = 65535,
						).execute(),
				'username': inquirer.text(
							message = 'MQTT broker username:',
							long_instruction = 'The username to connect to the MQTT broker. Leave empty for no authentication.',
							amark = '✓', 
						).execute(),
				'password': inquirer.secret(
							message = 'MQTT broker password:',
							long_instruction = 'The password to connect to the MQTT broker. Leave empty for no authentication.',
							amark = '✓', 
						).execute(),
				'transport': (transport := inquirer.text(
							message = 'MQTT transport protocol:',
							default= 'tcp',
							long_instruction = 'The transport protocol for mqtt only could be "tcp" or "websockets".',
							validate = lambda result: result in ['tcp', 'websockets'] or _containsVariable(result),
							amark = '✓',
						).execute()),
				**({
					'websocketPath': inquirer.text(
                message='WebSocket path:',
                default='/',
                long_instruction='The WebSocket path for MQTT over WebSockets connection.',
                amark='✓',
            ).execute()
        		} if transport == 'websockets' or (_containsVariable(transport) and 'websockets' in transport) else {})
			}
		
		if 'CoAP' in bindings:
			_print('\n[b][u]CoAP configuration[/]\n')
			_print('Please provide the connection parameters for the CoAP server.\n')
			result['coap'] = {
				'port': inquirer.number(
							message = 'CoAP server port:',
							default = 5683,
							long_instruction = 'The listening port number of the CoAP server.',
							amark = '✓', 
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
							max_allowed = 65535,
						).execute(),
			}
		
		if 'WebSocket' in bindings:
			_print('\n[b][u]WebSocket configuration[/]\n')
			_print('Please provide the connection parameters for the WebSocket server.\n')
			result['websocket'] = {
				'port': inquirer.number(
							message = 'WebSocket server port:',
							default = 8180,
							long_instruction = 'The listening port number of the WebSocket server.',
							amark = '✓', 
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
							max_allowed = 65535,
						).execute(),
			}

		return result



	#
	#	On-boarding Dialog

	Console().clear()
	cnf:List[str] = []

	try:
		_print(Rule(f'[b]Creating a New {Constants.textLogo} Configuration File', characters = '═', style = Style(color = Constants.logoColor)))
		_print('The following steps will create a new configuration file for the ACME CSE.\n')
		_print('Press CTRL-C to abort at any time.\n')
		
		
		# Prompt for directories and configuration file
		directoriesAndConfigFile()

		# Prompt for basic configuration
		basicConfig()
		cnf.append(f'cseType={cseType}')
	
		# Prompt for the CSE configuration
		for each in (bc := cseConfig()):
			cnf.append(f'{each}={bc[each]}')
		cseID = cast(str, bc['cseID'])

		# Add the CSE secret
		if cseSecret:
			cnf.append(f'secret={cseSecret}')

		
		# Prompt for registrar configuration
		match cseType:
			case 'IN':
				# Prompt for Service Provider registration
				spRegistration = spRegistrations()

			case 'MN' | 'ASN':
				for each in (regCnf := registrarConfig()):
					if each == 'INCSEcseID':
						continue
					cnf.append(f'{each}={regCnf[each]}')
				spRegistration = None


		# Prompt for the CSE database settings

		dbc = cseDatabase()
		cnf.append(f'databaseType={dbc["databaseType"]}')


		# Prompt for additional protocol bindings
		bindings = cseBindings()
		
		# Prompt for the CSE policies
		for each in (policyConfig := csePolicies()):
			cnf.append(f'{each}={policyConfig[each]}')


		cnfHeader = \
f"""\
; {configFile}
;
; Auto-generated configuration file for the [ACME] CSE.
;
; This file was created by the on-boarding process and can be modified manually by
; editing the values below, or by adding new sections to override the default values.
;
; The file is in the INI format. Lines starting with a semicolon (;) are comments.
; The configuration is divided into sections, each section starting with a section
; name in square brackets ([section.name]). The section name is followed by a list
; of key-value pairs, one per line, in the format key=value. The key and value are
; separated by an equal sign (=).
; 
; created: {datetime.now().isoformat(" ", "seconds")}
;
; CSE type: {cseType}
; Environment: {cseEnvironment}
;

"""

		cnfExtra = \
f"""

[cse.registration]
; Edit this to add more allowed originators.
allowedCSROriginators=id-in,id-mn,id-asn"""	# <- keep on same line. Will be extended below

		cnfRegular = \
"""

"""


		cnfDevelopment = \
"""
[textui]
startWithTUI=false

[cse.operation.requests]
enable=true

[http]
enableUpperTesterEndpoint=true
enableStructureEndpoint=true
"""

		cnfIntroduction = \
"""
[textui]
startWithTUI=true

[cse.operation.requests]
enable=true

[scripting]
scriptDirectories=${cse:resourcesPath}/demoLightbulb,${cse:resourcesPath}/demoDocumentationTutorials
"""

		cnfHeadless = \
"""
[console]
headless=True
"""

		cnfWSGI = \
"""
[http.wsgi]
enable=True
"""

		if dbc['databaseType'] == 'postgresql':
			cnfPostgreSQL = \
f"""
[database.postgresql]
database={dbc["dbName"]}
host={dbc["dbHost"]}
password={dbc["dbPassword"]}
port={dbc["dbPort"]}
role={dbc["dbUser"]}
schema={dbc["dbSchema"]}
"""
		else:
			cnfPostgreSQL = ''

		#
		#	Construct registrar configuration
		#

		if cseType in [ 'MN', 'ASN' ]:
			cnfRegistrar = \
f"""
[cse.registrar]
INCSEcseID=/{regCnf["INCSEcseID"]}
"""
		else:
			cnfRegistrar = ''
		
		#
		#	Construct the SP registration configuration
		#	Add to the cnfRegistrar part
		#

		if spRegistration:
			# Add SPs to the allowedCSROriginators list
			for spID, spCnf in spRegistration.items():
				cnfRegistrar += f',//{spCnf["SPID"]}/{spCnf["SPCSEID"]}'
			cnfRegistrar += '\n'

			# Generate the registrar configuration for each SP
			for spID, spCnf in spRegistration.items():
				cnfRegistrar += '\n'
				cnfRegistrar += f'[cse.sp.registrar.{spID}]\n'
				cnfRegistrar += f'spID=//{spCnf["SPID"]}\n'
				cnfRegistrar += f'cseID=/{spCnf["SPCSEID"]}\n'
				cnfRegistrar += f'resourceName={spCnf["SPCSERN"]}\n'
				cnfRegistrar += f'address={spCnf["url"]}\n'
		else:
			cnfRegistrar = '\n'

		#
		#	Construct the configuration
		#

		jcnf = '[basic.config]\n' + '\n'.join(cnf) + cnfExtra + cnfRegistrar

		# add more mode-specific configurations
		match cseEnvironment:
			case 'Regular':
				jcnf += cnfRegular
			case 'Development':
				jcnf += cnfDevelopment
			case 'Introduction':
				jcnf += cnfIntroduction
			case 'Headless':
				jcnf += cnfHeadless
			case 'WSGI':
				jcnf += cnfWSGI
		
		# Add the database configuration
		jcnf += cnfPostgreSQL



		# Add MQTT, CoAP, WebSocket configuration

		if 'mqtt' in bindings:
			jcnf += \
f"""
[mqtt]
enable=true
address={bindings['mqtt']['address']}
port={bindings['mqtt']['port']}
transport={bindings['mqtt']['transport']}
websocketPath={bindings['mqtt']['websocketPath'] if bindings['mqtt']['transport'] == 'websockets' else 'None'}
"""
			if bindings['mqtt']['transport'] == 'tcp':
				jcnf += f"""
"""
			if bindings['mqtt']['username']:
				jcnf += f"""
[mqtt.security]
username={bindings['mqtt']['username']}
password={bindings['mqtt']['password']}
"""
				
		if 'coap' in bindings:
			jcnf += \
f"""
[coap]
enable=true
port={bindings['coap']['port']}
"""
			
		if 'websocket' in bindings:
			jcnf += \
f"""
[websocket]
enable=true
port={bindings['websocket']['port']}
"""


		# Show configuration and confirm write
		_print(Rule('[b][b]Saving Configuration[/b]', style = 'dim'))
		_jcnf = jcnf.replace('[', r'\[')
		_print(f'[dim]{_jcnf}\n')

		# If the configuration file is provided, ask for confirmation to write the configuration file
		if configFile:

			configFile = f'{runtimeDirectory}{os.sep}{_configFile}'
			if not inquirer.confirm	(message = f'Write configuration to file "{configFile}"?', 
									default = True,
									long_instruction = 'Create the configuration file.',
									amark = '✓'
									).execute():
				_print('\n[red]Configuration canceled\n')
				return False, None, None
			
			try:
				os.makedirs(os.path.dirname(configFile), exist_ok=True)
				with open(configFile, 'w') as file:
					file.write(cnfHeader)
					file.write(jcnf)
			except Exception as e:
				_print(str(e))
				return False, None, None

		
		# Write to ZooKeeper if zkConfiguration is provided
		else:
			zkConfiguration = (zkConfiguration[0], zkConfiguration[1], zkConfiguration[2] or f'/{cseID}'	)
			if not inquirer.confirm	(message = f'Write configuration to ZooKeeper at {zkConfiguration[2]}?', 
									default = True,
									long_instruction = 'Create the configuration in ZooKeeper.',
									amark = '✓'
									).execute():
				_print('\n[red]Configuration canceled\n')
				return False, None, None

			# Open a connection to ZooKeeper and check if the root path already exists
			_zookeeperInstance = Zookeeper.Zookeeper(zkConfiguration[0], zkConfiguration[1], zkConfiguration[2])
			_zookeeperInstance.connect(False)

			if _zookeeperInstance.exists(zkConfiguration[2]): 			# zkConfiguration is a tuple of (host, port, rootPath)
				# If the root path already exists, ask for confirmation to overwrite it
				if not overwrite and not inquirer.confirm(
						message = f'ZooKeeper configuration "{zkConfiguration[2]}" already exists. Overwrite it?',
						default = False,
						long_instruction = 'Overwrite the existing ZooKeeper configuration.',
						amark = '✓'
					).execute():
					_print('\n[red]Configuration canceled\n')
					_zookeeperInstance.disconnect()
					return False, None, None

				# delete the existing root path
				with Console().status('Deleting existing ZooKeeper configuration...'):
					_zookeeperInstance.delete(zkConfiguration[2])

			with Console().status('Writing configuration to ZooKeeper...'):
				try:
					# create the root path 
					_zookeeperInstance.addKeyValue(zkConfiguration[2])
					
					# Write the configuration to ZooKeeper and disconnect afterwards
					_zookeeperInstance.storeIniConfig(jcnf, zkConfiguration[2])
				except Exception as e:
					_print(f'\n[red]Error writing configuration to ZooKeeper: {e}')
					return False, None, None
				finally:
					_zookeeperInstance.disconnect()

	except (KeyboardInterrupt, ConnectionError):
		_print('\n[red]Configuration canceled\n')
		return False, None, None

	_print(f'\n[spring_green2]New {cseType}-CSE configuration created.\n')
	return True, configFile, runtimeDirectory

