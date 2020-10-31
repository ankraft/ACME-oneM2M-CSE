
import pkgutil, os, fnmatch, importlib, time
from rich.console import Console
from rich.table import Column, Table
from rich.style import Style


# testRemoteCSE.py
# testTransferRequests.py
# testMgmt objs

if __name__ == '__main__':
	console       = Console()
	totalErrors   = 0
	totalRunTests = 0
	totalSuites   = 0
	totalSkipped  = 0
	modules       = []
	results       = {}


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
			console.print(f'[blue]Running tests from [bold]{name}')
			startProcessTime = time.process_time()
			startPerfTime = time.perf_counter()
			testExecuted, errors, skipped = module.run()	# type: ignore
			durationProcess = time.process_time() - startProcessTime
			duration = time.perf_counter() - startPerfTime
			if testExecuted > 0:	# don't count none-run tests
				totalErrors += errors
				totalRunTests += testExecuted
			totalSkipped += skipped
			results[name] = ( testExecuted, errors, duration, durationProcess, skipped )
			console.print('[spring_green3]Successfully executed tests: %d' % testExecuted)
			if errors > 0:
				console.print('[red]Errors: %d' % errors)
	totalProcessTime	= time.process_time() - totalProcessTimeStart
	totalExecTime 		= time.perf_counter() - totalTimeStart

	# Print Summary
	console.print()
	table = Table(show_header=True, header_style='blue', show_footer=True, footer_style='', title='[dim]\[[/dim][red][i]ACME[/i][/red][dim]][/dim] - Test Results')
	table.add_column('Test Suites', footer='Totals', no_wrap=True)
	table.add_column('Test Count', footer='[spring_green3]%d[/spring_green3]' % totalRunTests if totalErrors == 0 else str(totalRunTests))
	table.add_column('Skipped', footer='[yellow]%d[/yellow]' % totalSkipped if totalSkipped > 0 else '[spring_green3]0')
	table.add_column('Errors', footer='[red]%d[/red]' % totalErrors if totalErrors > 0 else '[spring_green3]0')
	table.add_column('Exec Time', footer='%.4f' % totalExecTime)
	table.add_column('Process Time', footer='%.4f' % totalProcessTime)
	table.add_column('Time Ratio', footer='%.4f' % (totalProcessTime/totalExecTime))
	styleDisabled = Style(dim=True)
	for k,v in results.items():
		table.add_row(	k, 
						str(v[0]), 
						'[yellow]%d[/yellow]' % v[4] if v[4] > 0 and v[0] > 0 else str(v[4]),
						'[red]%d[/red]' % v[1] if v[1] > 0 and v[0] > 0 else str(v[1]),
						'%.4f' % v[2] if v[0] > 0 else '', 
						'%.4f' % v[3] if v[0] > 0 else '',
						'%.4f' % (v[3]/v[2]) if v[0] > 0 else '',
						style=None if v[0] > 0 else styleDisabled)
	console.print(table)

