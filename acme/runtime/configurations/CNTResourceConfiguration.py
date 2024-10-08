#
#	CNTResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CNT Resource configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class CNTResourceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		# 	Defaults for Container Resources

		config.resource_cnt_enableLimits = parser.getboolean('resource.cnt', 'enableLimits', fallback = False)
		config.resource_cnt_mni = parser.getint('resource.cnt', 'mni', fallback = 10)
		config.resource_cnt_mbs = parser.getint('resource.cnt', 'mbs', fallback = 10000)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		if config.resource_cnt_mni <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.cnt]:mni[/i] must be > 0')
		if config.resource_cnt_mbs <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.cnt]:mbs[/i] must be > 0')
