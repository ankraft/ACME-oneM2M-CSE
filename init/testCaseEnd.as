#
#	testCaseEnd.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name testCaseEnd
@description Indicate the end of a test case to the CSE
@usage testCaseEnd <test case name>
@uppertester

if [< [argc] 1]
	logError Wrong number of arguments: testCaseEnd <test case name>
	quitWithError
endif

##################################################################

# Print start line to the debug log
logDivider End of [argv]

