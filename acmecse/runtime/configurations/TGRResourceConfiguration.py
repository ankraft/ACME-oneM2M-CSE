#
#	TGRResourceConfiguration.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TGR Resource configurations
#
""" This module contains the configuration for TriggerRequest resources."""

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class TGRResourceConfiguration(ModuleConfiguration):
	""" TriggerRequest Resource Configuration """

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Defaults for TriggerRequest Resources
		config.resource_tgr_maxTriggerValidityTime = parser.getint('resource.tgr', 'maxTriggerValidityTime', fallback=60)		# Seconds


	def validateConfiguration(self, config:Configuration, initial:Optional[bool]=False) -> None:
		if config.resource_tgr_maxTriggerValidityTime <= 0:
			raise ConfigurationError(rf'[i]\[resource.tgr]:maxTriggerValidityTime[/i] must be > 0\n[dim]Configured value: {config.resource_tgr_maxTriggerValidityTime}[/dim]')
