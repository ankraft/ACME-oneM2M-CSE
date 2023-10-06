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
from typing import List, cast
from datetime import datetime

from InquirerPy import inquirer
from InquirerPy.utils import InquirerPySessionResult
from InquirerPy.base import Choice

from rich.console import Console

from ..etc.Constants import Constants

from ..helpers import NetworkTools


_iniValues = {
	'IN' : { 
		'cseID': 'id-in',
		'cseName': 'cse-in',
		'adminID': 'CAdmin',
		'dataDirectory': '${baseDirectory}',
		'networkInterface': '0.0.0.0',
		'cseHost': NetworkTools.getIPAddress(),
		'httpPort': 8080,

		'logLevel': 'debug',
		'databaseInMemory': 'False',
	},
	'MN' : { 
		'cseID': 'id-mn',
		'cseName': 'cse-mn',
		'adminID': 'CAdmin',
		'dataDirectory': '${baseDirectory}',
		'networkInterface': '0.0.0.0',
		'cseHost': NetworkTools.getIPAddress(),
		'httpPort': 8081,

		'logLevel': 'debug',
		'databaseInMemory': 'False',

		'registrarCseHost': NetworkTools.getIPAddress(),
		'registrarCsePort': 8080,
		'registrarCseID': 'id-in',
		'registrarCseName': 'cse-in',
	},
	'ASN' : { 
		'cseID': 'id-asn',
		'cseName': 'cse-asn',
		'adminID': 'CAdmin',
		'dataDirectory': '${baseDirectory}',
		'networkInterface': '0.0.0.0',
		'cseHost': '127.0.0.1',
		'httpPort': 8082,

		'logLevel': 'debug',
		'databaseInMemory': 'False',

		'registrarCseHost': '127.0.0.1',
		'registrarCsePort': 8081,
		'registrarCseID': 'id-mn',
		'registrarCseName': 'cse-mn',
	}		
}


def _print(msg:str) -> None:
	""" Print a message to the console.
	
		Args:
			msg: The message to print.
	"""
	from ..services import CSE
	if not CSE.isHeadless:
		Console().print(msg)	# Print error message to console


