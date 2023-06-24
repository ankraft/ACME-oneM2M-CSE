#
#	runTest.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This script is a test runner for ACME's unit tests. 
#

from __future__ import annotations

import os, fnmatch, importlib, time, argparse
from types import ModuleType
from typing import Tuple
from inspect import getmembers, isfunction, isclass, getsourcelines
from unittest import SkipTest

from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.progress import track
import init
from acme.etc.Constants import Constants as C


# TODO testTransferRequests.py
# TODO list all test cases, but don't run them

loadTests 	= [ 'testLoad' ]
singleTests = []

def isRunTest(module:ModuleType) -> bool:
	name = module.__name__
	if args.runAll:						# run all tests
		return True
	if len(singleTests) > 0:			# run only specified tests
		return name in singleTests
	return (len([ n for n in loadTests if name.startswith(n) ]) > 0) == args.loadTestsOnly


def getTestFunctionsFromModule(module:ModuleType, sort:bool = False) -> list[Tuple[str, int]]:
	result:list[Tuple[str, int]] = []
	for _, cls in getmembers(module, isclass):						# Look for all classes of a module
		if cls.__module__ == module.__name__:						# If the class defined in the module itself
			result.extend([ (f[0], getsourcelines(f[1])[1])			# Add the names and line numbers of all functions that start with 'test_'
							for f in getmembers(cls, isfunction) 
							if f[0].startswith('test_')
						  ])
	
	return result if sort else sorted(result, key = lambda x:x[1])	# Sort by line number of occurence in the source file


