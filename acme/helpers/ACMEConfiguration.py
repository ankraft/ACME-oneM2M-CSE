#
#	ACMEConfiguration.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	ACME Configuration class for managing configuration settings.
	This class extends the standard *ConfigParser* to provide additional functionality.
"""

from typing import Optional
import configparser


class ACMEConfiguration(configparser.ConfigParser):
	"""	ACMEConfiguration class extends the standard ConfigParser to provide additional functionality
		for managing configuration settings in a structured way.
		It allows for case-sensitive option names and ensures that sections are created if
		they do not exist.
	"""

	def __init__(self, defaults:Optional[dict[str, str]] = None) -> None:
		""" Initialize the ACMEConfiguration object.

			Args:
				defaults: Optional dictionary with default values for the configuration.
		"""

		super().__init__(defaults=defaults, 
						 delimiters=('=', ':'),
						 interpolation=configparser.ExtendedInterpolation(),
						 # Convert csv to list, ignore empty elements
						 converters={'list': lambda x: [i.strip() for i in x.split(',') if i]}
						)


	def set(self, section:str, option:str, value:str|None = None) -> None:
		""" Set a configuration option in the specified section.

			This overrides the default *set* method to ensure that the section 
			is created if it does not exist.

			Args:
				section: The section in which to set the option.
				option: The option to set.
				value: The value to set for the option. If *None*, the option will be set without a value.
		"""
		if section not in self:
			self[section] = {}
		super().set(section, option, value)


