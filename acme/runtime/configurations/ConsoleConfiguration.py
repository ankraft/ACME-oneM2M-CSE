#
#	ConsoleConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Console configurations"""

from __future__ import annotations
from typing import Optional

import configparser

from ...etc.Types import TreeMode
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration
from ...etc.Constants import RuntimeConstants as RC

class ConsoleConfiguration(ModuleConfiguration):
	""" Console configurations
	"""

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		#	Console
		config.console_type = parser.get('console', 'type', fallback='rich')
		config.console_confirmQuit = parser.getboolean('console', 'confirmQuit', fallback=False)
		config.console_headless = parser.getboolean('console', 'headless', fallback=False)
		config.console_hideResources = parser.getlist('console', 'hideResources', fallback=[])		# type: ignore[attr-defined]
		config.console_refreshInterval = parser.getfloat('console', 'refreshInterval', fallback=2.0)
		config.console_theme = parser.get('console', 'theme', fallback='dark')
		config.console_treeIncludeVirtualResource = parser.getboolean('console', 'treeIncludeVirtualResources', fallback=False)
		config.console_treeMode = parser.get('console', 'treeMode', fallback='normal')


	def validateConfiguration(self, config:Configuration, initial:Optional[bool]=False) -> None:
		# override configuration with command line arguments
		if Configuration._args_headless:
			Configuration.console_headless = True
		if Configuration._args_lightScheme is not None:
			Configuration.console_theme = Configuration._args_lightScheme  # Override console theme 

		# Console settings

		if config.console_type not in [ 'rich', 'simple' ]:
			raise ConfigurationError(fr'[i]\[console]:type[/i] must be "rich" or "simple"')

		if config.console_refreshInterval <= 0.0:
			raise ConfigurationError(r'[i]\[console]:refreshInterval[/i] must be > 0.0')
		
		if isinstance(Configuration.console_treeMode, str):
			if not (treeMode := TreeMode.to(Configuration.console_treeMode, insensitive = True)):
				raise ConfigurationError(fr'[i]\[console]:treeMode[/i] must be one of {TreeMode.names()}')
			Configuration.console_treeMode = treeMode
		
		Configuration.console_theme = Configuration.console_theme.lower()
		if Configuration.console_theme not in [ 'dark', 'light' ]:
			raise ConfigurationError(fr'[i]\[console]:theme[/i] must be "light" or "dark"')

		if Configuration.console_headless:
			Configuration.logging_enableScreenLogging = False
			Configuration.textui_startWithTUI = False
			RC.isHeadless = True
			
