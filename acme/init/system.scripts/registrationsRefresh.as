;;
;;	registrationsRefresh.as
;;
;;	This script initiates a CSE reset
;;
@name Refresh Registrations
@description Check and refresh the registrations to the registrars
@tuiTool
@tuiExecuteButton Refresh Registrations
@onKey CTRL_R
@category CSE Operation

(clear-console)
(print "[dodger_blue2]Refreshing Registrations to Registrars[/]")

(if (runs-in-tui)
  (if (tui-confirm "Do you want to refresh the registrations to the registrars?" "CSE Registration Refresh" "Refresh" )
  	()
	((print "User cancelled registration refresh")
	 (quit))))

(refresh-registrations)

(print "Registration Refresh Initiated")
(if (runs-in-tui)
  (tui-notify "Registration Refresh Initiated" "CSE Registration Refresh"))

