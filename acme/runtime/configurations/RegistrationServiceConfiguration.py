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
from ...etc.IDUtils import isAbsolute, isSPRelative, isCSI


class RegistrationServiceConfiguration(ModuleConfiguration):

	def readConfiguration(self, parser:configparser.ConfigParser, config:Configuration) -> None:

		#	Registrations

		config.cse_registration_allowedAEOriginators = parser.getlist('cse.registration', 'allowedAEOriginators', fallback = ['C*','S*'])		# type: ignore [attr-defined]
		config.cse_registration_allowedCSROriginators = parser.getlist('cse.registration', 'allowedCSROriginators', fallback = [])				# type: ignore [attr-defined]
		config.cse_registration_checkLiveliness = parser.getboolean('cse.registration', 'checkLiveliness', fallback = True)
		config.cse_registration_checkInterval = parser.getint('cse.registration', 'checkInterval', fallback = 60)


	def validateConfiguration(self, config:Configuration, initial:Optional[bool] = False) -> None:

		if config.cse_registration_allowedCSROriginators:
			for originator in config.cse_registration_allowedCSROriginators:
				if (isAbsolute(originator) and isCSI(originator)) or \
				   (isSPRelative(originator) and isCSI(originator)):
					# Valid originator
					continue
				# Invalid originator
				raise ConfigurationError(f'Invalid originator: "{originator}" in \[cse.registration].allowedCSROriginators. Must be a CSE-ID in absolute or SP-relative form')

