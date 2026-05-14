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
from typing import cast, Tuple, Optional
import os, re, io
from datetime import datetime

from InquirerPy import inquirer
from InquirerPy.utils import InquirerPySessionResult
from InquirerPy.base import Choice
from InquirerPy.separator import Separator

from rich.console import Console
from rich.rule import Rule
from rich.panel import Panel
from rich.table import Table
from rich.progress_bar import ProgressBar
from rich.style import Style
from rich.syntax import Syntax

from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.IDUtils import isValidID, isValidPath
from ..helpers import Zookeeper, ACMEConfiguration, NetworkTools
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

console = Console()
""" The console to use for printing messages. """

totalSteps = 20
currentStep = -1
progressBar = ProgressBar(total=totalSteps, completed=currentStep, complete_style=Style(color=Constants.logoColor))

configParser = ACMEConfiguration.ACMEConfiguration()
cseEnvironment = 'None selected'



def _print(msg:str|Rule|Syntax='\n', clearScreen:Optional[bool]=True) -> None:
	""" Print a message to the console.
	
		Args:
			msg: The message to print. Could be a string, a Rule, or a Syntax object.
			clearScreen: If True, clear the console before printing the message.
	"""
	if not RC.isHeadless:
		console.print(msg, highlight=True)	# Print error message to console


def _incrementStep(count: int = 1) -> None:
	""" Increment the current step and update the progress bar. """
	global currentStep
	currentStep += count
	progressBar.update(currentStep)


def _printRule(title:str, extras:Optional[str]=None) -> None:
	
	# Update the progress bar each time a step is printed
	_incrementStep()

	if not RC.isHeadless:
		console.clear()
		_table = Table.grid(expand=True)
		_table.add_row('')
		_table.add_row('The following steps will create a new configuration for the ACME CSE.')
		_table.add_row('')
		_table.add_row(f'Selected environment: [{Constants.secondaryLogoColor}]{cseEnvironment}[/]')
		_table.add_row('')
		_table.add_row('Press CTRL-C to abort at any time.')
		_table.add_row('')
		if extras:
			_table.add_row(progressBar)
			_table.add_row('')
			_table.add_row(extras)
			_table.add_row('')
		
		console.print(Panel(_table,
			title=f'{Constants.textLogo} Onboarding',
			subtitle=f'[{Constants.secondaryLogoColor}]{title}[/]',
			subtitle_align='center',
		))

		console.print('\n')


def _printHeader(title:str) -> None:
	""" Print a header with the given title.
	
		Args:
			title: The title to print.
	"""
	if not RC.isHeadless:
		console.print(f'\n[{Constants.tertiaryLogoColor}]{title}[/]\n', highlight=False)


