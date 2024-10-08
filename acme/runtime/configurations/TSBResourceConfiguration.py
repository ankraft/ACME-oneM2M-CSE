#
#	TSBResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TSB Resource configurations
#

from __future__ import annotations
from typing import Optional

import configparser, isodate

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class TSBResourceConfiguration(ModuleConfiguration):


	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Defaults for TimeSyncBeacon Resources

		config.resource_tsb_bcni = parser.get('resource.tsb', 'bcni', fallback = 'PT1H')	# duration
		config.resource_tsb_bcnt = parser.getfloat('resource.tsb', 'bcnt', fallback = 60.0)	# seconds


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		
		# TimeSyncBeacon defaults
		try:
			isodate.parse_duration(Configuration.resource_tsb_bcni)
		except Exception as e:
			raise ConfigurationError(fr'Configuration Error: [i]\[resource.tsb]:bcni[/i]: configuration value must be an ISO8601 duration')
