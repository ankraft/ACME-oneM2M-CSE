#
#	LCPResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	LCP Resource configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class LCPResourceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Defaults for LocationPolicy Resources

		config.resource_lcp_mni = parser.getint('resource.lcp', 'mni', fallback = 10)
		config.resource_lcp_mbs = parser.getint('resource.lcp', 'mbs', fallback = 10000)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		if config.resource_lcp_mni <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.lcp]:mni[/i] must be > 0')
		if config.resource_lcp_mbs <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.lcp]:mbs[/i] must be > 0')
