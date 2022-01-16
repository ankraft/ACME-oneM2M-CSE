#
#	utReset.as
#
#	This script returns the CSE's runtime status
#
@name status
@usage Return the CSE status: status
@uppertester

if ${argc} > 0
	error "status" command has no arguments
	quit
endif

quit ${cseStatus}