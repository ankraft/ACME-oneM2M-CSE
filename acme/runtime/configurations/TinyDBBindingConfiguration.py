#
#	TinyDBBindingConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TinyDB DB configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ..Configuration import Configuration
from .ModuleConfiguration import ModuleConfiguration


class TinyDBBindingConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		"""	Read the TinyDB configuration from the configuration file.

			Args:
				parser: The configuration parser.
				config: The configuration object.
		"""
		config.database_tinydb_path = parser.get('database.tinydb', 'path', fallback = './data')
		config.database_tinydb_cacheSize = parser.getint('database.tinydb', 'cacheSize', fallback = 0)		# Default: no caching
		config.database_tinydb_writeDelay = parser.getint('database.tinydb', 'writeDelay', fallback = 1)		# Default: 1 second



	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		"""	Validate the TinyDB configuration.

			Args:
				config: The configuration object.
				initial: Flag indicating if this is the initial validation.
		"""
		
		# override configuration with command line arguments
		if Configuration._args_DBDataDirectory is not None:
			Configuration.database_tinydb_path = Configuration._args_DBDataDirectory

