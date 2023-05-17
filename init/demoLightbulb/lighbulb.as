;;
;;	lightbulb.as
;;
;;	Implementation of a Lightbulb for the Lightbulb Demo
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script is executed whenever a notification is received when the lightswitch changes its state.
;;

@name Lightbulb
@category Lightbulb Demo
@tuiTool
@onNotification acme://demo-lightbulb/lightswitch
@description # Lightbulb Demo - Lightbulb\n\nThis page displays the status of the lightbulb.\n\nThe state changes automatically when notifications from the lightswitch are received.\n\nPress the *Refresh* button to refresh the status manually.
@tuiExecuteButton Refresh


;; Check if the CSE is running and quit if not.
;;	Prevents the script from running when the CSE is starting or restarting.
(if (!= (cse-status) "RUNNING")
	(quit "CSE not running"))

;; Include some helper functions
(include-script "functions")

;; Define the lightswitch status retrieval function.
;; This function retrieves the latest ContentInstance wih the content attribute indicating the lightswitch status.
(defun get-lightswitch-status ()
	(	(setq response (retrieve-resource "CDemoLightbulb" "${(get-config \"cse.resourceName\")}/CDemoLightswitch/switchContainer/la"))
		(if (== (get-response-status response) 2000)
			(	(setq cin (get-response-resource response))
				(if (has-json-attribute cin "m2m:cin/con")
					(get-json-attribute cin "m2m:cin/con")))
			("unknown"))))	;;Fallback is always off for all errors


;; Define the lightbulb printing function.
;; This function prints the lightbulb status to the console.
(defun print-light (state)
	(	(case state
			("on" (setq color "dark_green"))
			("off" (setq color "red"))
			(otherwise (setq color "yellow")))
		
		;; Different output for TUI and console
		(if (runs-in-tui)			
			(	(clear-console)
				(print "
[b]The lightbulb is [u]${(state)}[/u][/b]


       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
       [${(color)}]████████████████████[/${(color)}]
"))
			(	(print "The lightbulb status is ${(state)}")))))


;; Check if the notification contains the content attribute and print the lightbulb state if it does
(if (is-defined "notification.resource")

	(	;; Set the json path to the content attribute of the notification
		(setq contentPath "m2m:sgn/nev/rep/m2m:cin/con")

		;; Get the status change from the notification
		(if (has-json-attribute notification.resource contentPath)
			(print-light (get-json-attribute notification.resource contentPath))))

	;; Otherwise retrieve the status from the lightswitch directly
	;; This is only necessary if the script is executed manually
	( (print-light (get-lightswitch-status)	))) 

