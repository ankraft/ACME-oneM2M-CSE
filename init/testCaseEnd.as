;;
;;	testCaseEnd.as
;;
;;	This script is supposed to be called by the test system via the upper tester interface
;;

@name testCaseEnd
@description Indicate the end of a test case to the CSE
@usage testCaseEnd <test case name>
@uppertester

(if (< argc 1)
	(	(log-error "Wrong number of arguments: testCaseEnd <test case name>")
		(quit-with-error)))

;; Print start line to the debug log
(log-divider "End of [(argv 1)]")
