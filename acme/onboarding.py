#
#	onboarding.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This modiule provides the stand-alone program to start the onboarding process for the ACME CSE.

	The onboarding process is used to create a first configuration file for the ACME CSE.

	This module can be run as a standalone script to create a configuration file as follows:

		::

			python -m acme.onboarding <configfile>
"""

from typing import Optional, Tuple
import argparse, os
from rich.console import Console
from .etc.Constants import Constants as C
from .runtime import Onboarding


def main() -> None:
	""" Main function to start the onboarding process. 
	"""

	Console().print(f'\n{C.textLogo} ' + C.version + ' - [bold]An open source CSE Middleware for Education - OnBoarding[/bold]\n\n', highlight = False)

	parser = argparse.ArgumentParser(prog='acme.onboarding',
									formatter_class=argparse.RawDescriptionHelpFormatter,
								    epilog="""
Use this program to create a configuration file for the ACME CSE. 
The configuration file can be used to start the ACME CSE with the 
specified configuration.

If you want to use Zookeeper for configuration management, specify
the Zookeeper host, port, and root node. Note, that you can only 
use either a configuration file or Zookeeper for the configuration,
not both at the same time.
""")

	# get file name and other configurations. The file and the zookeeper host are mutually exclusive
	groupConfig = parser.add_mutually_exclusive_group()
	groupConfig.add_argument('file', action='store', nargs='?', help='The configuration file to be created')
	groupConfig.add_argument('--zookeeper-host', action='store', dest='zkHost', default=None, metavar='<hostname>', help='specify the Zookeeper host name')

	parser.add_argument('--zookeeper-port', action='store', dest='zkPort', default=2181, metavar='<port>', help='specify the Zookeeper port (default: 2181)')
	parser.add_argument('--overwrite', '-o', help='Overwrite the file if it exists', action='store_true')
	args = parser.parse_args()

	zkConfiguration:Tuple[str, int, Optional[str]] = None
	configFile:str = None

	if args.file:

		# add the path if not given
		configFile = args.file
		if not os.path.dirname(args.file):
			configFile = os.path.join(os.getcwd(), args.file)
		
		# Check if file exists
		if os.path.exists(configFile) and not args.overwrite:
			Console().print(f'File {configFile} already exists. Please remove it first.', style='bold red')
			return
	
	# Check if Zookeeper host is given
	elif args.zkHost:
		zkConfiguration = (args.zkHost, args.zkPort, None)

	else:
		Console().print('Please specify either a configuration file or a Zookeeper host.', style='bold red')
		return
	
	# Start onboarding process
	Onboarding.buildUserConfigFile(configFile, zkConfiguration, args.overwrite)



if __name__ == '__main__':
	main()
