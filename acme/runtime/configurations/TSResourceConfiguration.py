#
#	TSResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TS Resource configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class TSResourceConfiguration(ModuleConfiguration):


	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Defaults for timeSeries Resources

		config.resource_ts_enableLimits = parser.getboolean('resource.ts', 'enableLimits', fallback = False)
		config.resource_ts_mbs = parser.getint('resource.ts', 'mbs', fallback = 10000)
		config.resource_ts_mdn = parser.getint('resource.ts', 'mdn', fallback = 10)
		config.resource_ts_mni = parser.getint('resource.ts', 'mni', fallback = 10)
		config.resource_ts_mia = parser.getint('resource.ts', 'mia', fallback = 60*60*24*365*5)  # 5 years, in seconds


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		if config.resource_ts_mbs <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.ts]:mbs[/i] must be > 0')
		if config.resource_ts_mdn < 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.ts]:mdn[/i] must be >= 0')
		if config.resource_ts_mni <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.ts]:mni[/i] must be > 0')
		if config.resource_ts_mia <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.ts]:mia[/i] must be > 0')
