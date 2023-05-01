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

from InquirerPy import prompt, inquirer
from InquirerPy.utils import InquirerPySessionResult
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
		'httpPort': '8080',
		'logLevel': 'debug',
		'databaseInMemory': 'False',
		'enableRequests': 'False',
	},
	'MN' : { 
		'cseID': 'id-mn',
		'cseName': 'cse-mn',
		'adminID': 'CAdmin',
		'dataDirectory': '${baseDirectory}',
		'networkInterface': '0.0.0.0',
		'cseHost': NetworkTools.getIPAddress(),
		'httpPort': '8081',
		'logLevel': 'debug',
		'databaseInMemory': 'False',
		'enableRequests': 'False',
		'registrarCseHost': NetworkTools.getIPAddress(),
		'registrarCsePort': '8080',
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
		'httpPort': '8082',
		'logLevel': 'debug',
		'databaseInMemory': 'False',
		'enableRequests': 'False',
		'registrarCseHost': '127.0.0.1',
		'registrarCsePort': '8081',
		'registrarCseID': 'id-mn',
		'registrarCseName': 'cse-mn',
	}		
}


def _print(msg:str) -> None:
	from ..services import CSE
	if not CSE.isHeadless:
		Console().print(msg)	# Print error message to console


def buildUserConfigFile(configFile:str) -> bool:
	from ..etc.Utils import isValidID

	cseType = 'IN'
	cseEnvironment = 'Development'


	def basicConfig() -> InquirerPySessionResult:
		_print('\n[b]Basic configuration\n')
		return prompt(
			[
				{	'type': 'input',
					'message': 'CSE-ID:',
					'long_instruction': 'The CSE-ID of the CSE and the resource ID of the CSEBase.',
					'default': _iniValues[cseType]['cseID'],
					'validate': lambda result: isValidID(result),
					'name': 'cseID',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Name of the CSE:',
					'long_instruction': 'This is the resource name of the CSEBase.',
					'default': _iniValues[cseType]['cseName'],
					'validate': lambda result: isValidID(result),
					'name': 'cseName',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Admin Originator:',
					'long_instruction': 'The originator who has admin access rights to the CSE and the CSE\'s resources.',
					'default': _iniValues[cseType]['adminID'],
					'validate': lambda result: isValidID(result),
					'name': 'adminID',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Data root directory:',
					'long_instruction': 'The directory under which the "data", "init" and "log" directories are located.',
					'default': _iniValues[cseType]['dataDirectory'],
					'name': 'dataDirectory',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Network interface to bind to (IP address):',
					'long_instruction': 'The network interface to listen for requests. Use "0.0.0.0" for all interfaces.',
					'validate': NetworkTools.isValidateIpAddress,
					'default': _iniValues[cseType]['networkInterface'],
					'name': 'networkInterface',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'CSE host address (IP address or host name):',
					'long_instruction': 'IP address or host name at which the CSE is reachable for requests.',
					'validate': lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result),
					'default': _iniValues[cseType]['cseHost'],
					'name': 'cseHost',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'CSE host http port:',
					'long_instruction': 'TCP port at which the CSE is reachable for requests.',
					'validate': NetworkTools.isValidPort,
					'default': _iniValues[cseType]['httpPort'],
					'name': 'httpPort',
					'amark': '✓',
				},
				{	'type': 'rawlist',
					'message': 'Log level:',
					'long_instruction': 'Set the logging verbosity',
					"choices": lambda _: [ 'debug', 'info', 'warning', 'error', 'off' ],
					'default': 1 if cseEnvironment in ('Development') else 3,
					'name': 'logLevel',
					'amark': '✓',
				},
				{	'type': 'rawlist',
					'message': 'Database location:',
					'long_instruction': 'Store data in memory (volatile) or on disk (persistent).',
					"choices": lambda _: [ 'memory', 'disk' ],
					'default': 1 if cseEnvironment in ('Development', 'Tutorial') else 2,
					"filter": lambda result: str(result == 'memory'),
					'name': 'databaseInMemory',
					'amark': '✓',
				},
			],
		)


	def registrarConfig() -> InquirerPySessionResult:
		_print('\n[b]Registrar configuration\n')
		return prompt(
			[
				{	'type': 'input',
					'message': 'Registrar CSE-ID:',
					'long_instruction': 'The CSE-ID of the remote (registrar) CSE.',
					'default': _iniValues[cseType]['registrarCseID'],
					'validate': lambda result: isValidID(result),
					'name': 'registrarCseID',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Name of the Registrar CSE:',
					'long_instruction': 'The resource name of the remote (registrar) CSE.',
					'default': _iniValues[cseType]['registrarCseName'],
					'validate': lambda result: isValidID(result),
					'name': 'registrarCseName',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Registrar CSE IP address / host name:',
					'long_instruction': 'The IP address or host name of the remote (registrar) CSE.',
					'default': _iniValues[cseType]['registrarCseHost'],
					'validate': lambda result: NetworkTools.isValidateIpAddress(result) or NetworkTools.isValidateHostname(result),
					'name': 'registrarCseHost',
					'amark': '✓',
				},
				{	'type': 'input',
					'message': 'Registrar CSE host http port:',
					'long_instruction': 'The TCP port of the remote (registrar) CSE.',
					'validate': NetworkTools.isValidPort,
					'default': _iniValues[cseType]['registrarCsePort'],
					'name': 'registrarCsePort',
					'amark': '✓',
				},
			]
		)

	Console().clear()
	cnf:List[str] = []

	try:
		_print(f'[b]Creating a new [/b]{Constants.textLogo}[b] configuration file\n')

		# Get the CSE Type first
		questionsStart = [
			{	'type': 'rawlist',
				'message': 'Target environment:',
				'long_instruction': 'Run the CSE for development and testing, running demonstrations, or learning.',
				'default': 1,
				'choices': lambda _: [ 'Development   - Enable development, testing, and debugging support', 
									   'Introduction  - Introduction to oneM2M (install extra demo resources) UNDER CONSTRUCTION',
									   'Demonstration - Disable development features'],
				'transformer': lambda result: result.split()[0],
				'filter': lambda result: result.split()[0],
				'name': 'cseEnvironment',
				'amark': '✓',
			},
			{	'type': 'rawlist',
				'message': 'What type of CSE do you want to run:',
				'long_instruction': 'Type of CSE to run: Infrastructure, Middle, or Application Service Node.',
				'default': 1,
				'choices': lambda _: [ 'IN  - Infrastructure Node', 
									   'MN  - Middle Node',
									   'ASN - Application Service Node' ],
				'transformer': lambda result: result.split()[0],
				'filter': lambda result: result.split()[0],
				'name': 'cseType',
				'amark': '✓',
			}
		]
		t = prompt(questionsStart)
		cseType = cast(str, t['cseType'])
		cseEnvironment = cast(str, t['cseEnvironment'])
		cnf.append(f'cseType={cseType}')
	
		# Prompt for the basic configuration
		for each in (bc := basicConfig()):
			cnf.append(f'{each}={bc[each]}')
		
		# Prompt for registrar configuration
		if cseType in [ 'MN', 'ASN' ]:
			for each in (bc := registrarConfig()):
				cnf.append(f'{each}={bc[each]}')

		# Header for the configuration
		# Split it into a header and configuration. 
		# Also easier to print with rich and the [...]'s
		cnfHeader = (
				f'; {configFile}',
				';',
				'; Simplified configuration file for the [ACME] CSE',
				';',
				f'; created: {datetime.now().isoformat(" ", "seconds")}',
				';',
				f'; CSE type: {cseType}',
				f'; Environment: {cseEnvironment}',
				';',
				'',
				'',
		)

		cnfExtra = (
				'',
				'',
				# Add basic registration configuration
				'[cse.registration]',
				'allowedCSROriginators=id-in,id-mn,id-asn'
				'',
				'',
		)


		# Construct the configuration
		jcnf = '[basic.config]\n' + '\n'.join(cnf) + '\n'.join(cnfExtra)

		# add more configurations for development
		if cseEnvironment in ('Development'):	
			jcnf += '\n'.join((
				'',
				'',
				'[textui]',
				'startWithTUI=false',
				'',
				'[cse.operation.requests]',
				'enable=true',
				'',
				'[http]',
				'enableUpperTesterEndpoint=true',
				'enableStructureEndpoint=true',
			))

		# Show configuration and confirm write
		_print('\n[b]Save configuration\n')
		_jcnf = jcnf.replace("[", "\[")
		_print(f'[dim]{_jcnf}\n')

		if not inquirer.confirm(message = f'Write configuration to file {configFile}?', amark = '✓', default = True).execute():
			_print('\n[red]Configuration canceled\n')
			return False

	except KeyboardInterrupt:
		_print('\n[red]Configuration canceled\n')
		return False

	try:
		with open(configFile, 'w') as file:
			file.write('\n'.join(cnfHeader))
			file.write(jcnf)
	except Exception as e:
		_print(str(e))
		return False

	_print(f'\n[spring_green2]New {cseType}-CSE configuration created.\n')
	return True

