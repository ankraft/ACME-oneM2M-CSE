#
#	acme.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Starter for the ACME CSE
#

import argparse, sys
sys.path.append('acme')
sys.path.append('apps')
from Configuration import defaultConfigFile, defaultImportDirectory
import CSE


version = '0.2.1'
description = 'ACME ' + version + ' - An open source CSE Middleware for Education'


# Handle command line arguments
def parseArgs():
	parser = argparse.ArgumentParser(description=description)
	parser.add_argument('--config', action='store', dest='configfile', default=defaultConfigFile, help='specify the configuration file')

	# two mutual exlcusive arguments
	group = parser.add_mutually_exclusive_group()
	group.add_argument('--apps', action='store_true', dest='appsenabled', default=None, help='enable internal applications')
	group.add_argument('--no-apps', action='store_false', dest='appsenabled', default=None, help='disable internal applications')

	parser.add_argument('--db-reset', action='store_true', dest='dbreset', default=None, help='reset the DB when starting the CSE')
	parser.add_argument('--db-storage', action='store', dest='dbstoragemode', default=None, choices=[ 'memory', 'disk' ], type=str.lower, help='specify the DB´s storage mode')
	parser.add_argument('--log-level', action='store', dest='loglevel', default=None, choices=[ 'info', 'error', 'warn', 'debug', 'off'], type=str.lower, help='set the log level, or turn logging off')
	parser.add_argument('--import-directory', action='store', dest='importdirectory', default=None, help='specify the import directory')
	
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
	print(description)
	CSE.startup(parseArgs())