def _setOption(config:ACMEConfiguration.ACMEConfiguration, 
			   section:str, 
			   option:str, 
			   value:str, 
			   toLower:Optional[bool]=False,
			   force:Optional[bool]=False) -> str:

	if value is None:
		return None
	
	# Only set the option if it is not the default
	_configValue = configParser.get(section, option)
	_configValue = str(_configValue).lower() if toLower else str(_configValue)
	value = str(value).lower() if toLower else str(value)

	if value != _configValue or force:
		# Only set the option if it does not exist yet or if force is True
		if not config.has_option(section, option):
			config.set(section, option, value)
	
	return value


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
	global cseEnvironment
	cseType = 'IN'
	cseID:str = None
	cseSecret:str = None
	spID:str = None
	runtimeDirectory = os.path.dirname(configFile) if configFile else None
	enDisFeatures:dict = {}
	_configFile = os.path.basename(configFile) if configFile else None
	_zookeeperInstance:Optional[Zookeeper.Zookeeper] = None

	def directoriesAndConfigFile() -> None:
		nonlocal runtimeDirectory, _configFile, _zookeeperInstance, zkConfiguration

		if configFile:
			_printRule('Directories and Configuration File', 
			  		   'The following questions determine the runtime data directory and the configuration file.')
			runtimeDirectory = inquirer.text(
								message='Runtime data directory:',
								default=str(Configuration.Configuration.baseDirectory) if Configuration.Configuration.baseDirectory else os.getcwd(),
								long_instruction='The directory under which the configuration file, and the "data", "init" and "log" directories are located.',
								amark='✓',
							).execute()
			_configFile = inquirer.text(
								message='Configuration file:',
								default=_configFile,
								long_instruction='The name of the configuration file in the runtime data directory.',
								amark='✓',
							).execute()
		else:
			_printRule('Zookeeper Server Configuration',
					   'You are using Zookeeper for configuration management.\n\nThis means that the configuration will be stored in Zookeeper instead of a local file.\n\nThe following questions determine the Zookeeper configuration.')
			_zkHost = inquirer.text(
					message='Zookeeper host:',
					default=zkConfiguration[0],
					validate=lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result),
					invalid_message='Invalid host name or IP address.',
					long_instruction='The host name or IP address of the Zookeeper server.',
					amark='✓',
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
					validate=lambda result: len(result.strip()) == 0 or isValidPath(result.strip()),
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
				_print(f'\n[red]Error connecting to the Zookeeper server: {e}')
				raise ConnectionError(f'Could not connect to the Zookeeper server at {_zkHost}:{_zkPort}') from e
			
			# set the Zookeeper configuration to the new values
			zkConfiguration = (_zkHost, _zkPort, _zkRoot)


	def basicConfig() -> None:
		nonlocal cseType, cseSecret
		global cseEnvironment

		_printRule('Basic Configuration',
			 	   'The following questions determine the basic CSE features and settings.')

		cseEnvironment = inquirer.select(
							message = 'Select the target features:',
							choices = [	Choice(name='Development  - Enable development, testing, and debugging support', 
								   			  value='Development'),
										Choice(name='Introduction - Install extra demo resources, documentation, and scripts',
											   value='Introduction'),
										Choice(name='Regular      - Disable development features',
											   value='Regular'),
										Choice(name='Minimal      - Disable most optional runtime features for a minimal setup',
				 							   value='Minimal'),
										Choice(name='Headless     - Like "regular", plus disable most screen output, and the console and text UIs',
											   value='Headless'),
										Choice(name='ETSI MEC     - Like "regular", but enable ETSI MEC support',
											   value='ETSI MEC'),
									],
							default='Development',
							transformer=lambda result: result.split()[0],
							instruction="(select with cursor keys, confirm with <enter>)", 
							long_instruction='Run the CSE for development, for learning, regular operation, or in headless mode.',
							amark='✓', 
						).execute()

		# Print header again because the environment selection has changed
		_printRule('Basic Configuration',
			 	   'The following questions determine the basic CSE features and settings.')

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
		_printRule('CSE Configuration',
			 	   'The following questions determine the CSE Identifier settings.')

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
			}


	def registrarConfig() -> InquirerPySessionResult:
		_printRule('Registrar Configuration',
				   'The following settings concern the registrar CSE to which this CSE will be registering.')

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
	

	def csePolicies() -> InquirerPySessionResult:
		""" Prompts for CSE policies. 

			Return:
				A dictionary with the selected policies.
		"""
		_printRule('CSE Policies',
			 	   'The following configuration settings determine miscellaneous CSE policies.')

		return {
			'logLevel': inquirer.select(
							message = 'Log level:',
							choices = [ 'debug', 'info', 'warning', 'error', 'off' ],
							default = 'debug' if cseEnvironment in ('Development') else 'warning',
							instruction="(select with cursor keys, confirm with <enter>)", 
							long_instruction = 'Set the logging verbosity',
							amark = '✓',
						).execute()
			}


	def cseUIs() -> InquirerPySessionResult:
		""" Prompts for CSE UI settings. 

			Return:
				A dictionary with the selected UI settings.
		"""
		_printRule('CSE UI Settings',
			 	   'The following configuration settings determine miscellaneous CSE UI settings.')

		result:InquirerPySessionResult = {}
		if cseEnvironment not in ('Headless'):
			result.update({

				'consoleType': inquirer.select(
									message = 'Console Type:',
									choices = [ Choice(name = 'Rich   - Full featured console all commands and features', 
													value = 'rich'),
												Choice(name = 'Simple - Minimal console for basic output.', 
													value = 'simple'),
											],
									default = 'simple' if cseEnvironment in ('Minimal') else 'rich',
									instruction="(select with cursor keys, confirm with <enter>)", 
									long_instruction = 'Set the console type.',
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
				'enableTextUI': inquirer.confirm(
									message = 'Enable the Text UI:',
									default = False if cseEnvironment in ('Minimal', 'Headless') else True,
									long_instruction = 'Enable or disable the rich Text UI.',
									amark = '✓',
								).execute()
				})
		else:
			# In headless mode, set the UI settings to the default values for headless mode
			result.update({
				'consoleType': 'simple',
				'consoleTheme': 'dark',
				'enableTextUI': 'false',
			})
			
		if bindings['http']['enable']:
			result.update({
				'enableWebUI': inquirer.confirm(
								message = 'Enable the Web UI:',
								default = False if cseEnvironment in ('Minimal', 'Headless') else True,
								long_instruction = 'Enable or disable the Web UI.',
								amark = '✓',
							).execute(),
			})
		return result


	def cseDatabase() -> InquirerPySessionResult:
		""" Prompts for CSE Database settings. 

			Return:
				A dictionary with the selected policies.
		"""
		_printRule('Database Configuration',
				   'The following configuration settings determine the database configuration.')

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
		_printRule('Protocol Bindings Configuration',
				   'The following allows to enable additional protocol bindings.')

		bindings = inquirer.checkbox(
			message='Select bindings to enable:',
        	choices=[
				Choice('HTTP', enabled=True),
				Choice('MQTT'),
				Choice('MQTT over WebSocket'),
				Choice('CoAP'),
				Choice('WebSocket'),
			],
	        instruction='(select at least one with cursor keys and <space>, confirm with <enter>)' , 
			long_instruction='Enable additional protocol bindings in addition to HTTP',
			amark='✓',
			transformer=lambda result: ', '.join(result),
			validate=lambda result: len(result) > 0,
			invalid_message='At least one binding must be selected.'
    	).execute()

		result = {}

		if 'HTTP' in bindings:
			_print('\n[b][u]HTTP configuration[/]\n')
			_print('Please provide the connection parameters for the HTTP server.\n')

			result['http'] = {
				'enable': 'true',
			}
			onboardingConfig['basic.config']['httpPort'] = inquirer.number(
							message = 'HTTP server port:',
							default = _iniValues[cseType]['httpPort'],
							long_instruction = 'The listening port number of the CSE\'s HTTP server.',
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
        					max_allowed = 65535,
							amark = '✓',
							invalid_message = 'Invalid port number. Must be a number between 1 and 65535.',
						).execute()

		else:
			result['http'] = {
				'enable': 'true',
			}
			onboardingConfig['basic.config']['httpPort'] = str(_iniValues[cseType]['httpPort'])

		if 'MQTT' in bindings or 'MQTT over WebSocket' in bindings:
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
			}

		if 'MQTT over WebSocket' in bindings:
			_print('\n[b][u]MQTT over WebSocket configuration[/]\n')
			_print('Please provide the connection parameters for the MQTT over WebSocket connection.\n')
			result['mqtt.websocket'] = {
				'enable': 'true',
				'path': inquirer.text(
					message='WebSocket URL path:',
					default='',
					long_instruction='The path for the WebSocket URL for MQTT over WebSockets connection.',
					amark='✓',
				).execute(),
				'port': inquirer.number(
							message = 'MQTT WebSocket port:',
							default = 8080,
							long_instruction = 'The WebSocket port number of the MQTT broker.',
							amark = '✓', 
							validate = lambda result: NetworkTools.isValidPort(result) or _containsVariable(result),
							min_allowed = 1,
							max_allowed = 65535,
						).execute(),
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


	def enableDisableFeatures() -> dict:
		""" Prompts for enable/disable features.

			Return:
				A dictionary with the selected features.
		"""
		_printRule('Enable/Disable Features',
				   f'The following configuration settings concern enabled and disabled features of the CSE.\n\nThis allows to disable certain features for a more minimal setup, or to enable extra features for development and testing purposes.')

		endis = {
			'action': cseEnvironment != 'Minimal',
			'group': cseEnvironment != 'Minimal',
			'location': cseEnvironment != 'Minimal',
			'semantic': cseEnvironment != 'Minimal',
			'statistics': cseEnvironment != 'Minimal',
			'time': cseEnvironment != 'Minimal',
			'timeseries': cseEnvironment != 'Minimal',
			'remotecse': cseEnvironment != 'Minimal',
			'announcement': cseEnvironment != 'Minimal',
			'httpmanagement': cseEnvironment in ('Development', 'Introduction', 'Regular', 'ETSI MEC'),
			'httpstructure': cseEnvironment in ('Development', 'Introduction', 'Regular', 'ETSI MEC'),
			'httpuppertester': cseEnvironment in ('Development', 'Introduction'),
		}
		if not inquirer.confirm(
				message='Do you want to enable or disable features?',
				default=False,
				long_instruction='Configure enabled/disabled features for the CSE.'
			).execute():
			onboardingConfig['http']['enableManagementEndpoint'] = str(endis.get('httpmanagement', configParser.getboolean('http', 'enableManagementEndpoint'))).lower()
			onboardingConfig['http']['enableStructureEndpoint'] = str(endis.get('httpstructure', configParser.getboolean('http', 'enableStructureEndpoint'))).lower()
			onboardingConfig['http']['enableUpperTesterEndpoint'] = str(endis.get('httpuppertester', configParser.getboolean('http', 'enableUpperTesterEndpoint'))).lower()
			return endis
	
		generalFeatures = inquirer.checkbox(
			message='Select GENERAL service features to enable:',
        	choices=[
				Choice('action', 'Action Handling', enabled=endis['action']),
				Choice('group', 'Group Management', enabled=endis['group']),
				Choice('location', 'Location Services', enabled=endis['location']),
				Choice('semantic', 'Semantic Support', enabled=endis['semantic']),
				Choice('statistics', 'Statistics', enabled=endis['statistics']),
				Choice('time', 'Time Services', enabled=endis['time']),
				Choice('timeseries', 'Time Series Support', enabled=endis['timeseries']),
			],
	        instruction='(select with cursor keys and <space>, confirm with <enter>)' , 
			long_instruction='Enable or disable certain CSE features',
			amark='✓',
			transformer=lambda result: ', '.join(result)
    	).execute()

		remoteFeatures = inquirer.checkbox(
			message='Select REMOTE service features to enable:',
        	choices=[
				Choice('remotecse', 'RemoteCSE', enabled=endis['remotecse']),
				Choice('announcement', 'Announcement', enabled=endis['announcement']),
			],
	        instruction='(select with cursor keys and <space>, confirm with <enter>)' , 
			long_instruction='Enable or disable remote CSE features',
			amark='✓',
			transformer=lambda result: ', '.join(result),
			validate=lambda result: False if ('announcement' in result and 'remotecse' not in result) else True,
			invalid_message='The "Announcement" feature requires the "RemoteCSE" feature to be enabled.',
    	).execute()

		# HTTP features are added to the onboardingConfig because they are needed later
		if onboardingConfig['http']['enable'].lower() == 'true':
			httpFeatures = inquirer.checkbox(
				message='Select HTTP API features to enable:',
				choices=[
					Choice('httpmanagement', 'HTTP Management API', enabled=endis['httpmanagement']),
					Choice('httpstructure', 'HTTP Structure API', enabled=endis['httpstructure']),
					Choice('httpuppertester', 'HTTP Upper Tester API', enabled=endis['httpuppertester']),
				],
				instruction='(select with cursor keys and <space>, confirm with <enter>)' , 
				long_instruction='Enable or disable certain CSE features',
				amark='✓',
				transformer=lambda result: ', '.join(result)
			).execute()
			onboardingConfig['http']['enableManagementEndpoint'] = 'true' if 'httpmanagement' in httpFeatures else 'false'
			onboardingConfig['http']['enableStructureEndpoint'] = 'true' if 'httpstructure' in httpFeatures else 'false'
			onboardingConfig['http']['enableUpperTesterEndpoint'] = 'true' if 'httpuppertester' in httpFeatures else 'false'

		return { k: True if k in generalFeatures + remoteFeatures else False for k in endis.keys() }


	def advancedSettings() -> dict:
		""" Prompts for advanced settings. 

			Return:
				A dictionary with the selected policies.
		"""

		def advancedCSE() -> dict:
			""" Prompts for advanced CSE settings.

				Return:
					A dictionary with the CSE settings.
			"""

			_printRule('Advanced - CSE Configuration',
					   'The following configuration settings concern advanced features of the CSE.')

			if inquirer.confirm(
					message='Do you want to configure advanced CSE settings?',
					default=False,
					long_instruction='Set advanced CSE settings, such as release version, serialization format etc',
					amark='✓',
				).execute():
				return {
					'releaseVersion': inquirer.select(
						message="The CSE's release version:",
						choices=[Choice(name='2a', value='2a'),
								Choice(name='3', value='3'),
								Choice(name='4', value='4'),
								Choice(name='5', value='5')
								],
						default=configParser.get('cse', 'releaseVersion'),
						long_instruction='The release version of the CSE.',
						amark='✓'
					).execute(),
					'supportedReleaseVersions': inquirer.checkbox(
								message='Select the supported release versions:',
								choices=[Choice('2a', enabled=True),
										Choice('3', enabled=True),
										Choice('4', enabled=True),
										Choice('5', enabled=True)
										],
								instruction="(select with cursor keys and <space>, confirm with <enter>)",
								long_instruction='Enable the supported release versions of the CSE.',
								amark='✓',
								transformer=lambda result: ', '.join(result),
					).execute(),
					'defaultSerialization': inquirer.select(
						message='Default serialization format for requests and responses by the CSE:',
						choices=[
							Choice(name='JSON', value='json'),
							Choice(name='CBOR', value='cbor'),
						],
						default=configParser.get('cse', 'defaultSerialization'),
						long_instruction='The default serialization format for requests and responses by the CSE.',
						amark='✓'
					).execute(),
					'enableSubscriptionVerificationRequests': inquirer.confirm(
						message='Enable subscription verification requests?',
						default=configParser.getboolean('cse', 'enableSubscriptionVerificationRequests'),
						long_instruction='Whether the CSE will send verification requests to notification targets\nwhen a subscription is created.',
						amark='✓'
					).execute(),
					'idLength': inquirer.number(
						message='Length of generated IDs:',
						default=configParser.getint('cse', 'idLength'),
						long_instruction='The length of generated IDs for resources, responses etc.\nThis number should be chosen carefully, as it determines the uniqueness of IDs.',
						min_allowed=5,
						filter=lambda result: int(result),
						amark='✓'
					).execute()
				}
			else:
				return {}


		def spRegistrations() -> dict:
			nonlocal spID

			# Disable automatically if remoteCSE feature is not enabled before
			if not enDisFeatures.get('remotecse', False):
				return {}

			_printRule('Advanced - Service Provider Registration',
					   'The following settings concern the service provider registration.\n\nThis is only relevant for Infrastructure Nodes (IN) in a multi-provider environment.')

			spRegistration = False
			result = {}
			if cseType in ['IN']:
				spRegistration = inquirer.confirm(
									message="Do you want to register this CSE with one or more service providers' IN-CSE?",
									default=False,
									long_instruction="Register this CSE with one or more service providers' IN-CSE."
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
					invalid_message = 'Invalid Service Provider Name. Must not be empty and must only contain letters, digits,\nand the characters [-, _, .] and must not end with ".security".',
					amark = '✓',
				).execute()
				_result['SPID'] = inquirer.text(
					message = 'Service Provider ID:',
					default = f'sp-{idx}.example.com',
					validate = lambda result: isValidID(result) or (result.startswith('//') and isValidID(result[2:])) or _containsVariable(result),
					invalid_message = 'Invalid Service Provider ID. Must not be empty and must only contain letters, digits,\nand the characters [-, _, .] .',
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
					invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits,\nand the characters [-, _, .] .',
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
		

		def advancedLogging() -> dict:
			""" Prompts for advanced logging settings. 

				Return:
					A dictionary with the selected logging settings.
			"""

			_printRule('Advanced - Logging Configuration',
					   'The following configuration settings concern advanced logging features of the CSE.')

			if inquirer.confirm(
					message='Do you want to configure advanced logging settings?',
					default=False,
					long_instruction='Set advanced logging settings, such as timezone, file logging, etc.',
					amark='✓',
				).execute():

				enableUTCTimezone = inquirer.select(
								message='Use UTC or local time for logging timestamps?',
								choices=[	Choice(name='Local - Use local time for timestamps', value=False),
											Choice(name='UTC - Use Coordinated Universal Time (UTC) for timestamps', value=True),
										],
								default='UTC',
								transformer=lambda result: result.split()[0],
								instruction="(select with cursor keys, confirm with <enter>)",
								long_instruction='Select the time zone to use for logging timestamps.',
								amark='✓',
							).execute()

				result = {	'enableFileLogging': False,
							'enableUTCTimezone': enableUTCTimezone,
						}

				if inquirer.confirm(
						message='Enable file logging?',
						default=False,
						long_instruction='Whether to enable file logging.',
						amark='✓',
					).execute():
		
					result.update({
						'enableFileLogging': True,
						'enableUTCTimezone': enableUTCTimezone,

						'count': inquirer.number(
									message='Number of log files:',
									default=10,
									long_instruction='The number of files to keep in log file rotation.',
									min_allowed=1,
									validate=lambda result: len(result.strip()) > 0,
									amark='✓',
								).execute(),
						'size': inquirer.number(
									message='Maximum log file size (in bytes):',
									default=100000,
									long_instruction='The maximum size of the log file before it is rotated.',
									min_allowed=1,
									validate=lambda result: len(result.strip()) > 0,
									amark='✓',
								).execute(),
					})

				if not inquirer.confirm(
						message='Enable screen logging?',
						default=True,
						long_instruction='Whether to enable logging to stdout.',
						amark='✓',
					).execute():

					result['enableScreenLogging'] = False
			
				return result
			else:
				return {}


		def advancedHTTP() -> dict:
			""" Prompts for advanced HTTP settings.

				Return:
					A dictionary with the HTTP settings.
			"""

			if onboardingConfig['http']['enable'].lower() == 'false':	# If HTTP binding is not enabled, skip HTTP settings
				_incrementStep()
				return {}

			_printRule('Advanced - HTTP Configuration',
					   'The following configuration settings concern advanced HTTP features.')

			if inquirer.confirm(
					message='Do you want to configure advanced HTTP settings?',
					default=False,
					long_instruction='Set advanced HTTP settings, such as timeout, headers etc',
					amark='✓',
				).execute():
				return {
					'useTLS': inquirer.confirm(
						message='Enable TLS for HTTP requests (receive and send)?',
						default=configParser.getboolean('http.security', 'useTLS'),
						long_instruction='Whether to enable TLS for HTTP requests.',
						amark='✓'
					).execute(),
					'enableBasicAuth': inquirer.confirm(
						message='Enable Basic Authentication for HTTP requests?',
						default=configParser.getboolean('http.security', 'enableBasicAuth'),
						long_instruction='Whether to enable Basic Authentication for HTTP requests.',
						amark='✓'
					).execute(),
					'enableTokenAuth': inquirer.confirm(
						message='Enable Token Authentication for HTTP requests?',
						default=configParser.getboolean('http.security', 'enableTokenAuth'),
						long_instruction='Whether to enable Token Authentication for HTTP requests.',
						amark='✓'
					).execute(),
					'timeout': inquirer.number(
						message='HTTP request timeout (in seconds):',
						float_allowed=True,
						default=configParser.getfloat('http', 'timeout'),
						long_instruction='The timeout for HTTP requests in seconds.',
						min_allowed=1.0,
						validate=lambda result: len(result.strip()) > 0,
						filter=lambda result: float(result),
						amark='✓'
					).execute(),
					'allowPatchForDelete': inquirer.confirm(
						message='Allow PATCH requests to DELETE resources?',
						default=configParser.getboolean('http', 'allowPatchForDelete'),
						long_instruction='Whether to allow PATCH requests to DELETE resources.\nThis is to support http/1.0 clients that do not support DELETE operations.',
						amark='✓'
					).execute(),
					'enableCORS': inquirer.confirm(
						message='Enable CORS support for HTTP requests?',
						default=configParser.getboolean('http.cors', 'enable'),
						long_instruction='Whether to enable CORS support for HTTP requests.',
						amark='✓'
					).execute(),
					'enableWSGI': inquirer.confirm(
						message='Enable WSGI support for HTTP requests?',
						default=True if cseEnvironment in ('Regular') else configParser.getboolean('http.wsgi', 'enable'),
						long_instruction='Whether to enable WSGI support for HTTP requests.',
						amark='✓'
					).execute()
				}
			else:
				return {}


		def advancedStatistics() -> dict:
			""" Prompts for advanced statistics settings. 

				Return:
					A dictionary with the selected statistics settings.
			"""

			_printRule('Advanced - Statistics Configuration',
					   'The following configuration settings concern advanced statistics features of the CSE.')

			# Disable automatically if statistics feature is not enabled before
			if not enDisFeatures.get('statistics', False):
				return {'enable': 'false'}
			
			if inquirer.confirm(
					message='Do you want to configure statistics settings?',
					default=False,
					long_instruction='Set advanced statistics settings',
					amark='✓',
				).execute():

				if inquirer.confirm(
						message='Do you want to enable statistics?',
						default=configParser.getboolean('cse.statistics', 'enable') if cseEnvironment not in ('Minimal') else False,
						long_instruction='Enable statistics collection and reporting.',
						amark='✓',
					).execute():
					return {
						'enable': 'true',
						'writeInterval': inquirer.number(
							message='Statistics database write interval (in seconds):',
							default=configParser.getint('cse.statistics', 'writeInterval'),
							long_instruction='The time interval that the CSE writes statistics to the database.',
							min_allowed=1,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					}
				return {'enable': 'false' }
			return {}
		

		def advancedConsole() -> dict:
			""" Prompts for advanced console settings. 

				Return:
					A dictionary with the selected console settings.
			"""

			if cseEnvironment in ('Headless'):
				return {
					'headless': True,
					'startWithTextUI': False,
				}

			_printRule('Advanced - Console Configuration',
					   'The following configuration settings concern advanced console features of the CSE.')

			if inquirer.confirm(
					message='Do you want to configure advanced console settings?',
					default=False,
					long_instruction='Set advanced console settings, such as headless mode, text UI, etc.',
					amark='✓',
				).execute():

				headless = inquirer.confirm(
						message='Do you want to run the CSE in headless mode?',
						default=configParser.getboolean('console', 'headless'),
						long_instruction='Run the CSE in headless mode, without a console or text UI.',
						amark='✓',
					).execute()
				startWithTextUI = False
				
				if onboardingConfig['textui']['enable'].lower() == 'true' and not headless and enDisFeatures.get('enableTextUI', True):
					startWithTextUI = inquirer.confirm(
						message='Do you want to start directly with the Text UI?',
						default=False,
						long_instruction='Start the CSE with the Text UI instead of the Console UI.',
						amark='✓',
					).execute()
				return {
					'headless': headless,
					'startWithTextUI': startWithTextUI,
				}
			else:
				return {}


		def advancedIntervalls() -> dict:
			""" Prompts for advanced intervalls settings.
				
				Return:
					A dictionary with the selected intervalls settings.
			"""

			_printRule('Advanced - Time Intervalls Configuration',
					   'The following configuration settings concern advanced processing intervalls of the CSE.')

			if inquirer.confirm(
					message='Do you want to configure advanced processing intervalls?',
					default=False,
					long_instruction='Configure advanced processing intervalls for the CSE.',
					amark='✓',
				).execute():
				return {
					'resourceExpiration': inquirer.number(
						message='Resource expiration check interval (in seconds):',
						default=60,
						long_instruction='The time interval that the CSE checks for resource expiration. 0 means no checking.',
						min_allowed=0,
						amark='✓',
						validate=lambda result: len(result.strip()) > 0,
						filter=lambda result: int(result),
					).execute(),
					'registrationCheck': inquirer.number(
						message='Registration check interval (in seconds):',
						default=60,
						long_instruction='The time interval that the CSE checks for other CSE registration status. 0 means no checking.',
						min_allowed=0,
						amark='✓',
						validate=lambda result: len(result.strip()) > 0,
						filter=lambda result: int(result),
					).execute(),
					'scriptFileCheck': inquirer.number(
						message='Script file check interval (in seconds):',
						default=2,
						long_instruction='The time interval that the CSE checks for script file changes. 0 means no checking.',
						min_allowed=0,
						amark='✓',
						validate=lambda result: len(result.strip()) > 0,
						filter=lambda result: int(result),
					).execute(),

				}
			return {}


		def advancedRequestRecording() -> dict:
			""" Prompts for advanced request recording settings.
				
				Return:
					A dictionary with the selected request recording settings.
			"""

			_printRule('Advanced - Request Recording Configuration',
					   'The following configuration settings concern request recording of the CSE.')

			if inquirer.confirm(
					message='Do you want to record requests to and from the CSE?',
					default=False,
					long_instruction='Record requests to and from the CSE. Disable for better performance.',
					amark='✓',
				).execute():
				return {
					'enable': 'true',
					'size': inquirer.number(
						message='Limit request recording size (count):',
						default=200,
						long_instruction='The maximum number of requests to store in the request recording.',
						min_allowed=1,
						amark='✓',
						validate=lambda result: len(result.strip()) > 0,
						filter=lambda result: int(result),
					).execute(),
				}
			return { 'enable': 'false' }


		def advancedManagement() -> dict:

			if onboardingConfig['http']['enable'].lower() == 'false':	# Return if http is disabled as management features require http
				_incrementStep()
				return {}

			_printRule('Advanced - Management Configuration',
					   'The following configuration settings concern remote management of the CSE.')

			if inquirer.confirm(
					message='Do you want to configure management settings?',
					default=False,
					long_instruction='Configure management settings for the CSE.\nThese settings enable remote management of the CSE, such as shutdown and restart.',
					amark='✓',
				).execute():
				return {
					'enableStructureEndpoint': inquirer.confirm(
						message='Enable Structure Endpoint?',
						default=onboardingConfig.getboolean('http', 'enableStructureEndpoint'),
						long_instruction='This endpoint provides information about the structure of the CSE.',
						amark='✓'
					).execute(),
					'enableUpperTesterEndpoint': inquirer.confirm(
						message='Enable Upper Tester Endpoint?',
						default=onboardingConfig.getboolean('http', 'enableUpperTesterEndpoint'),
						long_instruction='This endpoint is used for upper tester functionality, allowing remote testing of the CSE.',
						amark='✓'
					).execute(),
					'enableManagementEndpoint': inquirer.confirm(
						message='Enable Management API?',
						default=onboardingConfig.getboolean('http', 'enableManagementEndpoint'),
						long_instruction='This API provides management functionality for the CSE.',
						amark='✓'
					).execute(),
				}
			return {}


		def advancedResourceSettings() -> dict:

			_printRule('Advanced - Resource Configuration',
					   'The following configuration settings concern resource settings of the CSE.')

			if inquirer.confirm(
					message='Do you want to configure advanced resource settings?',
					default=False,
					long_instruction='Configure advanced resource settings for the CSE.\nThese settings enable fine-tuning of the resource environment, such as defaults, sizes and limits.',
					amark='✓',
				).execute():

				_printHeader('<Container> Resource Settings')
				cntResult = {
					'enableLimits' : inquirer.confirm(
						message='Enable limits for <Container> resources?',
						default=configParser.getboolean('resource.cnt', 'enableLimits'),
						long_instruction='Whether to enable limits for <Container> resources.',
						amark='✓'
					).execute(),
				}
				if cntResult['enableLimits']:
					cntResult.update({
						'mni': inquirer.number(
							message='Default: Maximum number of <ContentInstance> resources (0 = not set):',
							default=configParser.getint('resource.cnt', 'mni'),
							long_instruction='The default maximum number of <ContentInstance> resources for a <Container>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mbs': inquirer.number(
							message='Default: Maximum total size of <ContentInstance> resources (in bytes, 0 = not set):',
							default=configParser.getint('resource.cnt', 'mbs'),
							long_instruction='The default maximum total size of <ContentInstance> resources for a <Container>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mia': inquirer.number(
							message='Default: Maximum lifetime of <ContentInstance> resources (in seconds, 0 = not set):',
							default=configParser.getint('resource.cnt', 'mia'),
							long_instruction='The default maximum lifetime of <ContentInstance> resources for a <Container>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					})


				_printHeader('<FlexContainer> Resource Settings')
				fcntResult = {
					'enableLimits' : inquirer.confirm(
						message='Enable limits for <FlexContainer> resources?',
						default=configParser.getboolean('resource.fcnt', 'enableLimits'),
						long_instruction='Whether to enable limits for <FlexContainer> resources.',
						amark='✓'
					).execute(),
				}
				if fcntResult['enableLimits']:
					fcntResult.update({
						'mni': inquirer.number(
							message='Default: Maximum number of <FlexContainerInstance> resources (0 = not set):',
							default=configParser.getint('resource.fcnt', 'mni'),
							long_instruction='The default maximum number of <FlexContainerInstance> resources for a <FlexContainer>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mbs': inquirer.number(
							message='Default: Maximum total size of <FlexContainerInstance> resources (in bytes, 0 = not set):',
							default=configParser.getint('resource.fcnt', 'mbs'),
							long_instruction='The default maximum total size of <FlexContainerInstance> resources for a <FlexContainer>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mia': inquirer.number(
							message='Default: Maximum lifetime of <FlexContainerInstance> resources (in seconds, 0 = not set):',
							default=configParser.getint('resource.fcnt', 'mia'),
							long_instruction='The default maximum lifetime of <FlexContainerInstance> resources for a <FlexContainer>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					})


				_printHeader('<TimeSeries> Resource Settings')
				tsResult = {
					'enableLimits' : inquirer.confirm(
						message='Enable limits for <TimeSeries> resources?',
						default=configParser.getboolean('resource.ts', 'enableLimits'),
						long_instruction='Whether to enable limits for <TimeSeries> resources.',
						amark='✓'
					).execute(),
				}
				if tsResult['enableLimits']:
					tsResult.update({
						'mni': inquirer.number(
							message='Default: Maximum number of <TimeSeriesInstance> resources (0 = not set):',
							default=configParser.getint('resource.ts', 'mni'),
							long_instruction='The default maximum number of <TimeSeriesInstance> resources for a <TimeSeries>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mbs': inquirer.number(
							message='Default: Maximum total size of <TimeSeriesInstance> resources (in bytes, 0 = not set):',
							default=configParser.getint('resource.ts', 'mbs'),
							long_instruction='The default maximum total size of <TimeSeriesInstance> resources for a <TimeSeries>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mia': inquirer.number(
							message='Default: Maximum lifetime of <TimeSeriesInstance> resources (in seconds, 0 = not set):',
							default=configParser.getint('resource.ts', 'mia'),
							long_instruction='The default maximum lifetime of <TimeSeriesInstance> resources for a <TimeSeries>.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					})


				_printHeader('<Action> Resource Settings')
				if inquirer.confirm(
						message='Set defaults for <Action> resources?',
						default=False,
						long_instruction='Whether to update defaults for <Action> resources.',
						amark='✓'
					).execute():

					actResult = {
						'ecpContinuous' : inquirer.number(
							message='Default count value for "continuous" mode (number, 0 = indefinitely)?',
							default=configParser.getint('resource.actr', 'ecpContinuous'),
							long_instruction='The number of times the CSE shall trigger an event.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'ecpPeriodic' : inquirer.number(
							message='Default delay for "periodic" mode (in seconds)?',
							default=configParser.getint('resource.actr', 'ecpPeriodic'),
							long_instruction='The periodicity the CSE shall trigger an event.',
							min_allowed=1,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),

					}
				else:
					actResult = {}


				_printHeader('<Group> Resource Settings')
				if inquirer.confirm(
						message='Set defaults for <Group> resources?',
						default=False,
						long_instruction='Whether to update defaults for <Group> resources.',
						amark='✓'
					).execute():

					grpResult = {
						'resultExpirationTime': inquirer.number(
							message='Maximum time to wait for a <Group> request fan-outed to its members (in ms, 0 = no timeout):',
							default=configParser.getint('resource.grp', 'resultExpirationTime'),
							long_instruction='The default maximum time to wait for a <Group> to collect results.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					}
				else:
					grpResult = {}


				_printHeader('<LocationPolicy> Resource Settings')
				if inquirer.confirm(
						message='Set defaults for <LocationPolicy> resources?',
						default=False,
						long_instruction='Whether to update defaults for <LocationPolicy> resources.',
						amark='✓'
					).execute():

					lcpResult = {
						'mni': inquirer.number(
							message='Default for maxNrOfInstances for the <LocationPolicy> container (count, 0 = unlimited):',
							default=configParser.getint('resource.lcp', 'mni'),
							long_instruction='The default maximum number of <ContentInstances> for the <LocationPolicy> collecting container.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
						'mbs': inquirer.number(
							message='Default for maxByteSize for the <LocationPolicy> container (in bytes, 0 = unlimited):',
							default=configParser.getint('resource.lcp', 'mbs'),
							long_instruction='The default maximum size of <ContentInstances> for the <LocationPolicy> collecting container.',
							min_allowed=0,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					}
				else:
					lcpResult = {}


				_printHeader('<Request> Resource Settings')
				if inquirer.confirm(
						message='Set defaults for <Request> resources?',
						default=False,
						long_instruction='Whether to update defaults for <Request> resources.',
						amark='✓'
					).execute():

					reqResult = {
						'expirationTime': inquirer.number(
							message='Default for expirationTime for <Request> (in s):',
							default=configParser.getint('resource.req', 'expirationTime'),
							long_instruction='The default expiration time for <Request> resources.',
							min_allowed=1,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					}
				else:
					reqResult = {}


				_printHeader('<Subscription> Resource Settings')
				if inquirer.confirm(
						message='Set defaults for <Subscription> resources?',
						default=False,
						long_instruction='Whether to update defaults for <Subscription> resources.',
						amark='✓'
					).execute():

					subResult = {
						'batchNotifyDuration': inquirer.number(
							message='Default for "batchNotify/duration" for <Subscription> (in s):',
							default=configParser.getint('resource.sub', 'batchNotifyDuration'),
							long_instruction='The default batch notify duration for <Subscription> resources.',
							min_allowed=1,
							amark='✓',
							validate=lambda result: len(result.strip()) > 0,
							filter=lambda result: int(result),
						).execute(),
					}
				else:
					subResult = {}


				return {
					'cnt': cntResult,
					'fcnt': fcntResult,
					'ts': tsResult,
					'actr': actResult,
					'grp': grpResult,
					'lcp': lcpResult,
					'req': reqResult,
					'sub': subResult,
					# 'tsb': tsbResult,	TODO do we want this?
				}
			return {}


		_printRule('Advanced Settings',
				   'The following configuration settings concern advanced features of the CSE.\n\nBesides the settings handled here, you can also edit the configuration manually to add even more advanced settings.\n\nSee [u][link=https://acmecse.net/setup/Configuration-introduction/]https://acmecse.net/setup/Configuration-introduction[/link][/u] for more information.')

		if not inquirer.confirm(
				message='Do you want to configure advanced settings?',
				default=False,
				long_instruction='Configure advanced settings for the CSE.'
			).execute():
			_incrementStep(10)
			return {}

		if cseType == 'IN':	
			# Prompt for Service Provider registration
			spRegistration = spRegistrations()

		return {	'cse': advancedCSE(),
					'spRegistration': spRegistration,
		  			'logging': advancedLogging(),
					'console': advancedConsole(),
					'http': advancedHTTP(),
					'requestRecording': advancedRequestRecording(),
					'statistics': advancedStatistics(),
					'management': advancedManagement(),
					'intervalls': advancedIntervalls(),
					'resources': advancedResourceSettings(),
		  	}


	#
	#	Read the default configuration to use the default values later
	#
	global configParser
	if not Configuration.Configuration._defaultConfigFile:
		if not Configuration.Configuration.initDirectories():
			raise RuntimeError('Failed to initialize directories for the configuration file.')
	configParser.read(Configuration.Configuration._defaultConfigFile)

	# Create an onboarding configuration that we will with the confiugration
	# in the following steps
	onboardingConfig = ACMEConfiguration.ACMEConfiguration()


	#
	#	On-boarding Dialog
	#

	Console().clear()

	try:
		
		# Prompt for directories and configuration file
		directoriesAndConfigFile()

		# Prompt for basic configuration
		basicConfig()
		onboardingConfig.set('basic.config', 'cseType', cseType)
	
		# Prompt for the CSE configuration
		for each in (bc := cseConfig()):
			onboardingConfig['basic.config'][each] = bc[each]	# type:ignore[index, assignment]
		cseID = cast(str, bc['cseID'])

		# Add the CSE secret
		if cseSecret:
			onboardingConfig['basic.config']['cseSecret'] = cseSecret

		# Prompt for registrar configuration
		match cseType:
			case 'MN' | 'ASN':
				for each in (regCnf := registrarConfig()):
					if each == 'INCSEcseID':
						continue
					onboardingConfig['basic.config'][each] = regCnf[each]	# type:ignore[index, assignment]
				spRegistration = None


		# Prompt for the CSE database settings
		dbc = cseDatabase()
		onboardingConfig['basic.config']['databaseType'] = dbc['databaseType'] # type:ignore[index, assignment]


		# Prompt for additional protocol bindings
		# Add HTTP, MQTT, CoAP, WebSocket configuration
		bindings = cseBindings()
		if 'http' in bindings:
			onboardingConfig['http'] = {
				'enable': bindings['http'].get('enable')
			}
			
		if 'mqtt' in bindings or 'mqtt.websocket' in bindings:
			onboardingConfig['mqtt'] = {
				'enable': 'true',
			}

			mqtt = bindings['mqtt']
			_setOption(onboardingConfig, 'mqtt', 'address', mqtt.get('address'))
			_setOption(onboardingConfig, 'mqtt', 'port', mqtt.get('port'))

			if mqtt['username']:
				onboardingConfig['mqtt.security'] = {
					'username': mqtt['username'],
					'password': mqtt['password'],
				}
		

		if 'mqtt.websocket' in bindings:
			onboardingConfig['mqtt.websocket'] = {
				'enable': 'true',
			}
			mqttWebsocket = bindings['mqtt.websocket']
			_setOption(onboardingConfig, 'mqtt.websocket', 'port', mqttWebsocket.get('port'))
			_setOption(onboardingConfig, 'mqtt.websocket', 'path', mqttWebsocket.get('path'))


		if 'coap' in bindings:
			onboardingConfig['coap'] = {
				'enable': 'true',
			}
			coap = bindings['coap']
			_setOption(onboardingConfig, 'coap', 'port', coap.get('port'))


		if 'websocket' in bindings:
			onboardingConfig['websocket'] = {
				'enable': 'true',
			}
			webSocket = bindings['websocket']
			_setOption(onboardingConfig, 'websocket', 'port', webSocket.get('port'))


		# Prompt for console and UI settings
		if (uiConfigs := cseUIs()):
			onboardingConfig['basic.config']['consoleTheme'] = uiConfigs['consoleTheme']	# type:ignore[index, assignment]
			onboardingConfig['basic.config']['consoleType'] = uiConfigs['consoleType']		# type:ignore[index, assignment]
			_setOption(onboardingConfig, 'textui', 'enable', str(uiConfigs['enableTextUI']).lower())
			if 'enableWebUI' in uiConfigs:
				_setOption(onboardingConfig, 'webui', 'enable', str(uiConfigs['enableWebUI']).lower())

		# Prompt for  CSE policies
		# Don't optimize default values. This section should always be fully present
		for each in (policyConfig := csePolicies()):
			onboardingConfig['basic.config'][each] = policyConfig[each]	# type:ignore[index, assignment]

		#
		#	Add database configuration
		#
		if dbc['databaseType'] == 'postgresql':
			onboardingConfig['database.postgresql'] = {
				'database': dbc['dbName'],		# type:ignore[dict-item]
				'host': dbc['dbHost'],			# type:ignore[dict-item]
				'password': dbc['dbPassword'],	# type:ignore[dict-item]
				'port': str(dbc['dbPort']),		# type:ignore[dict-item]
				'role': dbc['dbUser'],			# type:ignore[dict-item]
				'schema': dbc['dbSchema'],		# type:ignore[dict-item]
			}


		# Add Registration originators
		onboardingConfig['cse.registration'] = {
			'allowedCSROriginators': '/id-in,/id-mn,/id-asn'
		}


		#	Add registrar configuration
		match cseType:
			case 'IN':
				pass
			
			case 'MN' | 'ASN':
				# Add the registrar configuration for the MN or ASN
				onboardingConfig.set('cse.registrar', 'INCSEcseID', f"/{regCnf['INCSEcseID']}")


		# prompt for enabled/disabled features

		enDisFeatures = enableDisableFeatures()

		# prompt for advanced settings
		advSettings = advancedSettings()

		#
		#	Advanced CSE Configuration
		#
		if (advancedCSE := advSettings.get('cse')):
			# Add the CSE configuration
			_setOption(onboardingConfig, 'cse', 'releaseVersion', advancedCSE.get('releaseVersion'))
			_setOption(onboardingConfig, 'cse', 'supportedReleaseVersions', ','.join(advancedCSE.get('supportedReleaseVersions')))
			_setOption(onboardingConfig, 'cse', 'defaultSerialization', advancedCSE.get('defaultSerialization'))
			_setOption(onboardingConfig, 'cse', 'enableSubscriptionVerificationRequests', advancedCSE.get('enableSubscriptionVerificationRequests'), True)
			_setOption(onboardingConfig, 'cse', 'idLength', advancedCSE.get('idLength'))

		#
		#	Advanced:
		#	Add the SP registration configuration
		#	Add to the cnfRegistrar part
		#
		if spRegistration := advSettings.get('spRegistration', {}):
			# Add SPs to the allowedCSROriginators list
			_ids = onboardingConfig['cse.registration']['allowedCSROriginators']
			for spID, spCnf in spRegistration.items():
				_ids += f',//{spCnf["SPID"]}/{spCnf["SPCSEID"]}'
			onboardingConfig.set('cse.registration', 'allowedCSROriginators', _ids)

			# Generate the registrar configuration for each SP
			for spID, spCnf in spRegistration.items():
				onboardingConfig[f'cse.sp.registrar.{spID}'] = {
					'spID': f"//{spCnf['SPID']}",
					'cseID': f"/{spCnf['SPCSEID']}",
					'resourceName': spCnf['SPCSERN'],
					'address': spCnf['url'],
				}

		#
		#	Advanced: Logging
		#
		if loggingSettings := advSettings.get('logging'):
			_setOption(onboardingConfig, 'logging', 'enableUTCTimezone', loggingSettings.get('enableUTCTimezone'), True)
			if _setOption(onboardingConfig, 'logging', 'enableFileLogging', loggingSettings.get('enableFileLogging'), True) == 'true':
				_setOption(onboardingConfig, 'logging', 'count', loggingSettings.get('count'))
				_setOption(onboardingConfig, 'logging', 'size', loggingSettings.get('size'))
			_setOption(onboardingConfig, 'logging', 'enableScreenLogging', loggingSettings.get('enableScreenLogging'), True)

		#
		#	Advanced: CSE Policies
		#
		if _setOption(onboardingConfig, 'cse', 'checkExpirationsInterval', advSettings.get('intervalls', {}).get('resourceExpiration')) == '0':
			onboardingConfig.set('cse', 'enableResourceExpiration', 'false')

		#
		#	Advanced: CSE Registration
		#
		if intervalls := advSettings.get('intervalls', {}):
			# Add the CSE registration check intervall
			if _setOption(onboardingConfig, 'cse.registration', 'checkInterval', intervalls.get('registrationCheck')) == '0':
				onboardingConfig.set('cse.registration', 'enableCheckLiveliness', 'false')

		#
		#	Advanced: HTTP
		#
		if httpSettings := advSettings.get('http'):
			_setOption(onboardingConfig, 'http', 'timeout', httpSettings.get('timeout'))
			_setOption(onboardingConfig, 'http', 'allowPatchForDelete', httpSettings.get('allowPatchForDelete'), True)
			_setOption(onboardingConfig, 'http.security', 'useTLS', httpSettings.get('useTLS'), True)
			_setOption(onboardingConfig, 'http.security', 'enableBasicAuth', httpSettings.get('enableBasicAuth'), True)
			_setOption(onboardingConfig, 'http.security', 'enableTokenAuth', httpSettings.get('enableTokenAuth'), True)
			_setOption(onboardingConfig, 'http.cors', 'enable', httpSettings.get('enableCORS'), True)
			_setOption(onboardingConfig, 'http.wsgi', 'enable', httpSettings.get('enableWSGI'), True)

		#
		#	Advanced: Scripts
		#
		_setOption(onboardingConfig, 'scripting', 'fileMonitoringInterval', advSettings.get('intervalls', {}).get('scriptFileCheck'))


		#
		#	Advanced: Request Recording
		#
		if requestRecording := advSettings.get('requestRecording'):
			_setOption(onboardingConfig, 'cse.operation.requests', 'enable', requestRecording.get('enable'), True)
			_setOption(onboardingConfig, 'cse.operation.requests', 'size', requestRecording.get('size'))

		#
		#	Advanced: Statistics
		#
		if statistics := advSettings.get('statistics'):
			if _setOption(onboardingConfig, 'cse.statistics', 'enable', statistics.get('enable'), True) == 'true':
				_setOption(onboardingConfig, 'cse.statistics', 'writeInterval', statistics.get('writeInterval'))

		#
		#	Advanced: Console
		#
		if consoleSettings := advSettings.get('console'):
			_setOption(onboardingConfig, 'console', 'headless', consoleSettings.get('headless'), True)
			_setOption(onboardingConfig, 'textui', 'startWithTUI', consoleSettings.get('startWithTextUI'), True)

		#
		#	Advanced: Management
		#
		if managementSettings := advSettings.get('management'):
			_setOption(onboardingConfig, 'http', 'enableStructureEndpoint', managementSettings.get('enableStructureEndpoint'), True)
			_setOption(onboardingConfig, 'http', 'enableUpperTesterEndpoint', managementSettings.get('enableUpperTesterEndpoint'), True)
			_setOption(onboardingConfig, 'http', 'enableManagementEndpoint', managementSettings.get('enableManagementEndpoint'), True)


		#
		#	Advanced: Resources
		#
		if resourceSettings := advSettings.get('resources'):
			if cnt := resourceSettings.get('cnt'):
				if _setOption(onboardingConfig, 'resource.cnt', 'enableLimits', cnt.get('enableLimits'), True) == 'true':
					_setOption(onboardingConfig, 'resource.cnt', 'mni', cnt.get('mni'))
					_setOption(onboardingConfig, 'resource.cnt', 'mbs', cnt.get('mbs'))
					_setOption(onboardingConfig, 'resource.cnt', 'mia', cnt.get('mia'))

			if fcnt := resourceSettings.get('fcnt'):
				if _setOption(onboardingConfig, 'resource.fcnt', 'enableLimits', fcnt.get('enableLimits'), True) == 'true':
					_setOption(onboardingConfig, 'resource.fcnt', 'mni', fcnt.get('mni'))
					_setOption(onboardingConfig, 'resource.fcnt', 'mbs', fcnt.get('mbs'))
					_setOption(onboardingConfig, 'resource.fcnt', 'mia', fcnt.get('mia'))

			if ts := resourceSettings.get('ts'):
				if _setOption(onboardingConfig, 'resource.ts', 'enableLimits', ts.get('enableLimits'), True) == 'true':
					_setOption(onboardingConfig, 'resource.ts', 'mni', ts.get('mni'))
					_setOption(onboardingConfig, 'resource.ts', 'mbs', ts.get('mbs'))
					_setOption(onboardingConfig, 'resource.ts', 'mia', ts.get('mia'))

			if actr := resourceSettings.get('actr'):
				_setOption(onboardingConfig, 'resource.actr', 'ecpContinuous', actr.get('ecpContinuous'))
				_setOption(onboardingConfig, 'resource.actr', 'ecpPeriodic', actr.get('ecpPeriodic'))

			if grp := resourceSettings.get('grp'):
				_setOption(onboardingConfig, 'resource.grp', 'resultExpirationTime', grp.get('resultExpirationTime'))

			if lcp := resourceSettings.get('lcp'):
				_setOption(onboardingConfig, 'resource.lcp', 'mni', lcp.get('mni'))
				_setOption(onboardingConfig, 'resource.lcp', 'mbs', lcp.get('mbs'))

			if req := resourceSettings.get('req'):
				_setOption(onboardingConfig, 'resource.req', 'expirationTime', req.get('expirationTime'))

			if sub := resourceSettings.get('sub'):
				_setOption(onboardingConfig, 'resource.sub', 'batchNotifyDuration', sub.get('batchNotifyDuration'))	


		#
		#	add more mode-specific configurations
		#
		match cseEnvironment:
			case 'Regular':
				# Add WSGI configuration
				_setOption(onboardingConfig, 'http.wsgi', 'enable', 'true')

			case 'Development':
				_setOption(onboardingConfig, 'textui', 'startWithTUI', 'false')
				_setOption(onboardingConfig, 'cse.operation.requests', 'enable', 'true')
				_v = onboardingConfig['http'].get('enable').lower()
				_setOption(onboardingConfig, 'http', 'enableUpperTesterEndpoint', _v, force=True)
				_setOption(onboardingConfig, 'http', 'enableStructureEndpoint', _v, force=True)
				_setOption(onboardingConfig, 'http', 'enableManagementEndpoint', _v, force=True)

			case 'Introduction':
				# Add introduction configuration
				_setOption(onboardingConfig, 'textui', 'startWithTUI', 'true')
				_setOption(onboardingConfig, 'cse.operation.requests', 'enable', 'true')
				_setOption(onboardingConfig, 'scripting', 'scriptDirectories', '${cse:resourcesPath}/demoLightbulb,${cse:resourcesPath}/demoDocumentationTutorials')

			case 'Headless':
				# Add headless configuration
				_setOption(onboardingConfig, 'textui', 'startWithTUI', 'false')
				_setOption(onboardingConfig, 'console', 'headless', 'true')

			case 'Minimal':
				# Add minimal configuration
				_setOption(onboardingConfig, 'cse.statistics', 'enable', 'false')
				_setOption(onboardingConfig, 'cse.operation.requests', 'enable', 'false', force=True)

			case 'ETSI MEC':
				# like development, but with MQTT enabled
				_setOption(onboardingConfig, 'textui', 'startWithTUI', 'false')
				_setOption(onboardingConfig, 'cse.operation.requests', 'enable', 'true')
				_setOption(onboardingConfig, 'http', 'enableUpperTesterEndpoint', 'true')
				_setOption(onboardingConfig, 'http', 'enableStructureEndpoint', 'true')
				_setOption(onboardingConfig, 'http', 'enableManagementEndpoint', 'true')

				# Enable MQTT binding
				_setOption(onboardingConfig, 'mqtt', 'enable', 'true')
				_setOption(onboardingConfig, 'mqtt', 'address', 'localhost')
				_setOption(onboardingConfig, 'mqtt', 'port', '1883')
				_setOption(onboardingConfig, 'mqtt', 'keepalive', '45')
				_setOption(onboardingConfig, 'mqtt.websocket', 'enable', 'true')
				_setOption(onboardingConfig, 'mqtt.websocket', 'port', '8080')

		#
		# Convert the final configuration to a string
		#
		with io.StringIO() as ss:
			onboardingConfig.write(ss)
			ss.seek(0) # rewind
			jcnf = ss.read()

		# Show configuration and confirm write
		_printRule('Saving New Configuration',
				   f'The configuration is ready.\n\nThe following settings will be written to {"a new configuration file" if configFile else "a ZooKeeper server"}.')
		_print(Syntax(jcnf, 'ini'))

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
			if not inquirer.confirm	(message = f'Write configuration to the ZooKeeper server at {zkConfiguration[2]}?', 
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
