#
#	ACMEHeader.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the header for the ACME text UI.
"""
from rich.text import Text
from textual.app import ComposeResult, RenderResult
from textual.widgets import Header, Label
from textual.widgets._header import HeaderClock, HeaderClockSpace, HeaderTitle
from textual.containers import Horizontal, Middle

from ..runtime import CSE
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.DateUtils import toISO8601Date
from ..etc.DateUtils import utcDatetime

class ACMEHeaderClock(HeaderClock):
	"""	Display a modified HeaderClock. It shows the time based on UTC to help
	  	with working with oneM2M timestamps, which are all UTC based."""
	
	def render(self) -> RenderResult:
		"""Render the header clock.

		Returns:
			The rendered clock.
		"""
		return Text(f'{toISO8601Date(utcDatetime(), readable = True)[:19]} UTC')	


class ACMEHeaderTitle(HeaderTitle):
	"""	Display the title / subtitle in the header."""

	def render(self) -> Text:
		"""Render the title.

			Returns:
				The rendered title.
		"""
		return Text.from_markup(f'{RC.cseType.name}-CSE : {RC.cseCsi}', overflow = 'ellipsis')


class ACMEHeader(Header):
	"""	Display the header of the ACME text UI."""

	def compose(self) -> ComposeResult:
		"""Compose the header.
		
			Yields:
				The header content.
		"""
		self.tall = True
		"""	Make the header tall. Inherited from the parent class. """

		_logoContainer = Middle()
		_logoContainer.styles.height = self.styles.height

		with Horizontal():
			with _logoContainer:
				yield Label(f'  {Constants.textLogo}')
			yield Label(' ' * 6)	# to align the title and the extra space of the clock
			yield ACMEHeaderTitle()
		yield ACMEHeaderClock() if self._show_clock else HeaderClockSpace()

