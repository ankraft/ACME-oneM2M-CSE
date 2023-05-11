;;
;;	utReset.as
;;
;;	This script initiates a CSE reset
;;
@name Reset
@description Reset and restart the CSE.\n# Be careful! This will reset the CSE and remove all resources!
@usage reset
@tool
@uppertester
@onKey Z

(print "Resetting CSE")
(reset-cse)
(print "CSE reset complete")