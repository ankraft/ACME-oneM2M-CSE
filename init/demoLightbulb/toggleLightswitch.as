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
@description # Lightbulb Demo - Toggle Switch\n\nThis tool is used to toggle the status of the lightswitch from **on** to **off** and vice versa. This will also create a *Notification* that is send to the subscribed *Lightbulb*.\n\nPress the **Toggle** Button to toggle the lightswitch status.\n\nSwitch to the **Lightbulb** tool to see the effect.\n\n
@tuiExecuteButton Toggle

;; Include some helper functions
(include-script "functions")


;; Define the lightswitch status retrieval function.
;; This function retrieves the latest ContentInstance wih the content attribute indicating the lightswitch status.
(defun get-lightswitch-status ()
	(	(setq response (retrieve-resource "CDemoLightswitch" "${(get-config \"cse.resourceName\")}/CDemoLightswitch/switchContainer/la"))
		(if (== (get-response-status response) 2000)
			(	(setq cin (get-response-resource response))
				(if (has-json-attribute cin "m2m:cin/con")
					(get-json-attribute cin "m2m:cin/con")))
			("off"))))	;;Fallback is always off for all errors


(defun set-lightswitch-status (st)
	(	(create-resource "CDemoLightswitch" "${(get-config \"cse.resourceName\")}/CDemoLightswitch/switchContainer" 
			{ "m2m:cin": {
				"con" : "${(st)}"
			}})))


(case (get-lightswitch-status)
	("on" 	(	(set-lightswitch-status "off")
				(print "Toggle Lightswitch to [b u]off[/b u]")))
	("off"	(	(set-lightswitch-status "on")
				(print "Toggle Lightswitch to [b u]on[/b u]"))))