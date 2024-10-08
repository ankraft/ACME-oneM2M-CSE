#
#	StorageConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CSE configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class StorageConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		config.database_type = parser.get('database', 'type', fallback = 'tinydb')
		config.database_resetOnStartup = parser.getboolean('database', 'resetOnStartup', fallback = False)
		config.database_backupPath = parser.get('database', 'backupPath', fallback = './data/backup')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		# override configuration with command line arguments
		if Configuration._args_DBReset is True:
			Configuration.database_resetOnStartup = True
		if Configuration._args_DBStorageMode is not None:
			Configuration.database_type = Configuration._args_DBStorageMode

		if config.database_type not in ['tinydb', 'postgresql', 'memory']:
			raise ConfigurationError(fr'Configuration Error: [i]\[database]:type[/i] must be "tinydb", "postgresql", or "memory"')


