#
#	StatisticsCofiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Statistics configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class StatisticsConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Statistics

		config.cse_statistics_enable = parser.getboolean('cse.statistics', 'enable', fallback = True)
		config.cse_statistics_writeInterval = parser.getint('cse.statistics', 'writeInterval', fallback = 60)		# Seconds


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		if config.cse_statistics_writeInterval <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[cse.statistics]:writeInterval[/i] must be > 0')
		
