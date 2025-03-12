#
#	TextUIConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Text UI configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration


class TextUIConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Text UI
		config.textui_refreshInterval = parser.getfloat('textui', 'refreshInterval', fallback = 2.0)
		config.textui_startWithTUI = parser.getboolean('textui', 'startWithTUI', fallback = False)
		config.textui_theme = parser.get('textui', 'theme', fallback = 'dark')
		config.textui_maxRequestSize = parser.getint('textui', 'maxRequestSize', fallback = 10000)
		config.textui_notificationTimeout = parser.getfloat('textui', 'notificationTimeout', fallback = 2.0)
		config.textui_enableTextEditorSyntaxHighlighting = parser.getboolean('textui', 'enableTextEditorSyntaxHighlighting', fallback = False)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		
		# override configuration with command line arguments
		if Configuration._args_lightScheme is not None:
			Configuration.textui_theme = Configuration._args_lightScheme
		if Configuration._args_textUI is not None:
			Configuration.textui_startWithTUI = Configuration._args_textUI

		# Text UI settings
		if config.textui_maxRequestSize <= 0:
			raise ConfigurationError(r'Configuration Error: [i]\[textui]:maxRequestSize[/i] must be > 0s')
		config.textui_theme = config.textui_theme.lower()
		if config.textui_theme not in [ 'dark', 'light' ]:
			raise ConfigurationError(fr'Configuration Error: [i]\[textui]:theme[/i] must be "light" or "dark"')
		if config.textui_maxRequestSize < 0:
			raise ConfigurationError(fr'Configuration Error: [i]\[textui]:maxRequestSize[/i] must be >= 0')
		if config.textui_notificationTimeout < 0.0:
			raise ConfigurationError(fr'Configuration Error: [i]\[textui]:notificationTimeout[/i] must be >= 0')

