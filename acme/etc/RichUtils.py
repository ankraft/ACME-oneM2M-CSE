#
#	RichUtils.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module contains function to work with rich objects.
"""

from typing import Optional
from rich.jupyter import JupyterMixin
from rich.console import Console
from rich.text import Text

def richToString(obj:JupyterMixin, width:Optional[int]=None) -> str:
	"""	Convert a rich object to a string.
	
		Args:
			obj: The rich object to convert.
			width: Optional width for the console output. If not provided, the default width is used.
		
		Return:
			A string representation of the rich object.
	"""
	console = Console(width=width)
	with console.capture() as capture:
		console.print(obj)
	return str(Text.from_ansi(capture.get()))
