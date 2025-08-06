;;
;;	shutdown.as
;;
;;	This script initiates a CSE shutdown
;;
@name Shutdown
@description Initiate a shutdown of the CSE.\n# Be careful! This will shutdown the CSE and its services!
@tuiTool
@tuiExecuteButton Shutdown CSE
@category CSE Operation

(clear-console)
(print "[dodger_blue2]Shutting down the CSE[/]")

(if (runs-in-tui)
  (if (tui-confirm "[red]Do you really want to shut down the CSE?[/]" "[red]CSE Shutdown[/]" "Shutdown" )
  	()
	((print "User cancelled CSE shutdown")
	 (quit))))

(shutdown-cse)

(print "CSE Shutdown Initiated")
(if (runs-in-tui)
  (tui-notify "CSE Shutdown Initiated" "CSE Shutdown" "warning"))

