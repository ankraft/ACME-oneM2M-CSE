#
#	ConsoleConfiguration.py
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

class ACTRResourceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		# 	Defaults for Actions

		config.resource_actr_ecpContinuous = parser.getint('resource.actr', 'ecpContinuous', fallback = 1000)
		config.resource_actr_ecpPeriodic = parser.getint('resource.actr', 'ecpPeriodic', fallback = 10000)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		if config.resource_actr_ecpContinuous <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.actr]:ecpContinuous[/i] must be > 0')
		if config.resource_actr_ecpPeriodic <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.actr]:ecpPeriodic[/i] must be > 0')

