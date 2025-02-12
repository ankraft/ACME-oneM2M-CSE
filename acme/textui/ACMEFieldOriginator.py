 #
#	ACMEFieldOriginator.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module defines an input field for the ACME text UI.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import cast

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Middle
from textual.widgets import Input, Label
from textual.suggester import SuggestFromList
from textual.validation import Function
from textual import on
from textual.message import Message


class ACMEInputField(Container):
	"""A generic input field for the ACME text UI.
	"""
	

	@dataclass
	class Submitted(Message):
		"""The message that is sent when the input field is submitted.
		"""

		input: ACMEInputField
		"""The *Input* widget that is being submitted."""
		value: str
		"""The value of the *Input* being submitted."""



	def __init__(self, label:str = 'a label',
		  			   value:str = '',
					   suggestions:list[str] = [],
					   placeholder:str = '',
					   validators:Function = None,
					   id:str = None) -> None:
		"""Initialize the input field.

			Args:
				label: The label of the input field.
				value: The value of the input field.
				suggestions: A list of suggestions for the input field.
				placeholder: The placeholder for the input field.
				validators: The validators for the input field.
				id: The ID of the input field.
		"""
		# TODO list of originators as a suggestion
		super().__init__(id = id)

		self._suggestions = suggestions
		"""The suggestions for the input field."""

		self._labelText = label
		"""The label text of the input field."""

		self._value = value
		"""The value of the input field."""

		self._placeholder = placeholder
		"""The placeholder text of the input field."""

		self._validators = validators
		"""The validators of the input field."""
		
		self._fieldLabel = Label(f'[b]{self._labelText}[/b] ', id = 'field-label')
		"""The label view of the input field."""

		self._fieldInput = Input(value = self._value, 
						placeholder = self._placeholder,
						suggester = SuggestFromList(self._suggestions),
						validators = self._validators,
						id = 'field-input')
		"""The input view of the input field."""

		self._fieldMessage = Label('', id = 'field-message')
		"""The message view of the input field."""



	def compose(self) -> ComposeResult:
		"""Compose the input field.

			Yields:
				The input field view.
		"""
		yield self._fieldLabel
		with Vertical(id = 'field-input-view'):
			yield self._fieldInput
			yield self._fieldMessage


	@on(Input.Changed)
	def show_validation_feedback(self, event:Input.Changed) -> None:
		"""Show the validation feedback.
		
			Args:
				event: The *Input.Changed* event that triggered the validation feedback.
		"""
		# Updating the UI to show the reasons why validation failed
		if event.validation_result and not event.validation_result.is_valid:  
			self.msgField.update(event.validation_result.failure_descriptions[0])
		else:
			self.msgField.update('')
 

	@on(Input.Submitted, '#field-input')
	async def submit(self, event:Input.Submitted) -> None:
		"""Submit the input field.
		
			Args:
				event: The *Input.Submitted* event that triggered the submission.
		"""
		self.post_message(self.Submitted(self, self.inputField.value))


	def setLabel(self, label:str) -> None:
		""" Set the label of the field.
		
			Args:
				label: The label to set.
		"""
		cast(Label, self._fieldLabel).update(f'[b]{label}[/b] ')
	

	@property
	def value(self) -> str:
		"""Return the value of the input field.
		
			Returns:
				The value of the input field.
		"""
		return self._fieldInput.value


	@value.setter
	def value(self, value:str) -> None:
		"""Set the value of the input field.

			Args:
				value: The value to set.
		"""
		self._value = value
		try:
			self._fieldInput.value = value
		except:
			pass
	
	
	@property
	def msgField(self) -> Label:
		"""Return the message field.
		
			Returns:
				The message field.
		"""
		return self._fieldMessage
	
	
	@property
	def inputField(self) -> Input:
		"""Return the input field.
		
			Returns:
				The input field.
		"""
		return self._fieldInput
	
	
	def setSuggestions(self, suggestions:list[str]) -> None:
		""" Set the suggestions for the input field.
		
			Args:
				suggestions: The suggestions to set.
		"""
		self._suggestions = suggestions
		self.inputField.suggester = SuggestFromList(self._suggestions)

# TODO This may has to be turned into a more generic field class

idFieldOriginator = 'field-originator'
"""The ID of the originator field."""

def validateOriginator(value: str) -> bool:
	"""Validate a originator.
	
		Args:
			value: The value to validate.
		
		Returns:
			True if the value is valid, False otherwise.
	"""
	return value is not None and len(value) > 1 and value.startswith(('C', 'S', '/')) and not set(value) & set(' \t\n')

#TODO add id to the field

class ACMEFieldOriginator(ACMEInputField):
	"""An input field for an *originator* in the ACME text UI.
	"""
	def __init__(self, originator:str, suggestions:list[str] = []) -> None:
		"""Initialize the originator field.
		
			Args:
				originator: The value of the field.
				suggestions: The suggestions for the field.
		"""
		super().__init__(label = 'Originator',
		   				 suggestions = suggestions,
						 placeholder = 'Originator',
						 validators = Function(validateOriginator, 
				 							   'Wrong originator format: Must start with "C", "S" or "/", contain now white spaces, and have length > 1.')
						)
		self.originator = originator
		"""The originator value of the field."""

		self.suggestions = suggestions
		"""The suggestions for the field."""

	def update(self, originator:str, suggestions:list[str] = []) -> None:
		"""Update the originator field.
		
			Args:
				originator: The value of the field.
				suggestions: The suggestions for the field.
		"""
		self.originator = originator
		self.suggestions = suggestions
		self.value = originator
		self.setSuggestions(suggestions)
