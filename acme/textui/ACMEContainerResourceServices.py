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
from textual.widgets import Button, Rule, Static, Markdown, Checkbox, LoadingIndicator, Label
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.Types import ResourceTypes
from ..resources.Resource import Resource
from ..runtime import CSE

class ACMEContainerResourceServices(Container):
	"""	The *Services* view for the ACME text UI.
	"""

	def __init__(self, id:str) -> None:
		"""	Initialize the view.

			Args:
				id:	The view ID.
		"""

		super().__init__(id = id)
		
		self.resource:Resource = None
		"""	The current resource. """

		self.exportIncludingChildResources:bool = True
		"""	Flag to indicate if child resources should be included in the export. """

		# Some resources upfront
		self._servicesExportResource = Vertical(id = 'services-export-resource')
		"""	The export resource view. """

		self._servicesExportInstances = Vertical(id = 'services-export-instances')
		"""	The export instances view. """

		self._servicesExportResourceResult = Static('', id = 'services-export-resource-result', classes = 'result')
		"""	The result view of the resource export. """

		self._servicesExportInstancesResult = Static('', id = 'services-export-instances-result', classes = 'result')
		"""	The result view of the instances export. """

		self._servicesExportResourceLoadingIndicator = LoadingIndicator(id = 'services-export-resource-loading-indicator', classes = 'loading-indicator')
		"""	The loading indicator for the resource export. """

		self._servicesExportInstancesLoadingIndicator = LoadingIndicator(id = 'services-export-instances-loading-indicator', classes = 'loading-indicator')
		"""	The loading indicator for the instances export. """

		self._servicesExportResourceCheckbox = Checkbox('Include child resources', self.exportIncludingChildResources, id = 'services-export-resource-checkbox')
		"""	The checkbox to include child resources in the export. """


	def compose(self) -> ComposeResult:
		""" Compose the view.

			Returns:
				The ComposeResult
		"""
		with VerticalScroll():
			# Export resource
			with self._servicesExportResource:
				self._servicesExportResource.border_title = 'Export Resource'
				yield Label('Export the resource to a file in the [i]./tmp[/i] directory as a [i]curl[/i] command.', classes='label')
				with Container(classes='service-command-area'):
					with Horizontal(classes = 'services-export-controls'):
						yield Button('Export', variant = 'primary', id = 'services-export-resource-button', classes = 'button')
						yield self._servicesExportResourceCheckbox
					yield self._servicesExportResourceLoadingIndicator
					yield self._servicesExportResourceResult
			
			# Export Instances
			with self._servicesExportInstances:
				self._servicesExportInstances.border_title = 'Export Instances'
				yield Label('Export the instances of the container resource to a [i]CSV[/i] file in the [i]./tmp[/i] directory or to the clipboard.', classes='label')
				with Container(classes='service-command-area'):
					with Horizontal():
						yield Button('Export CSV', variant = 'primary', id = 'services-export-instances-button', classes = 'button')
						yield Button('Copy CSV', variant = 'primary', id = 'services-copy-instances-button', classes = 'button')
					yield self._servicesExportInstancesLoadingIndicator
					yield self._servicesExportInstancesResult


	@property
	def exportResourceResult(self) -> Static:
		"""	Return the result view of the resource export.
		
			Returns:
				The result view.
		"""
		return self._servicesExportResourceResult
	

	@property
	def exportInstancesResult(self) -> Static:
		"""	Return the result view of the instances export.
		
			Returns:
				The result view.
		"""
		return self._servicesExportInstancesResult
	

	@property
	def exportResourceLoadingIndicator(self) -> LoadingIndicator:
		"""	Return the loading indicator for the resource export.
		
			Returns:
				The loading indicator.
		"""
		return self._servicesExportResourceLoadingIndicator
	

	@property
	def exportInstancesLoadingIndicator(self) -> LoadingIndicator:
		"""	Return the loading indicator for the instances export.
		
			Returns:
				The loading indicator view.
		"""
		return self._servicesExportInstancesLoadingIndicator
	

	@property
	def exportInstancesView(self) -> Vertical:
		"""	Return the export instances view.
		
			Returns:
				The export instances view.
		"""
		return self._servicesExportInstances


	@property
	def exportChildResourcesCheckbox(self) -> Checkbox:
		"""	Return the checkbox to include child resources in the export.
		
			Returns:
				The checkbox.
		"""
		return self._servicesExportResourceCheckbox
	

	def updateResource(self, resource:Resource) -> None:
		"""	Update the current resource for the services view.

			Args:
				resource: The resource to use for services.
		"""
		self.resource = resource

		# Clear the result fields
		self.exportResourceResult.update('')
		self.exportInstancesResult.update('')
	
		# Show export instances view if the current resource is a container resource
		self.exportInstancesView.display = ResourceTypes.isContainerResource(resource.ty)


	def on_show(self) -> None:
		"""	Called when the view is shown.
		"""
		from ..textui.ACMETuiApp import ACMETuiApp
		self._app = cast(ACMETuiApp, self.app)
		"""	The application. """

		# Hide the loading indicators
		self.exportResourceLoadingIndicator.display = False
		self.exportInstancesLoadingIndicator.display = False


	#
	# Export resource
	#
		
	def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
		"""	Callback when the checkbox to include child resources in the export is changed.

			Args:
				event: The *Checkbox.Changed* event.
		"""
		self.exportIncludingChildResources = event.value
		self.exportChildResourcesCheckbox.BUTTON_INNER = 'X' if self.exportIncludingChildResources else ' '
		self.exportChildResourcesCheckbox.refresh()


	@on(Button.Pressed, '#services-export-resource-button')
	def exportResource(self) -> None:
		"""	Callback to export the current resource.
		"""

		def _exportResource() -> None:
			"""	Background runner callback to xport the resource.
			"""
			count, filename = CSE.console.doExportResource(self.resource.ri, self.exportIncludingChildResources)
			self.exportResourceLoadingIndicator.display = False
			self.exportResourceResult.display = True
			self.exportResourceResult.update(n := f'Exported [{self._app.objectColor}]{count}[/] resource(s) to file [{self._app.objectColor}]{filename}[/]')
			self._app.showNotification(n, 'Resource Export', 'information')


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
		"""	Callback to export the current resource's instances as CSV.
		"""

		def _exportInstances() -> None:
			"""	Background runner callback to export the instances.
			"""
			count, filename = CSE.console.doExportInstances(self.resource.ri)
			self.exportInstancesLoadingIndicator.display = False
			self.exportInstancesResult.display = True
			self.exportInstancesResult.update(n := f"Exported [{self._app.objectColor}]{count}[/] data point(s) to file [@click=open_file('{filename}')]{filename}[/]")
			self._app.showNotification(n, 'Data Points Export', 'information')

		# Show the loading indicator instead of the result
		self.exportInstancesLoadingIndicator.display = True
		self.exportInstancesResult.display = False

		# Execute in the background to not block the UI
		BackgroundWorkerPool.runJob(_exportInstances)
	

	@on(Button.Pressed, '#services-copy-instances-button')
	def copyInstances(self) -> None:
		"""	Callback to copy the current resource's instances to the clipboard as CSV.
		"""

		def _copyInstances() -> None:
			"""	Background runner callback to copy the instances to the clipboard.
			"""
			count, data = CSE.console.doExportInstances(self.resource.ri, asString = True)
			self.exportInstancesLoadingIndicator.display = False
			self.exportInstancesResult.display = True
			if self._app.copyToClipboard(data):
				self.exportInstancesResult.update(n := f'Copied [{self._app.objectColor}]{count}[/] data point(s) to the clipboard')
				self._app.showNotification(n, 'Data Points Copy', 'information')


		# Show the loading indicator instead of the result
		self.exportInstancesLoadingIndicator.display = True
		self.exportInstancesResult.display = False

		# Execute in the background to not block the UI
		BackgroundWorkerPool.runJob(_copyInstances)
		