#
#	SUBResourceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	SUB Resource configurations
#
""" This module contains the configuration for Subscription resources."""

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class SUBResourceConfiguration(ModuleConfiguration):
	""" Subscription (SUB) Resource Configuration """

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Defaults for Subscription Resources

		config.resource_sub_batchNotifyDuration = parser.getint('resource.sub', 'batchNotifyDuration', fallback=60)	# seconds


	def validateConfiguration(self, config:Configuration, initial:Optional[bool]=False) -> None:
		# Check default subscription duration
		if config.resource_sub_batchNotifyDuration < 1:
			raise ConfigurationError(r'[i]\[resource.sub]:batchNotifyDuration[/i] must be > 0')
