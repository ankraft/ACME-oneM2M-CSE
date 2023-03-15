;;
;;	testCaseStart.as
;;
;;	This script is supposed to be called by the test system via the upper tester interface
;;

@name testCaseStart
@description Indicate a new test case to the CSE
@usage testCaseStart <test case name>
@uppertester

(if (< argc 2)
	(	(logError "Wrong number of arguments: testCaseStart <test case name>")
		(quit-with-error)))

;; Print start line to the debug log
(log-divider "Start of ${(argv 1)}$")

