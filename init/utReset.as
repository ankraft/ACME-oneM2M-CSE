#
#	utReset.as
#
#	This script initiates a CSE reset
#
@name reset
@usage Initiate a CSE reset: reset
@uppertester

if ${argc} > 0
	error "reset" command has no arguments
	quit
endif

reset