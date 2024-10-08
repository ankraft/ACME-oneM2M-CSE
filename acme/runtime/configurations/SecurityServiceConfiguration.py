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

		config.cse_security_enableACPChecks = parser.getboolean('cse.security', 'enableACPChecks', fallback = True)
		config.cse_security_fullAccessAdmin = parser.getboolean('cse.security', 'fullAccessAdmin', fallback = True)


	def validateConfiguration(sel, config:Configuration, initial:Optional[bool] = False) -> None:
		pass

