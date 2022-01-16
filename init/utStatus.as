#
#	utReset.as
#
#	This script returns the CSE's runtime status
#
@name status
@description Return the CSE status
@usage status
@uppertester

if ${argc} > 0
	error "status" command has no arguments
	quit
endif

quit ${cseStatus}