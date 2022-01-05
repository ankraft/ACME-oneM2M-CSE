
#
#	testEnableShortRequestExpiration.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name enableShortRequestExpiration
@usage (Tests) Enable shorter request expirations: enableShortRequestExpiration <seconds>
@uppertester

if ${argc} != 1
	error Wrong number of arguments: enableShortRequestExpiration <expirationTimeout>
	quit
endif

##################################################################

# Store and then set the CSE's request expiration timeout 
storagePut cse.requestExpirationDelta ${cse.requestExpirationDelta}
setConfig cse.requestExpirationDelta ${argv 1}

quit ${storageGet cse.requestExpirationDelta}