;;
;;	utReset.as
;;
;;	This script initiates a CSE reset
;;
@name Reset
@description Reset and restart the CSE.\n# Be careful! This will reset the CSE and remove all its resources!
@usage reset
@tuiTool
@tuiExecuteButton Reset CSE
@uppertester
@onKey Z
@category CSE Operation


(clear-console)
(print "[dodger_blue2]Resetting the CSE[/]")

(if (runs-in-tui)
  (if (tui-confirm (. "[red]Do you really want to reset the CSE?" nl "[red]THIS WILL REMOVE ALL RESOURCES FROM THE CSE![/]") "[red]CSE Reset" "Reset" )
  	()
	((print "User cancelled CSE reset")
	 (quit))))

(print "CSE Reset Initiated")
(if (runs-in-tui)
  (tui-notify "Resetting CSE" "CSE Reset" "warning"))

(reset-cse)

(print "CSE Reset Complete")
(if (runs-in-tui)
  (tui-notify "CSE Reset Complete" "CSE Reset" "warning"))


