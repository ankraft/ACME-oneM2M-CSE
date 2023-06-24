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

	BINDINGS = 	[ Binding('a', 'goto_repo', 'Open ACME @ GitHub') ]

	DEFAULT_CSS = """
#about-view {
	display: block;
	overflow: auto auto;  
	min-width: 100%;
}
"""


# 	logo = \
# f"""\
# [dim]███[/dim]     [{Constants.logoColor}] █████   ██████ ███    ███ ███████[/{Constants.logoColor}]     [dim]███[/dim] 
# [dim]██ [/dim]     [{Constants.logoColor}]██   ██ ██      ████  ████ ██     [/{Constants.logoColor}]     [dim] ██[/dim] 
# [dim]██ [/dim]     [{Constants.logoColor}]███████ ██      ██ ████ ██ █████  [/{Constants.logoColor}]     [dim] ██[/dim] 
# [dim]██ [/dim]     [{Constants.logoColor}]██   ██ ██      ██  ██  ██ ██     [/{Constants.logoColor}]     [dim] ██[/dim] 
# [dim]███[/dim]     [{Constants.logoColor}]██   ██  ██████ ██      ██ ███████[/{Constants.logoColor}]     [dim]███[/dim]""" 

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

	socialLink =  Text('Social: ') + Text('@acmeCSE@mstdn.social', style='link https://mstdn.social/@acmeCSE') + Text(' ')

	link =  Text('GitHub: ') + Text('https://github.com/ankraft/ACME-oneM2M-CSE', style='link https://github.com/ankraft/ACME-oneM2M-CSE') + Text(' ')

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


	def __init__(self) -> None:
		super().__init__(id = 'about')

		# HACK The following is a hack to get the focus on this page.
		# Otherwise, without an interactive element, the focus would not be on this page at all,
		# and the Bindings would not be shown.
		self.button = Button('hidden')
		self.button.styles.visibility = 'hidden'

	
	def on_show(self) -> None:
		self.button.focus()



	def compose(self) -> ComposeResult:
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
				yield self.button


	def action_goto_repo(self) -> None:
		webbrowser.open('https://github.com/ankraft/ACME-oneM2M-CSE')
