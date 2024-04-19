#
#	ACMEContainerResourceServices.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the *Actoions* view for the ACME text UI.
"""

from __future__ import annotations
from typing import cast

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.widgets import Button, Rule, Static, Markdown, Checkbox, LoadingIndicator
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.Types import ResourceTypes
from ..resources.Resource import Resource
from ..runtime import CSE

class ACMEContainerResourceServices(Container):

	DEFAULT_CSS = """
	ACMEContainerResourceServices {
		width: 100%;
	}

	/* Export Resource */

	#services-export-resource, #services-export-instances {
		height: 10;
		width: 100%;
	}

	#services-export-resource-area, #services-export-instances-area {
		margin-left: 4;
		margin-right: 4;
		width: 100%;
	}

	#services-export-resource-controls {
		height: 1;
	}

	#services-export-resource-checkbox {
		height: 1;
		border: none;
		margin-right: 0;
		min-width: 17;
	}

	#services-export-resource-button, #services-export-instances-button {
		height: 1;
		border: none;
		margin-right: 3;
		min-width: 14;
	}

	#services-export-resource-loading-indicator, #services-export-instances-loading-indicator {
		margin-top: 1;
		height: 1;
		color: $secondary;
	}

	#services-export-resource-result, #services-export-instances-result {
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

	def __init__(self, id:str) -> None:
		"""	Initialize the view.
		"""
		super().__init__(id = id)
		
		self.resource:Resource = None
		"""	The current resource. """

		self.exportIncludingChildResources:bool = True
		"""	Flag to indicate if child resources should be included in the export. """


	def compose(self) -> ComposeResult:
		""" Compose the view.

			Returns:
				The ComposeResult
		"""
		with VerticalScroll():
			yield Markdown('## Services')

			# Export resource
			with Vertical(id = 'services-export-resource'):
				yield Markdown(
'''### Export Resource
Export the resource to a file in the *./tmp* directory as a *curl* command.
''')
				with Container(id = 'services-export-resource-area'):
					with Horizontal(id = 'services-export-resource-controls'):
						yield Button('Export', variant = 'primary', id = 'services-export-resource-button')
						yield Checkbox('Include child resources', self.exportIncludingChildResources, id = 'services-export-resource-checkbox')
					yield LoadingIndicator(id = 'services-export-resource-loading-indicator')
					yield Static('', id = 'services-export-resource-result')
					yield Rule()
			
			# Export Instances
			with Vertical(id = 'services-export-instances'):
				yield Markdown(
'''### Export Instances
Export the instances of the container resource to a CSV file in the *./tmp* directory.
''')
				with Container(id = 'services-export-instances-area'):
					yield Button('Export CSV', variant = 'primary', id = 'services-export-instances-button')
					yield LoadingIndicator(id = 'services-export-instances-loading-indicator')
					yield Static('', id = 'services-export-instances-result')
					yield Rule()


	@property
	def exportResourceResult(self) -> Static:
		return cast(Static, self.query_one('#services-export-resource-result'))
	

	@property
	def exportInstancesResult(self) -> Static:
		return cast(Static, self.query_one('#services-export-instances-result'))
	

	@property
	def exportResourceLoadingIndicator(self) -> LoadingIndicator:
		return cast(LoadingIndicator, self.query_one('#services-export-resource-loading-indicator'))
	

	@property
	def exportInstancesLoadingIndicator(self) -> LoadingIndicator:
		return cast(LoadingIndicator, self.query_one('#services-export-instances-loading-indicator'))
	

	@property
	def exportInstancesView(self) -> Vertical:
		return cast(Vertical, self.query_one('#services-export-instances'))


	@property
	def exportChildResourcesCheckbox(self) -> Checkbox:
		return cast(Checkbox, self.query_one('#services-export-resource-checkbox'))
	

	def updateResource(self, resource:Resource) -> None:
		"""	Update the current resource for the services view.

			Args:
				resource: The resource to use for services
		"""
		self.resource = resource

		# Clear the result fields
		self.exportResourceResult.update('')
		self.exportInstancesResult.update('')
	
		# Show export instances view if the current resource is a container resource
		self.exportInstancesView.display = ResourceTypes.isContainerResource(resource.ty)


	def on_show(self) -> None:
		# Hide the loading indicators
		self.exportResourceLoadingIndicator.display = False
		self.exportInstancesLoadingIndicator.display = False


	#
	# Export resource
	#
		
	def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
		self.exportIncludingChildResources = event.value
		self.exportChildResourcesCheckbox.BUTTON_INNER = 'X' if self.exportIncludingChildResources else ' '
		self.exportChildResourcesCheckbox.refresh()


	@on(Button.Pressed, '#services-export-resource-button')
	def exportResource(self) -> None:
		"""	Callback to export the current resource.
		"""

		def _exportResource() -> None:
			count, filename = CSE.console.doExportResource(self.resource.ri, self.exportIncludingChildResources)
			self.exportResourceLoadingIndicator.display = False
			self.exportResourceResult.display = True
			self.exportResourceResult.update(f'Exported [{CSE.textUI.objectColor}]{count}[/] resource(s) to file [{CSE.textUI.objectColor}]{filename}[/]')
	

		# Show the loading indicator instead of the result
		self.exportResourceLoadingIndicator.display = True
		self.exportResourceResult.display = False

		# Execute in the background to not block the UI
		BackgroundWorkerPool.runJob(_exportResource)
	

	#
	# Export instances
	#
		
	@on(Button.Pressed, '#services-export-instances-button')
	def exportInstances(self) -> None:
		"""	Callback to export the current resource's instances
		"""

		def _exportInstances() -> None:
			count, filename = CSE.console.doExportInstances(self.resource.ri)
			self.exportInstancesLoadingIndicator.display = False
			self.exportInstancesResult.display = True
			self.exportInstancesResult.update(f"Exported [{CSE.textUI.objectColor}]{count}[/] data point(s) to file [@click=open_file('{filename}')]{filename}[/]")
	

		# Show the loading indicator instead of the result
		self.exportInstancesLoadingIndicator.display = True
		self.exportInstancesResult.display = False

		# Execute in the background to not block the UI
		BackgroundWorkerPool.runJob(_exportInstances)
	
