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
from textual.containers import Container, Center, Vertical
from textual.widgets import Label, Button
from textual.binding import Binding
from ..etc.Constants import Constants

class ACMEContainerAbout(Container):
	"""	About view for the ACME text UI.
	"""

	BINDINGS = 	[ Binding('a', 'goto_repo', 'Open ACME @ GitHub') ]
	"""	The key bindings for the *About* view. """

	DEFAULT_CSS = """
	#about-view {
		display: block;
		overflow: auto auto;  
		min-width: 100%;
	}

	#about-button {
		height:0;
		width:0;
		border: none;
	}
	"""
	"""	The CSS for the *About* view. """

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

	link =  Text('GitHub: ') + Text('https://github.com/ankraft/ACME-oneM2M-CSE', style='link https://github.com/ankraft/ACME-oneM2M-CSE') + Text(' ')
	"""	A link to the ACME CSE GitHub repository. """

	qrcode = \
"""\
█▀▀▀▀▀█ ▀▀▀▀▀▄█▀▄▄█  ▄█ ▄ █▀▀▀▀▀█
█ ███ █ ▀█▀▀  ███ █▄▄ █▀  █ ███ █
█ ▀▀▀ █ ▄▀▀▀▄██▀█▄▀▀██▀▀▀ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀▄█ █ ▀ ▀ █ ▀ ▀ ▀ ▀▀▀▀▀▀▀
▀▄▀▄ ▄▀▀ ███ ▀ ▀  ▄██ ▀█▄ ▄▀ ▄▀▄▀
▀▄▄█▄▀▀▄▄▀▄██▀█▄▄▀█▀ ▀█▀▀██▄▄█▀▀▄
▀ ▀ ██▀▄██ ▄▄██▀█▀█▀███ █ ▀ █ ▄██
█▀▄▀▀ ▀▀▀█▄▀  ▄▄█ ▀▄█  ▀ ▄▄██▄▄ ▀
▀▀▀ ▄ ▀▄▀████▄▄▄ ▄ ▄█▄ ██ █▀ ▄▀▀
█ ▄  █▀█▄▀█▄▀▄ ▀▀▄ █▄▄ ▀██▄▀▄█▀█▀
▀▄▀█ ▀▀ ▄█▀█ █ ▀ ▀   ▀ ▀▄▄▀█▀ ▄ ▄
▀▀▀ █▄▀▀▄ ▄▀▀█▄▀ ▀█▀  █ █▄█   ▄ █
▀▀ ▀  ▀ █ ▀▄▄▀ █▀  █▀  ██▀▀▀█ ▀█▄
█▀▀▀▀▀█ ▀ ▄▄▄▀ ▀█▀█▀▄▀█▄█ ▀ ██▀ █
█ ███ █  ▄▄▄ ▀▀▀█▀█ ████▀█▀██ ▄█  
█ ▀▀▀ █ ▀█▄▄▀▀▀▄█  ▄█ ▄█ ▀ ██▄▀▀▀
▀▀▀▀▀▀▀ ▀▀ ▀▀▀      ▀    ▀▀▀▀ ▀ ▀\
"""
	"""	The QR code for the ACME CSE. """


	
	def on_show(self) -> None:
		"""	Show the view. Callback from *textualize*.
		"""
		# HACK The following is a hack to get the focus on this page.
		# Otherwise, without an interactive element, the focus would not be on this page at all,
		# and the Bindings would not be shown.
		# The button is hidden using the CSS
		self.query_one('#about-button').focus()


	def compose(self) -> ComposeResult:
		"""	Compose the view. Callback from *textualize*.
		
			Returns:
				The ComposeResult.
		"""
		with Vertical(id = 'about-view'):
			with (_c := Center()):
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
				_c.styles.padding = (7, 0, 0, 0)
				yield Label(self.qrcode)
				yield Button('hidden', id = 'about-button')


	def action_goto_repo(self) -> None:
		"""	Open the ACME @ GitHub page in the browser.
		"""
		webbrowser.open('https://github.com/ankraft/ACME-oneM2M-CSE')
