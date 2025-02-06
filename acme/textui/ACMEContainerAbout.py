#
#	ACMEContainerAbout.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *About* view for the ACME text UI.
"""

from rich.text import Text
import webbrowser
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Center, Vertical
from textual.widgets import Label, Button
from textual.binding import Binding
from ..etc.Constants import Constants

class ACMEContainerAbout(VerticalScroll):
	"""	About view for the ACME text UI.
	"""

	BINDINGS = 	[ Binding('a', 'goto_homepage', 'Open Homepage') ]
	"""	The key bindings for the *About* view. """

	text = \
f"""\
[dim]███╗[/dim]    [{Constants.logoColor}] █████╗  ██████╗███╗   ███╗███████╗[/{Constants.logoColor}]    [dim]███╗[/dim]
[dim]██╔╝[/dim]    [{Constants.logoColor}]██╔══██╗██╔════╝████╗ ████║██╔════╝[/{Constants.logoColor}]    [dim]╚██║[/dim]
[dim]██║ [/dim]    [{Constants.logoColor}]███████║██║     ██╔████╔██║█████╗  [/{Constants.logoColor}]    [dim] ██║[/dim]
[dim]██║ [/dim]    [{Constants.logoColor}]██╔══██║██║     ██║╚██╔╝██║██╔══╝  [/{Constants.logoColor}]    [dim] ██║[/dim]
[dim]███╗[/dim]    [{Constants.logoColor}]██║  ██║╚██████╗██║ ╚═╝ ██║███████╗[/{Constants.logoColor}]    [dim]███║[/dim]
[dim]╚══╝[/dim]    [{Constants.logoColor}]╚═╝  ╚═╝ ╚═════╝╚═╝     ╚═╝╚══════╝[/{Constants.logoColor}]    [dim]╚══╝[/dim]

{Constants.version}

An open source CSE Middleware for Education

{Constants.copyright}

Available under the BSD 3-Clause License"""
	"""	The text for the ACME CSE about view."""

	socialLink =  Text('Social: ') + Text('@acmeCSE@mstdn.social', style='link https://mstdn.social/@acmeCSE') + Text(' ')
	"""	A link to the ACME CSE Mastodon account. """

	link =  Text('Homepage: ') + Text('https://acmecse.net', style='link https://acmecse.net') + Text(' ')
	"""	A link to the ACME CSE GitHub repository. """

	# curl qrcode.show  -H "X-QR-Quiet-Zone: true" -H "X-QR-Max-Width: 40" -H "X-QR-Max-Height: 40" -d https://acmecse.net
	qrcode = \
"""\
█████████████████████████████████
█████████████████████████████████
████ ▄▄▄▄▄ ██▄▀ ▄█  ▀█ ▄▄▄▄▄ ████
████ █   █ ██▄▄▀▄█ ▄██ █   █ ████
████ █▄▄▄█ █▀█ ▄█ █ ▄█ █▄▄▄█ ████
████▄▄▄▄▄▄▄█▄▀ ▀ █▄█▄█▄▄▄▄▄▄▄████
████ ▀█ ▀▄▄▀ ▄  ▀██▄▄ ▀▄████▀████
█████▄▀▀▀ ▄ ▄▀█▄██▀▀ ▀ ▀ ██▄▄████
█████ ▄█▀▀▄▀█ █▀ ███▄  ▀█ ▀▄ ████
████▄▀█ ▄▄▄▄▀▄▄█ ▀▀████▄ █▄▀▄████
████▄▄▄█▄█▄▄▀▀▀▄█▄▄█ ▄▄▄  ▄█▀████
████ ▄▄▄▄▄ █▀█▀▀█ █▄ █▄█  ▀▄ ████
████ █   █ █▀█▀  ▀▄█ ▄▄   ▀▄▄████
████ █▄▄▄█ ████   ▄▀▀▀█▄▄▀▄█▄████
████▄▄▄▄▄▄▄█▄█▄▄██▄▄▄▄▄▄███▄▄████
█████████████████████████████████
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\
"""
	"""	The QR code for the ACME CSE. """


	def __init__(self) -> None:
		"""	Initialize the view.
		"""
		super().__init__()

		self._aboutButton = Button('hidden', id = 'about-button')
		"""	A hidden button to get the focus on this page. """


	
	def on_show(self) -> None:
		"""	Show the view. Callback from *textualize*.
		"""
		# HACK The following is a hack to get the focus on this page.
		# Otherwise, without an interactive element, the focus would not be on this page at all,
		# and the Bindings would not be shown.
		# The button is hidden using the CSS
		self._aboutButton.focus()


	def compose(self) -> ComposeResult:
		"""	Compose the view. Callback from *textualize*.
		
			Returns:
				The ComposeResult.
		"""
		with Vertical(id = 'about-view'):
			with (_c := Center()):
				yield self._aboutButton
				_c.styles.padding = (4, 0, 0, 0)
				yield (_l := Label(self.text))
				_l.styles.text_align = 'center'
			with (_c := Center()):
				_c.styles.padding = (2, 0, 0, 0)
				yield Label(self.link)
			with (_c := Center()):
				_c.styles.padding = (1, 0, 0, 0)
				yield Label(self.socialLink)
			with (_c := Center()):
				_c.styles.padding = (3, 0, 0, 0)
				_c.styles.color = '#808080'
				yield Label(self.qrcode)


	def action_goto_homepage(self) -> None:
		"""	Open the ACME homepage in the browser.
		"""
		webbrowser.open('https://acmecse.net')
