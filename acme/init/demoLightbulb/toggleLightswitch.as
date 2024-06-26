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

@name Toggle Lightswitch
@category Lightbulb Demo
@tuiTool
@description This page is used to toggle the status of the *Lightswitch* from **on** to **off** and vice versa. This will also create a *Notification* that is send to the subscribed *Lightbulb*.\nPress the **Toggle Lightswitch** button to toggle the *Lightswitch* status.\nSwitch to the *Lightbulb* tool to see the effect.\n\n
@tuiExecuteButton Toggle Lightswitch
@tuiAutoRun
@onKey 8



;; Include some helper functions
(include-script "functions")


(setq on "
     ┏━━━━━━━━━━━━━━━┓
     ┃       [green1]■[/green1]       ┃
     ┃     ┏━━━┓     ┃
     ┃     ┃   ┃     ┃
     ┃     ┃   ┃     ┃
     ┃  ┏━━┻━━━┻━━┓  ┃
     ┃  ┃   ON    ┃  ┃
     ┃  ┗━━━━━━━━━┛  ┃
     ┃               ┃
     ┃               ┃
     ┃               ┃
     ┃       [green1]■[/green1]       ┃
     ┗━━━━━━━━━━━━━━━┛
")

(setq off "
     ┏━━━━━━━━━━━━━━━┓
     ┃       [red]▢[/red]       ┃
     ┃               ┃
     ┃               ┃
     ┃               ┃
     ┃  ┏━━━━━━━━━┓  ┃
     ┃  ┃   OFF   ┃  ┃
     ┃  ┗━━┳━━━┳━━┛  ┃
     ┃     ┃   ┃     ┃
     ┃     ┃   ┃     ┃
     ┃     ┗━━━┛     ┃
     ┃       [red]▢[/red]       ┃
     ┗━━━━━━━━━━━━━━━┛
")

;; Define the lightswitch status retrieval function.
;; This function tries to retrieve the current status from the storage first. If it is not available, it retrieves the latest
;; ContentInstance from the CSE. The fallback is always "off".
;; We could retrieve the current status from the CSE directly, but this would require a GET request to the CSE for every
;; status change. To emulate a real device, we use the storage here.
(defun get-lightswitch-status ()
  ((if (has-storage "lightswitchDemo" "status")
     ;; If the status is available in the storage, retrieve it from there
     (get-storage "lightswitchDemo" "status")
     ;; If the status is not available in the storage, retrieve it from the CSE
     ((setq response (retrieve-resource "CDemoLightswitch" "${get-config \"cse.resourceName\"}/CDemoLightswitch/switchContainer/la"))
	  ;; 
      (if (== (get-response-status response) 2000)
	    ;; If the retrieval was successful, retrieve the status from the ContentInstance
        ((setq cin (get-response-resource response))
         (if (has-json-attribute cin "m2m:cin/con")
           (get-json-attribute cin "m2m:cin/con")))
		;; If the retrieval was not successful, return "off"
        "off")) )))	;; Fallback is always off for all errors


(defun print-lightswitch (st)
  ;; Clear the console
  ((clear-console)
   ;; Print the lightswitch status as ASCII art. Transform the value of "st" to a symbol,
   ;; ie. the value "on" or "off", evaluate it as a symbol (ie as a variable) and print its value.
   (print (eval (to-symbol st)))))


;; Define the lightswitch status setting function.
;; This function sets the lightswitch status in the storage and creates a new ContentInstance in the CSE.
(defun set-lightswitch-status (st)
  ((print-lightswitch st)
   ;; Create a new ContentInstance in the CSE
   (create-resource "CDemoLightswitch" "${get-config \"cse.resourceName\"}/CDemoLightswitch/switchContainer" 
      { "m2m:cin": {
          "con" : "${st}"
      }})
   ;; Store the lightswitch status in the internal storage
   (put-storage "lightswitchDemo" "status" st)))


;; Check if this script is executed by the autorun mechanism. If so, just set the lightswitch status and quit.
(if (is-defined 'tui.autorun)
  (if tui.autorun
    ((print-lightswitch get-lightswitch-status)
     (quit))))


;; Toggle the lightswitch status
(set-lightswitch-status 
	(case get-lightswitch-status
	  ("on"   "off")
	  ("off"  "on")))
