;;
;;	testDisableShortRequestExpiration.as
;;
;;	This script is supposed to be called by the test system via the upper tester interface
;;

@name disableShortRequestExpiration
@description (Tests) Disable shorter request expirations
@usage disableShortRequestExpiration
@uppertester

(if (> argc 1)
	(	(log-error "Wrong number of arguments: disableShortRequestExpiration")
		(quit-with-error)))

(include-script "functions")

(restore-config-value "cse.requestExpirationDelta")
