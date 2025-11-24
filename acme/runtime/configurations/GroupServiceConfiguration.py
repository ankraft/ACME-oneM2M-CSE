#
#	GroupServiceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Group Service configurations
#
""" This module contains the configuration settings for the Group Service.
"""

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration

class GroupServiceConfiguration(ModuleConfiguration):
	""" This class defines the configuration settings for the Group Service.
	"""

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		#	Defaults for Group Resources

		config.resource_grp_resultExpirationTime = parser.getint('resource.grp', 'resultExpirationTime', fallback=0)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool]=False) -> None:
		# Check group resource defaults
		if config.resource_grp_resultExpirationTime < 0:
			raise ConfigurationError(fr'Configuration Error: [i]\[resource.grp]:resultExpirationTime[/i] must be >= 0')
