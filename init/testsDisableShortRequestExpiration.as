#
#	testDisableShortRequestExpiration.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name disableShortRequestExpiration
@usage (Tests) Disable shorter expirations: disableShortRequestExpiration
@uppertester

if ${argc} > 0
	error Wrong number of arguments: disableShortRequestExpiration
	quit
endif

##################################################################

# Restore the CSE's request expiration check
if ${storageHas cse.requestExpirationDelta}
	setConfig cse.requestExpirationDelta ${storageGet cse.requestExpirationDelta}
	storageRemove cse.requestExpirationDelta
endif

