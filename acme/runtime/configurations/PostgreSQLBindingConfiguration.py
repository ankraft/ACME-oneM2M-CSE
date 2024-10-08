#
#	PostgreSQLBindingConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	PostgreSQL DB configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...helpers.NetworkTools import isValidPort


class PostgreSQLBindingConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		"""	Read the configuration settings for the PostgreSQL database binding from the configuration file.

			Args:
				parser: The configuration parser object.
				config: The configuration object to store the settings.
		"""

		#	Database PostgreSQL

		config.database_postgresql_host = parser.get('database.postgresql', 'host', fallback = 'localhost')
		config.database_postgresql_port = parser.getint('database.postgresql', 'port', fallback = 5432)
		config.database_postgresql_role = parser.get('database.postgresql', 'role', fallback = None)	# CSE-ID
		config.database_postgresql_password = parser.get('database.postgresql', 'password', fallback = None)
		config.database_postgresql_database = parser.get('database.postgresql', 'database', fallback = 'acmecse')
		config.database_postgresql_schema = parser.get('database.postgresql', 'schema', fallback = 'acmecse')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		"""	Validate the configuration settings.

			Args:
				config: The configuration object to validate.
				initial: Whether this is the initial validation or not.
		"""

		# PostgreSQL

		if not isValidPort(config.database_postgresql_port):
			raise ConfigurationError(fr'Configuration Error: Invalid port number for [i]\[database.postgresql]:port[/i]: {config.database_postgresql_port}')

