;;
;;	restartCSE.as
;;
;;	This script initiates a CSE restart
;;
@name Restart
@description Initiate a "restart" shutdown of the CSE.\n# Be careful! This will shutdown the CSE and its services!
@tuiTool
@onKey %
@tuiExecuteButton Restart CSE
@category CSE Operation

(clear-console)
(print "[dodger_blue2]Restart shutdown the CSE[/]")

(if (runs-in-tui)
  (if (tui-confirm "[red]Do you really want to restart the CSE?[/]" "[red]CSE Restart[/]" "Restart" )
  	()
	((print "User cancelled CSE restart")
	 (quit))))

(restart-cse)

(print "CSE Restart Initiated")
(if (runs-in-tui)
  (tui-notify "CSE Restart Initiated" "CSE Restart" "warning"))

