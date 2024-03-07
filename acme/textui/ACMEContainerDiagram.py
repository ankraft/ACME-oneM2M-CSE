#
#	ACMEContainerDiagram.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines the Diagram view for for *Container* resources for the ACME text UI.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Callable, Optional

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Center, Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox
from textual.timer import Timer
from textual_plotext import PlotextPlot

from ..etc.DateUtils import fromISO8601Date
from ..services import CSE


class DiagramTypes(IntEnum):
	"""	Enumeration of the different diagram types.
	"""
	Line = 0
	Graph = 1
	Scatter = 2
	Bar = 3
	Timeline = 4


class ACMEContainerDiagram(Container):

	DEFAULT_CSS = '''
#diagram-view {
	height: 100%;
	padding: 0 1 1 1;
}

#diagram-plot {
	/*height: 100%;*/
}

#diagram-footer {
	width: 100%;
	margin-top: 1;
	height: 1;
}

#diagram-button-set {
	width: auto;
	margin-bottom: 0;
}

#diagram-line-button {
	height: 1;
	border: none;
	margin-right: 1;
	min-width: 10;
}

#diagram-graph-button {
	height: 1;
	border: none;
	margin-right: 1;
	min-width: 11;
}

#diagram-scatter-button {
	height: 1;
	border: none;
	margin-right: 1;
	min-width: 13;
}

#diagram-bar-button {
	height: 1;
	border: none;
	margin-right: 1;
	min-width: 9;
}

#diagram-timeline-button {
	height: 1;
	border: none;
	margin-right: 0;
	min-width: 14;
}

#diagram-refresh-button {
	height: 1;
	border: none;
	margin-left: 4;
	margin-right: 0;
	min-width: 13;
}

#diagram-autorefresh-checkbox {
	height: 1;
	border: none;
	margin-left: 2;
	margin-right: 0;
	min-width: 17;
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

'''


	from ..textui import ACMETuiApp

	def __init__(self, refreshCallback:Callable, tuiApp:ACMETuiApp.ACMETuiApp) -> None:
		super().__init__()
		self.tuiApp = tuiApp
		self.color = (0, 120, 212)
		self.type = DiagramTypes.Line
		self.plotContainer:Container = None
		self.plot:PlotextPlot = None
		self.values:list[float] = []
		self.dates:Optional[list[str]] = []
		self.refreshCallback = refreshCallback
		self.autoRefresh = False
		self.autoRefreshInterval = self.tuiApp.textUI.refreshInterval
		self.refreshTimer:Timer = None
		self.buttons = {
			DiagramTypes.Line: Button('Line', variant = 'success', id = 'diagram-line-button'),
			DiagramTypes.Graph: Button('Graph', variant = 'primary', id = 'diagram-graph-button'),
			DiagramTypes.Scatter: Button('Scatter', variant = 'primary', id = 'diagram-scatter-button'),
			DiagramTypes.Bar: Button('Bar', variant = 'primary', id = 'diagram-bar-button'),
			DiagramTypes.Timeline: Button('Timeline', variant = 'primary', id = 'diagram-timeline-button'),
		}
		self.refreshCheckbox = Checkbox('Auto Refresh', self.autoRefresh, id = 'diagram-autorefresh-checkbox')
		self.refreshCheckbox.BUTTON_INNER = ' '



	def compose(self) -> ComposeResult:
		self._newPlot()
		with Vertical(id = 'diagram-view'):
			yield self.plotContainer
			with Center(id = 'diagram-footer'):
				with Horizontal(id = 'diagram-button-set'):
					for button in self.buttons.values():
						yield button
					yield Button('Refresh', variant = 'primary', id = 'diagram-refresh-button')
					# _refreshCheckbox = Checkbox('Auto Refresh', self.autoRefresh, id = 'diagram-autorefresh-checkbox')
					# _refreshCheckbox.BUTTON_INNER = ' '
					yield self.refreshCheckbox


	def on_mount(self) -> None:
		self.refreshTimer = self.set_interval(self.autoRefreshInterval, 
											  self._refreshChart, 
											  pause = True)


	def on_show(self) -> None:
		self._activateButton(self.type)
		self.plotGraph()
		if self.autoRefresh:
			self._startRefreshTimer()
	
	
	def on_hide(self) -> None:
		self._stopRefreshTimer()


	@on(Button.Pressed, '#diagram-line-button')
	def lineButtonExecute(self) -> None:
		"""	Callback to switch to the line diagram.
		"""
		self._activateButton(DiagramTypes.Line)


	@on(Button.Pressed, '#diagram-graph-button')
	def graphButtonExecute(self) -> None:
		"""	Callback to switch to the graph diagram.
		"""
		self._activateButton(DiagramTypes.Graph)


	@on(Button.Pressed, '#diagram-scatter-button')
	def scatterButtonExecute(self) -> None:
		"""	Callback to switch to the scatter diagram.
		"""
		self._activateButton(DiagramTypes.Scatter)


	@on(Button.Pressed, '#diagram-bar-button')
	def barButtonExecute(self) -> None:
		"""	Callback to switch to the bar diagram.
		"""
		self._activateButton(DiagramTypes.Bar)


	@on(Button.Pressed, '#diagram-timeline-button')
	def timeLineButtonExecute(self) -> None:
		"""	Callback to switch to the timeline diagram.
		"""
		self._activateButton(DiagramTypes.Timeline)
	

	@on(Button.Pressed, '#diagram-refresh-button')
	def refreshButtonExecute(self) -> None:
		"""	Callback to refresh the diagram.
		"""
		self._refreshChart()
	

	def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
		"""	Callback to refresh the diagram.
		"""
		
		self.autoRefresh = event.value
		if self.autoRefresh:
			self._startRefreshTimer()
			self.refreshCheckbox.BUTTON_INNER = 'X'
		else:
			self.refreshCheckbox.BUTTON_INNER = ' '
			self._stopRefreshTimer()
		self.refreshCheckbox.refresh()


	def refreshPlot(self) -> None:
		"""	Refresh the diagram.
		"""
		self.plotGraph()

	
	def plotGraph(self) -> None:
		"""	Plot the graph.
		"""
		dates = [ fromISO8601Date(d).strftime('%d/%m/%Y %H:%M:%S') for d in self.dates ] if self.dates else None
		values = self.values

		# plt.clear_data()
		self._newPlot()

		plt = self.plot.plt
		match self.type:
			case DiagramTypes.Line:
				if dates is None:
					plt.plot(values, color = self.color)
				else:
					plt.plot(dates, values, color = self.color)
			case DiagramTypes.Graph:
				if dates is None:
					plt.plot(values, color = self.color, fillx=True)
				else:
					plt.plot(dates, values, color = self.color, fillx=True)
			case DiagramTypes.Scatter:
				if dates is None:
					plt.scatter(values, color = self.color)
				else:
					plt.scatter(dates, values, color = self.color)
			case DiagramTypes.Bar:
				if dates is None:
					plt.bar(values, color = self.color)
				else:
					plt.bar(dates, values, color = self.color)
			case DiagramTypes.Timeline:
				_d = [ fromISO8601Date(d).strftime('%d/%m/%Y %H:%M:%S') for d in self.dates ]
				if dates is None:
					plt.event_plot(_d, color = self.color)
				else:
					plt.event_plot(dates, _d, color = self.color)	# type: ignore[arg-type]
		self.plot.refresh(layout = True)

	
	def setData(self, values:list[float], dates:Optional[list[str]] = None) -> None:
		"""	Set the data to be displayed in the diagram.

			Args:
				values: The data to be displayed.
				dates: The dates for the data. If not given, the current time is used.
		"""
		self.values = values
		self.dates = dates


	#################################################################
	#
	#	Private
	#

	def _newPlot(self) -> None:
		"""	Create a new plot instance and update the container.
		"""

		# Remove a previous plot if there is one
		if not self.plotContainer:
			self.plotContainer = Container()
		else:
			self.plot.remove()
		
		# Create a new plot and configure its timestamp format
		self.plot = PlotextPlot()
		self.plot.plt.date_form('d/m/Y H:M:S', 'Y-m-d H:M:S')
		# TODO the output date format doesn't seem to work with the bar diagram

		# Add the plot to the container and refresh the container
		self.plotContainer._add_child(self.plot)
		self.plotContainer.refresh(layout=True)


	def _activateButton(self, type:DiagramTypes) -> None:
		"""	Activate a button.

			Args:
				type: The button to activate.
		"""
		if self.type != type:
			self.type = type
			for b in self.buttons.values():
				b.variant = 'primary'
			self.buttons[type].variant = 'success'
			self.plotGraph()


	def _refreshChart(self) -> None:
		"""	Refresh the chart.
		"""
		if self.refreshCallback:
			self.refreshCallback()
			self.plotGraph()


	def _startRefreshTimer(self) -> None:
		"""	Start the refresh timer.
		"""
		self.refreshTimer.resume()

	def _stopRefreshTimer(self) -> None:
		"""	Stop the refresh timer.
		"""
		self.refreshTimer.pause()
