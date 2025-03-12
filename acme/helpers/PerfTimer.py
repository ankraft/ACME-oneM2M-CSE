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
		
			with perfTimer(myCallback):
				# do something

			@perfTimer(lambda ms: print(f'someFunction took: {ms} ms'))
			def someFunction():
				# do something
"""

from typing import Callable, Generator
from contextlib import contextmanager
from time import perf_counter

@contextmanager
def perfTimer(callback:Callable = print ) -> Generator [None, None, None]:
	""" Meassure and print the elapsed time.

		Args:
			callback: The output callback function. It will receive the elapsed ms (float) as the only argument. Default is print.
	"""
	startTS = perf_counter()
	yield
	callback((perf_counter() - startTS) * 1000)