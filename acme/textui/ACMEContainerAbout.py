#
#	ACMEContainerAbout.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *About* view for the ACME text UI.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Center, Vertical
from textual.widgets import Label
from ..etc.Constants import Constants


idAbout = 'about'

class ACMEContainerAbout(Container):

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

(c) 2022 by Andreas Kraft

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
				_c.styles.padding = (8, 0, 0, 0)
				yield Label(self.qrcode)
