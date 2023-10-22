;;
;;	testEnableShortResourceExpiration.as
;;
;;	This script is supposed to be called by the test system via the upper tester interface
;;

@name enableShortResourceExpiration
@description (Tests) Enable shorter resource expirations
@usage enableShortResourceExpiration <seconds>
@uppertester

(if (!= argc 2)
	( (log-error " Wrong number of arguments: enableShortResourceExpiration <expirationInterval>")
	  (quit-with-error)))

(include-script "functions")

(setq expIntervall 
	  (set-and-store-config-value "cse.checkExpirationsInterval" 
	  							  (to-number (argv 1))))
(set-and-store-config-value "resource.req.et" (to-number (argv 1)))

;; Return the original cse.checkExpirationsInterval and cse.maxExpirationDelta
(quit (. expIntervall 
		 "," 
		 (get-config "cse.maxExpirationDelta")))
