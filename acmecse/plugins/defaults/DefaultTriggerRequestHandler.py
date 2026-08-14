#
#	DefaultTriggerRequestHandler.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Default handler for TriggerRequest functionality. 
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from acmecse.runtime.PluginSupport import Service, plugin, endpoint
from acmecse.runtime.Logging import Logging as L
from acmecse.etc.Constants import Constants as C

@plugin(tags=['acme', 'core', 'triggerRequestHandler', 'default'], priority=100)
class DefaultTriggerRequestHandler(Service):
	"""	Default handler for TriggerRequest functionality.

		This is a default handler for TriggerRequest functionality.
		It has the lowest priority and will be used if no other handler is available.
	"""

	@endpoint('acceptsM2MExtID')
	def acceptsM2MExtID(self, m2mExtID: str) -> bool:
		"""	Check whether the given m2mExtID is valid for this NSE handler, 
		that this handler can be used for triggering.

			Note:
				This is a default implementation that returns True for M2M-EXT-IDs that
				matches the domain "...@example.com" as part of the M2M-EXT-ID and False otherwise.

			Args:
				m2mExtID: The m2mExtID to check.

			Returns:
				True if the m2mExtID is valid for this handler, False otherwise.
		"""
		return m2mExtID.endswith(f'@{C.exampleDomain}')
	