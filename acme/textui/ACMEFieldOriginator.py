 #
#	ACMEFieldOriginator.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

from __future__ import annotations
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Input, Label
from textual.suggester import SuggestFromList
from textual.validation import Function
from textual import on


class ACMEField(Container):
	
	DEFAULT_CSS = """
	ACMEField {
		width: 1fr;
		height: 4;
		layout: horizontal;
		overflow: hidden hidden;
		# background: red;
		content-align: left middle;
		margin: 1 1 1 1;
	}

	#field-label {
		height: 1fr;
		content-align: left middle;
		align: left middle;
	}

	#field-input {
		height: 1fr;
		width: 1fr;
	}

	#field-pretty {
		height: 1fr;
		width: 1fr;
		margin-left: 1;
		color: red;
	}
	"""

	def __init__(self, label:str = 'a label',
					   suggestions:list[str] = [],
					   placeholder:str = '',
					   validators:Function = None,
					   id:str = None) -> None:
		# TODO list of originators as a suggestion
		super().__init__(id = id)
		self.suggestions = suggestions
		self.label = Label(f'[b]{label}[/b] ', id = f'field-label')
		self.input = Input(str(self.suggestions), 
						   placeholder = placeholder,
						   suggester = SuggestFromList(self.suggestions),
						   validators = validators,
						   id = 'field-input')
		self.msg = Label('jjj', id = 'field-pretty')

	def compose(self) -> ComposeResult:
		yield self.label
		with Vertical():
			yield self.input
			yield self.msg


	@on(Input.Changed)
	def show_invalid_reasons(self, event: Input.Changed) -> None:
		# Updating the UI to show the reasons why validation failed
		if not event.validation_result.is_valid:  
			self.msg.update(event.validation_result.failure_descriptions[0])
		else:
			self.msg.update('')
			self.originator = event.value






# TODO This may has to be turned into a more generic field class

idFieldOriginator = 'field-originator'

def validateOriginator(value: str) -> bool:
	return value is not None and len(value) > 1 and value.startswith(('C', 'S', '/')) and not set(value) & set(' \t\n')

class ACMEFieldOriginator(ACMEField):
	def __init__(self, originator:str, suggestions:list[str] = []) -> None:
		super().__init__(label = 'Originator',
		   				 suggestions = suggestions,
						 placeholder = 'Originator',
						 validators = Function(validateOriginator, 
			     							   'Wrong originator format: Must start with "C", "S" or "/", contain now white spaces, and have length > 1.')
						)
		self.originator = originator
		self.suggestions = suggestions

	def update(self, originator:str, suggestions:list[str] = []) -> None:
		self.originator = originator
		self.suggestions = suggestions
		self.input.value = originator
		self.input.suggester = SuggestFromList(self.suggestions)


# class ACMEFieldOriginator(Container):
	
# 	DEFAULT_CSS = """
# 	ACMEFieldOriginator {
# 		width: 1fr;
# 		height: 4;
# 		layout: horizontal;
# 		overflow: hidden hidden;
# 		# background: red;
# 		content-align: left middle;
# 		margin: 1 1 1 1;
# 	}

# 	#field-originator-label {
# 		height: 1fr;
# 		content-align: left middle;
# 		align: left middle;
# 	}

# 	#field-originator-input {
# 		height: 1fr;
# 		width: 1fr;
# 	}

# 	#field-originator-pretty {
# 		height: 1fr;
# 		width: 1fr;
# 		margin-left: 1;
# 		color: red;
# 	}
# 	"""

# 	def __init__(self, originator:str, suggestions:list[str] = []) -> None:
# 		# TODO list of originators as a suggestion
# 		super().__init__(id = idFieldOriginator)
# 		self.originator = originator
# 		self.suggestions = suggestions
# 		self.label = Label('[b]Originator[/b] ', id = 'field-originator-label')
# 		self.input = Input(str(self.suggestions), 
# 						   placeholder = 'Originator',
# 						   suggester = SuggestFromList(self.suggestions),
# 						   validators = Function(validateOriginator, 'Wrong originator format: Must start with "C", "S" or "/", and have length > 1.'),
# 						   id = 'field-originator-input')
# 		self.msg = Label('jjj', id = 'field-originator-pretty')

# 	def compose(self) -> ComposeResult:
# 		yield self.label
# 		with Vertical():
# 			yield self.input
# 			yield self.msg


# 	@on(Input.Changed)
# 	def show_invalid_reasons(self, event: Input.Changed) -> None:
# 		# Updating the UI to show the reasons why validation failed
# 		if not event.validation_result.is_valid:  
# 			self.msg.update(event.validation_result.failure_descriptions[0])
# 		else:
# 			self.msg.update('')
# 			self.originator = event.value


# 	def update(self, originator:str, suggestions:list[str] = []) -> None:
# 		self.originator = originator
# 		self.suggestions = suggestions
# 		self.input.value = originator
# 		self.input.suggester = SuggestFromList(self.suggestions)

