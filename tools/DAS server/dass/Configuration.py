#
#	Configuration.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration for DAS server
#
"""	Configuration for DAS server. """

import configparser, argparse, logging


log = logging.getLogger(__name__)


class Configuration:
	"""	DAS server configuration settings.
	"""

	def __init__(self, args: argparse.Namespace) -> None:
		self.configFileName = args.configFile

		try:
			config = configparser.ConfigParser(	interpolation=configparser.ExtendedInterpolation(),
												converters={'list': lambda x: [i.strip() for i in x.split(',')]},	# Convert csv to list
											)
			config.optionxform = str	# type: ignore[assignment]	# Preserve the case of option names instead of lowercasing them
			if len(config.read([self.configFileName])) == 0:
				raise FileNotFoundError(f'Configuration file not found: "{self.configFileName}"')
		except configparser.Error as e:
			log.error('Error in configuration file')
			raise e

		# Readd all target CSE settings, where the AE is to register
		# These sections start with 'cse.'
		self.cses: dict[str, dict[str, str]] = {}
		self.notifications: dict[str, str|int] = {}
		self.rules: dict[str, str|int] = {}

		for section in config.sections():
			match section:
				case 'notifications':
					self.notifications = {}
					for key, value in config.items(section):
						match key:
							case 'port':
								self.notifications[key] = int(value)
							case _:
								self.notifications[key] = value

				case 'rules':
					self.rules = {}
					for key, value in config.items(section):
						match key:
							case 'reloadInterval':
								self.rules[key] = int(value)
							case _:
								self.rules[key] = value
					self.rules.setdefault('path', 'rules')
					self.rules.setdefault('reloadInterval', 10)
					# TODO add sanity and completness checks

				case _ if section.startswith('cse.'):
					cseId = f'/{section[4:]}'	# Remove 'cse.' prefix, but add a leading slash
					self.cses[cseId] = {}
					for key, value in config.items(section):
						self.cses[cseId][key] = value

					# Sanity and completeness checks for CSE configuration
					_conf = self.cses[cseId]
					if 'releaseVersion' not in _conf:
						log.warning(f'Missing "releaseVersion" configuration for CSE: {cseId}. Using default value 5.')
						_conf['releaseVersion'] = '5'
					if 'httpAddress' not in _conf:
						raise ValueError(f'Missing "httpAddress" configuration for CSE: {cseId}')
					if 'aeResourceName' not in _conf:
						log.warning(f'Missing "aeResourceName" configuration for CSE: {cseId}. Using default value "das".')
						_conf['aeResourceName'] = 'das'
					if 'aeAppId' not in _conf:
						log.warning(f'Missing "aeAppId" configuration for CSE: {cseId}. Using default value "N{_conf["aeResourceName"]}".')
						_conf['aeAppId'] = f'N{_conf["aeResourceName"]}'
					if 'aeOriginator' not in _conf:
						log.warning(f'Missing "aeOriginator" configuration for CSE: {cseId}. Using default value "CDASServer".')
						_conf['aeOriginator'] = 'CDASServer'
					if _conf['aeOriginator'] in ('', 'C', 'S'):
						raise ValueError(f'Invalid "aeOriginator" configuration for CSE: {cseId}. Value cannot be empty or "C" or "S".')
					if 'aeHttpPOA' not in _conf:
						log.warning(f'Missing "aeHttpPOA" configuration for CSE: {cseId}. Using default value based on general host and notifications port.')
						_conf['aeHttpPOA'] = f'http://{self.notifications.get("host", "localhost")}:{self.notifications.get("port", 8080)}{self.notifications.get("endpoint", "")}'

		# The [rules] section is optional; provide defaults if it wasn't present at all
		self.rules.setdefault('path', 'rules')
		self.rules.setdefault('reloadInterval', 10)

		log.debug(f'CSE configurations: {self.cses}')
		log.debug(f'Notification configuration: {self.notifications}')
		log.debug(f'Rules configuration: {self.rules}')