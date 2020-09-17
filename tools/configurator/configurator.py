#
#	configurator.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Command line tool to quickly create a basic configuration
#

import re, configparser, sys, os
from rich.console import Console
from PyInquirer import prompt, Separator

messageColor = 'spring_green2'



##############################################################################
#
#	Utils
#

urlregex = re.compile(
        r'^(?:http|ftp)s?://' 						# http://, https://, ftp://, ftps://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9]))|' # localhost or single name w/o domain
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 		# ipv4
        r'(?::\d+)?' 								# optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)			# optional path


def isURL(url: str) -> bool:
	""" Check whether a given string is a URL. """
	return url is not None and re.match(urlregex, url) is not None


##############################################################################
#
#	CSE Basic
#
def typeDefault(values):
	return 2

def csiDefault(values):
	return { 'IN':'/id-in', 'MN':'/id-mn', 'ASN':'/id-asn'}[values['type']]

def csiValidate(value):
	return value.startswith('/') and not '/' in value[1:]

def csernDefault(values):
	return { 'IN':'cse-in', 'MN':'cse-mn', 'ASN':'cse-asn'}[values['type']]

def csernValidate(value):
	return not '/' in value[1:]

def originatorDefault(values):
	return 'CAdmin'

def originatorValidate(value):
	return re.match('^[0-9a-zA-Z_]*$',value) is not None

def spidDefault(values):
	return 'acme'

def spidValidate(value):
	return not '/' in value[1:]

def resourcesPathDefault(values):
	return './init'

def resourcesPathValidate(value):
	return os.path.exists(value) or os.access(os.path.dirname(value), os.W_OK)

cseQuestions = [
	{	'type': 'list',
		'name': 'type',
		'message': 'CSE Type?',
		'choices': [
			{	'name': 'IN  - Infrastructure Node',
				'value': 'IN'
			},
			{	'name': 'MN  - Middle Node',
				'value': 'MN'
			},
			{	'name': 'ASN - Application Service Node',
				'value': 'ASN'
			}
		],
		'default': typeDefault
	},
	{	'type': 'input',
		'name': 'cseID',
		'message': 'CSE-ID (must start with "/" )?',
		'default' : csiDefault,
		'validate': csiValidate
	},
	{	'type': 'input',
		'name': 'serviceProviderID',
		'message': 'Service Provide ID?',
		'default' : spidDefault,
		'validate': spidValidate
	},
	{	'type': 'input',
		'name': 'resourceName',
		'message': 'CSE Name?',
		'default' : csernDefault,
		'validate': csernValidate
	},
	{	'type': 'input',
		'name': 'originator',
		'message': 'Admin Originator?',
		'default' : originatorDefault,
		'validate': originatorValidate
	},
	{	'type': 'input',
		'name': 'resourcesPath',
		'message': 'Path to Initial Resources?',
		'default' : resourcesPathDefault,
		'validate': resourcesPathValidate
	},




# path=./logs
# level=debug
# enable=true
# enableFileLogging=true

# allowedCSROriginators=id-mn

# [cse.registrar]
# address=http://127.0.0.1:8081
# cseID=/in-cse
# resourceName=cse-in

]

##############################################################################
#
#	HTTP Server
#


def listenIFDefault(values):
	return '127.0.0.1'

def listenIFValidate(value):
	return re.match('^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',value) is not None

def portDefault(values):
	return { 'IN': '8080', 'MN':'8081', 'ASN':'8082'}[cseAnswers['type']]

def portValidate(value):
	return value.isdigit() and (p := int(value)) and p >= 0 and p <= 65535

def addressDefault(values):
	return 'http://%s:%s' % (values['listenIF'], values['port'])

def addressValidate(value):
	return isURL(value)

httpQuestions = [
	{	'type': 'input',
		'name': 'listenIF',
		'message': 'Listen Network Interface?',
		'default' : listenIFDefault,
		'validate': listenIFValidate
	},
	{	'type': 'input',
		'name': 'port',
		'message': 'Server Port?',
		'default' : portDefault,
		'validate': portValidate
	},
	{	'type': 'input',
		'name': 'address',
		'message': 'Server Address?',
		'default' : addressDefault,
		'validate': addressValidate
	},
]


##############################################################################
#
#	Database
#

# path=./data
# inMemory=false
# resetAtStartup=false

loggingQuestions = [
]



if __name__ == '__main__':

	console = Console()
	console.print('\n[dim][[[/dim][red][i]ACME[/i][/red][dim]][/dim] - [bold]Configuration Builder\n\n')
	console.print('Generate a basic configuration file for the ACME CSE')

	configuration = configparser.RawConfigParser()
	configuration.optionxform = lambda option: option 	# Allow case sensitive keys

	#
	#	CSE Basics
	#
	
	console.print('\n[%s]CSE Basics\n\n' % messageColor)
	if len((cseAnswers := prompt(cseQuestions))) == 0:
		sys.exit(1)
	configuration['cse'] = { k:v for k,v in cseAnswers.items() }

	#
	#	HTTP Server
	#

	console.print('\n[%s]HTTP Server\n\n' % messageColor)
	if len(httpAnswers := prompt(httpQuestions)) == 0:
		sys.exit(1)
	configuration['server.http'] = { k:v for k,v in httpAnswers.items() }

	#
	#	Logging
	#

	console.print('\n[%s]Logging\n\n' % messageColor)
	loggingAnswers = prompt(loggingQuestions)

	#
	#	Database
	#

	console.print('\n[%s]Database\n\n' % messageColor)

	console.print(cseAnswers)

	with sys.stdout as file:
		configuration.write(file, space_around_delimiters=False)

