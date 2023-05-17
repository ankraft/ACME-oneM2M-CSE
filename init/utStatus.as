;;
;;	utStatus.as
;;
;;	This script returns the CSE's runtime status
;;

@name status
@description Return the CSE status
@usage status
@uppertester
@category CSE Operation

(if (> argc 1)
	(quit-with-error "\"status\" script has no arguments"))
	
(quit (cse-status))
