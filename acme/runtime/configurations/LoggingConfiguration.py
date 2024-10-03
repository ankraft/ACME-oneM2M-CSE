#
#	LoggingConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Logging configurations
#

from __future__ import annotations
from typing import Optional, cast

import configparser

from ...etc.Types import LogLevel
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration

class LoggingConfiguration(ModuleConfiguration):


	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Logging

		config.logging_count = parser.getint('logging', 'count', fallback = 10)		# Number of log files
		config.logging_enableBindingsLogging = parser.getboolean('logging', 'enableBindingsLogging', fallback = False)
		config.logging_enableFileLogging = parser.getboolean('logging', 'enableFileLogging', fallback = False)
		config.logging_enableScreenLogging = parser.getboolean('logging', 'enableScreenLogging', fallback = True)
		config.logging_filter = parser.getlist('logging', 'filter', fallback = [])		# type: ignore [attr-defined]
		config.logging_level = parser.get('logging', 'level', fallback = 'debug')
		config.logging_maxLogMessageLength = parser.getint('logging', 'maxLogMessageLength', fallback = 1000)	# Max length of a log message
		config.logging_path = parser.get('logging', 'path', fallback = './logs')
		config.logging_queueSize = parser.getint('logging', 'queueSize', fallback = 5000)	# Size of the log queue
		config.logging_size = parser.getint('logging', 'size', fallback = 100000)
		config.logging_stackTraceOnError = parser.getboolean('logging', 'stackTraceOnError', fallback = True)
		config.logging_enableUTCTimezone = parser.getboolean('logging', 'enableUTCTimezone', fallback = False)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		# Loglevel and various overrides from command line
		logLevel = Configuration._args_loglevel if Configuration._args_loglevel else config.websocket_loglevel
		logLevel = cast(LogLevel, logLevel).name if isinstance(logLevel, LogLevel) else logLevel
		if isinstance(logLevel, str):
			if (ll := LogLevel.toLogLevel(logLevel)) is None:
				raise ConfigurationError(fr'Configuration Error: Unsupported \[logging]:level: {logLevel}')
			config.logging_level = ll
		else:
			raise ConfigurationError(fr'Configuration Error: Unsupported \[logging]:level: {logLevel}')

		# max message length
		if config.logging_maxLogMessageLength < 0:
			raise ConfigurationError(fr'Configuration Error: \[logging]:maxLogMessageLength must be 0 or greater')
		
		# Test for correct logging queue size
		if config.logging_queueSize < 0:
			raise ConfigurationError(fr'Configuration Error: \[logging]:queueSize must be 0 or greater')

