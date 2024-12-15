#
#	FCNTResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	FCNT Resource configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class FCNTResourceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		# 	Defaults for FlexContainer Resources
		config.resource_fcnt_enableLimits = parser.getboolean('resource.fcnt', 'enableLimits', fallback = False)
		config.resource_fcnt_mni = parser.getint('resource.fcnt', 'mni', fallback = 10)
		config.resource_fcnt_mbs = parser.getint('resource.fcnt', 'mbs', fallback = 10000)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		if config.resource_fcnt_mni <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.fcnt]:mni[/i] must be > 0')
		if config.resource_fcnt_mbs <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.fcnt]:mbs[/i] must be > 0')