if __name__ == '__main__':
	console       				= Console()
	totalErrors   				= 0
	totalRunTests 				= 0
	totalSuites   				= 0
	totalSkipped  				= 0
	modules:list[ModuleType]	= []
	results						= {}

	def checkPositive(value:str) -> int:
		ivalue = int(value)
		if ivalue <= 0:
			raise argparse.ArgumentTypeError(f'{value} is ivalid. It must be a positive int value')
		return ivalue

	# Parse command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('--all', action='store_true', dest='runAll', default=False, help='run all test suites (including load tests)')
	parser.add_argument('--load-only', action='store_true', dest='loadTestsOnly', default=False, help='run only load test suites')
	parser.add_argument('--verbose-requests', '-v', action='store_true', dest='verboseRequests', default=False, help='show verbose requests, responses and notifications output')
	parser.add_argument('--disable-teardown', '-notd', action='store_true', dest='disableTearDown', default=False, help='disable the tear-down / cleanup procedure at the end of a test suite')
	parser.add_argument('--run-teardown', '-runtd', action='store_true', dest='runTearDown', default=False, help='run the specified test cases\' tear-down functions and exit')
	parser.add_argument('--run-count', action='store', dest='numberOfRuns', type=checkPositive, default=1, help='run each test suite n times (default: 1)')
	parser.add_argument('--run-tests', '-run', action='store', dest='testCaseName', nargs='+', type=str, default=None, help='run only the specified test cases from the set of test suites')
	parser.add_argument('--show-skipped', action='store_true', dest='showSkipped', default=False, help='show skipped test cases in summary')
	parser.add_argument('--no-failfast', action='store_false', dest='failFast', default=True, help='continue running test cases after a failure')

	
	groupList = parser.add_mutually_exclusive_group()
	groupList.add_argument('--list-tests', '-ls', action='store_true', dest='listTests', default=False, help='list the test cases of the specified test suites in the order they are defined and exit')
	groupList.add_argument('--list-tests-sorted', '-lss', action='store_true', dest='listTestsSorted', default=False, help='alphabetical sorted list the test cases of the specified test suites and exit')

	parser.add_argument('TESTSUITE', nargs='*', help='specific test suites to run. Run all test suites if empty')
	args = parser.parse_args()

	# Clean optional single tests
	singleTests = [ testSuite if not testSuite.endswith('.py') else testSuite[:-3] for testSuite in args.TESTSUITE ]


	# Get all filenames with tests and load them as modules
	filenames = fnmatch.filter(os.listdir('.'), 'test*.py')
	filenames.sort()
	init.verboseRequests = args.verboseRequests 

	# Import all test* modules.
	for name in filenames:
		modules.append(importlib.import_module(name[:-3]))
	
	# List the test functions for all test suites. Then exit.
	if args.listTests:
		for m in modules:
			if isRunTest(m):
				console.print(f'[bright_blue]{m.__name__}')
				for f in getTestFunctionsFromModule(m):
					console.print(f'    {f[0]}')
		quit()
	
	# List the test functions for all test suites (sorted). Then exit.
	if args.listTestsSorted:
		for m in modules:
			if isRunTest(m):
				console.print(f'[bright_blue]{m.__name__}')
				for f in getTestFunctionsFromModule(m, True):
					console.print(f'    {f[0]}')
		quit()
		
	# If test cases are given then only run those modules that contain the test cases
	if args.testCaseName:
		_modules:list[ModuleType] = []
		for m in modules:
			if isRunTest(m):
				for f in getTestFunctionsFromModule(m):
					if f[0] in args.testCaseName:
						_modules.append(m)
						break
		modules = _modules
	


	# Run the tests and get some measurements
	totalTimeStart		  = time.perf_counter()
	totalProcessTimeStart = time.process_time()
	totalSleepTime		  = 0.0
	init.requestCount	  = 0
	init.testCaseNames	  = args.testCaseName
	init.enableTearDown   = not args.disableTearDown

	# Run the tearDown functions of the test cases and then exit
	if args.runTearDown:
		console.print('[bright_blue]Running tear-down functions for test suites: ')
		# for module in track(modules, 'Tearing down test cases', console=console, show_speed=False):
		for module in modules:
			if isRunTest(module):
				for nm, cls in getmembers(module, isclass):									# Look for all classes of a module
					if nm.lower().startswith(module.__name__.lower()):		# find the class with the module name
						console.print(f'    - {nm}')
						try:
							if (f := getattr(cls, 'tearDownClass')):
								f()
						except SkipTest:
							pass
		quit()
			

	
	for module in modules:
		if hasattr(module, 'run'):
			totalSuites += 1
			name = module.__name__
			if isRunTest(module): 	# exclude / include some tests
				for n in range(args.numberOfRuns):
					if args.numberOfRuns > 1:
						name = f'{module.__name__}_{n}'
					console.print(f'[bright_blue]Running tests from [bold]{name}{" (skipping tear-down)" if args.disableTearDown else ""}')
					startProcessTime = time.process_time()
					startPerfTime = time.perf_counter()
					startRequestCount = init.requestCount

					# Clear counters
					init.clearSleepTimeCount()

					testExecuted, errors, skipped, sleepTimeCount = module.run(testFailFast = args.failFast)	# type: ignore
					init.stopNotificationServer()	# In case something prevented the module to stop the notification server

					durationProcess = time.process_time() - startProcessTime
					duration = time.perf_counter() - startPerfTime
					if testExecuted > 0:	# don't count none-run tests
						totalErrors += errors
						totalRunTests += testExecuted
					totalSkipped += skipped
					totalSleepTime += sleepTimeCount
					results[name] = ( testExecuted, errors, duration, durationProcess, skipped, init.requestCount - startRequestCount, sleepTimeCount )
					console.print(f'[spring_green3]Successfully executed tests: {testExecuted}')
					if errors > 0:
						console.print(f'[red]Errors: {errors}')
				else:
					if args.showSkipped:
						results[name] = ( 0, 0, 0, 0, 1, init.requestCount - startRequestCount, 0.0 )

	totalProcessTime	= time.process_time() - totalProcessTimeStart
	totalExecTime 		= time.perf_counter() - totalTimeStart

	# No test run?
	if totalRunTests == 0 or init.requestCount == 0:
		console.print('[yellow]0 tests run')
		quit()
		
	# Print Summary
	console.print()
	table = Table(show_header=True, header_style='bright_blue', show_footer=True, footer_style='', title=f'{C.textLogo} - Test Results')
	table.add_column('Test Suite', footer='Totals', no_wrap=True)
	table.add_column('Count', footer=f'[spring_green3]{totalRunTests if totalErrors == 0 else str(totalRunTests)}[/spring_green3]', justify='right')
	table.add_column('Skipped', footer=f'[yellow]{totalSkipped}[/yellow]' if totalSkipped > 0 else '[spring_green3]0[spring_green3]', justify='right')
	table.add_column('Errors', footer=f'[red]{totalErrors}[/red]' if totalErrors > 0 else '[spring_green3]0[spring_green3]', justify='right')
	table.add_column('Times\nExec | Sleep | Proc', footer=f'{totalExecTime:8.4f} | {totalSleepTime:6.2f} | {totalProcessTime:8.4f}', justify='center')
	# table.add_column('Exec Time', footer=f'{totalExecTime:.4f}', justify='right')
	# table.add_column('Sleep Time', footer=f'{totalSleepTime:.2f}' if totalRunTests != 0 else '0.0', justify='right')
	# table.add_column('Proc Time', footer=f'{totalProcessTime:.4f}', justify='right')
	table.add_column('Exec Time per\nTest | Request', footer=f'{totalExecTime/totalRunTests:7.4f} | {totalExecTime/init.requestCount:7.4f}' if totalRunTests != 0 else '000.0000 | 000.0000', justify='center')
	table.add_column('Proc Time per\nTest | Request', footer=f'{totalProcessTime/totalRunTests:7.4f} | {totalProcessTime/init.requestCount:7.4f}' if totalRunTests != 0 else '000.0000 | 000.0000', justify='center')
	table.add_column('Requests', footer=f'{init.requestCount}', justify='right')
	# Styles
	styleDisabled = Style(dim=True)
	styleDisabled2 = Style(dim=True, bgcolor='grey11')
	styleEnabled = Style()
	styleEnabled2 = Style(bgcolor='grey11')
	cnt = 0
	for k,v in results.items():
		cnt += 1
		if cnt%2 == 0:
			style = styleEnabled2 if v[0] > 0 else styleDisabled2
		else:
			style = styleEnabled if v[0] > 0 else styleDisabled
		table.add_row(	k, 
						str(v[0]), 
						f'[yellow]{v[4]}[/yellow]' if v[4] > 0 and v[0] > 0 else str(v[4]),
						f'[red]{v[1]}[/red]' if v[1] > 0 and v[0] > 0 else str(v[1]),
						f'{v[2]:8.4f} | {v[6]:6.2f} | {v[3]:8.4f}' if v[0] > 0 else f'{0:8.4f} | {0:6.2f} | {0:8.4f}', 
						# f'{v[6]:.2f}',
						# f'{v[3]:.4f}' if v[0] > 0 else '',
						f'{(v[2]/v[0]):7.4f} | {(v[2]/v[5]):7.4f}' if v[0] > 0 else f'{0:7.4f} | {0:7.4f}',
						f'{(v[3]/v[0]):7.4f} | {(v[3]/v[5]):7.4f}' if v[0] > 0 else f'{0:7.4f} | {0:7.4f}',
						f'{v[5]}',
						style=style)
	console.print(table)

