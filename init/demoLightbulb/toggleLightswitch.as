;;
;;	toggleLightswitch.as
;;
;;	Implementation of a toggle lightswitch for the Lightbulb Demo
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script is execued by pressing the toggle button in the TUI.
;;

@category Lightbulb Demo
@name Toggle Lightswitch
@tuiTool
@description ## Lightbulb Demo - Toggle Switch\n\nThis page is used to toggle the status of the *Lightswitch* from **on** to **off** and vice versa. This will also create a *Notification* that is send to the subscribed *Lightbulb*.\nPress the **Toggle Lightswitch** button to toggle the *Lightswitch* status.\nSwitch to the *Lightbulb* tool to see the effect.\n\n
@tuiExecuteButton Toggle Lightswitch
@tuiAutoRun


;; Include some helper functions
(include-script "functions")


(setq on "
     ┌───────────────┐
     │       [green1]■[/green1]       │
     │     ┌───┐     │
     │     │   │     │
     │     │   │     │
     │  ┌──┴───┴──┐  │
     │  │   ON    │  │
     │  └─────────┘  │
     │               │
     │               │
     │               │
     │       [green1]■[/green1]       │
     └───────────────┘
")
(setq off "
     ┌───────────────┐
     │       [red]▢[/red]       │
     │               │
     │               │
     │               │
     │  ┌─────────┐  │
     │  │   OFF   │  │
     │  └──┬───┬──┘  │
     │     │   │     │
     │     │   │     │
     │     └───┘     │
     │       [red]▢[/red]       │
     └───────────────┘
")

;; Define the lightswitch status retrieval function.
;; This function retrieves the latest ContentInstance wih the content attribute indicating the lightswitch status.
(defun get-lightswitch-status ()
	(	(setq response (retrieve-resource "CDemoLightswitch" "${(get-config \"cse.resourceName\")}/CDemoLightswitch/switchContainer/la"))
		(if (== (get-response-status response) 2000)
			(	(setq cin (get-response-resource response))
				(if (has-json-attribute cin "m2m:cin/con")
					(get-json-attribute cin "m2m:cin/con")))
			("off"))))	;;Fallback is always off for all errors


(defun print-lightswitch (st)
	(	(clear-console)
		(case (st)
			("on" 	(print "${(on)}"))
			("off"	(print "${(off)}")))))


(defun set-lightswitch-status (st)
	(	(print-lightswitch st)
		(create-resource "CDemoLightswitch" "${(get-config \"cse.resourceName\")}/CDemoLightswitch/switchContainer" 
			{ "m2m:cin": {
				"con" : "${(st)}"
			}})))


;; Check if this script is executed by the autorun mechanism. If so, just set the lightswitch status and quit.
(if (is-defined 'is-autorun)
	(if (== is-autorun true)
		(	(print-lightswitch (get-lightswitch-status))
			(quit))))


;; Toggle the lightswitch status
(case (get-lightswitch-status)
	("on" 	(set-lightswitch-status "off"))
	("off"	(set-lightswitch-status "on")))
