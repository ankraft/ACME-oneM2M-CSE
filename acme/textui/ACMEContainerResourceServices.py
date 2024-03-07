#
#	ACMEContainerResourceServices.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Actoions* view for the ACME text UI.
"""

from __future__ import annotations
import time
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Rule, Static, Markdown, Checkbox, LoadingIndicator
from .ACMEFieldOriginator import ACMEFieldOriginator
from ..etc.Types import Operation, ResponseStatusCode
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.DateUtils import getResourceDate
from ..etc.Utils import uniqueRI
from ..resources.Resource import Resource
from ..services import CSE

idResourceServices = 'resource-services'


class ACMEContainerResourceServices(Container):

	DEFAULT_CSS = """
	ACMEContainerResourceServices {
		width: 100%;
	}

	#export-area {
		margin-left: 4;
		width: 100%;
	}

	#export-controls {
		height: 1;
	}

	#export-checkbox {
		height: 1;
		border: none;
		margin-right: 0;
		min-width: 17;
	}
	#export-button {
		height: 1;
		border: none;
		margin-right: 3;
		min-width: 10;
	}
	#export-loading-indicator {
		margin-top: 1;
		height: 1;
		color: $secondary;
	}

	#export-result {
		margin-top: 1;
		height: 1;
	}

		
	/* Toggle Button */

	ToggleButton > .toggle--button {
		color: $background;
		text-style: bold;
		background: $foreground 15%;
	}

	ToggleButton:focus > .toggle--button {
		background: $foreground 25%;
	}

	ToggleButton.-on > .toggle--button {
		background: $success 75%;
	}

	ToggleButton.-on:focus > .toggle--button {
		background: $success;
	}


	ToggleButton:light > .toggle--button {
			color: $background;
			text-style: bold;
			background: $foreground 15%;
	}

	ToggleButton:light:focus > .toggle--button {
		background: $foreground 25%;
	}

	ToggleButton:light.-on > .toggle--button {
		color: $foreground 10%;
		background: $success;
	}

	ToggleButton:light.-on:focus > .toggle--button {
		color: $foreground 10%;
		background: $success 75%;
	}
	"""
	# margin-left: 2;


	def __init__(self) -> None:
		"""	Initialize the view.
		"""
		super().__init__(id = idResourceServices)
		
		# Injected current resource
		self.resource:Resource = None

		# Export
		self.exportIncludingChildResources:bool = True
		self.exportView = Vertical(id = 'services-export')
		self.exportResult:Static = Static('', id = 'export-result')
		self.exportLoadingIndicator = LoadingIndicator(id = 'export-loading-indicator')
		self.exportCheckbox = Checkbox('Include child resources', self.exportIncludingChildResources, id = 'export-checkbox')



	def compose(self) -> ComposeResult:
		""" Compose the view.

			Returns:
				The ComposeResult
		"""
		with Container():
			yield Markdown('## Services')

			# Export
			with self.exportView:
				yield Markdown(
'''### Export Resource
Export the resource  to a file in the *./tmp* directory as a *curl* command.
''')
				with Container(id = 'export-area'):
					with Horizontal(id = 'export-controls'):
						yield Button('Export', variant = 'primary', id = 'export-button')
						yield self.exportCheckbox
					self.exportLoadingIndicator.display = False
					yield self.exportLoadingIndicator
					yield self.exportResult
					yield Rule()


	def updateResource(self, resource:Resource) -> None:
		"""	Update the current resource for the services view.

			Args:
				resource: The resource to use for services
		"""
		self.resource = resource
		self.exportResult.update('')


	def on_show(self) -> None:
		...


	#
	# Export
	#
		
	def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
		self.exportIncludingChildResources = event.value
		self.exportCheckbox.BUTTON_INNER = 'X' if self.exportIncludingChildResources else ' '
		self.exportCheckbox.refresh()

	@on(Button.Pressed, '#export-button')
	def exportresource(self) -> None:
		"""	Callback to export the current resource.
		"""

		def _exportResource() -> None:
			count, filename = CSE.console.doExportResource(self.resource.ri, self.exportIncludingChildResources)
			self.exportLoadingIndicator.display = False
			self.exportResult.display = True
			self.exportResult.update(f'Exported [{CSE.textUI.objectColor}]{count}[/] resource(s) to file [{CSE.textUI.objectColor}]{filename}[/]')
	
		self.exportLoadingIndicator.display = True
		self.exportResult.display = False
		# Execute in the background to not block the UI
		BackgroundWorkerPool.runJob(_exportResource)
	
