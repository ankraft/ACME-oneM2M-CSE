;;
;;	testDisableShortResourceExpiration.as
;;
;;	This script is supposed to be called by the test system via the upper tester interface
;;

@name disableShortResourceExpiration
@description (Tests) Disable shorter resource expirations
@usage disableShortResourceExpiration
@uppertester

(if (> argc 1)
	(	(log-error "Wrong number of arguments: disableShortResourceExpiration")
		(quit-with-error)))

(include-script "functions")

(restore-config-value "cse.checkExpirationsInterval")
(restore-config-value "resource.req.et")
