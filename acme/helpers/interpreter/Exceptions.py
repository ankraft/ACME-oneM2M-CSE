#
#	Exceptions.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .PContext import PContext

class PException(Exception):
	"""	Baseclass for interpreter exceptions. 
	"""

	def __init__(self, pcontext:PContext) -> None:
		"""	Exception initialization.
		
			Args:
				pcontext: `PContext` object with the interpreter state and error messages.
		"""
		self.pcontext = pcontext
		"""	`PContext` object with the interpreter state and error messages."""
	

	def __str__(self) -> str:
		"""	Nicely printable version of the exception.

			Return:
				String.
		"""
		if self.pcontext:
			return str(self.pcontext.error)
		return super().__str__()


class PAssertionFailed(PException):
	"""	Exception to indicate a failed assertion. """
	...


class PDivisionByZeroError(PException):
	"""	Exception to indicate a division-by-zero error. """
	...


class PInterruptedError(PException):
	"""	Exception when the script execution was interrupted. """
	...


class PInvalidArgumentError(PException):
	"""	Exception when there was an invalid argument to a symbol etc. """
	...


class PInvalidTypeError(PException):
	"""	Exception when an invalid type was encountered. """
	...


class PNotANumberError(PException):
	"""	Exception when a number is expected. """
	...


class PPermissionError(PException):
	"""	Exception when execution of a function is not allowed. """
	...


class PQuitWithError(PException):
	"""	Exception to regularly quit the script execution with an error status. """
	...


class PQuitRegular(PException):
	"""	Exception to regularly quit the script execution without an error. """
	...


class PReturnFrom(PException):
	"""	Exception to indicate an executed *return-from* commands. """

	def __init__(self, pcontext:PContext, name:str) -> None:
		"""	Exception initialization.
		
			Args:
				pcontext: `PContext` object with the interpreter state and error messages.
				name: Name of the block to return to.
		"""
		super().__init__(pcontext)
		self.name = name
		"""	Name of the block to return to. """


class PRuntimeError(PException):
	"""	Exception to indicate an interpreter runtime error. """
	...


class PTimeoutError(PException):
	"""	Exception to indicate a timeout of the running script. """
	...


class PUndefinedError(PException):
	"""	Exception to indicate an undefined symbol, variable, etc. """
	...


class PUnsupportedError(PException):
	"""	Exception to indicate an unsupported type or feature. """
	...

