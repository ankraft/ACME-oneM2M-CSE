#
#	acme.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Starter for the ACME CSE
#

import argparse, sys
from rich.console import Console
sys.path.append('acme')
sys.path.append('apps')
sys.path.append('webui')
from Constants import Constants as C
import CSE

# Handle command line arguments
def parseArgs() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument('--config', action='store', dest='configfile', default=C.defaultConfigFile, metavar='<filename>', help='specify the configuration file')

	# two mutual exlcusive arguments
	groupRemoteCSE = parser.add_mutually_exclusive_group()
	groupRemoteCSE.add_argument('--http', action='store_false', dest='http', default=None, help='run CSE with http server')
	groupRemoteCSE.add_argument('--https', action='store_true', dest='https', default=None, help='run CSE with https server')

	groupApps = parser.add_mutually_exclusive_group()
	groupApps.add_argument('--apps', action='store_true', dest='appsenabled', default=None, help='enable internal applications')
	groupApps.add_argument('--no-apps', action='store_false', dest='appsenabled', default=None, help='disable internal applications')

	groupRemoteCSE = parser.add_mutually_exclusive_group()
	groupRemoteCSE.add_argument('--remote-cse', action='store_true', dest='remotecseenabled', default=None, help='enable remote CSE connections')
	groupRemoteCSE.add_argument('--no-remote-cse', action='store_false', dest='remotecseenabled', default=None, help='disable remote CSE connections')

	groupRemoteCSE = parser.add_mutually_exclusive_group()
	groupRemoteCSE.add_argument('--statistics', action='store_true', dest='statisticsenabled', default=None, help='enable collecting CSE statistics')
	groupRemoteCSE.add_argument('--no-statistics', action='store_false', dest='statisticsenabled', default=None, help='disable collecting CSE statistics')

	groupRemoteCSE = parser.add_mutually_exclusive_group()
	groupRemoteCSE.add_argument('--validation', action='store_true', dest='validationenabled', default=None, help='enable attributes and arguments validation')
	groupRemoteCSE.add_argument('--no-validation', action='store_false', dest='validationenabled', default=None, help='disable attributes and arguments validation')

	groupApps = parser.add_mutually_exclusive_group()
	groupApps.add_argument('--remote-configuration', action='store_true', dest='remoteconfigenabled', default=None, help='enable http remote configuration endpoint')
	groupApps.add_argument('--no-remote-configuration', action='store_false', dest='remoteconfigenabled', default=None, help='disable http remote configuration endpoint')

	parser.add_argument('--db-reset', action='store_true', dest='dbreset', default=None, help='reset the DB when starting the CSE')
	parser.add_argument('--db-storage', action='store', dest='dbstoragemode', default=None, choices=[ 'memory', 'disk' ], type=str.lower, help='specify the DB´s storage mode')
	parser.add_argument('--http-address', action='store', dest='httpaddress', metavar='<server URL>',  help='specify the CSE\'s http server URL')
	parser.add_argument('--import-directory', action='store', dest='importdirectory', default=None, metavar='<directory>', help='specify the import directory')
	parser.add_argument('--network-interface', action='store', dest='listenif', metavar='<ip address>', default=None, help='specify the network interface/IP address to bind to')
	parser.add_argument('--log-level', action='store', dest='loglevel', default=None, choices=[ 'info', 'error', 'warn', 'debug', 'off'], type=str.lower, help='set the log level, or turn logging off')
	parser.add_argument('--headless', action='store_true', dest='headless', default=None, help='operate the CSE in headless mode')
	
	return parser.parse_args()

	# TODO init directory


if __name__ == '__main__':

	#	Start the CSE with command line arguments.
	#	In case the CSE should be started without command line parsing, the values
	#	can be passed instead. Unknown arguments are ignored.
	#	For example:
	#
	#		CSE.startup(None, configfile=defaultConfigFile, loglevel='error', resetdb=None)
	#
	#	Note: Always pass at least 'None' as first and then the 'configfile' parameter.
	console = Console()
	console.print('\n[dim][[/dim][red][i]ACME[/i][/red][dim]][/dim] ' + C.version + ' - [bold]An open source CSE Middleware for Education[/bold]\n\n', highlight=False)
	CSE.startup(parseArgs())
