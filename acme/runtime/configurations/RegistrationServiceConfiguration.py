#
#	RegistrationServiceConfiguration.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Registration Manager configurations
#

from __future__ import annotations
from typing import Optional

import configparser

from ..Configuration import Configuration, ConfigurationError
from .ModuleConfiguration import ModuleConfiguration


class RegistrationServiceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Registrations

		config.cse_registration_allowedAEOriginators = parser.getlist('cse.registration', 'allowedAEOriginators', fallback = ['C*','S*'])		# type: ignore [attr-defined]
		config.cse_registration_allowedCSROriginators = parser.getlist('cse.registration', 'allowedCSROriginators', fallback = [])				# type: ignore [attr-defined]
		config.cse_registration_checkLiveliness = parser.getboolean('cse.registration', 'checkLiveliness', fallback = True)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:
		pass

