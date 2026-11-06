#
#	dass.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DAS server implementation
#
"""	DAS server implementation. """

import argparse, asyncio, logging
from rich.logging import RichHandler
from .App import App
from .Configuration import Configuration


log = logging.getLogger(__name__)


def parseArgs() -> argparse.Namespace:
	"""	Parse command line arguments. """

	parser = argparse.ArgumentParser(description='DAS Server')
	parser.add_argument('--config', '-c', action='store', dest='configFile', default='config.ini', help='Configuration file to use (default: config.ini)')
	parser.add_argument('--no-deregister', '-ndr', action='store_true', dest='noDeregister', default=False, help='Do not deregister the AE on shutdown')
	parser.add_argument('--ignore-registration-error', '-ire', action='store_true', dest='ignoreRegistrationError', default=False, help='Ignore registration errors and continue running (default: False)')
	parser.add_argument('--log-level', '-l', action='store', dest='logLevel', default='INFO',
						 choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'), help='Log level (default: INFO)')
	return parser.parse_args()


if __name__ == '__main__':

	args = parseArgs()

	# Set up rich logging. The level is applied to the root logger so that it
	# takes effect for every module's logger, not just this one.
	logging.basicConfig(	level=args.logLevel,
							format='%(message)s',
							datefmt='[%X]',
							handlers=[ RichHandler(rich_tracebacks=True, show_path=False, markup=True) ])

	# Read configuration
	try:
		config = Configuration(args)
	except Exception as e:
		log.error(f'Failed to read configuration: {e}')
		exit(1)

	# Run the asyncio application
	asyncio.run(App(config, ignoreRegistrationError=args.ignoreRegistrationError, noDeregister=args.noDeregister).run())