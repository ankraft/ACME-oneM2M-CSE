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


import argparse, os
from rich.console import Console
from .etc.Constants import Constants as C
from .runtime import Onboarding


def main() -> None:
	""" Main function to start the onboarding process. 
	"""

	Console().print(f'\n{C.textLogo} ' + C.version + ' - [bold]An open source CSE Middleware for Education - OnBoarding[/bold]\n\n', highlight = False)

	parser = argparse.ArgumentParser(prog='acme.onboarding')

	# get file name and other configurations
	parser.add_argument('file', help='The configuration file to be created')
	parser.add_argument('--overwrite', '-o', help='Overwrite the file if it exists', action='store_true')
	args = parser.parse_args()

	# add the path if not given
	configFile = args.file
	if not os.path.dirname(args.file):
		configFile = os.path.join(os.getcwd(), args.file)
	
	# Check if file exists
	if os.path.exists(configFile) and not args.overwrite:
		Console().print(f'File {configFile} already exists. Please remove it first.', style='bold red')
		return
	
	# Start onboarding process
	Onboarding.buildUserConfigFile(configFile)



if __name__ == '__main__':
	main()
