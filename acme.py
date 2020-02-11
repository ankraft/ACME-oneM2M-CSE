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
from Configuration import defaultConfigFile
import CSE


version = '0.1'
description = 'ACME ' + version + ' - An open source Cse Middleware for Education'


# Handle command line arguments
def parseArgs():
	parser = argparse.ArgumentParser(description=description)
	parser.add_argument('--config', action='store', dest='configfile', default=defaultConfigFile, help='Specify configuration file')
	parser.add_argument('--reset-db', action='store_true', dest='resetdb', default=None, help='Reset the DB when starting the CSE')
	parser.add_argument('--log-level', action='store', dest='loglevel', default=None, choices=[ 'info', 'error', 'warn', 'debug'], type=str.lower, help='Set the logging level')
	return parser.parse_args()

	# TODO init directory


if __name__ == '__main__':
	CSE.startup(parseArgs())
