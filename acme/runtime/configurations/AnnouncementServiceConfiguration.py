#
#	AnnouncementServiceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" Announcement Service configurations
"""
from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class AnnouncementServiceConfiguration(ModuleConfiguration):
	""" Announcement Service configurations
	"""

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		""" Read the configuration from the configuration file.
		
			Args:
				parser: The configuration parser
				config: The configuration instance
		"""

		#	Announcements

		config.cse_announcements_allowAnnouncementsToHostingCSE = parser.getboolean('cse.announcements', 'allowAnnouncementsToHostingCSE', fallback = True)
		config.cse_announcements_delayAfterRegistration = parser.getfloat('cse.announcements', 'delayAfterRegistration', fallback = 3.0)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		""" Validate the configuration.

			Args:
				config: The configuration object
				initial: If True, this is the initial validation

			Raises:
				ConfigurationError if the configuration is invalid
		"""

		# check intervals
		if config.cse_announcements_delayAfterRegistration < 0.0:
			raise ConfigurationError(fr'Configuration Error: \[cse.announcements]:delayAfterRegistration must be 0 or greater')