def buildUserConfigFile(configFile:str) -> bool:
	from ..etc.Utils import isValidID

	cseType = 'IN'
	cseEnvironment = 'Development'


	def basicConfig() -> None:
		nonlocal cseType, cseEnvironment
		_print('[b]Basic configuration\n')

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
							long_instruction = 'Type of CSE to run: Infrastructure, Middle, or Application Service Node.',
							amark = '✓', 
						).execute()


	def cseConfig() -> InquirerPySessionResult:
		_print('\n\n[b]CSE configuration\n')
		_print('The following questions determine basic CSE settings.\n')

		return {
			'cseID': inquirer.text(
						message = 'CSE-ID:',
						default = _iniValues[cseType]['cseID'],
						long_instruction = 'The CSE-ID of the CSE and the resource ID of the CSEBase.',
						validate = lambda result: isValidID(result),
						amark = '✓', 
						invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits, and the characters "-", "_", and ".".',
					 ).execute(),
			'cseName': inquirer.text(
							message = 'Name of the CSE:',
							default = _iniValues[cseType]['cseName'],
							long_instruction = 'This is the resource name of the CSEBase.',
							validate = lambda result: isValidID(result),
							amark = '✓', 
							invalid_message = 'Invalid CSE name. Must not be empty and must only contain letters, digits, and the characters "-", "_", and ".".',
						).execute(),
			'adminID': inquirer.text(
							message = 'Admin Originator:',
							default = _iniValues[cseType]['adminID'],
							long_instruction = 'The originator who has admin access rights to the CSE and the CSE\'s resources.',
							validate = lambda result: isValidID(result) and result.startswith('C'),
							amark = '✓', 
							invalid_message = 'Invalid Originator ID. Must start with "C", must not be empty and must only contain letters, digits, and the characters "-", "_", and ".".',
						).execute(),
			'dataDirectory': inquirer.text(
								message = 'Data root directory:',
								default = _iniValues[cseType]['dataDirectory'],
								long_instruction = 'The directory under which the "data", "init" and "log" directories are located. Usually the CSE\'s base directory.',
								amark = '✓', 
							).execute(),
			'networkInterface': inquirer.text(
								message = 'Network interface to bind to (IP address):',
								default = _iniValues[cseType]['networkInterface'],
								long_instruction = 'The network interface to listen for requests. Use "0.0.0.0" for all interfaces.',
								validate = NetworkTools.isValidateIpAddress,
								amark = '✓', 
								invalid_message = 'Invalid IPv4 or IPv6 address.',
							).execute(),
			'cseHost': inquirer.text(
							message = 'CSE host address (IP address or host name):',
							default = _iniValues[cseType]['cseHost'],
							long_instruction = 'The network interface to listen for requests. Use "0.0.0.0" for all interfaces.',
							validate =  lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result),
							amark = '✓', 
							invalid_message = 'Invalid IPv4 or IPv6 address or hostname.',
						).execute(),
			'httpPort': inquirer.number(
							message = 'CSE host http port:',
							default = _iniValues[cseType]['httpPort'],
							long_instruction = 'TCP port at which the CSE is reachable for requests.',
							validate = NetworkTools.isValidPort,
							min_allowed = 1,
        					max_allowed = 65535,
							amark = '✓',
							invalid_message = 'Invalid port number. Must be a number between 1 and 65535.',
						).execute(),
			}


	def registrarConfig() -> InquirerPySessionResult:
		_print('\n\n[b]Registrar configuration\n')
		_print('The following settings concern the registrar CSE to which this CSE will be registering.\n')

		return {
			'registrarCseID':	inquirer.text(
									message = 'The Registrar CSE-ID:',
									default = _iniValues[cseType]['registrarCseID'],
									long_instruction = 'This is the CSE-ID of the remote (Registrar) CSE.',
									validate = lambda result: isValidID(result),
									amark = '✓', 
									invalid_message = 'Invalid CSE-ID. Must not be empty and must only contain letters, digits, and the characters "-", "_", and ".".',
								).execute(),
			'registrarCseName':	inquirer.text(
									message = 'The Name of the Registrar CSE:',
									default = _iniValues[cseType]['registrarCseName'],
									long_instruction = 'The resource name of the remote (Registrar) CSE.',
									validate = lambda result: isValidID(result),
									amark = '✓', 
									invalid_message = 'Invalid CSE Name. Must not be empty and must only contain letters, digits, and the characters "-", "_", and ".".',
								).execute(),
			'registrarCseHost':	inquirer.text(
									message = 'The Registrar CSE\' IP address / host name:',
									default = _iniValues[cseType]['registrarCseHost'],
									long_instruction = 'The IP address or host name of the remote (Registrar) CSE.',
									validate = lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result),
									amark = '✓', 
									invalid_message = 'Invalid IPv4 or IPv6 address or hostname.',
								).execute(),
			'registrarCsePort': inquirer.number(
							message = 'The Registrar CSE\' host http port:',
							default = _iniValues[cseType]['registrarCsePort'],
							long_instruction = 'The TCP port of the remote (Registrar) CSE.',
							validate = NetworkTools.isValidPort,
							min_allowed = 1,
        					max_allowed = 65535,
							amark = '✓',
							invalid_message = 'Invalid port number. Must be a number between 1 and 65535.',
						).execute(),
		}


	def csePolicies() -> InquirerPySessionResult:
		""" Prompts for CSE policies. 

			Return:
				A dictionary with the selected policies.
		"""
		_print('\n\n[b]CSE Policies\n')
		_print('The following configuration settings determine miscellaneous CSE policies.\n')

		return {
			'logLevel': inquirer.select(
							message = 'Log level:',
							choices = [ 'debug', 'info', 'warning', 'error', 'off' ],
							default = 'debug' if cseEnvironment in ('Development') else 'warning',
							long_instruction = 'Set the logging verbosity',
							amark = '✓',
						).execute(),
			'databaseInMemory': inquirer.select(
							message = 'Database location policy:',
							choices = [ Choice(name = 'memory - Faster, but data is lost when the CSE terminates', 
			  								   value = True),
		  								Choice(name = 'disk   - Slower, but data is persisted across CSE restarts', 
		   									   value = False),
									  ],
							default = cseEnvironment in ('Development', 'Introduction'),
							transformer = lambda result: result.split()[0],
							long_instruction = 'Store data in memory (volatile) or on disk (persistent).',
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
								long_instruction = 'Set the console and Text UI theme',
								amark = '✓',
							).execute(),
			}


	#
	#	On-boarding Dialog

	Console().clear()
	cnf:List[str] = []

	try:
		_print(f'[u][b]Creating a new [/b]{Constants.textLogo}[b] configuration file\n')
		_print('You may press CTRL-C at any point to cancel the configuration.\n')
		
		# Prompt for basic configuration
		basicConfig()
		cnf.append(f'cseType={cseType}')
	
		# Prompt for the CSE configuration
		for each in (bc := cseConfig()):
			cnf.append(f'{each}={bc[each]}')
		
		# Prompt for registrar configuration
		if cseType in [ 'MN', 'ASN' ]:
			for each in (bc := registrarConfig()):
				cnf.append(f'{each}={bc[each]}')
		
		# Prompt for the CSE policies
		for each in (bc := csePolicies()):
			cnf.append(f'{each}={bc[each]}')


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
allowedCSROriginators=id-in,id-mn,id-asn
"""

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

		# Construct the configuration
		jcnf = '[basic.config]\n' + '\n'.join(cnf) + cnfExtra

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

		# Show configuration and confirm write
		_print('\n[b]Save configuration\n')
		_jcnf = jcnf.replace("[", "\[")
		_print(f'[dim]{_jcnf}\n')

		if not inquirer.confirm	(message = f'Write configuration to file {configFile}?', 
			   					default = True,
								long_instruction = 'Write the configuration file and start the CSE afterwards.',
			  					amark = '✓'
								).execute():
			_print('\n[red]Configuration canceled\n')
			return False

	except KeyboardInterrupt:
		_print('\n[red]Configuration canceled\n')
		return False

	try:
		with open(configFile, 'w') as file:
			file.write(cnfHeader)
			file.write(jcnf)
	except Exception as e:
		_print(str(e))
		return False

	_print(f'\n[spring_green2]New {cseType}-CSE configuration created.\n')
	return True

