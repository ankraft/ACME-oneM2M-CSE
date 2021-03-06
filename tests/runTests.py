
import pkgutil, os, fnmatch, importlib, time, argparse
from rich.console import Console
from rich.table import Column, Table
from rich.style import Style


# testRemoteCSE.py
# testTransferRequests.py
# testMgmt objs

loadTests = [ 'testLoad' ]

def isRunTest(name:str) -> bool:
	if args.runAll:						# run all tests
		return True
	if len(args.tests) > 0:				# run only specified tests
		return name in args.tests
	if args.includeLoadTests:			# include all load tests
		return True
	if args.loadTestsOnly: 
		return name in loadTests		# only load tests
	else:
		return name not in loadTests	# only not load tests
	

if __name__ == '__main__':
	console       = Console()
	totalErrors   = 0
	totalRunTests = 0
	totalSuites   = 0
	totalSkipped  = 0
	modules       = []
	results       = {}

	# Parse some command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('--load-include', action='store_true', dest='includeLoadTests', default=False, help='include load tests in test runs')
	parser.add_argument('--load-only', action='store_true', dest='loadTestsOnly', default=False, help='run only load tests in test runs')
	parser.add_argument('--all', action='store_true', dest='runAll', default=False, help='run all tests')
	parser.add_argument('--show-skipped', action='store_true', dest='showSkipped', default=False, help='show skipped tests in summary')
	parser.add_argument('--verbosity', action='store', dest='verbosity', type=int, choices=[0,1,2], default=2, help='set verbosity (default: 2)')

	groupFail = parser.add_mutually_exclusive_group()
	groupFail.add_argument('--failfast', action='store_true', dest='failFast', default=True, help='Stop tests after failure (default)')
	groupFail.add_argument('--no-failfast', action='store_false', dest='failFast', default=True, help='Continue tests after failure')

	parser.add_argument('tests', nargs='*', help='specify tests to run only')
	args = parser.parse_args()


	# Get all filenames with tests and load them as modules
	filenames = fnmatch.filter(os.listdir('.'), 'test*.py')
	filenames.sort()
	for name in filenames:
		modules.append(importlib.import_module(name[:-3]))

	# Run the tests and get some measurements
	totalTimeStart		  = time.perf_counter()
	totalProcessTimeStart = time.process_time()

	for module in modules:
		if hasattr(module, 'run'):
			totalSuites += 1
			name = module.__name__
			if isRunTest(name): 	# exclude / include some tests
				console.print(f'[blue]Running tests from [bold]{name}')
				startProcessTime = time.process_time()
				startPerfTime = time.perf_counter()
				testExecuted, errors, skipped = module.run(testVerbosity=args.verbosity, testFailFast=args.failFast)	# type: ignore
				durationProcess = time.process_time() - startProcessTime
				duration = time.perf_counter() - startPerfTime
				if testExecuted > 0:	# don't count none-run tests
					totalErrors += errors
					totalRunTests += testExecuted
				totalSkipped += skipped
				results[name] = ( testExecuted, errors, duration, durationProcess, skipped )
				console.print(f'[spring_green3]Successfully executed tests: {testExecuted}')
				if errors > 0:
					console.print(f'[red]Errors: {errors}')
			else:
				if args.showSkipped:
					results[name] = ( 0, 0, 0, 0, 1 )

	totalProcessTime	= time.process_time() - totalProcessTimeStart
	totalExecTime 		= time.perf_counter() - totalTimeStart

	# Print Summary
	console.print()
	table = Table(show_header=True, header_style='blue', show_footer=True, footer_style='', title='[dim][[/dim][red][i]ACME[/i][/red][dim]][/dim] - Test Results')
	table.add_column('Test Suites', footer='Totals', no_wrap=True)
	table.add_column('Test Count', footer=f'[spring_green3]{totalRunTests if totalErrors == 0 else str(totalRunTests)}[/spring_green3]')
	table.add_column('Skipped', footer=f'[yellow]{totalSkipped if totalSkipped > 0 else "[spring_green3]0"}[/yellow]')
	table.add_column('Errors', footer=f'[red]{totalErrors if totalErrors > 0 else "[spring_green3]0"}[/red]')
	table.add_column('Exec Time', footer=f'{totalExecTime:.4f}')
	table.add_column('Process Time', footer=f'{totalProcessTime:.4f}')
	table.add_column('Time / Test', footer=f'{totalExecTime/totalRunTests:.4f}' if totalRunTests != 0 else '')
	styleDisabled = Style(dim=True)
	for k,v in results.items():
		table.add_row(	k, 
						str(v[0]), 
						f'[yellow]{v[4]}[/yellow]' if v[4] > 0 and v[0] > 0 else str(v[4]),
						f'[red]{v[1]}[/red]' if v[1] > 0 and v[0] > 0 else str(v[1]),
						f'{v[2]:4f}' if v[0] > 0 else '', 
						f'{v[3]:.4f}' if v[0] > 0 else '',
						f'{(v[2]/v[0]):.4f}' if v[0] > 0 else '',
						style=None if v[0] > 0 else styleDisabled)
	console.print(table)

