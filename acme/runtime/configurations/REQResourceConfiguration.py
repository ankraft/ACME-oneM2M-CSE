#
#	REQResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	REQ Resource configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class REQResourceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Defaults for Request Resources

		config.resource_req_et = parser.getint('resource.req', 'expirationTime', fallback = 60)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		if config.resource_req_et <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[resource.req]:expirationTime[/i] must be > 0')
		