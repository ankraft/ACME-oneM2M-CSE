#
#	ScriptingConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Scripting configurations
#

from __future__ import annotations
from typing import Optional

import configparser, os

from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration

class ScriptingConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:
		config.scripting_fileMonitoringInterval = parser.getfloat('scripting', 'fileMonitoringInterval', fallback = 2.0)
		config.scripting_scriptDirectories = parser.getlist('scripting', 'scriptDirectories', fallback = []) # type: ignore[attr-defined]
		config.scripting_verbose = parser.getboolean('scripting', 'verbose', fallback = False)
		config.scripting_maxRuntime = parser.getfloat('scripting', 'maxRuntime', fallback = 60.0)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		# Script settings
		if config.scripting_fileMonitoringInterval < 0.0:
			raise ConfigurationError(fr'Configuration Error: [i]\[scripting]:fileMonitoringInterval[/i] must be >= 0.0')
		if config.scripting_maxRuntime < 0.0:
			raise ConfigurationError(fr'Configuration Error: [i]\[scripting]:maxRuntime[/i] must be >= 0.0')
		if (scriptDirs := config.scripting_scriptDirectories):
			lst = []
			for each in scriptDirs:
				if not each:
					continue
				if not os.path.isdir(each):
					raise ConfigurationError(fr'Configuration Error: [i]\[scripting]:scriptDirectory[/i]: directory "{each}" does not exist, is not a directory or is not accessible')
				lst.append(each)
			config.scripting_scriptDirectories = lst

