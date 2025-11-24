#
#	ModuleConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration handling base class
#
""" This module implements the configuration of the CSE. It reads the configuration file, performs checks,
	and provides access to the configuration values. """

from __future__ import annotations
from typing import Optional
from abc import ABC, abstractmethod
import configparser

from ..Configuration import Configuration

class ModuleConfiguration(ABC):
	"""	This abstract class defines the interface for module configurations.
	"""

	@abstractmethod
	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		""" Read a configuration from the configuration file.
		
			Args:
				parser: The configuration parser
				config: The configuration instance
		"""
		...

	@abstractmethod
	def validateConfiguration(self, config:Configuration, initial:Optional[bool]=False) -> None:
		""" Validate a configuration.

			Args:
				config: The configuration object
				initial: If True, this is the initial validation

			Raises:
				May raise ConfigurationError if the configuration is invalid
		"""

		...
