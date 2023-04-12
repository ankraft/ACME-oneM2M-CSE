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
▀▀▀▀▀▀▀ ▀▀ ▀▀▀      ▀    ▀▀▀▀ ▀ ▀"""

												   
	def __init__(self) -> None:
		super().__init__(id = idAbout)
	
		self.logoView = Center(_l := Label(self.text))
		_l.styles.text_align = 'center'
		self.logoView.styles.padding = (4, 0, 0, 0)

		self.linkView = Center(Label(self.link))
		self.linkView.styles.padding = (2, 0, 0, 0)

		self.socialLinkView = Center(Label(self.socialLink))
		self.socialLinkView.styles.padding = (1, 0, 0, 0)

		self.qrcodeView = Center(Label(self.qrcode))
		self.qrcodeView.styles.padding = (8, 0, 0, 0)

		self.aboutView = Vertical(self.logoView, 
								  self.linkView,
								  self.socialLinkView,
								  self.qrcodeView,
								  id = 'about-view')


	def compose(self) -> ComposeResult:
		yield self.aboutView

	async def onShow(self) -> None:
		...
