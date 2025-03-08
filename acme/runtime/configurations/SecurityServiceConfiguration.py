#
#	SecurityServiceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Security Manager configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ...etc.Types import TreeMode
from ...runtime.Configuration import Configuration, ConfigurationError
from ...runtime.configurations.ModuleConfiguration import ModuleConfiguration

class SecurityServiceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	CSE Security

		config.cse_security_secret = parser.get('cse.security', 'secret', fallback = 'acme')
		config.cse_security_enableACPChecks = parser.getboolean('cse.security', 'enableACPChecks', fallback = True)
		config.cse_security_fullAccessAdmin = parser.getboolean('cse.security', 'fullAccessAdmin', fallback = True)


	def validateConfiguration(sel, config:Configuration, initial:Optional[bool] = False) -> None:
		if not config.cse_security_secret:
			raise ConfigurationError('Configuration Error: Missing or empty [i]\[cse.security\]:secret[/i] configuration')
		if config.cse_security_secret == 'acme':
			Configuration._print(r'[orange3]Configuration Warning: Using default [i]secret[/i] key. Consider changing this value for security reasons in \[cse.security].secret or \[basic.config].secret[/orange3]')
