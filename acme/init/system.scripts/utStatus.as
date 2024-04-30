;;
;;	utStatus.as
;;
;;	This script returns the CSE's runtime status
;;

@name Status
@description Print and return the CSE status.
@usage Status
@uppertester
@tuiTool
@tuiExecuteButton Get Status
@tuiAutoRun
@category CSE Operation

(if (> argc 1)
  (quit-with-error "\"Status\" script has no arguments"))
(print (cse-status))
	
(quit (cse-status))
