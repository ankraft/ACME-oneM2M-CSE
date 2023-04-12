#
#	ACMEHeader.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the header for the ACME text UI.
"""

from textual.app import ComposeResult
from textual.widgets import Header
from textual.widgets._header import HeaderIcon, HeaderClock, HeaderClockSpace
from ..textui.ACMEHeaderTitle import ACMEHeaderTitle

class ACMEHeader(Header):

	def compose(self) -> ComposeResult:
		yield HeaderIcon()
		yield ACMEHeaderTitle()
		yield HeaderClock() if self._show_clock else HeaderClockSpace()

