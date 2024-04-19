#
#	ACMEContainerAbout.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Registrations* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from ..runtime import CSE


class ACMEContainerRegistrations(Container):

	DEFAULT_CSS = '''
	#registrations-view {
		display: block;
		overflow: auto auto;  
		min-width: 100%;
	}
	'''

	def compose(self) -> ComposeResult:
		yield Static(expand = True, id = 'registrations-view')


	@property
	def registrationView(self) -> Static:
		return cast(Static, self.query_one('#registrations-view'))


	def on_show(self) -> None:
		self.registrationsUpdate()
	
	def registrationsUpdate(self) -> None:
		self.registrationView.update(CSE.console.getRegistrationsRich())
	

