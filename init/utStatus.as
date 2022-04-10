#
#	utStatus.as
#
#	This script returns the CSE's runtime status
#
@name status
@description Return the CSE status
@usage status
@uppertester

if [> [argc] 0]
	quitWithError \"status" command has no arguments
endif

quit [cseStatus]