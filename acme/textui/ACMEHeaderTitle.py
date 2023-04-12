#
#	ACMEHeaderTitle.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the header title for the ACME text UI.
"""

from rich.text import Text
from textual.widgets._header import HeaderTitle
from ..etc.Constants import Constants
from ..services import CSE

class ACMEHeaderTitle(HeaderTitle):
	"""	Display the title / subtitle in the header."""

	def render(self) -> Text:
		return Text.from_markup(f'{Constants.textLogo}[dim] {CSE.cseType.name}-CSE : {CSE.cseCsi}', overflow = 'ellipsis')
