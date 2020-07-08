
import pkgutil, os, fnmatch, importlib, time
from rich.console import Console
from rich.table import Column, Table


# testRemoteCSE.py
# testTransferRequests.py
# testRCN.py
# testDiscovery.py
# testMgmt objs

if __name__ == '__main__':
	console       = Console()
	totalErrors   = 0
	totalRunTests = 0
	totalSuites   = 0
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
			console.print('[blue]Running tests from [bold]%s' % name)
			startProcessTime = time.process_time()
			startPerfTime = time.perf_counter()
			testExecuted, errors = module.run()
			durationProcess = time.process_time() - startProcessTime
			duration = time.perf_counter() - startPerfTime
			totalErrors += errors
			totalRunTests += testExecuted
			results[name] = ( testExecuted, errors, duration, durationProcess )
			console.print('[spring_green3]Successfully executed tests: %d' % testExecuted)
			if errors > 0:
				console.print('[red]Errors: %d' % errors)
	totalProcessDuration = time.process_time() - totalProcessTimeStart
	totalDuration 		 = time.perf_counter() - totalTimeStart

	# Print Summary
	console.print()
	table = Table(show_header=True, header_style="blue", show_footer=True, footer_style='', title='Test Results')
	table.add_column('Test Suites', footer='Totals')
	table.add_column('Executed Tests', footer='[spring_green3]%d[/spring_green3]' % totalRunTests if totalErrors == 0 else str(totalRunTests))
	table.add_column('Errors', footer='[red]%d[/red]' % totalErrors if totalErrors > 0 else '[spring_green3]0')
	table.add_column('Duration', footer='%.4f' % totalDuration)
	table.add_column('Process Time', footer='%.4f' % totalProcessDuration)
	for k,v in results.items():
		table.add_row(	k, 
						str(v[0]), 
						'[red]%d[/red]' % v[1] if v[1] > 0 else str(v[1]),
						'%.4f' % v[2], 
						'%.4f' % v[3])
	console.print(table)

