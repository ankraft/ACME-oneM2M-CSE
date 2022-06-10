#
#	testCaseStart.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name testCaseStart
@description Indicate a new test case to the CSE
@usage testCaseStart <test case name>
@uppertester

if [< [argc] 1]
	logError Wrong number of arguments: testCaseStart <test case name>
	quitWithError
endif

##################################################################

# Print start line to the debug log
logDivider Start of [argv]

