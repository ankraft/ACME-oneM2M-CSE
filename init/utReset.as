;;
;;	utReset.as
;;
;;	This script initiates a CSE reset
;;
@name Reset
@description Reset and restart the CSE.\n# Be careful! This will reset the CSE and remove all resources!
@usage reset
@tuiTool
@tuiExecuteButton Reset CSE
@uppertester
@onKey Z
@category CSE Operation


(print "Resetting CSE")
(reset-cse)
(print "CSE reset complete")