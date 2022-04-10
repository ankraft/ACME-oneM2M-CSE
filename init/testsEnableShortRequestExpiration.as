
#
#	testEnableShortRequestExpiration.as
#
#	This script is supposed to be called by the test system via the upper tester interface
#

@name enableShortRequestExpiration
@description (Tests) Enable shorter request expirations
@usage enableShortRequestExpiration <seconds>
@uppertester

if [!= [argc] 1]
	logError Wrong number of arguments: enableShortRequestExpiration <expirationTimeout>
	quitWithError
endif

##################################################################

# Store and then set the CSE's request expiration timeout 
storagePut cse.requestExpirationDelta [cse.requestExpirationDelta]
setConfig cse.requestExpirationDelta [argv 1]

quit [storageGet cse.requestExpirationDelta]