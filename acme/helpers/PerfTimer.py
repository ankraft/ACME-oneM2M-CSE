#
#	PerfTimer.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

""" This module provides a context manager to measure the elapsed time of a block of code.
	It can also be used as a decorator.

	Example:

		::
		
			with perfTimer("some code"):
				# do something

			@perfTimer("some code")
			def someFunction():
				# do something
"""


from typing import Callable
import contextlib
from time import perf_counter
from typing import Generator

@contextlib.contextmanager
def perfTimer(subject:str = "time", outCB:Callable = print ) -> Generator [None, None, None]:
	""" Meassure and print the elapsed time.

		Args:
			subject: The subject of the time measurement.
			outCB: The output callback function. Default is print.
	"""
	startTS = perf_counter()
	yield
	elapsedTS = perf_counter() - startTS
	elapsedMs = elapsedTS * 1000
	outCB(f"{subject}: elapsed {elapsedMs:.4f}ms")