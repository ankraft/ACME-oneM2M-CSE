;;
;;	testEnableShortRequestExpiration.as
;;
;;	This script is supposed to be called by the test system via the upper tester interface
;;

@name enableShortRequestExpiration
@description (Tests) Enable shorter request expirations
@usage enableShortRequestExpiration <seconds>
@uppertester

(if (!= argc 2)
	( (log-error "Wrong number of arguments: enableShortRequestExpiration <expirationTimeout>")
	  (quit-with-error)))

(include-script "functions")

;; Set a new value and return the original expiration delta
(quit 
	(set-and-store-config-value "cse.requestExpirationDelta" (to-number (argv 1))))
