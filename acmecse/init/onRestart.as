;;
;;	onRestart.as
;;
;;	This script is executed during the restart of the CSE. It makes some checks and
;;  may create some resources if they are missing.
;;

@onRestart
@name onRestart
@description This script runs during the restart of the CSE
@hidden

(setq cse-originator (get-config "cse.originator"))

;;
;;	Update CSEBase with the triggerRecipientID and m2mExtID from the configuration file
;;

(let* 	(csebase 
			{ "m2m:cb": {
			}})
		(csebase (set-json-attribute csebase "m2m:cb/mei" (get-config "cse.m2mExtID")))
		(csebase (set-json-attribute csebase "m2m:cb/tri" (get-config "cse.triggerRecipientID"))))

(update-raw cse-originator (get-config "cse.resourceName") csebase)

(print "onRestart.as executed successfully")
