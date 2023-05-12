#
#	ACMEHeader.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the header for the ACME text UI.
"""
from datetime import datetime, timezone

from rich.text import Text
from textual.app import ComposeResult, RenderResult
from textual.widgets import Header
from textual.widgets._header import HeaderIcon, HeaderClock, HeaderClockSpace, HeaderTitle

from ..services import CSE
from ..etc.Constants import Constants
from ..etc.DateUtils import toISO8601Date


class ACMEHeaderClock(HeaderClock):
	"""	Display a modified HeaderClock. It shows the time based on UTC to help
	  	with working with oneM2M timestamps, which are all UTC based."""
	
	DEFAULT_CSS = """
	HeaderClockSpace {
		width: 25;
	}
	"""
	
	def render(self) -> RenderResult:
		"""Render the header clock.

		Returns:
			The rendered clock.
		"""
		return Text(f'{toISO8601Date(datetime.now(tz = timezone.utc), readable = True)[:19]} UTC')	


class ACMEHeaderTitle(HeaderTitle):
	"""	Display the title / subtitle in the header."""

	def render(self) -> Text:
		return Text.from_markup(f'{Constants.textLogo}[dim] {CSE.cseType.name}-CSE : {CSE.cseCsi}', overflow = 'ellipsis')


class ACMEHeader(Header):

	def compose(self) -> ComposeResult:
		yield HeaderIcon()
		yield ACMEHeaderTitle()
		yield ACMEHeaderClock() if self._show_clock else HeaderClockSpace()

